# 🚀 Big Data Pipeline - Commands Reference

## 📋 **Table of Contents**
1. [🔄 Complete System Startup Guide](#complete-system-startup-guide)
2. [System Management](#system-management)
3. [Kafka Operations](#kafka-operations)
4. [Producer Operations](#producer-operations)
5. [Consumer Operations](#consumer-operations)
6. [Database Operations](#database-operations)
7. [Monitoring Commands](#monitoring-commands)
8. [Troubleshooting Commands](#troubleshooting-commands)
9. [Data Verification](#data-verification)

---

## 🔄 **Complete System Startup Guide**

### **🌅 Starting Fresh (Tomorrow/After Shutdown)**

**Step 1: Navigate to Project Directory**
```bash
cd "D:\DE Projects\Big Data Project"
```

**Step 2: Verify Docker is Running**
```bash
# Check Docker Desktop is running
docker --version
docker ps
```

**Step 3: Start the Complete System**
```bash
# Start all services (takes 2-3 minutes first time)
docker-compose up -d

# Check all containers are running
docker ps
```

**Step 4: Verify System Health (Wait 2-3 minutes)**
```bash
# Check container status
docker-compose ps

# Verify logs are flowing
docker logs air-quality-app --tail 10

# Check Kafka topics exist
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Verify consumer group is active
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list
```

**Step 5: Verify Data Flow**
```bash
# Check recent messages in Kafka
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic air-quality-data --max-messages 3

# Check database has data
docker exec postgres psql -U airquality_user -d airquality -c "SELECT COUNT(*) FROM air_quality_measurements;"

# Check latest data timestamp
docker exec postgres psql -U airquality_user -d airquality -c "SELECT MAX(timestamp) FROM air_quality_measurements;"
```

**Step 6: Access Web Interfaces**
```bash
# Kafka UI (monitor topics/consumers)
Start-Process "http://localhost:8080"

# Grafana (create dashboards)
Start-Process "http://localhost:3000"  # admin/admin

# Application logs (processing monitoring)
Write-Host "Check application logs: docker logs air-quality-app --tail 20"
```

### **⚡ Quick Start Commands (All-in-One)**
```bash
# Complete startup sequence
cd "D:\DE Projects\Big Data Project"
docker-compose up -d
Start-Sleep 120  # Wait 2 minutes
docker logs air-quality-app --tail 5
Start-Process "http://localhost:8080"
Start-Process "http://localhost:3000"
```

### **🛑 Complete Shutdown**
```bash
# Graceful shutdown (preserves data)
docker-compose down

# Nuclear shutdown (removes everything - BE CAREFUL!)
docker-compose down -v
docker system prune -f
```

### **🔧 If Something Goes Wrong**
```bash
# Restart just the application
docker-compose restart air-quality-app

# Restart infrastructure
docker-compose restart kafka postgres

# Check for errors
docker logs air-quality-app
docker logs kafka
docker logs postgres

# Reset consumer offset (if consumer gets stuck)
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --group air-quality-consumer-group --reset-offsets --to-latest --topic air-quality-data --execute
```

### **🚨 Common Issue: Data Not Updating in PostgreSQL/Grafana**

**Problem**: Producer working, Kafka has messages, but PostgreSQL/Grafana not updating

**Diagnosis Steps:**
```bash
# 1. Check if consumer is active
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group air-quality-consumer-group

# 2. Check for lag (unprocessed messages)
# Look for: LAG > 0 = consumer behind
# Look for: "no active members" = consumer crashed

# 3. Check latest database timestamp
docker exec postgres psql -U airquality_user -d airquality -c "SELECT MAX(timestamp) FROM air_quality_measurements;"

# 4. Compare with current time - if > 10 minutes old, consumer crashed

# 5. Check consumer logs for errors
docker logs air-quality-app --tail 20 | findstr "📊\|❌\|ERROR"
```

**Common Causes & Fixes:**

**A) Consumer Crashed/Stopped (Most Common)**
```bash
# Symptoms: "no active members", LAG > 0, old database timestamp
# Fix: Restart the application
docker-compose restart air-quality-app

# Verify fix
docker logs air-quality-app --tail 10
# Should see: "📊 Processed: City - AQI: XX"
```

**B) Consumer Timeout Issue**
```bash
# Symptoms: Consumer processes then stops, "consumer closed" in logs
# This was fixed in kafka_consumer.py with consumer_timeout_ms=-1
# If it still happens, restart:
docker-compose restart air-quality-app
```

**C) PostgreSQL Connection Issues**
```bash
# Check PostgreSQL is running
docker exec postgres pg_isready

# Test database connection from app
docker exec air-quality-app python -c "
import psycopg2
try:
    conn = psycopg2.connect(host='postgres', database='airquality', user='airquality_user', password='airquality_pass')
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

**D) Kafka Connection Issues**
```bash
# Check if topics exist
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Test message consumption manually
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic air-quality-data --max-messages 3
```

**Quick Fix Command (Try This First):**
```bash
# This fixes 90% of data update issues
docker-compose restart air-quality-app
Start-Sleep 30
docker logs air-quality-app --tail 5
```

### **📊 Daily Health Check**
```bash
echo "=== Daily System Health Check ==="
echo "1. Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo "2. Data Freshness:"
docker exec postgres psql -U airquality_user -d airquality -c "SELECT COUNT(*) as records, MAX(timestamp) as latest FROM air_quality_measurements;"

echo "3. Consumer Status:"
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group air-quality-consumer-group

echo "4. Recent Alerts:"
docker exec postgres psql -U airquality_user -d airquality -c "SELECT city, alert_level, timestamp FROM air_quality_alerts ORDER BY timestamp DESC LIMIT 3;"

echo "5. Consumer Processing (should show recent activity):"
docker logs air-quality-app --tail 5 | findstr "📊 Processed"
```

### **🔍 Data Pipeline Verification Script**
```bash
# Complete end-to-end verification
echo "🧪 Testing Complete Data Pipeline..."

echo "📤 Producer Status:"
docker logs air-quality-app --tail 5 | findstr "published"

echo "📮 Kafka Topics:"
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

echo "📥 Consumer Group:"
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group air-quality-consumer-group

echo "🗄️ Database Status:"
docker exec postgres psql -U airquality_user -d airquality -c "
SELECT 
    COUNT(*) as total_records,
    MAX(timestamp) as latest_update,
    COUNT(DISTINCT city) as cities_monitored,
    AGE(NOW(), MAX(timestamp)) as data_age
FROM air_quality_measurements;
"

echo "✅ Pipeline verification complete!"
```

---

## 🏗️ **System Management**

### **Start/Stop the Entire System**
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart air-quality-app

# View all running containers
docker ps

# View system status
docker-compose ps
```

### **Service Health Checks**
```bash
# Check all container logs
docker-compose logs

# Check specific service logs
docker-compose logs -f air-quality-app
docker-compose logs -f kafka
docker-compose logs -f postgres

# Follow logs in real-time
docker-compose logs -f --tail=50
```

---

## 📮 **Kafka Operations**

### **Topic Management**
```bash
# List all topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Describe topic details
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic air-quality-data
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic air-quality-alerts

# Create new topic (if needed)
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic new-topic --partitions 3 --replication-factor 1

# Delete topic (careful!)
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic topic-name
```

### **Message Inspection**
```bash
# View latest messages from topic
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic air-quality-data --max-messages 5

# View messages from beginning
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic air-quality-data --from-beginning --max-messages 10

# View alert messages
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic air-quality-alerts --from-beginning --max-messages 5

# Monitor live message flow (Ctrl+C to stop)
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic air-quality-data
```

---

## 📤 **Producer Operations**

### **Test Manual Producer**
```bash
# Send test message to air-quality-data topic
docker exec -it kafka kafka-console-producer --bootstrap-server localhost:9092 --topic air-quality-data

# Then type a JSON message:
{"city": "Test City", "aqi": 45, "timestamp": "2025-06-29T12:00:00Z", "message_type": "air_quality_measurement"}
```

### **Monitor Producer Performance**
```bash
# Check producer logs
docker logs air-quality-app | grep -i "producer\|publish"

# View producer metrics in application logs
docker logs air-quality-app --tail 20 | findstr "published"
```

### **Run Standalone Producer**
```bash
# Run just the data collector and producer (if you want to test separately)
docker exec air-quality-app python /app/src/kafka_producer.py
```

---

## 📥 **Consumer Operations**

### **Consumer Group Management**
```bash
# List all consumer groups
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list

# Describe your consumer group
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group air-quality-consumer-group

# Check consumer lag (how far behind)
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group air-quality-consumer-group --verbose

# Reset consumer group offset (start from beginning)
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --group air-quality-consumer-group --reset-offsets --to-earliest --topic air-quality-data --execute
```

### **Run Standalone Consumer**
```bash
# Run the Kafka consumer separately
docker exec air-quality-app python /app/src/kafka_consumer.py

# Run with debug logging
docker exec air-quality-app python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from src.kafka_consumer import main
main()
"
```

### **Consumer Performance Monitoring**
```bash
# Monitor consumer processing
docker logs air-quality-app | grep -i "processed\|consumer"

# Real-time consumer logs
docker logs air-quality-app -f | findstr "📊 Processed"
```

---

## 🗄️ **Database Operations**

### **PostgreSQL Operations**
```bash
# Connect to PostgreSQL
docker exec -it postgres psql -U airquality_user -d airquality

# Quick data queries
docker exec postgres psql -U airquality_user -d airquality -c "SELECT COUNT(*) FROM air_quality_measurements;"

docker exec postgres psql -U airquality_user -d airquality -c "SELECT city, aqi, timestamp FROM air_quality_measurements ORDER BY timestamp DESC LIMIT 10;"

docker exec postgres psql -U airquality_user -d airquality -c "SELECT city, AVG(aqi) as avg_aqi FROM air_quality_measurements GROUP BY city ORDER BY avg_aqi DESC;"

# Check table structure
docker exec postgres psql -U airquality_user -d airquality -c "\d air_quality_measurements"

# Get database size
docker exec postgres psql -U airquality_user -d airquality -c "SELECT pg_size_pretty(pg_database_size('airquality'));"
```

### **Data Export**
```bash
# Export data to CSV
docker exec postgres psql -U airquality_user -d airquality -c "COPY (SELECT * FROM air_quality_measurements) TO '/tmp/air_quality_export.csv' CSV HEADER;"

# Copy exported file from container
docker cp postgres:/tmp/air_quality_export.csv ./air_quality_data.csv
```

---

## 📊 **Monitoring Commands**

### **System Resource Monitoring**
```bash
# Check container resource usage
docker stats

# Check specific container resources
docker stats air-quality-app kafka postgres

# Check disk usage
docker system df

# Check network
docker network ls
docker network inspect bigdataproject_airquality-network
```

### **Application Monitoring**
```bash
# Real-time data collection monitoring
docker logs air-quality-app -f | findstr "Data Collection Cycle"

# Monitor Kafka message flow
docker logs air-quality-app -f | findstr "📊\|✅\|🚨"

# Monitor system health
docker logs air-quality-app | findstr "Health check"
```

### **Performance Metrics**
```bash
# Get total processed messages
docker exec postgres psql -U airquality_user -d airquality -c "
SELECT 
    COUNT(*) as total_measurements,
    COUNT(DISTINCT city) as cities_monitored,
    MAX(timestamp) as latest_data,
    MIN(timestamp) as first_data
FROM air_quality_measurements;
"

# Get alert statistics
docker exec postgres psql -U airquality_user -d airquality -c "
SELECT 
    COUNT(*) as total_alerts,
    alert_level,
    COUNT(*) as count_by_level
FROM air_quality_alerts 
GROUP BY alert_level;
"
```

---

## 🔍 **Troubleshooting Commands**

### **Debug Container Issues**
```bash
# Check if containers are running
docker ps -a

# Check container health
docker inspect air-quality-app | grep -i health

# Access container shell
docker exec -it air-quality-app bash
docker exec -it kafka bash
docker exec -it postgres bash

# Check container environment variables
docker exec air-quality-app env | grep -i kafka
docker exec air-quality-app env | grep -i postgres
```

### **Debug Network Issues**
```bash
# Test network connectivity between containers
docker exec air-quality-app ping kafka
docker exec air-quality-app ping postgres
docker exec air-quality-app telnet kafka 29092
docker exec air-quality-app telnet postgres 5432
```

### **Debug Data Flow Issues**
```bash
# Check if producer is publishing
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic air-quality-data --max-messages 1

# Check if consumer is processing
docker logs air-quality-app --tail 50 | findstr "Processed"

# Check database connectivity
docker exec air-quality-app python -c "
import psycopg2
try:
    conn = psycopg2.connect(host='postgres', database='airquality', user='airquality_user', password='airquality_pass')
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

---

## 📈 **Data Verification**

### **Verify Data Pipeline**
```bash
# 1. Check if producer is creating messages
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic air-quality-data --max-messages 3 --timeout-ms 10000

# 2. Check if consumer is processing
docker logs air-quality-app --tail 10 | findstr "📊 Processed"

# 3. Verify data in database
docker exec postgres psql -U airquality_user -d airquality -c "SELECT COUNT(*) as records, MAX(timestamp) as latest FROM air_quality_measurements;"

# 4. Check for alerts
docker exec postgres psql -U airquality_user -d airquality -c "SELECT city, message, timestamp FROM air_quality_alerts ORDER BY timestamp DESC LIMIT 5;"
```

### **Data Quality Checks**
```bash
# Check for data completeness
docker exec postgres psql -U airquality_user -d airquality -c "
SELECT 
    city,
    COUNT(*) as record_count,
    AVG(aqi) as avg_aqi,
    MIN(timestamp) as first_record,
    MAX(timestamp) as last_record
FROM air_quality_measurements 
GROUP BY city 
ORDER BY record_count DESC;
"

# Check for missing data
docker exec postgres psql -U airquality_user -d airquality -c "
SELECT city, COUNT(*) 
FROM air_quality_measurements 
WHERE aqi IS NULL OR pm25 IS NULL 
GROUP BY city;
"

# Check data freshness
docker exec postgres psql -U airquality_user -d airquality -c "
SELECT 
    city,
    timestamp,
    AGE(NOW(), timestamp) as data_age
FROM air_quality_measurements 
WHERE timestamp = (SELECT MAX(timestamp) FROM air_quality_measurements WHERE city = air_quality_measurements.city)
ORDER BY timestamp DESC;
"
```

---

## 🎛️ **Management Commands**

### **Start Individual Components**
```bash
# Start only infrastructure
docker-compose up -d zookeeper kafka postgres grafana

# Start application separately
docker-compose up -d air-quality-app

# Restart failed components
docker-compose restart kafka
docker-compose restart air-quality-app
```

### **Scale Components**
```bash
# Scale Kafka consumers (if you modify docker-compose.yml)
docker-compose up -d --scale air-quality-app=2

# Check scaled services
docker-compose ps
```

### **Cleanup Commands**
```bash
# Remove all containers and volumes (DESTRUCTIVE!)
docker-compose down -v

# Clean up Docker system
docker system prune -f

# Remove only data volumes
docker volume rm $(docker volume ls -q | grep bigdataproject)

# Reset Kafka topics (delete all messages)
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic air-quality-data
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic air-quality-alerts
```

---

## 🌐 **Web Interface Access**

### **Service URLs**
```bash
# Open web interfaces (use your browser)
# Kafka UI: http://localhost:8080
# Grafana: http://localhost:3000 (admin/admin)
# Application monitoring: Check logs with 'docker logs air-quality-app'

# Quick open commands (Windows)
start http://localhost:8080    # Kafka UI
start http://localhost:3000    # Grafana
docker logs air-quality-app --tail 20    # Application logs

# Quick open commands (PowerShell)
Start-Process "http://localhost:8080"    # Kafka UI
Start-Process "http://localhost:3000"    # Grafana
docker logs air-quality-app --tail 20    # Application logs
```

---

## 🔄 **Complete System Test**

### **End-to-End Verification Script**
```bash
echo "🧪 Testing Complete Data Pipeline..."

echo "1️⃣ Checking containers..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "2️⃣ Checking Kafka topics..."
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

echo "3️⃣ Checking consumer groups..."
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list

echo "4️⃣ Checking database records..."
docker exec postgres psql -U airquality_user -d airquality -c "SELECT COUNT(*) as total_records FROM air_quality_measurements;"

echo "5️⃣ Checking latest data..."
docker exec postgres psql -U airquality_user -d airquality -c "SELECT city, aqi, timestamp FROM air_quality_measurements ORDER BY timestamp DESC LIMIT 5;"

echo "✅ System test complete!"
```

---

## 📝 **Quick Reference Card**

| Task | Command |
|------|---------|
| **Start System** | `docker-compose up -d` |
| **Check Logs** | `docker logs air-quality-app -f` |
| **View Topics** | `docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list` |
| **Check Consumers** | `docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list` |
| **Query Database** | `docker exec postgres psql -U airquality_user -d airquality -c "SELECT COUNT(*) FROM air_quality_measurements;"` |
| **Monitor Messages** | `docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic air-quality-data --max-messages 5` |
| **System Status** | `docker ps` |
| **Stop System** | `docker-compose down` |

---

> 💡 **Pro Tip**: Bookmark this file and use `Ctrl+F` to quickly find commands for specific tasks! 