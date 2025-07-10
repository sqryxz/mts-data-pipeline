# MTS Crypto Data Pipeline - Production Deployment Guide

This guide covers the production deployment and management of the MTS (Multi-Trading Strategy) Crypto Data Pipeline.

## 🚀 Quick Start

1. **Prerequisites Setup**
   ```bash
   # Install Docker and Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Initial Setup**
   ```bash
   # Clone repository
   git clone <your-repo-url>
   cd MTS-data-pipeline
   
   # Run interactive setup
   ./deploy.sh setup
   ```

3. **Configure Environment**
   - Edit `.env` file with your API keys and settings
   - Update strategy configurations in `config/strategies/`

4. **Deploy**
   ```bash
   # Start all services
   ./deploy.sh start
   
   # Or with monitoring
   ./deploy.sh start --with-monitoring
   ```

5. **Verify Deployment**
   ```bash
   # Check service health
   ./deploy.sh health
   
   # View API documentation
   curl http://localhost:8000/docs
   ```

## 📋 System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **Network**: Stable internet connection

### Recommended for Production
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **Network**: High-bandwidth, low-latency connection

### Supported Platforms
- Ubuntu 20.04+ LTS
- CentOS 8+
- Amazon Linux 2
- Docker-compatible systems

## 🔧 Configuration

### Environment Variables

The system uses environment variables for configuration. Key variables include:

#### API Security
- `API_SECRET_KEY`: JWT secret key (generate with `openssl rand -hex 32`)
- `FRED_API_KEY`: Federal Reserve Economic Data API key

#### Database & Caching
- `DATABASE_PATH`: SQLite database location
- `REDIS_URL`: Redis connection string

#### Strategy Configuration
- `ENABLED_STRATEGIES`: Comma-separated list of strategies
- `STRATEGY_WEIGHTS`: Strategy weight mapping
- `MAX_POSITION_SIZE`: Maximum position size (0.0-1.0)

#### Intervals & Timing
- `SIGNAL_GENERATION_INTERVAL_MINUTES`: How often to generate signals
- `DATA_COLLECTION_INTERVAL_MINUTES`: How often to collect crypto data
- `MACRO_DATA_COLLECTION_INTERVAL_HOURS`: How often to collect macro data

### Strategy Configuration Files

Located in `config/strategies/`:

#### VIX Correlation Strategy (`vix_correlation.json`)
```json
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
```

#### Mean Reversion Strategy (`mean_reversion.json`)
```json
{
    "name": "Mean_Reversion_Strategy",
    "assets": ["bitcoin", "ethereum", "binancecoin"],
    "vix_spike_threshold": 25,
    "drawdown_threshold": 0.10,
    "lookback_days": 14,
    "position_size": 0.025
}
```

## 🐳 Docker Architecture

### Services Overview

1. **mts-pipeline**: Main application container
   - FastAPI server for REST API
   - Signal generation and data collection
   - Health monitoring

2. **redis**: Caching and message queue
   - Signal caching
   - API response caching
   - Task queue management

3. **prometheus** (optional): Metrics collection
   - System metrics
   - Application metrics
   - Custom business metrics

4. **grafana** (optional): Monitoring dashboard
   - Real-time dashboards
   - Alerts and notifications
   - Historical data visualization

### Network Architecture
```
Internet → Nginx (Port 80/443) → MTS API (Port 8000)
                                     ↓
                               Redis (Port 6379)
                                     ↓
                            SQLite Database (Volume)
```

## 🚢 Deployment Options

### Option 1: Single Server Deployment
Best for development, testing, or small-scale production.

```bash
# Deploy with all services on one server
./deploy.sh start --with-monitoring
```

### Option 2: API-Only Deployment
Deploy only the API service (useful for scaling).

```bash
# Deploy only API
python3 production_main.py --mode api-only
```

### Option 3: Scheduled Tasks Only
Run data collection and signal generation without API.

```bash
# Run collection tasks
python3 production_main.py --mode collector-only

# Run signal generation
python3 production_main.py --mode signals-only
```

## 📊 API Documentation

### Core Endpoints

#### Signal Generation
- `POST /signals/generate`: Generate new trading signals
- `GET /signals/latest`: Get latest generated signals

#### Backtesting
- `POST /backtest`: Run strategy backtest
- `GET /strategies`: List available strategies

#### System
- `GET /health`: System health check
- `GET /config`: Current configuration
- `GET /`: API information

### Example API Usage

```bash
# Generate signals
curl -X POST "http://localhost:8000/signals/generate" \
     -H "Content-Type: application/json" \
     -d '{"days": 30, "force_refresh": true}'

# Get latest signals
curl "http://localhost:8000/signals/latest?limit=10"

# Run backtest
curl -X POST "http://localhost:8000/backtest" \
     -H "Content-Type: application/json" \
     -d '{
       "strategy_name": "vix_correlation",
       "start_date": "2023-01-01",
       "end_date": "2023-12-31"
     }'

# Check health
curl "http://localhost:8000/health"
```

## 🔍 Monitoring & Observability

### Built-in Health Checks

The system includes comprehensive health monitoring:

- **Database connectivity**: SQLite database access
- **External APIs**: CoinGecko and FRED API status
- **Signal generation**: Recent signal generation status
- **System resources**: CPU, memory, disk usage

### Prometheus Metrics

When monitoring is enabled, the following metrics are collected:

- `mts_signals_generated_total`: Total signals generated
- `mts_api_requests_total`: API request count
- `mts_collection_duration_seconds`: Data collection duration
- `mts_errors_total`: Error count by type

### Grafana Dashboards

Pre-configured dashboards include:
- System overview
- Signal generation metrics
- API performance
- Error tracking

Access Grafana at: `http://localhost:3000` (admin/admin)

## 🚨 Alerts & Notifications

### Configurable Alerts

Set up email alerts for:
- API service downtime
- Data collection failures
- Signal generation errors
- System resource exhaustion

### Alert Configuration

```env
ENABLE_ALERTS=true
ALERT_EMAIL_SMTP_SERVER=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_USERNAME=your-email@example.com
ALERT_EMAIL_PASSWORD=your-app-password
ALERT_EMAIL_FROM=mts-pipeline@example.com
ALERT_EMAIL_TO=admin@example.com
```

## 🔐 Security Best Practices

### API Security
- Use strong JWT secret keys
- Enable HTTPS in production
- Implement rate limiting
- Regular security updates

### Container Security
- Run containers as non-root user
- Use official base images
- Regular image updates
- Network isolation

### Data Security
- Encrypt sensitive environment variables
- Regular database backups
- Secure API key storage
- Access logging

## 💾 Backup & Recovery

### Automated Backups

```bash
# Create backup
./deploy.sh backup

# Backups are stored in ./backups/ directory
# Format: mts-backup-YYYYMMDD-HHMMSS.tar.gz
```

### Manual Backup

```bash
# Stop services
./deploy.sh stop

# Create manual backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/ config/

# Restart services
./deploy.sh start
```

### Recovery Process

```bash
# Stop services
./deploy.sh stop

# Restore from backup
tar -xzf backup-YYYYMMDD.tar.gz

# Start services
./deploy.sh start
```

## 🔄 Updates & Maintenance

### Update Deployment

```bash
# Automated update (with backup)
./deploy.sh update
```

### Manual Update

```bash
# Create backup
./deploy.sh backup

# Pull latest code
git pull

# Rebuild and restart
./deploy.sh build
./deploy.sh restart
```

### Regular Maintenance

1. **Weekly**:
   - Check system health
   - Review error logs
   - Verify backup integrity

2. **Monthly**:
   - Update dependencies
   - Review performance metrics
   - Clean old log files

3. **Quarterly**:
   - Security audit
   - Performance optimization
   - Strategy review

## 🐛 Troubleshooting

### Common Issues

#### API Not Responding
```bash
# Check service status
./deploy.sh status

# View logs
./deploy.sh logs mts-pipeline

# Restart services
./deploy.sh restart
```

#### Redis Connection Issues
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

#### Data Collection Failures
```bash
# Check API keys
grep FRED_API_KEY .env

# Test external API connectivity
curl "https://api.coingecko.com/api/v3/ping"
```

### Log Analysis

```bash
# View real-time logs
./deploy.sh logs

# Search for errors
./deploy.sh logs | grep -i error

# Check specific service
./deploy.sh logs redis
```

### Performance Issues

```bash
# Check resource usage
./deploy.sh status

# Monitor performance
docker stats

# Check disk space
df -h
```

## 📞 Support & Resources

### Documentation
- API Documentation: `http://localhost:8000/docs`
- System Health: `http://localhost:8000/health`
- Monitoring: `http://localhost:3000` (Grafana)

### Useful Commands

```bash
# Deployment management
./deploy.sh setup        # Initial setup
./deploy.sh start        # Start services
./deploy.sh stop         # Stop services
./deploy.sh status       # Show status
./deploy.sh health       # Health check
./deploy.sh logs         # View logs
./deploy.sh backup       # Create backup
./deploy.sh update       # Update deployment

# Direct Python execution
python3 production_main.py --mode api-only
python3 production_main.py --mode collector-only
python3 production_main.py --mode signals-only
```

### Directory Structure

```
MTS-data-pipeline/
├── production_main.py      # Production entry point
├── deploy.sh              # Deployment script
├── docker-compose.yml     # Docker services
├── Dockerfile            # Application container
├── .env                  # Environment configuration
├── data/                 # Database and data files
├── logs/                 # Application logs
├── config/              # Configuration files
│   └── strategies/      # Strategy configurations
├── monitoring/          # Monitoring configurations
└── backups/            # Backup files
```

## 🎯 Production Checklist

Before going live:

- [ ] Configure all environment variables
- [ ] Set up FRED API key
- [ ] Generate secure API secret key
- [ ] Configure alerts and notifications
- [ ] Set up monitoring dashboards
- [ ] Test backup and recovery
- [ ] Verify SSL/TLS configuration
- [ ] Run security audit
- [ ] Load test the API
- [ ] Document disaster recovery plan

---

For additional support or questions, please refer to the main README.md or create an issue in the repository. 