# Quick Start Guide - Fixed Version

## What was fixed?
The database permission error has been resolved. The application now stores the database in a `data/` directory with proper permissions.

## 🔒 Data Persistence

**Your data is automatically saved!** The database file is stored in the `data/` folder on your computer, NOT inside the Docker container. This means:

✅ Data survives container restarts
✅ Data survives container rebuilds  
✅ Data survives `docker-compose down`
✅ You can backup by copying the `data/` folder
✅ You can restore by replacing the `data/` folder

**The database will persist even if you:**
- Stop the container (`docker-compose down`)
- Rebuild the container (`docker-compose up --build`)
- Delete and recreate containers
- Update the application code

**Your data is located at:**
- `./data/karate_tracker.db` (relative to your project folder)
- Example: `/Users/yourname/karate-tracker/data/karate_tracker.db`

## Installation Steps

### Option 1: Docker (Recommended)

1. **Extract all files** from the ZIP

2. **Open terminal/command prompt** in the extracted folder

3. **Create data directory**:
   ```bash
   mkdir data
   ```

4. **Run Docker Compose**:
   ```bash
   docker-compose up --build
   ```

5. **Open browser**: http://localhost:8000

✅ **Done!**

---

### Option 2: Manual Installation

#### Windows:

1. Extract all files
2. Open PowerShell in the folder
3. Run:
   ```powershell
   mkdir data
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```
4. Open browser: http://localhost:8000

#### Mac/Linux:

1. Extract all files
2. Open Terminal in the folder
3. Run:
   ```bash
   mkdir -p data
   chmod +x setup.sh
   ./setup.sh
   ```
4. If using manual installation:
   ```bash
   source venv/bin/activate
   python main.py
   ```
5. Open browser: http://localhost:8000

---

## Troubleshooting

### Still getting database errors?

**For Docker:**
```bash
# Stop everything
docker-compose down

# Remove old containers
docker-compose rm -f

# Create data directory with full permissions
mkdir -p data
chmod 777 data

# Rebuild and start
docker-compose up --build
```

**For Manual Installation:**
```bash
# Create data directory
mkdir -p data

# Give it write permissions (Mac/Linux)
chmod 777 data

# Or on Windows PowerShell:
New-Item -ItemType Directory -Force -Path data
```

### Permission denied on setup.sh?
```bash
chmod +x setup.sh
```

### Port 8000 already in use?

**Edit docker-compose.yml:**
```yaml
ports:
  - "8001:8000"  # Change first number
```

**Or for manual:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

---

## What Changed?

1. ✅ Database now stored in `data/` directory
2. ✅ Docker container has proper permissions
3. ✅ Volume mapping for database persistence
4. ✅ Environment variable for database path
5. ✅ All database connections updated

---

## Verify Installation

After starting, you should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Then:
1. Open http://localhost:8000
2. Enter your name
3. Upload sample_tasks.csv
4. Start your first task! 🥋

---

## File Structure

```
karate-tracker/
├── data/                    ← NEW! Database stored here
│   └── karate_tracker.db   ← Created on first run
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   └── results.html
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── sample_tasks.csv
```

---

## Need Help?

**Check logs (Docker):**
```bash
docker-compose logs -f
```

**Check logs (Manual):**
Look at the terminal where you ran `python main.py`

**Reset everything:**
```bash
# Stop the app
docker-compose down  # or Ctrl+C for manual

# Delete database
rm -rf data/

# Start fresh
mkdir data
docker-compose up --build
```

---

## Success Indicators

✅ No error messages in logs
✅ Can access http://localhost:8000
✅ Can create a student profile
✅ Can upload CSV file
✅ Can start and finish tasks
✅ Database file exists in `data/karate_tracker.db`

---

Happy training! 🥋
