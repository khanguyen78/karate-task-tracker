# 🥋 Karate Task Tracker

A web application designed specifically for autistic students at a karate school to track their training tasks with visual feedback, clear progress indicators, and motivational features.

## Features

### Backend (FastAPI + SQLite)
- ✅ FastAPI web framework for high performance
- ✅ SQLite database for persistent storage
- ✅ Safe CSV cleaning to prevent injection attacks
- ✅ Difficulty weighting based on estimated time
- ✅ Focus score calculation (estimated vs actual time)
- ✅ Impact score combining difficulty and focus
- ✅ Student progress tracking over time
- ✅ Active session management
- ✅ Streak tracking for daily consistency

### Frontend (Jinja2 Templates + Vanilla JS)
- ✅ Clean, colorful UI with large tap targets
- ✅ Highlighted active task cards
- ✅ Big, accessible buttons for Start/Finish
- ✅ Live timer display when task is active
- ✅ Confetti animation on task completion
- ✅ Complete button outputs total time and scores
- ✅ Dashboard with live results
- ✅ Responsive design for mobile and desktop

### Special Features for Autistic Students
- 🎯 Clear visual hierarchy
- 🎨 High contrast colors
- 📊 Progress visualization
- 🎉 Positive reinforcement (confetti!)
- ⏱️ Time awareness with live timer
- 🔥 Streak tracking for motivation
- 📈 Achievement badges
- 🎮 Gamification elements

## Quick Start

### Using Docker (Recommended)

1. **Build and run with Docker Compose:**
```bash
docker-compose up --build
```

2. **Access the application:**
Open your browser to `http://localhost:8000`

### Manual Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the application:**
```bash
python main.py
```

3. **Access the application:**
Open your browser to `http://localhost:8000`

## Usage Guide

### 1. Student Registration
- Enter your name on the home page
- Click "Start Training!" to create your profile
- Returning students can click their name to continue

### 2. Upload Tasks
- Prepare a CSV file with three columns:
  - `task`: Name of the task
  - `description`: Brief description (optional)
  - `estimated_time`: Time in minutes

Example CSV:
```csv
task,description,estimated_time
Warm-up Stretches,Leg and arm stretches before training,10
Basic Kata Practice,Practice first 3 katas,20
Punching Drills,50 punches with proper form,15
Kicking Drills,Side kicks and front kicks,20
Cool Down,Breathing exercises and stretches,10
```

- Click "Upload Tasks" and select your CSV file

### 3. Complete Tasks
- Click "🚀 Start" on any task to begin
- The timer will start automatically
- Complete your task
- Click "✅ Finished!" when done
- Enjoy the confetti celebration! 🎉

### 4. View Progress
- Click "📊 View Results" to see your history
- Track your total time, focus scores, and streak
- See all completed tasks with detailed metrics

## Scoring System

### Focus Score (0.0 - 1.0)
- Measures how well you stayed on track
- Based on estimated vs actual time
- Higher score = better time management

### Impact Score (0.0 - 10.0)
- Combines difficulty and focus
- Weighted average: 40% difficulty, 60% focus
- Higher score = bigger achievement!

### Difficulty Weight
- Easy (🟢): 0-5 minutes = 0.5x
- Medium (🟡): 6-15 minutes = 1.0x
- Hard (🟠): 16-30 minutes = 1.5x
- Expert (🔴): 30+ minutes = 2.0x

### Streak System
- Complete tasks daily to build your streak
- Each consecutive day adds to your streak
- Display shows 🔥 with your current streak

## Project Structure

```
karate-tracker/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── README.md              # This file
├── static/
│   └── style.css          # Stylesheet
├── templates/
│   ├── index.html         # Home page
│   ├── dashboard.html     # Task dashboard
│   └── results.html       # Results page
└── karate_tracker.db      # SQLite database (created on first run)
```

## Database Schema

### Students Table
- id: Primary key
- name: Student name
- created_at: Registration timestamp

### Tasks Table
- id: Primary key
- title: Task name
- description: Task description
- estimated_time: Expected duration in minutes
- difficulty_weight: Calculated difficulty (0.5 - 2.0)
- created_at: Creation timestamp

### Task Completions Table
- id: Primary key
- student_id: Foreign key to students
- task_id: Foreign key to tasks
- start_time: When task started
- end_time: When task finished
- actual_time: Duration in seconds
- focus_score: Performance metric (0.0 - 1.0)
- impact_score: Achievement metric (0.0 - 10.0)
- completed_at: Completion timestamp

### Active Sessions Table
- id: Primary key
- student_id: Foreign key to students
- task_id: Foreign key to tasks
- start_time: Session start time

## API Endpoints

### Frontend Routes
- `GET /` - Home page
- `GET /student/{student_id}` - Student dashboard
- `GET /results/{student_id}` - Results page

### API Routes
- `POST /student/create` - Create new student
- `POST /upload-tasks/{student_id}` - Upload CSV tasks
- `POST /task/start/{student_id}/{task_id}` - Start a task
- `POST /task/finish/{student_id}` - Finish active task
- `GET /api/session-status/{student_id}` - Check active session

## Customization

### Colors and Themes
Edit `static/style.css` to change:
- Gradient backgrounds
- Button colors
- Card styles
- Font sizes

### Difficulty Levels
Modify `calculate_difficulty_weight()` in `main.py` to adjust:
- Time thresholds
- Weight multipliers

### Scoring Algorithm
Adjust `calculate_focus_score()` and `calculate_impact_score()` in `main.py` for different scoring logic.

## Troubleshooting

### Database Issues
```bash
# Reset database
rm karate_tracker.db
python main.py  # Will recreate database
```

### Port Already in Use
```bash
# Change port in docker-compose.yml or run manually:
uvicorn main:app --host 0.0.0.0 --port 8001
```

### CSV Upload Fails
- Ensure CSV has headers: `task`, `description`, `estimated_time`
- Check file encoding is UTF-8
- Verify no special characters in task names

## Development

### Running in Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Building Docker Image
```bash
docker build -t karate-tracker .
docker run -p 8000:8000 karate-tracker
```

## Safety Features

1. **CSV Sanitization**: All CSV input is cleaned to prevent injection
2. **Input Validation**: Names and tasks are validated before storage
3. **SQL Injection Prevention**: Uses parameterized queries
4. **Session Management**: One active task per student
5. **Error Handling**: Graceful error messages

## License

This project is open source and available for educational purposes.

## Credits

Built with:
- FastAPI
- SQLite
- Jinja2
- Canvas Confetti
- Modern CSS3

Designed for accessibility and ease of use for neurodivergent learners.

---

Made with ❤️ for karate students everywhere! 🥋



chmod +x setup.sh
./setup.sh
```

## 📁 New File Structure:
```
karate-tracker/
├── data/                    ← Database stored here
│   └── karate_tracker.db   ← Auto-created
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   └── results.html
├── main.py                  ← Updated
├── Dockerfile               ← Updated
├── docker-compose.yml       ← Updated
├── setup.sh                 ← Updated
├── .dockerignore            ← New
├── QUICKSTART.md            ← New
└── ...
