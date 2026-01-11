# Installation Guide - Karate Task Tracker

## Quick Start (3 Easy Steps!)

### Option 1: Using Docker (Recommended)

**Prerequisites:**
- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))

**Steps:**
1. Extract the ZIP file to a folder
2. Open terminal/command prompt in that folder
3. Run:
   ```bash
   docker-compose up --build
   ```
4. Open your browser to `http://localhost:8000`

**That's it! 🎉**

---

### Option 2: Manual Installation

**Prerequisites:**
- Python 3.8 or higher ([Download here](https://www.python.org/downloads/))

**Steps:**

#### Windows:
1. Extract the ZIP file to a folder
2. Open Command Prompt in that folder (Shift + Right Click → "Open PowerShell window here")
3. Run these commands:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```
4. Open your browser to `http://localhost:8000`

#### Mac/Linux:
1. Extract the ZIP file to a folder
2. Open Terminal in that folder
3. Run these commands:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
4. If using manual installation:
   ```bash
   source venv/bin/activate
   python main.py
   ```
5. Open your browser to `http://localhost:8000`

---

## File Structure

After extraction, you should see:

```
karate-tracker/
├── main.py                   # Main application
├── requirements.txt          # Dependencies
├── Dockerfile               # Docker setup
├── docker-compose.yml       # Docker Compose config
├── setup.sh                 # Setup script (Mac/Linux)
├── README.md                # Documentation
├── INSTALLATION.md          # This file
├── sample_tasks.csv         # Example tasks to upload
├── .gitignore              # Git ignore rules
├── static/
│   └── style.css           # Styles
└── templates/
    ├── index.html          # Home page
    ├── dashboard.html      # Task dashboard
    └── results.html        # Results page
```

---

## First Time Setup

1. **Start the application** (using either method above)

2. **Open your browser** to `http://localhost:8000`

3. **Enter your name** on the home page

4. **Upload tasks:**
   - Use the included `sample_tasks.csv` file, or
   - Create your own CSV file with columns: `task`, `description`, `estimated_time`

5. **Start training!** 🥋

---

## Troubleshooting

### Problem: Port 8000 is already in use

**Solution 1 (Docker):**
Edit `docker-compose.yml` and change:
```yaml
ports:
  - "8001:8000"  # Change 8000 to any available port
```

**Solution 2 (Manual):**
Run with a different port:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Problem: Docker commands don't work

**Solution:**
- Make sure Docker Desktop is running
- On Windows, run Command Prompt as Administrator
- Try `docker-compose` instead of `docker compose`

### Problem: Python not found

**Solution:**
- Windows: Try `py` instead of `python`
- Mac/Linux: Try `python3` instead of `python`
- Make sure Python is added to your PATH

### Problem: Permission denied (Mac/Linux)

**Solution:**
```bash
chmod +x setup.sh
sudo chmod -R 755 .
```

### Problem: CSV upload fails

**Solution:**
- Check CSV format has headers: `task`, `description`, `estimated_time`
- Make sure file encoding is UTF-8
- Try the included `sample_tasks.csv` first

---

## Stopping the Application

**Docker:**
```bash
docker-compose down
```

**Manual:**
Press `Ctrl+C` in the terminal where the app is running

---

## Updating the Application

1. Stop the application
2. Replace files with new version
3. Restart using the same commands

Your database (`karate_tracker.db`) will be preserved!

---

## Creating Your Own Tasks CSV

Create a text file named `my_tasks.csv` with this format:

```csv
task,description,estimated_time
Warm Up,Stretching exercises,10
Kata Practice,Practice basic kata,20
Kicks,Practice side and front kicks,15
```

**Rules:**
- First line must be: `task,description,estimated_time`
- Time is in minutes
- Keep descriptions short and clear
- No special characters in task names

---

## Advanced Configuration

### Change Database Location
Edit `main.py` line 26:
```python
conn = sqlite3.connect('karate_tracker.db')  # Change path here
```

### Modify Difficulty Levels
Edit `main.py` function `calculate_difficulty_weight()` to adjust:
- Time thresholds
- Difficulty multipliers

### Customize Colors
Edit `static/style.css` to change:
- Backgrounds
- Button colors
- Fonts

---

## Getting Help

If you encounter issues:

1. Check this installation guide
2. Read the README.md file
3. Make sure all files are extracted properly
4. Try the Docker method if manual installation fails
5. Check that your ports aren't blocked by firewall

---

## System Requirements

**Minimum:**
- 2GB RAM
- 100MB disk space
- Modern web browser (Chrome, Firefox, Safari, Edge)

**Recommended:**
- 4GB RAM
- Tablet or larger screen for best experience
- Touch screen for easier interaction

---

## Security Notes

- The application runs locally on your computer
- No data is sent to external servers
- Database is stored in the application folder
- Safe for children to use

---

## Next Steps

After installation:
1. ✅ Read the README.md for full documentation
2. ✅ Upload your first tasks using `sample_tasks.csv`
3. ✅ Start completing tasks and earning streaks!
4. ✅ Check your progress in the Results page

**Happy training! 🥋**