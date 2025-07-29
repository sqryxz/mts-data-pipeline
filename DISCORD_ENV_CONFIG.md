# Discord Environment Variable Configuration

This document explains how to configure Discord webhook alerts using environment variables instead of hardcoded values.

## 🎯 Overview

The Discord webhook integration now supports environment variable configuration for better security and flexibility. This allows you to:

- **Secure your webhook URL** by storing it in environment variables
- **Configure alerts per environment** (development, staging, production)
- **Avoid hardcoded secrets** in configuration files
- **Use different settings** for different deployments

## 🔧 Environment Variables

### Required Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DISCORD_WEBHOOK_URL` | Your Discord webhook URL | `""` | `https://discord.com/api/webhooks/123/abc` |
| `DISCORD_ALERTS_ENABLED` | Enable/disable Discord alerts | `false` | `true` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DISCORD_MIN_CONFIDENCE` | Minimum confidence for alerts | `0.6` | `0.8` |
| `DISCORD_MIN_STRENGTH` | Minimum signal strength | `WEAK` | `STRONG` |
| `DISCORD_RATE_LIMIT_SECONDS` | Rate limit between alerts | `60` | `30` |

## 📝 Configuration Setup

### 1. Update Your `.env` File

Add these variables to your `.env` file:

```env
# Discord Webhook Configuration
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
DISCORD_ALERTS_ENABLED=true
DISCORD_MIN_CONFIDENCE=0.6
DISCORD_MIN_STRENGTH=WEAK
DISCORD_RATE_LIMIT_SECONDS=60
```

### 2. Environment-Specific Configuration

You can use different settings for different environments:

**Development:**
```env
DISCORD_ALERTS_ENABLED=false
DISCORD_WEBHOOK_URL=
```

**Production:**
```env
DISCORD_ALERTS_ENABLED=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/prod/webhook
DISCORD_MIN_CONFIDENCE=0.8
DISCORD_MIN_STRENGTH=STRONG
DISCORD_RATE_LIMIT_SECONDS=30
```

## 🔄 How It Works

### 1. Environment Variable Loading

The system automatically loads environment variables from your `.env` file:

```python
# Automatically loaded by python-dotenv
load_dotenv()

# Access environment variables
webhook_url = os.getenv('DISCORD_WEBHOOK_URL', '')
discord_enabled = os.getenv('DISCORD_ALERTS_ENABLED', 'false').lower() == 'true'
```

### 2. Configuration Resolution

The `SignalAggregator` uses environment variables to configure Discord alerts:

```python
def __init__(self, strategy_weights, aggregation_config):
    # Get Discord configuration from environment variables
    discord_config = get_discord_config_from_env()
    
    # Validate the configuration
    if validate_discord_config(discord_config):
        self.discord_manager = DiscordAlertManager(
            discord_config['webhook_url'],
            discord_config
        )
```

### 3. Validation

The system validates your configuration before initializing Discord alerts:

```python
def validate_discord_config(config):
    # Check required fields
    if not config.get('webhook_url'):
        return False
    
    # Validate numeric values
    if not (0 <= config.get('min_confidence', 0) <= 1):
        return False
    
    return True
```

## 🛠️ Configuration Utilities

### Environment Variable Resolution

The system includes utilities for resolving environment variables in JSON configuration files:

```python
from src.utils.config_utils import resolve_env_vars, load_config_with_env_vars

# Resolve environment variables in a configuration
config = {
    "webhook_url": "${DISCORD_WEBHOOK_URL}",
    "min_confidence": "${DISCORD_MIN_CONFIDENCE}"
}

resolved_config = resolve_env_vars(config)
# Result: {"webhook_url": "actual_url", "min_confidence": "0.6"}
```

### Configuration Validation

Validate your Discord configuration:

```python
from src.utils.config_utils import validate_discord_config

config = get_discord_config_from_env()
if validate_discord_config(config):
    print("Configuration is valid")
else:
    print("Configuration is invalid")
```

## 📊 Configuration Examples

### Basic Configuration

```env
# .env file
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc
DISCORD_ALERTS_ENABLED=true
```

### Advanced Configuration

```env
# .env file
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc
DISCORD_ALERTS_ENABLED=true
DISCORD_MIN_CONFIDENCE=0.8
DISCORD_MIN_STRENGTH=STRONG
DISCORD_RATE_LIMIT_SECONDS=30
```

### Development Configuration

```env
# .env file (development)
DISCORD_ALERTS_ENABLED=false
# DISCORD_WEBHOOK_URL not set
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Discord Alerts Not Working

**Problem:** Discord alerts are not being sent.

**Solution:** Check your environment variables:
```bash
# Verify your .env file has the correct values
cat .env | grep DISCORD
```

#### 2. Configuration Validation Fails

**Problem:** You see "Discord alerts enabled but configuration is invalid" in logs.

**Solution:** Check your webhook URL:
```env
# Make sure this is a valid Discord webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
```

#### 3. Environment Variables Not Loading

**Problem:** Environment variables are not being read.

**Solution:** Ensure your `.env` file is in the project root:
```bash
# Check if .env file exists
ls -la .env

# Verify it's being loaded
python3 -c "import os; print(os.getenv('DISCORD_WEBHOOK_URL'))"
```

### Debug Configuration

Run the configuration test to verify your setup:

```bash
python3 test_env_discord_config.py
```

This will test:
- ✅ Environment variable resolution
- ✅ Configuration validation
- ✅ SignalAggregator integration
- ✅ Missing variable handling

## 🧪 Testing

### Manual Testing

1. **Set up your environment variables:**
   ```env
   DISCORD_WEBHOOK_URL=your_webhook_url
   DISCORD_ALERTS_ENABLED=true
   ```

2. **Run the test suite:**
   ```bash
   python3 test_env_discord_config.py
   ```

3. **Test with real signals:**
   ```bash
   python3 discord_alerts_demo.py
   ```

### Automated Testing

The system includes comprehensive tests:

```bash
# Test environment variable configuration
python3 test_env_discord_config.py

# Test complete Discord fixes
python3 test_discord_complete_fixes.py

# Test Discord integration
python3 test_discord_fixes.py
```

## 📈 Benefits

### 1. Security
- ✅ **No hardcoded secrets** in configuration files
- ✅ **Environment-specific settings** for different deployments
- ✅ **Secure webhook URL storage** in environment variables

### 2. Flexibility
- ✅ **Easy configuration changes** without code modifications
- ✅ **Environment-specific settings** (dev/staging/prod)
- ✅ **Runtime configuration** without restarts

### 3. Maintainability
- ✅ **Centralized configuration** in `.env` files
- ✅ **Version control friendly** (`.env` in `.gitignore`)
- ✅ **Clear separation** of code and configuration

### 4. Validation
- ✅ **Automatic validation** of configuration
- ✅ **Graceful error handling** for invalid settings
- ✅ **Default values** for missing variables

## 🔄 Migration from Hardcoded Configuration

### Before (Hardcoded)
```python
# Old way - hardcoded in code
discord_config = {
    'webhook_url': 'https://discord.com/api/webhooks/123/abc',
    'min_confidence': 0.6,
    'min_strength': 'WEAK'
}
```

### After (Environment Variables)
```env
# .env file
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc
DISCORD_MIN_CONFIDENCE=0.6
DISCORD_MIN_STRENGTH=WEAK
```

```python
# New way - environment variables
discord_config = get_discord_config_from_env()
```

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Set environment variables
ENV DISCORD_ALERTS_ENABLED=true
ENV DISCORD_MIN_CONFIDENCE=0.8

# Run application
CMD ["python3", "main.py"]
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mts-pipeline
spec:
  template:
    spec:
      containers:
      - name: mts-pipeline
        image: mts-pipeline:latest
        env:
        - name: DISCORD_WEBHOOK_URL
          valueFrom:
            secretKeyRef:
              name: discord-secret
              key: webhook-url
        - name: DISCORD_ALERTS_ENABLED
          value: "true"
```

## 📋 Summary

The Discord webhook integration now supports environment variable configuration with:

- ✅ **Secure webhook URL storage** in environment variables
- ✅ **Flexible configuration** for different environments
- ✅ **Automatic validation** of settings
- ✅ **Graceful error handling** for invalid configurations
- ✅ **Comprehensive testing** for all scenarios

### Quick Start

1. **Add to your `.env` file:**
   ```env
   DISCORD_WEBHOOK_URL=your_webhook_url_here
   DISCORD_ALERTS_ENABLED=true
   ```

2. **Test the configuration:**
   ```bash
   python3 test_env_discord_config.py
   ```

3. **Start using Discord alerts!**

The system will automatically load your environment variables and configure Discord alerts accordingly. 🎉 