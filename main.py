from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import sqlite3
import csv
import io
import os
import logging
import logging.handlers
from pathlib import Path

app = FastAPI()

Path("static").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_PATH = os.getenv('DATABASE_PATH', 'data/karate_tracker.db')

# --- Logging configuration ---
# LOG_ENABLED: set to "true" to enable file logging (default: false)
# LOG_LEVEL:   DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
# LOG_PATH:    directory to write karate_tracker.log (default: /var/log)

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
        logger.info(f"Logging initialized — level={LOG_LEVEL_STR}, file={log_file}")
    except PermissionError:
        logging.basicConfig(level=LOG_LEVEL)
        logger.warning(
            f"Cannot write to {log_file} (permission denied). Falling back to stderr."
        )
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
                  FOREIGN KEY (student_id) REFERENCES students(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS task_completions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  student_id INTEGER,
                  task_id INTEGER,
                  start_time TIMESTAMP,
                  end_time TIMESTAMP,
                  actual_time INTEGER,
                  focus_score REAL,
                  impact_score REAL,
                  completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  completed INTEGER DEFAULT 1,
                  FOREIGN KEY (student_id) REFERENCES students(id),
                  FOREIGN KEY (task_id) REFERENCES tasks(id))''')
    # Migrate: add completed column if missing
    try:
        c.execute("ALTER TABLE task_completions ADD COLUMN completed INTEGER DEFAULT 1")
    except Exception:
        pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS active_sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  student_id INTEGER,
                  task_id INTEGER,
                  start_time TIMESTAMP,
                  FOREIGN KEY (student_id) REFERENCES students(id),
                  FOREIGN KEY (task_id) REFERENCES tasks(id))''')
    
    conn.commit()
    conn.close()

# Migrate existing tasks table if it lacks student_id column
def migrate_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info(tasks)")
    columns = [row[1] for row in c.fetchall()]
    if 'student_id' not in columns:
        c.execute("ALTER TABLE tasks ADD COLUMN student_id INTEGER REFERENCES students(id)")
        conn.commit()
    conn.close()

init_db()
migrate_db()

def clean_csv_value(value: str) -> str:
    if not value:
        return ""
    cleaned = value.strip().replace('\n', ' ').replace('\r', '')
    return cleaned[:500]

def calculate_difficulty_weight(estimated_time: int) -> float:
    """estimated_time is in seconds"""
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
    """Parse difficulty from CSV field, fall back to time-based if blank/invalid."""
    if not value:
        return calculate_difficulty_weight(estimated_time)
    normalized = value.strip().lower()
    if normalized in DIFFICULTY_MAP:
        return DIFFICULTY_MAP[normalized]
    return calculate_difficulty_weight(estimated_time)

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

def get_student_streak(student_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''SELECT DATE(completed_at) as date, COUNT(*) as count
                 FROM task_completions
                 WHERE student_id = ?
                 GROUP BY DATE(completed_at)
                 ORDER BY date DESC
                 LIMIT 30''', (student_id,))
    
    dates = c.fetchall()
    conn.close()
    
    if not dates:
        return 0
    
    streak = 0
    current_date = datetime.now().date()
    
    for date_str, count in dates:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if date == current_date or date == current_date - timedelta(days=streak):
            streak += 1
            current_date = date
        else:
            break
    
    return streak

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM students ORDER BY created_at DESC")
    students = [{"id": row[0], "name": row[1]} for row in c.fetchall()]
    conn.close()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "students": students
    })

@app.post("/student/create")
async def create_student(name: str = Form(...)):
    name = clean_csv_value(name)
    if not name or len(name) < 2:
        raise HTTPException(400, "Please enter a valid name (at least 2 characters)")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO students (name) VALUES (?)", (name,))
        conn.commit()
        student_id = c.lastrowid
        logger.info(f"New student created: '{name}' (id={student_id})")
    except sqlite3.IntegrityError:
        c.execute("SELECT id FROM students WHERE name = ?", (name,))
        student_id = c.fetchone()[0]
        logger.debug(f"Student '{name}' already exists (id={student_id}), redirecting")
    
    conn.close()
    return RedirectResponse(f"/student/{student_id}", status_code=303)

@app.get("/student/{student_id}", response_class=HTMLResponse)
async def student_dashboard(request: Request, student_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT name FROM students WHERE id = ?", (student_id,))
    student = c.fetchone()
    if not student:
        conn.close()
        logger.warning(f"Dashboard requested for unknown student_id={student_id}")
        raise HTTPException(404, "Student not found")
    
    logger.debug(f"Dashboard loaded for student '{student[0]}' (id={student_id})")
    
    c.execute("SELECT id, title, description, estimated_time, difficulty_weight FROM tasks WHERE student_id = ?", (student_id,))
    tasks = [{"id": row[0], "title": row[1], "description": row[2], 
              "estimated_time": row[3],
              "difficulty_weight": row[4]} for row in c.fetchall()]
    
    c.execute('''SELECT a.id, a.task_id, t.title, t.description, t.estimated_time, a.start_time
                 FROM active_sessions a
                 JOIN tasks t ON a.task_id = t.id
                 WHERE a.student_id = ?''', (student_id,))
    active = c.fetchone()
    active_session = None
    if active:
        start_time = datetime.fromisoformat(active[5])
        elapsed = int((datetime.now() - start_time).total_seconds())
        active_session = {
            "id": active[0],
            "task_id": active[1],
            "task_title": active[2],
            "task_description": active[3],
            "estimated_time": active[4],
            "start_time": active[5],
            "elapsed": elapsed
        }
    
    streak = get_student_streak(student_id)
    conn.close()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "student_id": student_id,
        "student_name": student[0],
        "tasks": tasks,
        "active_session": active_session,
        "streak": streak
    })

@app.post("/upload-tasks/{student_id}")
async def upload_tasks(student_id: int, file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        logger.warning(f"Student {student_id} attempted to upload non-CSV file: {file.filename}")
        raise HTTPException(400, "Please upload a CSV file")
    
    logger.info(f"Student {student_id} uploading task CSV: {file.filename}")
    
    contents = await file.read()
    csv_file = io.StringIO(contents.decode('utf-8'))
    reader = csv.DictReader(csv_file)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    tasks_added = 0
    for row in reader:
        title = clean_csv_value(row.get('task', ''))
        description = clean_csv_value(row.get('description', ''))
        
        time_str = clean_csv_value(row.get('estimated_time', ''))
        try:
            estimated_time = int(''.join(filter(str.isdigit, time_str))) if time_str else 900
        except:
            estimated_time = 900  # default 15 minutes in seconds
        
        if title:
            diff_str = clean_csv_value(row.get('difficulty', ''))
            difficulty = parse_difficulty(diff_str, estimated_time)
            c.execute('''INSERT INTO tasks (student_id, title, description, estimated_time, difficulty_weight)
                         VALUES (?, ?, ?, ?, ?)''', (student_id, title, description, estimated_time, difficulty))
            tasks_added += 1
    
    conn.commit()
    conn.close()
    
    logger.info(f"Student {student_id} CSV upload complete: {tasks_added} tasks added from '{file.filename}'")
    return {"success": True, "tasks_added": tasks_added}

@app.get("/tasks/export/{student_id}")
async def export_tasks(student_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT name FROM students WHERE id = ?", (student_id,))
    student = c.fetchone()
    if not student:
        conn.close()
        raise HTTPException(404, "Student not found")

    c.execute("SELECT title, description, estimated_time, difficulty_weight FROM tasks WHERE student_id = ? ORDER BY id", (student_id,))
    rows = c.fetchall()
    conn.close()

    weight_to_label = {0.5: 'easy', 1.0: 'medium', 1.5: 'hard', 2.0: 'expert'}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['task', 'description', 'estimated_time', 'difficulty'])
    for row in rows:
        writer.writerow([row[0], row[1] or '', row[2], weight_to_label.get(row[3], 'medium')])

    filename = f"{student[0].replace(' ', '_')}_tasks.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/task/start/{student_id}/{task_id}")
async def start_task(student_id: int, task_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id FROM active_sessions WHERE student_id = ?", (student_id,))
    if c.fetchone():
        conn.close()
        logger.warning(f"Student {student_id} tried to start task {task_id} but already has an active session")
        raise HTTPException(400, "Please finish your current task first!")
    
    start_time = datetime.now().isoformat()
    c.execute('''INSERT INTO active_sessions (student_id, task_id, start_time)
                 VALUES (?, ?, ?)''', (student_id, task_id, start_time))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Student {student_id} started task {task_id} at {start_time}")
    return {"success": True, "start_time": start_time}

@app.post("/task/finish/{student_id}")
async def finish_task(student_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''SELECT a.id, a.task_id, a.start_time, t.estimated_time, t.difficulty_weight
                 FROM active_sessions a
                 JOIN tasks t ON a.task_id = t.id
                 WHERE a.student_id = ?''', (student_id,))
    
    session = c.fetchone()
    if not session:
        conn.close()
        logger.warning(f"Student {student_id} tried to finish a task but has no active session")
        raise HTTPException(400, "No active task found")
    
    session_id, task_id, start_time, estimated_time, difficulty = session
    
    start = datetime.fromisoformat(start_time)
    end = datetime.now()
    actual_time = int((end - start).total_seconds())  # store as seconds

    focus_score = calculate_focus_score(estimated_time, actual_time)
    impact_score = calculate_impact_score(difficulty, focus_score)
    
    c.execute('''INSERT INTO task_completions 
                 (student_id, task_id, start_time, end_time, actual_time, focus_score, impact_score)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (student_id, task_id, start_time, end.isoformat(), actual_time, 
               focus_score, impact_score))
    
    c.execute("DELETE FROM active_sessions WHERE id = ?", (session_id,))
    
    conn.commit()
    conn.close()
    
    logger.info(
        f"Student {student_id} finished task {task_id}: "
        f"actual={actual_time}s, estimated={estimated_time}s, "
        f"focus={round(focus_score,2)}, impact={round(impact_score,2)}"
    )
    return {
        "success": True,
        "actual_time": actual_time,
        "time_display": f"{actual_time}s",
        "focus_score": round(focus_score, 2),
        "impact_score": round(impact_score, 2)
    }

@app.post("/task/cancel/{student_id}")
async def cancel_task(student_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("DELETE FROM active_sessions WHERE student_id = ?", (student_id,))
    deleted = c.rowcount
    
    conn.commit()
    conn.close()
    
    if deleted > 0:
        logger.info(f"Student {student_id} cancelled their active task")
        return {"success": True, "message": "Task cancelled"}
    else:
        logger.warning(f"Student {student_id} tried to cancel but had no active task")
        raise HTTPException(400, "No active task to cancel")

@app.post("/task/abandon/{student_id}")
async def abandon_task(student_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''SELECT a.id, a.task_id, a.start_time, t.estimated_time, t.difficulty_weight
                 FROM active_sessions a
                 JOIN tasks t ON a.task_id = t.id
                 WHERE a.student_id = ?''', (student_id,))
    session = c.fetchone()
    if not session:
        conn.close()
        raise HTTPException(400, "No active task found")

    session_id, task_id, start_time, estimated_time, difficulty = session
    start = datetime.fromisoformat(start_time)
    end = datetime.now()
    actual_time = int((end - start).total_seconds())

    focus_score = calculate_focus_score(estimated_time, actual_time)
    impact_score = calculate_impact_score(difficulty, focus_score)

    c.execute('''INSERT INTO task_completions
                 (student_id, task_id, start_time, end_time, actual_time, focus_score, impact_score, completed)
                 VALUES (?, ?, ?, ?, ?, ?, ?, 0)''',
              (student_id, task_id, start_time, end.isoformat(), actual_time, focus_score, impact_score))

    c.execute("DELETE FROM active_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

    logger.info(f"Student {student_id} abandoned task {task_id}: actual={actual_time}s (incomplete)")
    return {"success": True, "actual_time": actual_time}

@app.get("/results/{student_id}", response_class=HTMLResponse)
async def results(request: Request, student_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT name FROM students WHERE id = ?", (student_id,))
    student = c.fetchone()
    if not student:
        conn.close()
        raise HTTPException(404, "Student not found")
    
    c.execute('''SELECT tc.id, t.title, t.description, t.estimated_time, tc.actual_time,
                        tc.focus_score, tc.impact_score, tc.completed_at,
                        COALESCE(tc.completed, 1)
                 FROM task_completions tc
                 JOIN tasks t ON tc.task_id = t.id
                 WHERE tc.student_id = ?
                 ORDER BY tc.completed_at DESC''', (student_id,))
    
    completions = []
    total_time = 0
    total_focus = 0
    
    for row in c.fetchall():
        actual_seconds = row[4]
        total_time += actual_seconds
        total_focus += row[5]
        
        completions.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "estimated_time": row[3],
            "actual_time_display": f"{actual_seconds}s",
            "actual_time": actual_seconds,
            "focus_score": round(row[5], 2),
            "impact_score": round(row[6], 2),
            "completed_at": row[7],
            "completed": row[8]
        })
    
    count = len(completions)
    avg_focus = round(total_focus / count, 2) if count > 0 else 0
    
    streak = get_student_streak(student_id)
    
    conn.close()
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "student_id": student_id,
        "student_name": student[0],
        "completions": completions,
        "total_tasks": count,
        "total_time_display": f"{total_time}s",
        "avg_focus_score": avg_focus,
        "streak": streak
    })

@app.post("/student/{student_id}/reset")
async def reset_student_data(student_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id FROM students WHERE id = ?", (student_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(404, "Student not found")

    c.execute("DELETE FROM active_sessions WHERE student_id = ?", (student_id,))
    deleted = c.rowcount

    conn.commit()
    conn.close()

    logger.info(f"Student {student_id} active session reset (deleted={deleted})")
    return {"success": True, "message": "Active session cleared"}

@app.post("/tasks/clear")
async def clear_all_tasks(student_id: int = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("DELETE FROM task_completions WHERE student_id = ?", (student_id,))
    completions_deleted = c.rowcount

    c.execute("DELETE FROM active_sessions WHERE student_id = ?", (student_id,))

    c.execute("DELETE FROM tasks WHERE student_id = ?", (student_id,))
    tasks_deleted = c.rowcount

    c.execute("DELETE FROM students WHERE id = ?", (student_id,))

    conn.commit()
    conn.close()

    logger.info(f"Student {student_id} cleared their tasks and was removed: {tasks_deleted} tasks and {completions_deleted} completions deleted")
    return {
        "success": True,
        "tasks_deleted": tasks_deleted,
        "completions_deleted": completions_deleted,
        "message": "All tasks and related data have been cleared"
    }

@app.post("/tasks/clear/{student_id}")
async def clear_student_tasks(student_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("DELETE FROM task_completions WHERE student_id = ?", (student_id,))
    completions_deleted = c.rowcount
    
    c.execute("DELETE FROM active_sessions WHERE student_id = ?", (student_id,))
    
    c.execute("DELETE FROM tasks WHERE student_id = ?", (student_id,))
    tasks_deleted = c.rowcount
    
    conn.commit()
    conn.close()
    
    logger.info(f"Student {student_id} cleared all tasks: {tasks_deleted} tasks, {completions_deleted} completions deleted")
    return {
        "success": True,
        "tasks_deleted": tasks_deleted,
        "completions_deleted": completions_deleted,
        "message": "All tasks and related data have been cleared"
    }

@app.get("/task/{task_id}/edit", response_class=HTMLResponse)
async def edit_task_form(request: Request, task_id: int, student_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id, title, description, estimated_time, difficulty_weight FROM tasks WHERE id = ? AND student_id = ?", (task_id, student_id))
    task = c.fetchone()
    conn.close()

    if not task:
        raise HTTPException(404, "Task not found")

    difficulty_label = {0.5: 'easy', 1.0: 'medium', 1.5: 'hard', 2.0: 'expert'}.get(task[4], 'medium')

    return templates.TemplateResponse("edit_task.html", {
        "request": request,
        "student_id": student_id,
        "task": {
            "id": task[0],
            "title": task[1],
            "description": task[2],
            "estimated_time": task[3],
            "difficulty": difficulty_label
        }
    })

@app.post("/task/{task_id}/update")
async def update_task(
    task_id: int,
    student_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    estimated_time: int = Form(...),
    difficulty: str = Form("")
):
    title = clean_csv_value(title)
    description = clean_csv_value(description)

    if not title or len(title) < 2:
        raise HTTPException(400, "Title must be at least 2 characters")

    if estimated_time < 0:
        raise HTTPException(400, "Estimated time cannot be negative")

    difficulty_weight = parse_difficulty(difficulty, estimated_time)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''UPDATE tasks
                 SET title = ?, description = ?, estimated_time = ?, difficulty_weight = ?
                 WHERE id = ? AND student_id = ?''',
              (title, description, estimated_time, difficulty_weight, task_id, student_id))

    conn.commit()
    conn.close()

    logger.info(f"Student {student_id} updated task {task_id}: title='{title}', estimated_time={estimated_time}s, difficulty={difficulty_weight}")
    return {"success": True, "message": "Task updated successfully"}

@app.delete("/task/{task_id}")
async def delete_task(task_id: int, student_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if task has completions
    c.execute("SELECT COUNT(*) FROM task_completions WHERE task_id = ?", (task_id,))
    completion_count = c.fetchone()[0]
    
    # Delete task scoped to this student
    c.execute("DELETE FROM tasks WHERE id = ? AND student_id = ?", (task_id, student_id))
    deleted = c.rowcount
    
    # Delete any active sessions for this task
    c.execute("DELETE FROM active_sessions WHERE task_id = ? AND student_id = ?", (task_id, student_id))
    
    conn.commit()
    conn.close()
    
    if deleted > 0:
        logger.info(f"Student {student_id} deleted task {task_id} (had {completion_count} completions)")
        return {
            "success": True,
            "message": f"Task deleted (had {completion_count} completions in history)"
        }
    else:
        logger.warning(f"Student {student_id} tried to delete task {task_id} but it was not found")
        raise HTTPException(404, "Task not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
