# Quick Network Setup for Multiple Devices

## 🚀 5-Minute Setup for Family/Dojo Use

### Step 1: Start the Application
```bash
docker-compose up -d
```

### Step 2: Find Your Computer's IP Address

**Mac:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Look for something like: inet 192.168.1.100
```

**Windows:**
```cmd
ipconfig
# Look for "IPv4 Address" like: 192.168.1.100
```

**Linux:**
```bash
hostname -I
# First IP is usually what you need: 192.168.1.100
```

### Step 3: Access from Other Devices

On any phone, tablet, or computer **on the same WiFi**:
```
http://192.168.1.100:8000
```
(Replace `192.168.1.100` with YOUR computer's IP)

### Step 4: Each User Selects Their Profile
- Open the URL
- Enter name or select existing profile
- Start training!

---

## ✅ What Works Right Now

Your current setup supports:
- ✅ Multiple students using the same device (taking turns)
- ✅ Multiple devices on same WiFi network
- ✅ Up to ~10 concurrent users without issues
- ✅ Separate progress tracking per student
- ✅ Shared task list (all students see same tasks)

---

## 🎯 Example Scenarios

### Scenario 1: Family with 3 Kids
**Setup:** One iPad running Docker container
**Usage:** Kids take turns, each selects their name
**Works perfectly!** ✅

### Scenario 2: Small Karate Class (8 Students)
**Setup:** Teacher's laptop running container
**Usage:** Each student has tablet, connects to teacher's laptop IP
**Works perfectly!** ✅

### Scenario 3: After-School Program (15 Students)
**Setup:** Dedicated computer running container
**Usage:** Students connect from classroom tablets via WiFi
**Works well!** ✅ (may need PostgreSQL for 20+)

### Scenario 4: Multiple Dojos
**Setup:** Cloud deployment (Fly.io/Railway)
**Usage:** Each dojo accesses via internet URL
**Best option!** ✅

---

## 🔥 Quick Test

1. **On main computer:** Run `docker-compose up -d`
2. **On main computer:** Find IP with `ifconfig` or `ipconfig`
3. **On phone:** Connect to same WiFi
4. **On phone:** Browse to `http://YOUR_IP:8000`
5. **Success!** You should see the app

---

## 🐛 Troubleshooting

### Can't connect from other devices?

**Check 1: Same network?**
```bash
# Both devices should show similar IPs
# Main: 192.168.1.100
# Phone: 192.168.1.45  ← Same 192.168.1.X range
```

**Check 2: Container running?**
```bash
docker ps
# Should show karate-tracker container
```

**Check 3: Firewall?**
```bash
# Mac: System Preferences → Security → Firewall
# Windows: Windows Defender Firewall
# Linux: sudo ufw allow 8000
```

**Check 4: Port binding**
Make sure docker-compose.yml has:
```yaml
ports:
  - "0.0.0.0:8000:8000"  # Not just "8000:8000"
```

### Different students editing same task?

This is OK! Each student's session is tracked separately:
- Student A starts "Punching Drills" → tracked for Student A
- Student B starts "Punching Drills" → tracked separately for Student B
- Both finish independently → both get separate completion records

---

## 📊 How Many Users Can It Handle?

| Users | Performance | Notes |
|-------|-------------|-------|
| 1-5 | Excellent ⚡ | No issues at all |
| 5-10 | Great ✅ | Occasional delays if finishing simultaneously |
| 10-20 | Good 👍 | Works fine, may see brief locks |
| 20-30 | OK ⚠️ | Consider PostgreSQL upgrade |
| 30+ | Upgrade 🔧 | Definitely upgrade to PostgreSQL |

---

## 🌐 For Internet Access

**Option 1: Cloud Deploy (Easiest)**
Use Fly.io, Railway, or similar:
```bash
fly launch
fly deploy
# Access from anywhere: https://your-app.fly.dev
```

**Option 2: Port Forward (Advanced)**
- Login to your router
- Forward port 8000 to your computer
- Access via public IP
- ⚠️ Security risk - use HTTPS!

**Option 3: VPN (Secure)**
- Setup Tailscale or WireGuard
- All devices join VPN
- Access via VPN IP addresses
- Most secure option

---

## 💡 Recommended Setups

### Home Use (2-5 kids)
```
Device: Family computer/iPad
Access: Same device, take turns
Network: Not needed
Cost: Free
Setup time: 2 minutes
```

### Small Dojo (5-15 students)
```
Device: Teacher's laptop
Access: Students' tablets via WiFi
Network: Local WiFi
Cost: Free
Setup time: 5 minutes
```

### Medium Dojo (15-30 students)
```
Device: Dedicated server computer
Access: All devices via WiFi
Network: Dedicated WiFi or wired
Cost: $0-50 (server computer)
Setup time: 15 minutes
```

### Large Organization (30+ students)
```
Device: Cloud service (Fly.io)
Access: Internet URL
Network: Internet
Cost: $5-20/month
Setup time: 30 minutes
```

---

## 🎓 Best Practices

1. **Start Simple:** Use localhost first, then expand
2. **Test Network:** Try from one other device before class
3. **Backup Data:** Before major events/tests
4. **Monitor Usage:** Check active sessions periodically
5. **Update Regularly:** Pull latest code updates

---

## 🚀 Next Steps

**You're ready to go!** The app already supports multiple users.

**Want to expand?**
1. See [MULTI_USER_GUIDE.md](MULTI_USER_GUIDE.md) for advanced setups
2. See [DATA_PERSISTENCE.md](DATA_PERSISTENCE.md) for backups
3. See [README.md](README.md) for full documentation

Happy training! 🥋
