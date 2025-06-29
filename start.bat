@echo off
setlocal enabledelayedexpansion

:: Air Quality Monitoring System - Windows Startup Script
title Air Quality Monitoring System Setup

echo.
echo 🌍 Air Quality Monitoring System
echo ==================================
echo.

:: Check if Docker is installed
echo [INFO] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop from: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed or not in PATH
    echo Please install Docker Desktop which includes Docker Compose
    pause
    exit /b 1
)

echo [SUCCESS] Docker and Docker Compose are installed
echo.

:: Create directories
echo [INFO] Setting up project structure...
if not exist "src" mkdir src
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "spark" mkdir spark
if not exist "spark\apps" mkdir spark\apps
if not exist "spark\data" mkdir spark\data
if not exist "grafana" mkdir grafana
if not exist "grafana\provisioning" mkdir grafana\provisioning
if not exist "grafana\provisioning\dashboards" mkdir grafana\provisioning\dashboards
if not exist "grafana\provisioning\datasources" mkdir grafana\provisioning\datasources

:: Create .env file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating .env configuration file...
    (
        echo # Air Quality Monitoring System Configuration
        echo OPENWEATHER_API_KEY=your_openweather_api_key_here
        echo AIRVISUAL_API_KEY=your_airvisual_api_key_here
        echo WAQI_API_KEY=your_waqi_api_key_here
        echo.
        echo # PostgreSQL Configuration
        echo POSTGRES_DB=airquality
        echo POSTGRES_USER=airquality_user
        echo POSTGRES_PASSWORD=airquality_pass
        echo.
        echo # Kafka Configuration
        echo KAFKA_BOOTSTRAP_SERVERS=kafka:29092
        echo.
        echo # InfluxDB Configuration
        echo INFLUXDB_URL=http://influxdb:8086
        echo INFLUXDB_TOKEN=my-super-secret-auth-token
        echo INFLUXDB_ORG=airquality-org
        echo INFLUXDB_BUCKET=airquality-bucket
    ) > .env
    echo [SUCCESS] .env file created
) else (
    echo [INFO] .env file already exists
)

echo [SUCCESS] Project structure created
echo.

:: API Key Configuration
echo [INFO] API Key Configuration
echo.
echo The system can work with mock data, but for real air quality data,
echo you'll need API keys from these FREE services:
echo.
echo 1. OpenWeatherMap (1000 calls/day): https://openweathermap.org/api
echo 2. AirVisual (10000 calls/month): https://www.iqair.com/air-pollution-data-api  
echo 3. World Air Quality Index (free): https://aqicn.org/data-platform/token/
echo.
set /p configure_apis="Do you want to configure API keys now? (y/n): "

if /i "!configure_apis!"=="y" (
    echo.
    set /p openweather_key="OpenWeatherMap API Key (press Enter to skip): "
    set /p airvisual_key="AirVisual API Key (press Enter to skip): "
    set /p waqi_key="WAQI API Key (press Enter to skip): "
    
    if not "!openweather_key!"=="" (
        powershell -Command "(Get-Content .env) -replace 'OPENWEATHER_API_KEY=.*', 'OPENWEATHER_API_KEY=!openweather_key!' | Set-Content .env"
    )
    if not "!airvisual_key!"=="" (
        powershell -Command "(Get-Content .env) -replace 'AIRVISUAL_API_KEY=.*', 'AIRVISUAL_API_KEY=!airvisual_key!' | Set-Content .env"
    )
    if not "!waqi_key!"=="" (
        powershell -Command "(Get-Content .env) -replace 'WAQI_API_KEY=.*', 'WAQI_API_KEY=!waqi_key!' | Set-Content .env"
    )
    echo [SUCCESS] API keys configured
)

echo.
echo [INFO] Starting Air Quality Monitoring System...
echo This may take a few minutes as Docker downloads and starts all services...
echo.

:: Start the system
docker-compose up -d

if errorlevel 1 (
    echo [ERROR] Failed to start the system
    echo Please check Docker Desktop is running and try again
    pause
    exit /b 1
)

echo [SUCCESS] System started!
echo.

:: Wait for services
echo [INFO] Waiting for services to be ready (this may take 2-3 minutes)...
timeout /t 30 /nobreak >nul

echo.
echo 🎉 Air Quality Monitoring System is running!
echo.
echo Access Points:
echo ==============
echo • Kafka UI:        http://localhost:8080
echo • Grafana:         http://localhost:3000 (admin/admin)  
echo • Spark Master:    http://localhost:8081
echo • PostgreSQL:      localhost:5432
echo.
echo Useful Commands:
echo ===============
echo • View logs:       docker-compose logs -f
echo • Stop system:     docker-compose down
echo • System status:   docker-compose ps
echo.

:: Ask to open dashboards
set /p open_browser="Would you like to open the dashboards in your browser? (y/n): "
if /i "!open_browser!"=="y" (
    echo [INFO] Opening dashboards...
    start http://localhost:3000
    start http://localhost:8080
    timeout /t 2 /nobreak >nul
    start http://localhost:8081
)

echo.
echo [SUCCESS] Setup complete! The Air Quality Monitoring System is running.
echo [INFO] Check the browser tabs for your dashboards.
echo [INFO] To stop the system, run: docker-compose down
echo.
echo Press any key to exit this setup script...
pause >nul 