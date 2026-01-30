# Data Persistence Guide

## 🔒 How Your Data is Protected

Your karate training data is **automatically persistent** and will survive container restarts, rebuilds, and updates.

## 📂 Where is Your Data Stored?

### Local Directory (Current Setup)
```
karate-tracker/
├── data/
│   └── karate_tracker.db  ← YOUR DATA IS HERE
├── main.py
├── docker-compose.yml
└── ...
```

The `data/` folder is on **your computer**, not inside the Docker container. This is called a "bind mount" or "volume mapping."

## ✅ What Persists

**Your data includes:**
- Student profiles and names
- All uploaded tasks
- Task completion history
- Focus scores and impact scores
- Streak information
- Active sessions

**All of this is stored in:** `./data/karate_tracker.db`

## 🛡️ Data Survival Scenarios

| Action | Data Safe? | Explanation |
|--------|-----------|-------------|
| `docker-compose down` | ✅ YES | Stops container, data in `./data/` untouched |
| `docker-compose up` | ✅ YES | Restarts container, reconnects to `./data/` |
| `docker-compose restart` | ✅ YES | Quick restart, data persists |
| `docker-compose up --build` | ✅ YES | Rebuilds image, data in `./data/` safe |
| Delete container | ✅ YES | Container deleted, `./data/` remains |
| Delete image | ✅ YES | Image deleted, `./data/` remains |
| Update code files | ✅ YES | Code changes don't affect data |
| Computer restart | ✅ YES | Data is a regular file on disk |
| Move project folder | ✅ YES | Just move entire folder with `data/` |
| `rm -rf data/` | ❌ NO | Manually deleting data folder loses data |
| `docker system prune -a` | ✅ YES | Cleans Docker, but `./data/` is safe |

## 🔄 How Docker Volume Mapping Works

In `docker-compose.yml`:
```yaml
volumes:
  - ./data:/app/data
```

This means:
- `./data` = folder on YOUR computer
- `/app/data` = folder inside the container
- They are **linked** (same data, two locations)
- When container writes to `/app/data`, it writes to YOUR `./data`
- When container is destroyed, YOUR `./data` remains

## 💾 Backup Your Data

### Quick Backup
```bash
# Copy the entire data folder
cp -r data data_backup_2024-01-30

# Or create a zip
zip -r karate_data_backup.zip data/
```

### Automated Backup Script
Create `backup.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR
cp -r data "$BACKUP_DIR/data_backup_$DATE"
echo "✅ Backup created: $BACKUP_DIR/data_backup_$DATE"
```

Run it:
```bash
chmod +x backup.sh
./backup.sh
```

## 📥 Restore Your Data

### From Backup
```bash
# Stop the application
docker-compose down

# Replace data folder
rm -rf data
cp -r data_backup_2024-01-30 data

# Restart
docker-compose up -d
```

### From Another Computer
```bash
# Copy data folder from old computer to new computer
# Place it in the karate-tracker/ directory

# Start application
docker-compose up -d

# Your data is now restored!
```

## 🔍 Verify Data Persistence

### Test It Yourself

1. **Create some data:**
   ```bash
   docker-compose up -d
   # Use the app, create student, complete tasks
   ```

2. **Check the database exists:**
   ```bash
   ls -lh data/
   # Should show: karate_tracker.db
   ```

3. **Destroy the container:**
   ```bash
   docker-compose down
   docker container prune -f
   ```

4. **Verify data still exists:**
   ```bash
   ls -lh data/
   # Still shows: karate_tracker.db
   ```

5. **Restart and check:**
   ```bash
   docker-compose up -d
   # Open browser, your data is still there!
   ```

## 🚀 Advanced: Named Volumes (Optional)

If you want Docker to manage the data location:

**Edit docker-compose.yml:**
```yaml
version: '3.8'

volumes:
  karate-data:

services:
  karate-tracker:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - karate-data:/app/data  # Named volume instead of ./data
    environment:
      - PYTHONUNBUFFERED=1
      - DATABASE_PATH=/app/data/karate_tracker.db
    restart: unless-stopped
```

**Advantages:**
- Docker manages the storage location
- Better performance on some systems
- Works identically on Windows/Mac/Linux

**Disadvantages:**
- Data location is hidden (managed by Docker)
- Harder to manually backup

**Backup named volume:**
```bash
docker run --rm -v karate-data:/data -v $(pwd):/backup ubuntu tar czf /backup/karate-backup.tar.gz /data
```

**Restore named volume:**
```bash
docker run --rm -v karate-data:/data -v $(pwd):/backup ubuntu tar xzf /backup/karate-backup.tar.gz -C /
```

## 📊 Check Database Size

```bash
# See how much space your data uses
du -sh data/

# See detailed file info
ls -lh data/karate_tracker.db
```

## 🔧 Troubleshooting

### "Database is locked" error
```bash
# Stop all containers
docker-compose down

# Check for stray processes
ps aux | grep karate

# Restart
docker-compose up -d
```

### Can't find database file
```bash
# Check if data directory exists
ls -la data/

# If missing, create it
mkdir -p data

# Set permissions (Mac/Linux)
chmod 755 data

# Restart
docker-compose up -d
```

### Want to start fresh
```bash
# Stop container
docker-compose down

# Backup old data
mv data data_old

# Create new empty data folder
mkdir data

# Start fresh
docker-compose up -d
```

### Migrate to another computer
```bash
# On old computer
tar czf karate-tracker-backup.tar.gz karate-tracker/

# Copy file to new computer

# On new computer
tar xzf karate-tracker-backup.tar.gz
cd karate-tracker
docker-compose up -d
```

## 🎯 Best Practices

1. **Regular Backups**: Copy `data/` folder weekly
2. **Version Control**: Use git for code, NOT for `data/`
3. **Test Restores**: Verify backups work before you need them
4. **Monitor Size**: Check database size periodically
5. **Multiple Students**: Each student's data is separate in the DB

## 📋 Quick Reference

```bash
# Backup
cp -r data data_backup_$(date +%Y%m%d)

# Restore
cp -r data_backup_20240130 data

# Check data exists
ls -lh data/karate_tracker.db

# View database directly (if sqlite3 installed)
sqlite3 data/karate_tracker.db "SELECT * FROM students;"

# Export all data to CSV
sqlite3 -header -csv data/karate_tracker.db "SELECT * FROM task_completions;" > completions.csv
```

## 🔐 Security Note

The database file contains student names and training history. Keep backups secure:
- Don't commit `data/` to public git repositories
- Encrypt backups if storing in cloud
- Use appropriate file permissions

**Add to .gitignore:**
```
data/
*.db
*.sqlite
backups/
```

---

Your data is safe and persistent! 🥋
