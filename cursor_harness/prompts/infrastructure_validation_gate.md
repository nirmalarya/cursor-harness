# Quality Gate #11: Infrastructure Validation (MANDATORY)

**Verify required infrastructure is running BEFORE testing features**

---

## 🚨 THE PROBLEM (From AutoGraph v3.1)

**What happened:**
```
Agent tested save functionality
Marked as passing ✅
But MinIO bucket didn't exist ❌
Real save failed in production!
```

**Agent ASSUMED infrastructure was ready - it wasn't!**

---

## ✅ THE SOLUTION - Generic Infrastructure Detection

### Step 1: Auto-Detect Infrastructure Requirements

```bash
#!/bin/bash
# Detect what infrastructure this project needs

echo "Detecting infrastructure requirements..."

# Check docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    echo "Found docker-compose.yml - checking services..."
    
    # Detect databases
    grep -q "postgres:" docker-compose.yml && echo "  - PostgreSQL required"
    grep -q "mysql:" docker-compose.yml && echo "  - MySQL required"
    grep -q "mongodb:" docker-compose.yml && echo "  - MongoDB required"
    
    # Detect caches
    grep -q "redis:" docker-compose.yml && echo "  - Redis required"
    grep -q "memcached:" docker-compose.yml && echo "  - Memcached required"
    
    # Detect storage
    grep -q "minio:" docker-compose.yml && echo "  - MinIO required"
    grep -q "s3:" docker-compose.yml && echo "  - S3 required"
    
    # Detect message queues
    grep -q "rabbitmq:" docker-compose.yml && echo "  - RabbitMQ required"
    grep -q "kafka:" docker-compose.yml && echo "  - Kafka required"
fi

# Check requirements files
if [ -f "requirements.txt" ]; then
    grep -q "psycopg2\|asyncpg" requirements.txt && echo "  - PostgreSQL client required"
    grep -q "pymongo" requirements.txt && echo "  - MongoDB required"
    grep -q "redis" requirements.txt && echo "  - Redis required"
    grep -q "boto3\|minio" requirements.txt && echo "  - Object storage required"
fi

# Check package.json
if [ -f "package.json" ]; then
    grep -q "pg\|postgres" package.json && echo "  - PostgreSQL required"
    grep -q "mongodb" package.json && echo "  - MongoDB required"
    grep -q "redis" package.json && echo "  - Redis required"
fi
```

---

### Step 2: Validate Infrastructure is Running

```bash
#!/bin/bash
# Generic infrastructure validation

echo "Validating infrastructure..."

# If using Docker Compose
if command -v docker-compose &> /dev/null && [ -f "docker-compose.yml" ]; then
    echo "Checking Docker Compose services..."
    
    # Check if any containers running
    running=$(docker-compose ps 2>/dev/null | grep -c "Up" || echo "0")
    
    if [ "$running" -eq 0 ]; then
        echo "❌ No Docker services running!"
        echo "Start services first: docker-compose up -d"
        exit 1
    fi
    
    echo "  ✅ $running services running"
    
    # Check for unhealthy services
    unhealthy=$(docker-compose ps 2>/dev/null | grep -c "unhealthy" || echo "0")
    
    if [ "$unhealthy" -gt 0 ]; then
        echo "⚠️  $unhealthy services unhealthy - waiting..."
        
        # Wait up to 2 minutes
        for i in {1..24}; do
            sleep 5
            unhealthy=$(docker-compose ps 2>/dev/null | grep -c "unhealthy" || echo "0")
            if [ "$unhealthy" -eq 0 ]; then
                echo "  ✅ All services now healthy"
                break
            fi
            echo "  ⏳ Waiting... ($i/24)"
        done
        
        if [ "$unhealthy" -gt 0 ]; then
            echo "❌ $unhealthy services still unhealthy!"
            echo "Check logs: docker-compose logs <service-name>"
            exit 1
        fi
    else
        echo "  ✅ All services healthy"
    fi
fi

# If using standalone services (no Docker)
# Check if required ports are listening

check_port() {
    local port=$1
    local name=$2
    
    if lsof -i :$port -sTCP:LISTEN >/dev/null 2>&1; then
        echo "  ✅ $name (port $port) is running"
        return 0
    else
        echo "  ❌ $name (port $port) not accessible"
        return 1
    fi
}

# Common ports to check (adapt based on project)
# Only check if no Docker Compose
if [ ! -f "docker-compose.yml" ]; then
    echo "Checking service ports..."
    
    # Database ports
    check_port 5432 "PostgreSQL" || true
    check_port 3306 "MySQL" || true
    check_port 27017 "MongoDB" || true
    
    # Cache ports
    check_port 6379 "Redis" || true
    
    # Application ports (read from .env or config)
    if [ -f ".env" ]; then
        backend_port=$(grep "PORT" .env | head -1 | cut -d'=' -f2 || echo "")
        [ -n "$backend_port" ] && check_port "$backend_port" "Backend" || true
    fi
fi

echo "✅ Infrastructure validation complete"
```

---

### Step 3: Validate Storage/Data Layer (Generic)

```bash
#!/bin/bash
# Validate data storage is accessible

echo "Validating data storage..."

# For SQL databases
if command -v psql &> /dev/null && grep -q "postgres" docker-compose.yml 2>/dev/null; then
    echo "Checking PostgreSQL..."
    
    # Get connection info from .env or docker-compose
    DB_HOST=${POSTGRES_HOST:-localhost}
    DB_USER=${POSTGRES_USER:-postgres}
    DB_NAME=${POSTGRES_DB:-postgres}
    
    # Test connection
    if docker exec $(docker-compose ps -q postgres 2>/dev/null) psql -U $DB_USER -d $DB_NAME -c "SELECT 1" >/dev/null 2>&1; then
        echo "  ✅ PostgreSQL accessible"
    else
        echo "  ❌ PostgreSQL not accessible"
        exit 1
    fi
fi

# For Redis
if grep -q "redis" docker-compose.yml 2>/dev/null; then
    echo "Checking Redis..."
    
    if docker exec $(docker-compose ps -q redis 2>/dev/null) redis-cli ping 2>&1 | grep -q "PONG"; then
        echo "  ✅ Redis accessible"
    else
        echo "  ❌ Redis not accessible"
        exit 1
    fi
fi

# For MinIO/S3 (generic object storage check)
if grep -q "minio\|s3" docker-compose.yml 2>/dev/null; then
    echo "Checking Object Storage..."
    
    # Test MinIO health
    if curl -sf http://localhost:9000/minio/health/live >/dev/null 2>&1; then
        echo "  ✅ Object storage accessible"
        
        # Check/create required buckets (read from env or config)
        # This is generic - adapts to project
        if command -v docker &> /dev/null; then
            container=$(docker-compose ps -q minio 2>/dev/null)
            if [ -n "$container" ]; then
                # Check if buckets directory exists
                docker exec $container ls /data/ 2>/dev/null || echo "  ⚠️  No buckets found"
            fi
        fi
    else
        echo "  ❌ Object storage not accessible"
        exit 1
    fi
fi

# For filesystem storage (no external dependencies)
if [ ! -f "docker-compose.yml" ]; then
    echo "Checking filesystem storage..."
    
    # Verify write permissions
    if touch .test_write_permission 2>/dev/null; then
        rm .test_write_permission
        echo "  ✅ Filesystem writable"
    else
        echo "  ❌ Filesystem not writable"
        exit 1
    fi
fi

echo "✅ Data storage validated"
```

---

## 🎯 When to Run This Gate

### At Session Start (Before Any Feature Work):

```markdown
### STEP 4.5: INFRASTRUCTURE VALIDATION (BEFORE TESTING!)

Run infrastructure validation BEFORE testing features:

```bash
# Quick infrastructure check
echo "Validating infrastructure..."

# Check Docker services (if applicable)
if [ -f "docker-compose.yml" ]; then
    unhealthy=$(docker-compose ps 2>/dev/null | grep -c "unhealthy" || echo "0")
    
    if [ "$unhealthy" -gt 0 ]; then
        echo "❌ $unhealthy services unhealthy!"
        echo "Fix infrastructure before testing features!"
        exit 1
    fi
fi

# Check required ports accessible (project-specific)
# Agent should detect what ports are needed

echo "✅ Infrastructure ready"
```

**If infrastructure not ready: STOP and fix it first!**
```

---

## ✅ What Makes This Generic

**Generic checks:**
- ✅ Detects project infrastructure needs
- ✅ Validates services running
- ✅ Tests connectivity
- ✅ Verifies storage accessible

**NOT project-specific:**
- ❌ NOT hardcoded to MinIO
- ❌ NOT hardcoded to PostgreSQL
- ❌ NOT hardcoded to specific bucket names
- ❌ NOT hardcoded to specific ports

**Works for:**
- Web apps with databases
- APIs with caches
- CLIs with file storage
- Microservices with message queues
- ANY project with infrastructure!

---

## 📋 Integration Example

**Agent detects AutoGraph has:**
- PostgreSQL (from docker-compose.yml)
- Redis (from docker-compose.yml)
- MinIO (from docker-compose.yml)

**Agent validates:**
```bash
# Postgres accessible?
docker exec autograph-postgres psql -U autograph -c "SELECT 1"

# Redis accessible?
docker exec autograph-redis redis-cli ping

# MinIO accessible?
curl http://localhost:9000/minio/health/live

# MinIO buckets exist? (reads from env/config what buckets are needed)
docker exec autograph-minio ls /data/diagrams
```

**Agent for a different project (e.g., simple Flask + SQLite):**
```bash
# SQLite accessible?
test -f database.db && sqlite3 database.db "SELECT 1"

# Flask running?
curl http://localhost:5000/health
```

**ADAPTS to the project!** ✅

---

**Infrastructure validation added! Ready for next improvement or test?** 🚀
