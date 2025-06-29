# 🚀 5-Minute Quick Start Guide

Get your Air Quality Monitoring System up and running in just 5 minutes!

## Step 1: Prerequisites ✅

Make sure you have:
- **Docker Desktop** installed and running
- At least **4GB RAM** available for Docker
- **Internet connection** for downloading images

> **Don't have Docker?** Download it from: https://docs.docker.com/desktop/windows/

## Step 2: Run the System 🏃‍♂️

### Option A: Automated Setup (Recommended)
```bash
# Double-click this file or run in PowerShell:
start.bat
```

### Option B: Manual Setup
```bash
# 1. Start all services
docker-compose up -d

# 2. Wait 2-3 minutes for services to start
# 3. Open your browser to http://localhost:3000
```

## Step 3: Access Your Dashboards 📊

Once the system is running, open these URLs:

| Service | URL | Login |
|---------|-----|-------|
| **Grafana (Main Dashboard)** | http://localhost:3000 | admin/admin |
| **Kafka UI (Data Streams)** | http://localhost:8080 | - |


## Step 4: See Your Data 📈

1. **Go to Grafana**: http://localhost:3000
2. **Login**: admin/admin
3. **You'll see**: Real-time air quality data for 8 major cities
4. **Data includes**: AQI, PM2.5, PM10, temperature, humidity, alerts

## What You're Seeing 🔍

- **Real-time air quality data** from 8 cities (New York, London, Tokyo, Beijing, Delhi, LA, Mexico City, São Paulo)
- **Mock data** that simulates realistic air quality patterns
- **Kafka streams** processing data in real-time
- **Kafka Consumer** analyzing and enriching the data
- **PostgreSQL** storing processed data
- **PostgreSQL** storing processed air quality data

## Common Commands 🛠️

```bash
# View logs
docker-compose logs -f

# Stop the system
docker-compose down

# Restart the system
docker-compose up -d

# Check status
docker-compose ps
```

## Troubleshooting 🔧

### Services won't start?
```bash
# Check Docker is running
docker version

# Check available resources
docker system df

# Restart Docker Desktop
```

### No data appearing?
- Wait 5-10 minutes for all services to initialize
- Check logs: `docker-compose logs air-quality-app`
- The system uses mock data by default (works without API keys)

### Grafana won't load?
- Wait 2-3 minutes after starting
- Try: http://localhost:3000
- Check container: `docker-compose ps`

## Next Steps 🌟

1. **Get Real Data**: Add API keys to `.env` file
2. **Add Cities**: Edit `src/config.py` to monitor your city
3. **Customize Alerts**: Modify alert thresholds in config
4. **Explore Kafka**: Check real-time data streams in Kafka UI
5. **Learn**: Study the code to understand the data pipeline

## Need Help? 💬

- Check the full **README.md** for detailed documentation
- Look at **docker-compose.yml** to understand the architecture
- Examine **src/** folder for Python code
- Use `docker-compose logs <service-name>` to debug issues

---

## 🎯 You've Built a Production-Ready Big Data System!

**What you just deployed:**
- Real-time data streaming with **Apache Kafka**
- Stream processing with **Python Kafka Consumer**
- Relational database with **PostgreSQL**
- Relational database with **PostgreSQL**
- Real-time dashboards with **Grafana**
- Containerized microservices with **Docker**

**This is enterprise-grade technology** used by companies like Netflix, Uber, and Airbnb!

---

🚀 **Start exploring your dashboards now!** 