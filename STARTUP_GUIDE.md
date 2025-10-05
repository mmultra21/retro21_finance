# 🚀 Startup Scripts Guide

Complete management scripts for your Personal Finance RAG System.

---

## 📋 Available Scripts

### 1. **start.sh** - Start All Services
Starts the API server and Hermes LLM server with health checks and logging.

```bash
./start.sh
```

**Features:**
- ✅ Checks virtual environment
- ✅ Validates required files
- ✅ Cleans up any existing processes on ports
- ✅ Starts Hermes LLM Server (port 11434)
- ✅ Starts API Server (port 8000)
- ✅ Verifies all services are healthy
- ✅ Creates PID files for process management
- ✅ Logs to `logs/api_server.log` and `logs/hermes_server.log`

**Output:**
```
╔════════════════════════════════════════════════════════════════╗
║  Personal Finance RAG System - Startup                         ║
╚════════════════════════════════════════════════════════════════╝

✓ Virtual environment found
✓ All required files present

ℹ Starting services...

✓ Hermes LLM Server started (PID: 12345)
✓ API Server started (PID: 12346)

ℹ Verifying services...
✓ Hermes LLM: http://127.0.0.1:11434
✓ API Server: http://127.0.0.1:8000

╔════════════════════════════════════════════════════════════════╗
║  ✓ All Services Started Successfully                           ║
╚════════════════════════════════════════════════════════════════╝
```

---

### 2. **stop.sh** - Stop All Services
Gracefully stops all running services and cleans up processes.

```bash
./stop.sh
```

**Features:**
- ✅ Stops services using PID files
- ✅ Kills processes on ports 8000 and 11434
- ✅ Cleans up all background Python processes
- ✅ Removes stale PID files

**Output:**
```
╔════════════════════════════════════════════════════════════════╗
║  Personal Finance RAG System - Shutdown                        ║
╚════════════════════════════════════════════════════════════════╝

ℹ Stopping API Server (PID: 12346)...
✓ API Server stopped

ℹ Stopping Hermes LLM Server (PID: 12345)...
✓ Hermes LLM Server stopped

ℹ Cleaning up background Python processes...
✓ Background processes cleaned up

✓ All services stopped successfully
```

---

### 3. **status.sh** - Check Service Status
Displays comprehensive status of all services and components.

```bash
./status.sh
```

**Features:**
- ✅ Shows service status (Running/Stopped)
- ✅ Displays PIDs and port status
- ✅ Performs health checks
- ✅ Shows Qdrant database stats
- ✅ Displays recent log activity
- ✅ Lists quick action commands

**Output:**
```
╔════════════════════════════════════════════════════════════════╗
║  Personal Finance RAG System - Status                          ║
╚════════════════════════════════════════════════════════════════╝

Hermes LLM Server:
  Status:  ● Running
  PID:     12345
  Port:    11434 (in use)
  Health:  ✓ OK
  URL:     http://127.0.0.1:11434/health

API Server:
  Status:  ● Running
  PID:     12346
  Port:    8000 (in use)
  Health:  ✓ OK
  URL:     http://127.0.0.1:8000/health

Qdrant Vector Database:
  Status:  ● Initialized
  Path:    data/qdrant_db
  Size:    24K
  Documents: 4

Recent Activity (Last 5 lines):
...

Quick Actions:
  • Start services:    ./start.sh
  • Stop services:     ./stop.sh
  • Restart services:  ./stop.sh && ./start.sh
  • View API logs:     tail -f logs/api_server.log
  • View Hermes logs:  tail -f logs/hermes_server.log
```

---

## 🎯 Common Usage Patterns

### First Time Setup
```bash
# Make scripts executable (only needed once)
chmod +x start.sh stop.sh status.sh

# Start the system
./start.sh
```

### Daily Usage
```bash
# Start services
./start.sh

# Check status anytime
./status.sh

# Stop when done
./stop.sh
```

### Restart Services
```bash
# Quick restart
./stop.sh && ./start.sh

# Or restart individual services
./stop.sh
./start.sh
```

### View Logs
```bash
# Follow API server logs
tail -f logs/api_server.log

# Follow Hermes server logs
tail -f logs/hermes_server.log

# View last 50 lines
tail -50 logs/api_server.log

# View all logs
cat logs/api_server.log
```

---

## 📂 Directory Structure

After running the scripts, you'll have:

```
retro21_finance/
├── start.sh              # Start script
├── stop.sh               # Stop script
├── status.sh             # Status script
├── pids/                 # Process ID files
│   ├── api_server.pid
│   └── hermes_server.pid
└── logs/                 # Log files
    ├── api_server.log
    └── hermes_server.log
```

---

## 🔧 Troubleshooting

### Port Already in Use
The `start.sh` script automatically cleans up ports before starting. If you still have issues:

```bash
# Manual port cleanup
lsof -ti:8000 | xargs kill -9
lsof -ti:11434 | xargs kill -9

# Then start normally
./start.sh
```

### Services Won't Start
Check the logs for errors:

```bash
cat logs/api_server.log
cat logs/hermes_server.log
```

Common issues:
- **Missing .env file**: Create one with SerpAPI key
- **Virtual environment**: Ensure `venv/` exists and packages are installed
- **Python version**: Requires Python 3.12+

### Stale PID Files
If you see "stale PID file" warnings:

```bash
# Clean up PID files
rm -rf pids/

# Then start normally
./start.sh
```

### Check What's Running
```bash
# See all Python processes
ps aux | grep python

# See what's on ports
lsof -i:8000
lsof -i:11434
```

---

## 🌐 Access Points

Once started, access your system at:

| Service | URL | Description |
|---------|-----|-------------|
| **Main App** | http://127.0.0.1:8000 | Web UI interface |
| **API Docs** | http://127.0.0.1:8000/docs | Interactive API documentation |
| **Hermes LLM** | http://127.0.0.1:11434 | LLM server info |
| **Health Check** | http://127.0.0.1:8000/health | API health status |

---

## 🎨 Color Output

The scripts use colored output for better readability:

- 🟢 **Green**: Success messages
- 🔵 **Blue**: Information
- 🟡 **Yellow**: Warnings
- 🔴 **Red**: Errors
- 🟣 **Purple**: Headers
- 🔵 **Cyan**: Section titles

---

## 🔄 Systemd Integration (Optional)

To run as a system service on Linux:

1. Create service file: `/etc/systemd/system/finance-rag.service`

```ini
[Unit]
Description=Personal Finance RAG System
After=network.target

[Service]
Type=forking
User=your_username
WorkingDirectory=/path/to/retro21_finance
ExecStart=/path/to/retro21_finance/start.sh
ExecStop=/path/to/retro21_finance/stop.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl enable finance-rag
sudo systemctl start finance-rag
sudo systemctl status finance-rag
```

---

## 📝 Notes

- Scripts create `logs/` and `pids/` directories automatically
- PID files track running processes for clean shutdown
- Log files rotate automatically (implement logrotate if needed)
- Services start in background (daemon mode)
- Health checks ensure services are fully operational before exiting

---

**✨ Your Personal Finance RAG System is ready to manage!**

For more information, see [SYSTEM_STATUS.md](SYSTEM_STATUS.md)
