# Multi-User Deployment Guide

## Can Multiple Users Use This App?

**YES!** The Karate Task Tracker supports multiple users simultaneously. Here's how it works and how to set it up for different scenarios.

## 🏠 Scenario 1: Home/Family Use (Current Setup)

**Best for:** 2-10 students sharing a device or on the same network

### How It Works
- One Docker container running
- One shared SQLite database
- Each student has their own profile
- Students select their name when they log in
- All data kept separate by student ID

### Setup
Already configured! Just run:
```bash
docker-compose up -d
```

### Access From Multiple Devices

1. **Find your computer's IP address:**

   **Mac/Linux:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```
   
   **Windows:**
   ```cmd
   ipconfig
   ```
   
   Look for something like: `192.168.1.100`

2. **Access from other devices on same network:**
   ```
   http://192.168.1.100:8000
   ```
   (Replace with your actual IP)

3. **Each device/student:**
   - Opens the URL
   - Selects or creates their profile
   - Works independently

### Limitations
- ⚠️ SQLite can handle ~10 concurrent users
- ⚠️ All devices must be on same local network
- ⚠️ Not accessible from internet (unless you port forward)

---

## 🥋 Scenario 2: Small Dojo (10-30 Students)

**Best for:** Karate school with multiple tablets/devices

### Recommended Setup

**Option A: Shared Server**
- Run on a dedicated computer/server
- All tablets connect to server's IP
- Centralized data management

**Option B: Individual Tablets**
- Each tablet runs its own container
- Students sync data manually via CSV export/import
- More privacy, less coordination

### Setup (Shared Server)

1. **On the server computer:**
   ```bash
   docker-compose up -d
   ```

2. **Configure firewall (if needed):**
   
   **Mac:**
   ```bash
   # Allow incoming connections on port 8000
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which docker)
   ```
   
   **Linux (Ubuntu):**
   ```bash
   sudo ufw allow 8000/tcp
   ```
   
   **Windows:**
   - Windows Defender Firewall
   - Allow incoming connections on port 8000

3. **Find server IP:**
   ```bash
   hostname -I  # Linux
   ipconfig getifaddr en0  # Mac
   ipconfig  # Windows
   ```

4. **On each tablet/device:**
   - Connect to same WiFi
   - Open browser to `http://SERVER_IP:8000`
   - Select student profile

### Performance Tips
- Use wired ethernet for server if possible
- Consider upgrading to PostgreSQL for 30+ users
- Monitor database size and backup regularly

---

## 🌐 Scenario 3: Internet Access (Remote Students)

**Best for:** Students accessing from home, cloud deployment

### Option A: Cloud Deployment (Recommended)

Deploy to a cloud service for reliable internet access:

#### Deploy to Fly.io (Free Tier Available)

1. **Install Fly.io CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Create fly.toml:**
   ```toml
   app = "karate-tracker-yourname"
   
   [build]
     dockerfile = "Dockerfile"
   
   [[services]]
     internal_port = 8000
     protocol = "tcp"
   
     [[services.ports]]
       handlers = ["http"]
       port = 80
     
     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
   
   [[mounts]]
     source = "karate_data"
     destination = "/app/data"
   ```

4. **Deploy:**
   ```bash
   fly launch
   fly volumes create karate_data --size 1
   fly deploy
   ```

5. **Access:**
   ```
   https://karate-tracker-yourname.fly.dev
   ```

#### Deploy to Railway.app

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Connect your repo
4. Railway auto-detects Dockerfile
5. Add volume mount for `/app/data`
6. Deploy!

### Option B: Home Server with Port Forwarding

**⚠️ Security Warning:** Only do this if you understand the risks

1. **Setup dynamic DNS (optional):**
   - Use No-IP or DynDNS
   - Get a domain like `mykarate.ddns.net`

2. **Port forward on router:**
   - Login to router admin panel
   - Forward external port 8000 to your server's IP:8000

3. **Access from anywhere:**
   ```
   http://YOUR_PUBLIC_IP:8000
   ```

**Security considerations:**
- Use HTTPS with SSL certificate (Let's Encrypt)
- Add authentication middleware
- Use firewall rules
- Consider VPN instead

---

## 🔐 Scenario 4: High Security (Separate Containers)

**Best for:** Privacy-sensitive environments, HIPAA compliance

### Setup: One Container Per Student

Create separate docker-compose files:

**docker-compose-student1.yml:**
```yaml
version: '3.8'
services:
  karate-tracker-student1:
    build: .
    ports:
      - "8001:8000"
    volumes:
      - ./data-student1:/app/data
    environment:
      - DATABASE_PATH=/app/data/karate_tracker.db
```

**docker-compose-student2.yml:**
```yaml
version: '3.8'
services:
  karate-tracker-student2:
    build: .
    ports:
      - "8002:8000"
    volumes:
      - ./data-student2:/app/data
    environment:
      - DATABASE_PATH=/app/data/karate_tracker.db
```

**Run all containers:**
```bash
docker-compose -f docker-compose-student1.yml up -d
docker-compose -f docker-compose-student2.yml up -d
```

**Access:**
- Student 1: `http://localhost:8001`
- Student 2: `http://localhost:8002`

---

## ⚡ Performance Comparison

| Scenario | Users | Response Time | Setup Difficulty | Cost |
|----------|-------|---------------|------------------|------|
| Single Container (SQLite) | 1-10 | Instant | Easy | Free |
| Shared Server (SQLite) | 10-30 | <100ms | Medium | $0-50/mo |
| Cloud (SQLite) | 30-100 | 100-300ms | Medium | $5-20/mo |
| PostgreSQL + Cloud | 100+ | 50-200ms | Hard | $20-100/mo |
| Separate Containers | Any | Instant | Easy | Free |

---

## 🔧 Upgrading to PostgreSQL (30+ Users)

For better concurrent access with many users:

1. **Create docker-compose-postgres.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: karate_tracker
      POSTGRES_USER: karate
      POSTGRES_PASSWORD: changeme123
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  karate-tracker:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql://karate:changeme123@postgres:5432/karate_tracker
    restart: unless-stopped

volumes:
  postgres-data:
```

2. **Update main.py to use PostgreSQL:**
   - Replace `sqlite3` with `psycopg2`
   - Update connection strings
   - Modify SQL syntax if needed

---

## 📊 Monitoring Multi-User Usage

### Check Active Connections (SQLite)
```bash
# Inside container
docker exec -it karate-tracker bash
sqlite3 /app/data/karate_tracker.db "SELECT COUNT(*) FROM active_sessions;"
```

### View All Students
```bash
sqlite3 data/karate_tracker.db "SELECT id, name, created_at FROM students;"
```

### See Active Tasks
```bash
sqlite3 data/karate_tracker.db "
SELECT s.name, t.title, a.start_time 
FROM active_sessions a 
JOIN students s ON a.student_id = s.id 
JOIN tasks t ON a.task_id = t.id;
"
```

---

## 🎯 Best Practices

### For Small Groups (2-10 users)
✅ Use default SQLite setup
✅ Run on one computer, access via LAN
✅ Backup data folder weekly

### For Medium Groups (10-30 users)
✅ Dedicated server computer
✅ Wired ethernet connection
✅ Daily backups
✅ Monitor disk space

### For Large Groups (30+ users)
✅ Cloud deployment
✅ Consider PostgreSQL
✅ Automated backups
✅ Load balancing if needed

### For Maximum Privacy
✅ Separate containers per student
✅ Different ports
✅ Isolated databases
✅ Export data to personal devices

---

## 🚨 Troubleshooting Multi-User Issues

### "Database is locked"
```bash
# Stop all containers
docker-compose down

# Wait 5 seconds
sleep 5

# Restart
docker-compose up -d
```

### Slow performance with many users
- Upgrade to PostgreSQL
- Use cloud deployment
- Add more RAM to server
- Check network bandwidth

### Can't access from other devices
```bash
# Check container is running
docker ps

# Check port is open
netstat -an | grep 8000

# Check firewall (Linux)
sudo ufw status

# Try binding to 0.0.0.0
# Edit docker-compose.yml: ports: "0.0.0.0:8000:8000"
```

### Different students see each other's tasks
- This is expected - tasks are shared
- To separate: use "Clear All Tasks" and upload different CSVs
- Or use separate containers per group

---

## 💡 Quick Decision Guide

**Choose Single Container if:**
- Less than 10 students
- Same location/network
- Simple setup preferred

**Choose Cloud Deployment if:**
- Remote access needed
- 10+ students
- Want automatic backups
- Professional environment

**Choose Separate Containers if:**
- Privacy is critical
- Different task sets per student
- Isolated data required

**Choose PostgreSQL if:**
- 30+ concurrent users
- High-traffic environment
- Enterprise deployment

---

## 📱 Mobile Access

All setups work on:
- ✅ iPhone/iPad Safari
- ✅ Android Chrome
- ✅ Tablets
- ✅ Desktop browsers

**Responsive design** adapts to any screen size!

---

## 🔒 Security Recommendations

**For home use:**
- Keep on local network only
- No port forwarding needed

**For internet access:**
- Use HTTPS (Let's Encrypt)
- Add password authentication
- Regular security updates
- Monitor access logs

**For schools:**
- Comply with student data privacy laws
- Get parental consent for data collection
- Use encrypted backups
- Regular security audits

---

Your current setup already supports multiple users perfectly for home/small dojo use! 🥋
