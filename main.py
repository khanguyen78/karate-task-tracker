from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import sqlite3
import csv
import io
import os
from pathlib import Path

app = FastAPI()

Path("static").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_PATH = os.getenv('DATABASE_PATH', 'data/karate_tracker.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  description TEXT,
                  estimated_time INTEGER,
                  difficulty_weight REAL DEFAULT 1.0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
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
                  FOREIGN KEY (student_id) REFERENCES students(id),
                  FOREIGN KEY (task_id) REFERENCES tasks(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS active_sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  student_id INTEGER,
                  task_id INTEGER,
                  start_time TIMESTAMP,
                  FOREIGN KEY (student_id) REFERENCES students(id),
                  FOREIGN KEY (task_id) REFERENCES tasks(id))''')
    
    conn.commit()
    conn.close()

init_db()

def clean_csv_value(value: str) -> str:
    if not value:
        return ""
    cleaned = value.strip().replace('\n', ' ').replace('\r', '')
    return cleaned[:500]

def calculate_difficulty_weight(estimated_time: int) -> float:
    if estimated_time <= 5:
        return 0.5
    elif estimated_time <= 15:
        return 1.0
    elif estimated_time <= 30:
        return 1.5
    else:
        return 2.0

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
    except sqlite3.IntegrityError:
        c.execute("SELECT id FROM students WHERE name = ?", (name,))
        student_id = c.fetchone()[0]
    
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
        raise HTTPException(404, "Student not found")
    
    c.execute("SELECT id, title, description, estimated_time, difficulty_weight FROM tasks")
    tasks = [{"id": row[0], "title": row[1], "description": row[2], 
              "estimated_time": row[3], "difficulty_weight": row[4]} for row in c.fetchall()]
    
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
        raise HTTPException(400, "Please upload a CSV file")
    
    contents = await file.read()
    csv_file = io.StringIO(contents.decode('utf-8'))
    reader = csv.DictReader(csv_file)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    tasks_added = 0
    for row in reader:
        title = clean_csv_value(row.get('task', ''))
        description = clean_csv_value(row.get('description', ''))
        
        time_str = clean_csv_value(row.get('estimated_time', '0'))
        try:
            estimated_time = int(''.join(filter(str.isdigit, time_str)))
        except:
            estimated_time = 15
        
        if title:
            difficulty = calculate_difficulty_weight(estimated_time)
            c.execute('''INSERT INTO tasks (title, description, estimated_time, difficulty_weight)
                         VALUES (?, ?, ?, ?)''', (title, description, estimated_time, difficulty))
            tasks_added += 1
    
    conn.commit()
    conn.close()
    
    return {"success": True, "tasks_added": tasks_added}

@app.post("/task/start/{student_id}/{task_id}")
async def start_task(student_id: int, task_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id FROM active_sessions WHERE student_id = ?", (student_id,))
    if c.fetchone():
        conn.close()
        raise HTTPException(400, "Please finish your current task first!")
    
    start_time = datetime.now().isoformat()
    c.execute('''INSERT INTO active_sessions (student_id, task_id, start_time)
                 VALUES (?, ?, ?)''', (student_id, task_id, start_time))
    
    conn.commit()
    conn.close()
    
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
        raise HTTPException(400, "No active task found")
    
    session_id, task_id, start_time, estimated_time, difficulty = session
    
    start = datetime.fromisoformat(start_time)
    end = datetime.now()
    actual_time = int((end - start).total_seconds())
    
    focus_score = calculate_focus_score(estimated_time * 60, actual_time)
    impact_score = calculate_impact_score(difficulty, focus_score)
    
    c.execute('''INSERT INTO task_completions 
                 (student_id, task_id, start_time, end_time, actual_time, focus_score, impact_score)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (student_id, task_id, start_time, end.isoformat(), actual_time, 
               focus_score, impact_score))
    
    c.execute("DELETE FROM active_sessions WHERE id = ?", (session_id,))
    
    conn.commit()
    conn.close()
    
    minutes = actual_time // 60
    seconds = actual_time % 60
    time_display = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
    
    return {
        "success": True,
        "actual_time": actual_time,
        "time_display": time_display,
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
        return {"success": True, "message": "Task cancelled"}
    else:
        raise HTTPException(400, "No active task to cancel")

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
                        tc.focus_score, tc.impact_score, tc.completed_at
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
        
        minutes = actual_seconds // 60
        seconds = actual_seconds % 60
        
        completions.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "estimated_time": row[3],
            "actual_time_display": f"{minutes}m {seconds}s",
            "actual_time": actual_seconds,
            "focus_score": round(row[5], 2),
            "impact_score": round(row[6], 2),
            "completed_at": row[7]
        })
    
    count = len(completions)
    avg_focus = round(total_focus / count, 2) if count > 0 else 0
    
    total_minutes = total_time // 60
    total_hours = total_minutes // 60
    remaining_minutes = total_minutes % 60
    
    streak = get_student_streak(student_id)
    
    conn.close()
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "student_id": student_id,
        "student_name": student[0],
        "completions": completions,
        "total_tasks": count,
        "total_time_display": f"{total_hours}h {remaining_minutes}m" if total_hours > 0 else f"{remaining_minutes}m",
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
    
    c.execute("DELETE FROM task_completions WHERE student_id = ?", (student_id,))
    completions_deleted = c.rowcount
    
    c.execute("DELETE FROM active_sessions WHERE student_id = ?", (student_id,))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "completions_deleted": completions_deleted,
        "message": "All session data has been reset"
    }

@app.post("/tasks/clear")
async def clear_all_tasks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("DELETE FROM task_completions")
    completions_deleted = c.rowcount
    
    c.execute("DELETE FROM active_sessions")
    
    c.execute("DELETE FROM tasks")
    tasks_deleted = c.rowcount
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "tasks_deleted": tasks_deleted,
        "completions_deleted": completions_deleted,
        "message": "All tasks and related data have been cleared"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
