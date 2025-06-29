#!/bin/bash

# Air Quality Monitoring System - Startup Script
# This script helps you get started with the system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "🌍 Air Quality Monitoring System"
    echo "=================================="
    echo -e "${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check system resources
check_resources() {
    print_info "Checking system resources..."
    
    # Check available memory (Linux/Mac)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        total_mem=$(free -g | awk '/^Mem:/{print $2}')
        if [ "$total_mem" -lt 8 ]; then
            print_warning "Your system has less than 8GB RAM. The system might run slowly."
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        total_mem=$(sysctl hw.memsize | awk '{print int($2/1024/1024/1024)}')
        if [ "$total_mem" -lt 8 ]; then
            print_warning "Your system has less than 8GB RAM. The system might run slowly."
        fi
    fi
    
    # Check available disk space
    available_space=$(df . | tail -1 | awk '{print $4}')
    if [ "$available_space" -lt 20000000 ]; then  # 20GB in KB
        print_warning "You have less than 20GB free disk space. Consider freeing up space."
    fi
    
    print_success "System resources checked"
}

# Setup project
setup_project() {
    print_info "Setting up project structure..."
    
    if ! command -v make &> /dev/null; then
        print_warning "Make is not installed. Running setup manually..."
        mkdir -p src data logs spark/apps spark/data grafana/provisioning/dashboards grafana/provisioning/datasources
    else
        make setup
    fi
    
    print_success "Project structure created"
}

# Configure API keys
configure_apis() {
    print_info "API Key Configuration"
    echo ""
    echo "The system can work with mock data, but for real air quality data,"
    echo "you'll need API keys from these free services:"
    echo ""
    echo "1. OpenWeatherMap (1000 calls/day): https://openweathermap.org/api"
    echo "2. AirVisual (10000 calls/month): https://www.iqair.com/air-pollution-data-api"
    echo "3. World Air Quality Index (free): https://aqicn.org/data-platform/token/"
    echo ""
    
    if [ -f .env ]; then
        print_info "Found existing .env file. You can edit it to add your API keys."
        echo ""
        read -p "Do you want to configure API keys now? (y/n): " configure_now
        
        if [[ $configure_now =~ ^[Yy]$ ]]; then
            echo ""
            read -p "OpenWeatherMap API Key (press Enter to skip): " openweather_key
            read -p "AirVisual API Key (press Enter to skip): " airvisual_key
            read -p "WAQI API Key (press Enter to skip): " waqi_key
            
            if [ ! -z "$openweather_key" ]; then
                sed -i "s/OPENWEATHER_API_KEY=.*/OPENWEATHER_API_KEY=$openweather_key/" .env
            fi
            
            if [ ! -z "$airvisual_key" ]; then
                sed -i "s/AIRVISUAL_API_KEY=.*/AIRVISUAL_API_KEY=$airvisual_key/" .env
            fi
            
            if [ ! -z "$waqi_key" ]; then
                sed -i "s/WAQI_API_KEY=.*/WAQI_API_KEY=$waqi_key/" .env
            fi
            
            print_success "API keys configured"
        fi
    else
        print_warning ".env file not found. Please run 'make setup' first."
    fi
}

# Start the system
start_system() {
    print_info "Starting Air Quality Monitoring System..."
    print_info "This may take a few minutes as Docker downloads and starts all services..."
    
    if command -v make &> /dev/null; then
        make up
    else
        docker-compose up -d
    fi
    
    print_success "System started!"
}

# Wait for services to be ready
wait_for_services() {
    print_info "Waiting for services to be ready..."
    
    # Wait for Kafka
    print_info "Waiting for Kafka..."
    timeout=60
    while ! docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; do
        sleep 5
        timeout=$((timeout - 5))
        if [ $timeout -le 0 ]; then
            print_warning "Kafka is taking longer than expected to start"
            break
        fi
    done
    
    # Wait for PostgreSQL
    print_info "Waiting for PostgreSQL..."
    timeout=60
    while ! docker exec postgres pg_isready -U airquality_user &> /dev/null; do
        sleep 5
        timeout=$((timeout - 5))
        if [ $timeout -le 0 ]; then
            print_warning "PostgreSQL is taking longer than expected to start"
            break
        fi
    done
    
    print_success "Services are ready!"
}

# Show access information
show_access_info() {
    echo ""
    print_success "🎉 Air Quality Monitoring System is running!"
    echo ""
    echo "Access Points:"
    echo "=============="
    echo "• Kafka UI:        http://localhost:8080"
    echo "• Grafana:         http://localhost:3000 (admin/admin)"
    echo "• Spark Master:    http://localhost:8081"
    echo "• Prometheus:      http://localhost:9090"
    echo "• PostgreSQL:      localhost:5432"
    echo ""
    echo "Useful Commands:"
    echo "==============="
    echo "• View logs:       make logs"
    echo "• Stop system:     make down"
    echo "• System status:   make status"
    echo "• Monitor system:  make monitor"
    echo ""
    echo "📖 For detailed documentation, see README.md"
    echo ""
}

# Open dashboards
open_dashboards() {
    read -p "Would you like to open the dashboards in your browser? (y/n): " open_browser
    
    if [[ $open_browser =~ ^[Yy]$ ]]; then
        print_info "Opening dashboards..."
        
        # Try to open URLs in default browser
        if command -v open &> /dev/null; then  # macOS
            open http://localhost:3000 &  # Grafana
            open http://localhost:8080 &  # Kafka UI
        elif command -v xdg-open &> /dev/null; then  # Linux
            xdg-open http://localhost:3000 &  # Grafana
            xdg-open http://localhost:8080 &  # Kafka UI
        else
            print_info "Please manually open these URLs in your browser:"
            echo "  http://localhost:3000 (Grafana)"
            echo "  http://localhost:8080 (Kafka UI)"
        fi
    fi
}

# Main execution
main() {
    print_header
    
    print_info "Starting setup process..."
    
    # Step 1: Check prerequisites
    check_docker
    check_resources
    
    # Step 2: Setup project
    setup_project
    
    # Step 3: Configure APIs (optional)
    configure_apis
    
    # Step 4: Start system
    start_system
    
    # Step 5: Wait for services
    wait_for_services
    
    # Step 6: Show access information
    show_access_info
    
    # Step 7: Open dashboards (optional)
    open_dashboards
    
    print_success "Setup complete! The Air Quality Monitoring System is running."
    print_info "Press Ctrl+C to stop the system, or run 'make down' to stop all services."
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}Stopping setup...${NC}"; exit 1' INT

# Run main function
main "$@" 