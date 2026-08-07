from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import sqlite3
import csv
import io
import os
import json
import logging
import logging.handlers
import uuid
from pathlib import Path

app = FastAPI()

Path("static").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_PATH = os.getenv('DATABASE_PATH', 'data/karate_tracker.db')

LOG_ENABLED = os.getenv('LOG_ENABLED', 'false').lower() == 'true'
LOG_LEVEL_STR = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_PATH = os.getenv('LOG_PATH', '/var/log')

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}
LOG_LEVEL = LOG_LEVELS.get(LOG_LEVEL_STR, logging.INFO)

logger = logging.getLogger('karate_tracker')
logger.setLevel(LOG_LEVEL)

if LOG_ENABLED:
    log_dir = Path(LOG_PATH)
    log_file = log_dir / 'karate_tracker.log'
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        file_handler.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        logging.basicConfig(level=LOG_LEVEL)
else:
    logger.addHandler(logging.NullHandler())


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  student_id INTEGER,
                  title TEXT NOT NULL,
                  description TEXT,
                  estimated_time INTEGER,
                  difficulty_weight REAL DEFAULT 1.0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  archived INTEGER DEFAULT 0,
                  FOREIGN KEY (student_id) REFERENCES students(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS task_completions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  student_id INTEGER,
                  task_id INTEGER,
                  session_id TEXT,
                  start_time TIMESTAMP,
                  end_time TIMESTAMP,
                  actual_time INTEGER,
                  focus_score REAL,
                  impact_score REAL,
                  status_color TEXT DEFAULT 'green',
                  completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  completed INTEGER DEFAULT 1,
                  FOREIGN KEY (student_id) REFERENCES students(id),
                  FOREIGN KEY (task_id) REFERENCES tasks(id))''')

    try:
        c.execute("ALTER TABLE task_completions ADD COLUMN status_color TEXT DEFAULT 'green'")
    except Exception:
        pass

    try:
        c.execute("ALTER TABLE task_completions ADD COLUMN session_id TEXT")
    except Exception:
        pass
    
    conn.commit()
    conn.close()

init_db()


def clean_csv_value(value: str) -> str:
    if not value:
        return ""
    cleaned = value.strip().replace('\n', ' ').replace('\r', '')
    return cleaned[:500]


def auto_detect_icon(title: str, custom_icon: str = "") -> str:
    if custom_icon:
        return custom_icon
    t = title.lower()
    if 'kick' in t or 'geri' in t: return '🦵'
    if 'punch' in t or 'zuki' in t or 'strike' in t or 'bag' in t: return '🥊'
    if 'plank' in t or 'hold' in t or 'stretch' in t: return '🧘'
    if 'break' in t or 'water' in t or 'rest' in t: return '💧'
    if 'kata' in t or 'form' in t or 'karate' in t: return '🥋'
    if 'warm' in t or 'jump' in t or 'run' in t: return '⏱️'
    return '🥋'


def calculate_difficulty_weight(estimated_time: int) -> float:
    if estimated_time <= 300:
        return 0.5
    elif estimated_time <= 900:
        return 1.0
    elif estimated_time <= 1800:
        return 1.5
    else:
        return 2.0


DIFFICULTY_MAP = {
    'easy': 0.5, 'medium': 1.0, 'hard': 1.5, 'expert': 2.0,
    '0.5': 0.5, '1.0': 1.0, '1.5': 1.5, '2.0': 2.0,
}


def parse_difficulty(value: str, estimated_time: int) -> float:
    if not value:
        return calculate_difficulty_weight(estimated_time)
    normalized = value.strip().lower()
    return DIFFICULTY_MAP.get(normalized, calculate_difficulty_weight(estimated_time))


def calculate_focus_score(estimated: int, actual: int) -> float:
    if estimated == 0:
        return 1.0
    ratio = actual / estimated
    if ratio <= 1.0:
        return min(1.0, 2.0 - ratio)
    else:
        return max(0.1, 1.0 / ratio)


def calculate_impact_score(difficulty: float, focus: float) -> float:
    return (difficulty * 0.4 + focus * 0.6) * 10


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM students ORDER BY created_at DESC")
    students = [{"id": row[0], "name": row[1]} for row in c.fetchall()]
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "students": students})


@app.post("/session/create")
async def create_session(
    names: str = Form(...), 
    show_timer: bool = Form(False),
    auto_advance: bool = Form(False),
    enable_chime: bool = Form(False),
    file: UploadFile = File(None)
):
    raw_names = [clean_csv_value(n).title() for n in names.split(",") if clean_csv_value(n)]
    if not raw_names:
        raise HTTPException(400, "Please enter at least one valid student name.")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    student_ids = []

    for name in raw_names:
        c.execute("SELECT id FROM students WHERE name = ? COLLATE NOCASE", (name,))
        row = c.fetchone()
        if row:
            student_ids.append(row[0])
        else:
            c.execute("INSERT INTO students (name) VALUES (?)", (name,))
            student_ids.append(c.lastrowid)

    if file and file.filename:
        contents = await file.read()
        if contents:
            csv_file = io.StringIO(contents.decode('utf-8'))
            reader = csv.DictReader(csv_file)

            incoming = []
            for row in reader:
                title = clean_csv_value(row.get('task', ''))
                if not title:
                    continue
                description = clean_csv_value(row.get('description', ''))
                time_str = clean_csv_value(row.get('estimated_time', ''))
                diff_str = clean_csv_value(row.get('difficulty', '')).lower()
                icon_str = clean_csv_value(row.get('icon', ''))
                
                try:
                    estimated_time = int(''.join(filter(str.isdigit, time_str))) if time_str else 900
                except Exception:
                    estimated_time = 900

                is_countup = 'countup' in diff_str or 'up' in diff_str or 'plank' in title.lower() or 'hold' in title.lower() or 'break' in title.lower() or 'rest' in title.lower()
                difficulty = 0.0 if is_countup else parse_difficulty(diff_str, estimated_time)
                
                incoming.append((title, description, estimated_time, difficulty, icon_str))

            for sid in student_ids:
                c.execute("UPDATE tasks SET archived = 1 WHERE student_id = ?", (sid,))
                for title, description, estimated_time, difficulty, icon_str in incoming:
                    c.execute('''INSERT INTO tasks (student_id, title, description, estimated_time, difficulty_weight, archived)
                                 VALUES (?, ?, ?, ?, ?, 0)''',
                              (sid, title, description, estimated_time, difficulty))

    conn.commit()
    conn.close()

    session_id = str(uuid.uuid4())[:8]
    ids_param = ",".join(str(i) for i in student_ids)
    hide_timer = not show_timer
    timer_flag = "1" if hide_timer else "0"
    advance_flag = "1" if auto_advance else "0"
    chime_flag = "1" if enable_chime else "0"
    
    return RedirectResponse(f"/session/dashboard?ids={ids_param}&hide_timer={timer_flag}&auto_advance={advance_flag}&enable_chime={chime_flag}&session_id={session_id}", status_code=303)


@app.post("/session/add-student")
async def add_student_mid_session(name: str = Form(...)):
    clean_name = clean_csv_value(name).title()
    if not clean_name:
        raise HTTPException(400, "Name cannot be empty.")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id, name FROM students WHERE name = ? COLLATE NOCASE", (clean_name,))
    row = c.fetchone()
    if row:
        student_id, student_name = row[0], row[1]
    else:
        c.execute("INSERT INTO students (name) VALUES (?)", (clean_name,))
        student_id, student_name = c.lastrowid, clean_name

    conn.commit()
    conn.close()

    return {"success": True, "student": {"id": student_id, "name": student_name}}


@app.get("/session/dashboard", response_class=HTMLResponse)
async def session_dashboard(request: Request, ids: str, hide_timer: str = "1", auto_advance: str = "0", enable_chime: str = "0", session_id: str = "default"):
    student_ids = [int(i) for i in ids.split(",") if i.isdigit()]
    if not student_ids:
        raise HTTPException(400, "No valid students specified.")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    placeholders = ",".join("?" for _ in student_ids)
    c.execute(f"SELECT id, name FROM students WHERE id IN ({placeholders})", student_ids)
    students = [{"id": row[0], "name": row[1]} for row in c.fetchall()]

    c.execute(f"""SELECT DISTINCT title, description, estimated_time, difficulty_weight 
                 FROM tasks 
                 WHERE student_id IN ({placeholders}) AND archived = 0 
                 ORDER BY id""", student_ids)
    raw_tasks = c.fetchall()

    tasks = []
    for idx, row in enumerate(raw_tasks):
        title = row[0]
        diff_weight = row[3]
        is_countup = diff_weight == 0.0 or 'plank' in title.lower() or 'hold' in title.lower() or 'countup' in title.lower() or 'break' in title.lower() or 'rest' in title.lower()
        
        tasks.append({
            "id": idx + 1,
            "title": title,
            "description": row[1] or "",
            "estimated_time": row[2],
            "difficulty_weight": diff_weight,
            "is_countup": is_countup,
            "icon": auto_detect_icon(title)
        })

    conn.close()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "students": students,
        "student_ids_str": ids,
        "session_id": session_id,
        "tasks": tasks,
        "hide_timer": hide_timer == "1",
        "auto_advance": auto_advance == "1",
        "enable_chime": enable_chime == "1"
    })


@app.post("/task/record-completion")
async def record_completion(
    student_id: int = Form(...),
    task_title: str = Form(...),
    actual_time: int = Form(...),
    estimated_time: int = Form(...),
    status_color: str = Form("green"),
    session_id: str = Form("default")
):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id, difficulty_weight FROM tasks WHERE student_id = ? AND title = ? AND archived = 0", (student_id, task_title))
    task_row = c.fetchone()
    
    difficulty = task_row[1] if task_row else calculate_difficulty_weight(estimated_time)
    task_id = task_row[0] if task_row else None

    focus_score = calculate_focus_score(estimated_time, actual_time)
    impact_score = calculate_impact_score(difficulty, focus_score)

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO task_completions 
                 (student_id, task_id, session_id, start_time, end_time, actual_time, focus_score, impact_score, status_color, completed_at, completed)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)''',
              (student_id, task_id, session_id, now_iso, now_iso, actual_time, focus_score, impact_score, status_color, now_iso))

    conn.commit()
    conn.close()
    return {"success": True, "student_id": student_id, "actual_time": actual_time, "status_color": status_color}


@app.get("/session/summary")
async def session_summary(
    ids: str,
    client_date: str = None,
    client_time: str = None,
    session_id: str = None
):
    student_ids = [int(i) for i in ids.split(",") if i.isdigit()]
    if not student_ids:
        raise HTTPException(400, "No valid students provided")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    summary_data = []

    if client_date and client_time:
        formatted_date = client_date
        formatted_time = client_time
    else:
        now = datetime.now()
        formatted_date = now.strftime("%A, %B %d, %Y")
        formatted_time = now.strftime("%I:%M %p")

    for sid in student_ids:
        c.execute("SELECT name FROM students WHERE id = ?", (sid,))
        s_row = c.fetchone()
        name = s_row[0] if s_row else f"Student #{sid}"

        if session_id:
            c.execute("""SELECT tc.actual_time, COALESCE(tc.status_color, 'green'), COALESCE(t.title, 'Group Task')
                         FROM task_completions tc
                         LEFT JOIN tasks t ON tc.task_id = t.id
                         WHERE tc.student_id = ? AND tc.session_id = ?
                         ORDER BY tc.id ASC""", (sid, session_id))
            rows = c.fetchall()
        else:
            c.execute("""SELECT tc.actual_time, COALESCE(tc.status_color, 'green'), COALESCE(t.title, 'Group Task')
                         FROM task_completions tc
                         LEFT JOIN tasks t ON tc.task_id = t.id
                         WHERE tc.student_id = ?
                         ORDER BY tc.id DESC LIMIT 15""", (sid,))
            rows = c.fetchall()
            rows.reverse()

        total_time = sum(r[0] for r in rows)
        total_tasks = len(rows)
        green_count = sum(1 for r in rows if r[1] == 'green')
        yellow_count = sum(1 for r in rows if r[1] == 'yellow')
        blue_count = sum(1 for r in rows if r[1] == 'blue')

        tasks_details = [
            {"title": r[2], "actual_time": r[0], "status": r[1]}
            for r in rows
        ]

        summary_data.append({
            "student_id": sid,
            "name": name,
            "total_tasks": total_tasks,
            "total_time": total_time,
            "green_count": green_count,
            "yellow_count": yellow_count,
            "blue_count": blue_count,
            "tasks_details": tasks_details
        })

    conn.close()
    return {
        "date": formatted_date,
        "time": formatted_time,
        "summary": summary_data
    }


# --- ADMIN CONTROL PANEL ROUTES ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT s.id, s.name,
                        COUNT(tc.id) as total_completions,
                        MAX(tc.completed_at) as last_active
                 FROM students s
                 LEFT JOIN task_completions tc ON tc.student_id = s.id
                 GROUP BY s.id
                 ORDER BY last_active DESC, s.name ASC''')
    students_raw = c.fetchall()
    
    students = []
    for row in students_raw:
        students.append({
            "id": row[0],
            "name": row[1],
            "total_completions": row[2],
            "last_active": row[3] if row[3] else "Never"
        })
        
    conn.close()
    return templates.TemplateResponse("admin.html", {"request": request, "students": students})


@app.get("/admin/student/{student_id}/history")
async def admin_student_history(student_id: int, date: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT name FROM students WHERE id = ?", (student_id,))
    s_row = c.fetchone()
    if not s_row:
        conn.close()
        raise HTTPException(404, "Student not found")

    student_name = s_row[0]

    if date:
        date_pattern = f"{date}%"
        c.execute('''SELECT tc.id, tc.session_id, COALESCE(t.title, 'Group Drill') as title, 
                            tc.actual_time, COALESCE(tc.status_color, 'green'), tc.completed_at
                     FROM task_completions tc
                     LEFT JOIN tasks t ON tc.task_id = t.id
                     WHERE tc.student_id = ? AND tc.completed_at LIKE ?
                     ORDER BY tc.completed_at DESC, tc.id DESC''', (student_id, date_pattern))
    else:
        c.execute('''SELECT tc.id, tc.session_id, COALESCE(t.title, 'Group Drill') as title, 
                            tc.actual_time, COALESCE(tc.status_color, 'green'), tc.completed_at
                     FROM task_completions tc
                     LEFT JOIN tasks t ON tc.task_id = t.id
                     WHERE tc.student_id = ?
                     ORDER BY tc.completed_at DESC, tc.id DESC''', (student_id,))

    rows = c.fetchall()
    conn.close()

    sessions = {}
    for r in rows:
        raw_time = r[5]
        date_key = raw_time[:10] if raw_time and len(raw_time) >= 10 else "Older Records"
        
        if date_key not in sessions:
            sessions[date_key] = []
            
        sessions[date_key].append({
            "id": r[0],
            "session_id": r[1] or "N/A",
            "title": r[2],
            "actual_time": r[3],
            "status_color": r[4],
            "completed_at": r[5]
        })

    return {
        "student_id": student_id,
        "student_name": student_name,
        "sessions": sessions
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
