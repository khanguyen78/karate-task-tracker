# 🥋 Karate Task Tracker

A web-based training task tracker built with FastAPI and SQLite. Students log in by name, upload a CSV task list, run timed drills, and review focus and impact scores.

---

## 🚀 Getting Started

### Requirements
- Python 3.9+
- FastAPI, Uvicorn, Jinja2, python-multipart

### Install & Run
```bash
pip install fastapi uvicorn jinja2 python-multipart
mkdir -p data
uvicorn main:app --reload
```

The app runs at `http://localhost:8000` by default.

### Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DATABASE_PATH` | `data/karate_tracker.db` | Path to the SQLite database file |
| `LOG_ENABLED` | `false` | Set to `true` to enable file logging |
| `LOG_LEVEL` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |
| `LOG_PATH` | `/var/log` | Directory for `karate_tracker.log` |

---

## 📁 File Structure

```
main.py                  # FastAPI backend
templates/
  index.html             # Home / login page
  dashboard.html         # Student task dashboard
  results.html           # Completion history & scores
  edit_task.html         # Edit a single task
  users.html             # Admin: all users, import/export
static/
  style.css              # Shared stylesheet
data/
  karate_tracker.db      # SQLite database (auto-created)
```

---

## 📄 CSV Format

Tasks are loaded from a CSV file with the following columns:

```
taskid,task,description,estimated_time,difficulty
1,Front Kick,Practice front kick technique,600,easy
2,Roundhouse Kick,Focus on hip rotation,900,medium
3,Kata Heian Shodan,Full kata run-throughs,1200,hard
4,Sparring Drills,Partner sparring combos,1800,expert
5,Cool Down Stretches,,300,
```

| Column | Required | Description |
|---|---|---|
| `taskid` | Recommended | Unique integer. Sets display order and is used to match tasks across uploads. |
| `task` | ✅ Yes | Task name (must be at least 2 characters). |
| `description` | No | Optional detail shown under the task name. |
| `estimated_time` | No | Time in **seconds**. Set to `0` for no countdown. Defaults to 900 if blank. |
| `difficulty` | No | `easy`, `medium`, `hard`, or `expert`. Auto-assigned by time if blank. |

### Difficulty Auto-Assignment (when blank)
| Estimated Time | Difficulty | Weight |
|---|---|---|
| Under 5 min (< 300s) | 🟢 Easy | 0.5 |
| 5–15 min (300–900s) | 🟡 Medium | 1.0 |
| 15–30 min (900–1800s) | 🟠 Hard | 1.5 |
| Over 30 min (> 1800s) | 🔴 Expert | 2.0 |

---

## 🕹️ Using the App

### Logging In
Enter your name on the home page and click **Start Training! 🚀**

- Names are **case-insensitive** and stored in title case (`john doe` → `John Doe`)
- If the name already exists, you go straight to your dashboard
- If the name is new, an account is created and you'll be prompted to upload a CSV

### Running Tasks
1. Upload your CSV — tasks appear in `taskid` order
2. Click **🚀 Start** on any task, or **▶️ Begin All Tasks** to run them in sequence
3. The timer counts down from the estimated time
4. When it hits zero, a sound plays and it counts **up** in red (overtime)
5. Click **✅ Finished!** when done — time is recorded and the next task starts automatically

### No-Countdown Tasks
Set `estimated_time` to `0` in your CSV or edit form. No timer is shown — just click Finished when ready.

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| `Enter` | Click Finished (when task is active and not paused) |
| `Space` | Same as Enter |
| `P` | Pause / Resume the active task timer |

> Shortcuts are disabled when typing in a text field, textarea, or dropdown.

---

## ☰ Hamburger Menu Reference

Open the menu with the **☰** button in the top-right corner of the dashboard.

Items marked 🔒 require the **admin password** (default: `admin`). The password is remembered for the rest of the browser session once entered.

### Navigation
| Item | Password | Description |
|---|---|---|
| 📊 View Results | No | Opens completion history with scores and totals |
| ⬇️ Download My CSV | No | Downloads current task list as a CSV |
| 💾 Export My Data | No | Downloads full JSON backup (tasks + completion history) |
| 🏠 Home | No | Returns to the login page |
| 👥 All Users | No | Admin view: all students, per-user export, data import |

### Task Controls
| Item | Password | Description |
|---|---|---|
| ⏸️ Pause | No | Freezes/resumes the timer. Also: keyboard **P** |
| ❌ Cancel Task | No | Records task as incomplete, advances to next task |
| 📋 Upload New CSV | 🔒 Yes | Replaces entire task list; archives old tasks; clears session |
| ➕ Add a Task | 🔒 Yes | Merges additional CSV into existing task list |
| ✏️ Modify a Task | 🔒 Yes | Edit title, description, time, or difficulty of a task |
| 🗑️ Remove a Task | 🔒 Yes | Permanently delete a task from the list |

### Danger Zone
| Item | Password | Description |
|---|---|---|
| 🔄 Reset Session | 🔒 Yes | Cancels the active task session. History and tasks are kept. |
| 🧹 Clear Session | 🔒 Yes | Same as Reset Session |
| 🗑️ Clear All Data for User | 🔒 Yes | Deletes the account, all tasks, and all history. **Cannot be undone.** |

### Sound
| Item | Description |
|---|---|
| 🔔 Sound ▸ | Hover to expand. Options: No Sound (default), Ding, Chime, Bell. Saved across sessions via localStorage. |

---

## 📊 Scores Explained

### Focus Score (0.0 – 1.0)
Measures how closely you matched the estimated time.

- Finish exactly on time → **1.0** (perfect)
- Finish early → slightly below 1.0
- Run over time → decreases toward 0.1
- Tasks with `estimated_time = 0` always score **1.0**

### Impact Score (0 – 10)
`impact = (difficulty_weight × 0.4 + focus_score × 0.6) × 10`

| Difficulty | Perfect Focus Score | Max Impact |
|---|---|---|
| 🟢 Easy (0.5) | 1.0 | 5.0 |
| 🟡 Medium (1.0) | 1.0 | 10.0... wait |

Actually the formula: `(0.4 × weight + 0.6 × focus) × 10`

| Difficulty | Weight | Max Impact |
|---|---|---|
| 🟢 Easy | 0.5 | (0.4×0.5 + 0.6×1.0)×10 = **8.0** |
| 🟡 Medium | 1.0 | (0.4×1.0 + 0.6×1.0)×10 = **10.0** |
| 🟠 Hard | 1.5 | (0.4×1.5 + 0.6×1.0)×10 = **12.0** |
| 🔴 Expert | 2.0 | (0.4×2.0 + 0.6×1.0)×10 = **14.0** |

### Result Badges
| Badge | Meaning |
|---|---|
| 🌟 Finished Early | Completed under the estimated time |
| ⏱️ Time to Complete | Completed but took longer than estimated |
| ❌ Incomplete | Cancelled — time recorded, marked incomplete |

---

## 👥 All Users Page (`/users`)

Accessible from the hamburger menu. Shows all registered students with:
- Task count and completion count
- Links to each student's dashboard and results
- Per-user **⬇️ Export** (JSON)
- Global **⬇️ Export All Users** (single JSON with everyone)
- **📥 Import Session Data** — upload a JSON export to restore one or more users

### Import / Export Format
Exports are self-contained JSON files. They can be used to:
- Back up a student's data before clearing
- Move data between servers
- Restore after a database reset

Tasks are matched by `csv_task_id` first, then by title, so history links up correctly even if the database IDs change.

---

## 🔒 Admin Password

The default password is **`admin`**.

Protected actions: Add a Task, Modify a Task, Remove a Task, Upload New CSV, Reset Session, Clear Session, Clear All Data for User.

The password is checked client-side and remembered for the browser session. To change it, update the string `'admin'` in `adminAuth()` in `dashboard.html`.

---

## 🗄️ Database Schema

| Table | Key Columns |
|---|---|
| `students` | `id`, `name` (unique, case-insensitive), `created_at` |
| `tasks` | `id`, `student_id`, `title`, `description`, `estimated_time`, `difficulty_weight`, `archived`, `task_order`, `csv_task_id` |
| `task_completions` | `id`, `student_id`, `task_id`, `actual_time`, `focus_score`, `impact_score`, `completed` (1=done, 0=cancelled) |
| `active_sessions` | `id`, `student_id`, `task_id`, `start_time` |

The database is auto-created on first run. Migrations for new columns run automatically on startup.

---

## 🔗 API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Home / login page |
| POST | `/student/create` | Find or create student by name |
| GET | `/student/{id}` | Dashboard |
| GET | `/results/{id}` | Results page |
| GET | `/users` | All users admin page |
| POST | `/upload-tasks/{id}` | Merge CSV into task list |
| POST | `/upload-tasks/overwrite/{id}` | Replace task list with new CSV |
| GET | `/tasks/export/{id}` | Download task list as CSV |
| POST | `/tasks/archive-all/{id}` | Archive all active tasks |
| GET | `/export/user/{id}` | Download full JSON export for one user |
| GET | `/export/all` | Download JSON export for all users |
| POST | `/import/data` | Import JSON export file |
| POST | `/task/start/{sid}/{tid}` | Start a task |
| POST | `/task/finish/{sid}` | Finish a task (complete) |
| POST | `/task/abandon/{sid}` | Finish a task (incomplete/cancelled) |
| POST | `/task/cancel/{sid}` | Cancel without recording |
| GET | `/task/{tid}/edit` | Edit task form |
| POST | `/task/{tid}/update` | Save task edits |
| DELETE | `/task/{tid}` | Delete a task |
| POST | `/student/{id}/reset` | Clear active session |
| POST | `/tasks/clear` | Delete all user data and account |
