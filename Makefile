# Air Quality Monitoring System Makefile

.PHONY: help setup build up down logs clean test kafka-topics kafka-ui postgres grafana spark

# Default target
help:
	@echo "Air Quality Monitoring System"
	@echo "============================="
	@echo ""
	@echo "Available commands:"
	@echo "  setup       - Initial setup (create directories, .env file)"
	@echo "  build       - Build Docker images"
	@echo "  up          - Start all services"
	@echo "  down        - Stop all services"
	@echo "  restart     - Restart all services"
	@echo "  logs        - Show logs from all services"
	@echo "  clean       - Clean up containers, volumes, and images"
	@echo ""
	@echo "Individual services:"
	@echo "  kafka-ui    - Open Kafka UI in browser"
	@echo "  postgres    - Connect to PostgreSQL"
	@echo "  grafana     - Open Grafana in browser"
	@echo "  spark       - Open Spark Master UI in browser"
	@echo ""
	@echo "Kafka management:"
	@echo "  kafka-topics - List Kafka topics"
	@echo "  kafka-reset  - Reset Kafka topics (delete all data)"
	@echo ""
	@echo "Development:"
	@echo "  test        - Run tests"
	@echo "  format      - Format Python code"
	@echo "  lint        - Lint Python code"

# Setup project
setup:
	@echo "Setting up Air Quality Monitoring System..."
	@mkdir -p src data logs spark/apps spark/data grafana/provisioning/dashboards grafana/provisioning/datasources
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		echo "# Air Quality Monitoring System Configuration" > .env; \
		echo "OPENWEATHER_API_KEY=your_openweather_api_key_here" >> .env; \
		echo "AIRVISUAL_API_KEY=your_airvisual_api_key_here" >> .env; \
		echo "WAQI_API_KEY=your_waqi_api_key_here" >> .env; \
		echo "" >> .env; \
		echo "# PostgreSQL Configuration" >> .env; \
		echo "POSTGRES_DB=airquality" >> .env; \
		echo "POSTGRES_USER=airquality_user" >> .env; \
		echo "POSTGRES_PASSWORD=airquality_pass" >> .env; \
		echo "" >> .env; \
		echo "# Kafka Configuration" >> .env; \
		echo "KAFKA_BOOTSTRAP_SERVERS=kafka:29092" >> .env; \
		echo "" >> .env; \
		echo "# InfluxDB Configuration" >> .env; \
		echo "INFLUXDB_URL=http://influxdb:8086" >> .env; \
		echo "INFLUXDB_TOKEN=my-super-secret-auth-token" >> .env; \
		echo "INFLUXDB_ORG=airquality-org" >> .env; \
		echo "INFLUXDB_BUCKET=airquality-bucket" >> .env; \
		echo ".env file created. Please edit it with your API keys."; \
	else \
		echo ".env file already exists."; \
	fi
	@echo "Setup complete! Please edit .env file with your API keys."
	@echo "Run 'make up' to start the system."

# Build Docker images
build:
	@echo "Building Docker images..."
	docker-compose build

# Start all services
up:
	@echo "Starting Air Quality Monitoring System..."
	docker-compose up -d
	@echo ""
	@echo "Services starting up... This may take a few minutes."
	@echo ""
	@echo "Access points:"
	@echo "  Kafka UI:        http://localhost:8080"
	@echo "  Grafana:         http://localhost:3000 (admin/admin)"
	@echo "  Spark Master:    http://localhost:8081"
	@echo "  Prometheus:      http://localhost:9090"
	@echo "  PostgreSQL:      localhost:5432"
	@echo ""
	@echo "Use 'make logs' to see logs from all services."

# Stop all services
down:
	@echo "Stopping Air Quality Monitoring System..."
	docker-compose down

# Restart services
restart: down up

# Show logs
logs:
	docker-compose logs -f

# Show logs for specific service
logs-%:
	docker-compose logs -f $*

# Clean up everything
clean:
	@echo "Cleaning up containers, volumes, and images..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "Cleanup complete."

# Open Kafka UI
kafka-ui:
	@echo "Opening Kafka UI..."
	@python -c "import webbrowser; webbrowser.open('http://localhost:8080')" 2>/dev/null || \
	echo "Please open http://localhost:8080 in your browser"

# List Kafka topics
kafka-topics:
	@echo "Kafka topics:"
	docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Reset Kafka topics (delete all data)
kafka-reset:
	@echo "Resetting Kafka topics..."
	docker exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic air-quality-data || true
	docker exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic air-quality-alerts || true
	@echo "Kafka topics reset."

# Connect to PostgreSQL
postgres:
	@echo "Connecting to PostgreSQL..."
	docker exec -it postgres psql -U airquality_user -d airquality

# Open Grafana
grafana:
	@echo "Opening Grafana..."
	@python -c "import webbrowser; webbrowser.open('http://localhost:3000')" 2>/dev/null || \
	echo "Please open http://localhost:3000 in your browser (admin/admin)"

# Open Spark Master UI
spark:
	@echo "Opening Spark Master UI..."
	@python -c "import webbrowser; webbrowser.open('http://localhost:8081')" 2>/dev/null || \
	echo "Please open http://localhost:8081 in your browser"

# Run tests
test:
	@echo "Running tests..."
	docker-compose exec air-quality-app python -m pytest tests/ -v

# Format Python code
format:
	@echo "Formatting Python code..."
	docker-compose exec air-quality-app python -m black src/ --line-length 100

# Lint Python code
lint:
	@echo "Linting Python code..."
	docker-compose exec air-quality-app python -m flake8 src/ --max-line-length 100

# Show system status
status:
	@echo "System Status:"
	@echo "=============="
	docker-compose ps

# Show container stats
stats:
	@echo "Container Stats:"
	@echo "==============="
	docker stats --no-stream

# Backup data
backup:
	@echo "Creating backup..."
	@mkdir -p backups
	docker exec postgres pg_dump -U airquality_user airquality > backups/postgres_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in backups/"

# Restore data
restore:
	@echo "Available backups:"
	@ls -la backups/*.sql 2>/dev/null || echo "No backups found"
	@echo "To restore: docker exec -i postgres psql -U airquality_user airquality < backups/your_backup.sql"

# Development server (without Docker)
dev:
	@echo "Starting development server..."
	@echo "Make sure you have PostgreSQL, Kafka, and other services running locally."
	cd src && python main.py

# Install Python dependencies locally
install:
	pip install -r requirements.txt

# Generate sample data for testing
sample-data:
	@echo "Generating sample data..."
	docker-compose exec air-quality-app python -c "from src.data_collector import AirQualityDataCollector; c = AirQualityDataCollector(); print(c.collect_all_cities_data())"

# Monitor system
monitor:
	@echo "System monitoring (Press Ctrl+C to stop)..."
	watch -n 5 'echo "=== Container Status ==="; docker-compose ps; echo ""; echo "=== Kafka Topics ==="; docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null || echo "Kafka not ready"; echo ""; echo "=== Latest Logs ==="; docker-compose logs --tail=10' 