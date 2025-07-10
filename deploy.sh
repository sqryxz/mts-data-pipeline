#!/bin/bash
# MTS Production Deployment Script
set -e

# Configuration
PROJECT_NAME="mts-pipeline"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if user is in docker group
    if ! groups $USER | grep &> /dev/null '\bdocker\b'; then
        log_warning "User $USER is not in the docker group. You may need to use sudo with docker commands."
    fi
    
    log_success "Prerequisites check completed"
}

# Create environment file if it doesn't exist
create_env_file() {
    if [[ ! -f $ENV_FILE ]]; then
        log_info "Creating environment file..."
        cat > $ENV_FILE << EOF
# MTS Pipeline Environment Configuration

# API Security
API_SECRET_KEY=$(openssl rand -hex 32)

# External APIs
FRED_API_KEY=your_fred_api_key_here
COINGECKO_BASE_URL=https://api.coingecko.com/api/v3

# Database
DATABASE_PATH=/app/data/crypto_data.db

# Redis
REDIS_URL=redis://redis:6379/0

# Monitoring
GRAFANA_PASSWORD=admin_change_me

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Strategy Configuration
ENABLED_STRATEGIES=vix_correlation,mean_reversion
STRATEGY_WEIGHTS=vix_correlation:0.6,mean_reversion:0.4

# Risk Management
MAX_POSITION_SIZE=0.10
MAX_DAILY_TRADES=50
MAX_PORTFOLIO_RISK=0.25

# Intervals (minutes)
SIGNAL_GENERATION_INTERVAL_MINUTES=60
DATA_COLLECTION_INTERVAL_MINUTES=30
MACRO_DATA_COLLECTION_INTERVAL_HOURS=6

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8001
HEALTH_CHECK_INTERVAL_SECONDS=60

# Alerts
ENABLE_ALERTS=false
ALERT_EMAIL_SMTP_SERVER=
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_USERNAME=
ALERT_EMAIL_PASSWORD=
ALERT_EMAIL_FROM=
ALERT_EMAIL_TO=
EOF
        log_success "Environment file created at $ENV_FILE"
        log_warning "Please edit $ENV_FILE with your actual configuration values"
    else
        log_info "Environment file already exists"
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p data logs config/strategies monitoring/grafana monitoring ssl
    
    # Create strategy config files if they don't exist
    if [[ ! -f config/strategies/vix_correlation.json ]]; then
        cat > config/strategies/vix_correlation.json << EOF
{
    "name": "VIX_Correlation_Strategy",
    "assets": ["bitcoin", "ethereum", "binancecoin"],
    "correlation_thresholds": {
        "strong_negative": -0.6,
        "strong_positive": 0.6
    },
    "lookback_days": 30,
    "position_size": 0.02
}
EOF
    fi
    
    if [[ ! -f config/strategies/mean_reversion.json ]]; then
        cat > config/strategies/mean_reversion.json << EOF
{
    "name": "Mean_Reversion_Strategy",
    "assets": ["bitcoin", "ethereum", "binancecoin"],
    "vix_spike_threshold": 25,
    "drawdown_threshold": 0.10,
    "lookback_days": 14,
    "position_size": 0.025
}
EOF
    fi
    
    log_success "Directories and configuration files created"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    docker-compose build --no-cache
    
    log_success "Docker images built successfully"
}

# Start services
start_services() {
    log_info "Starting MTS services..."
    
    # Start core services first
    docker-compose up -d redis
    sleep 5
    
    # Start main application
    docker-compose up -d mts-pipeline
    sleep 10
    
    # Start optional monitoring services
    if [[ "${1:-}" == "--with-monitoring" ]]; then
        log_info "Starting monitoring services..."
        docker-compose up -d prometheus grafana
    fi
    
    log_success "Services started successfully"
}

# Stop services
stop_services() {
    log_info "Stopping MTS services..."
    
    docker-compose down
    
    log_success "Services stopped successfully"
}

# Check service health
check_health() {
    log_info "Checking service health..."
    
    # Wait for services to be ready
    sleep 10
    
    # Check API health
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "API service is healthy"
    else
        log_error "API service is not responding"
        return 1
    fi
    
    # Check Redis
    if docker-compose exec redis redis-cli ping | grep -q PONG; then
        log_success "Redis service is healthy"
    else
        log_error "Redis service is not responding"
        return 1
    fi
    
    log_success "All services are healthy"
}

# View logs
view_logs() {
    local service=${1:-mts-pipeline}
    log_info "Viewing logs for $service..."
    
    docker-compose logs -f $service
}

# Backup data
backup_data() {
    log_info "Creating backup..."
    
    mkdir -p $BACKUP_DIR
    backup_file="$BACKUP_DIR/mts-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    tar -czf $backup_file data/ logs/ config/
    
    log_success "Backup created: $backup_file"
}

# Update deployment
update_deployment() {
    log_info "Updating deployment..."
    
    # Create backup first
    backup_data
    
    # Pull latest changes
    git pull
    
    # Rebuild images
    build_images
    
    # Restart services
    docker-compose down
    start_services
    
    # Check health
    check_health
    
    log_success "Deployment updated successfully"
}

# Show status
show_status() {
    log_info "Service Status:"
    docker-compose ps
    
    echo ""
    log_info "Resource Usage:"
    docker stats --no-stream
    
    echo ""
    log_info "Recent Logs:"
    docker-compose logs --tail=10 mts-pipeline
}

# Interactive setup
setup_interactive() {
    log_info "Starting interactive setup..."
    
    # Check prerequisites
    check_prerequisites
    
    # Create environment file
    create_env_file
    
    # Prompt for FRED API key
    if ! grep -q "your_fred_api_key_here" $ENV_FILE 2>/dev/null; then
        echo ""
        read -p "Enter your FRED API key: " fred_key
        if [[ -n "$fred_key" ]]; then
            sed -i "s/your_fred_api_key_here/$fred_key/" $ENV_FILE
        fi
    fi
    
    # Create directories
    create_directories
    
    echo ""
    log_info "Setup completed. You can now run: ./deploy.sh start"
}

# Show help
show_help() {
    cat << EOF
MTS Pipeline Deployment Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  setup           Interactive setup (run this first)
  start           Start all services
  stop            Stop all services
  restart         Restart all services
  status          Show service status
  logs [service]  View logs (default: mts-pipeline)
  health          Check service health
  backup          Create data backup
  update          Update deployment
  build           Build Docker images
  
Options:
  --with-monitoring   Include monitoring services (Prometheus, Grafana)
  
Examples:
  $0 setup                    # Initial setup
  $0 start --with-monitoring  # Start with monitoring
  $0 logs redis              # View Redis logs
  $0 status                  # Show status
  
For more information, see README.md
EOF
}

# Main script logic
main() {
    check_root
    
    case "${1:-}" in
        setup)
            setup_interactive
            ;;
        start)
            create_directories
            start_services "$2"
            check_health
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            start_services "$2"
            check_health
            ;;
        status)
            show_status
            ;;
        logs)
            view_logs "$2"
            ;;
        health)
            check_health
            ;;
        backup)
            backup_data
            ;;
        update)
            update_deployment
            ;;
        build)
            build_images
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: ${1:-}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 