# Redis Testing Guide

## Quick Start

### 1. Check if Redis is Installed
```bash
redis-cli --version
```

If not installed:
- **macOS**: `brew install redis`
- **Linux**: `sudo apt-get install redis-server`
- **Docker**: `docker run -d -p 6379:6379 --name redis redis`

### 2. Start Redis

**macOS (Homebrew):**
```bash
brew services start redis
```

**Linux:**
```bash
sudo systemctl start redis
# OR run directly:
redis-server
```

**Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis
```

### 3. Test Redis Connection
```bash
redis-cli ping
# Should return: PONG
```

### 4. Test with Python Script
```bash
python test_redis.py
```

This will:
- Check if Redis is connected
- Test SET operation
- Test GET operation
- Test DELETE operation

### 5. Test with Your API

1. Start your FastAPI server:
```bash
uvicorn app.main:app --reload
```

2. Make a request (first time - cache miss):
```bash
curl http://localhost:8000/players/1/features?season=2023-24
```

3. Make the same request again (should be faster - cache hit):
```bash
curl http://localhost:8000/players/1/features?season=2023-24
```

4. Check Redis to see cached data:
```bash
redis-cli
> KEYS *
> GET player:1:features:2023-24
> TTL player:1:features:2023-24  # See remaining time
> exit
```

### 6. Stop Redis

**macOS (Homebrew):**
```bash
brew services stop redis
```

**Linux:**
```bash
sudo systemctl stop redis
# OR kill the process:
pkill redis-server
```

**Docker:**
```bash
docker stop redis
docker rm redis
```

## Check Redis Status

**macOS:**
```bash
brew services list | grep redis
```

**Linux:**
```bash
sudo systemctl status redis
```

**Docker:**
```bash
docker ps | grep redis
```

## Useful Redis Commands

```bash
redis-cli

# List all keys
KEYS *

# Get a specific key
GET player:1:features:2023-24

# See TTL (time to live) of a key
TTL player:1:features:2023-24

# Delete a key
DEL player:1:features:2023-24

# Delete all keys (use with caution!)
FLUSHDB

# Get info about Redis
INFO

# Exit
exit
```

## Troubleshooting

### Redis not connecting?
1. Check if Redis is running: `redis-cli ping`
2. Check Redis logs
3. Verify connection settings in `app/cache.py`
4. Check firewall/port 6379

### Application works without Redis?
That's normal! The app gracefully degrades - it will just query the database directly if Redis is unavailable.
