# Discord Webhook Integration for MTS Pipeline

This document describes the Discord webhook integration that allows the MTS Pipeline to send real-time trading signal alerts to Discord channels.

## 🎯 Overview

The Discord integration provides:
- **Real-time signal alerts** when trading signals are generated
- **Rich embed formatting** with signal details, risk metrics, and volatility data
- **Configurable filtering** based on confidence, strength, and asset type
- **Rate limiting** to prevent spam
- **Error handling and retry logic** for reliable delivery
- **Async processing** for non-blocking alert delivery

## 📁 Files Added

### Core Integration
- `src/utils/discord_webhook.py` - Discord webhook client and alert manager
- `config/discord_alerts.json` - Configuration file for Discord alerts
- `discord_alerts_demo.py` - Demonstration script

### Modified Files
- `src/signals/signal_aggregator.py` - Added Discord alert integration
- `requirements.txt` - Added aiohttp dependency

## 🔧 Configuration

### 1. Discord Webhook Setup

1. **Create a Discord webhook:**
   - Go to your Discord server
   - Right-click on the channel you want alerts in
   - Select "Edit Channel" → "Integrations" → "Webhooks"
   - Click "New Webhook" and give it a name (e.g., "MTS Signal Bot")
   - Copy the webhook URL

2. **Update configuration:**
   ```json
   {
       "webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN",
       "username": "MTS Signal Bot",
       "min_confidence": 0.6,
       "enabled_assets": ["bitcoin", "ethereum"],
       "rate_limit": 60
   }
   ```

### 2. Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `webhook_url` | string | Required | Discord webhook URL |
| `username` | string | "MTS Signal Bot" | Bot username in Discord |
| `avatar_url` | string | null | Bot avatar URL |
| `min_confidence` | float | 0.6 | Minimum confidence for alerts |
| `min_strength` | string | "WEAK" | Minimum signal strength |
| `enabled_assets` | array | ["bitcoin", "ethereum"] | Assets to send alerts for |
| `enabled_signal_types` | array | ["LONG", "SHORT"] | Signal types to alert |
| `rate_limit` | int | 60 | Seconds between alerts per asset |
| `include_risk_metrics` | bool | true | Include stop loss/take profit |
| `include_volatility_metrics` | bool | true | Include volatility data |
| `batch_alerts` | bool | true | Send multiple signals together |

## 🚀 Usage

### 1. Basic Integration

The Discord integration is automatically enabled when you configure the signal aggregator:

```python
from src.signals.signal_aggregator import SignalAggregator

# Configure with Discord alerts
aggregation_config = {
    'discord_alerts': True,
    'discord_webhook_url': 'YOUR_WEBHOOK_URL',
    'discord_config': {
        'min_confidence': 0.7,
        'enabled_assets': ['bitcoin', 'ethereum']
    }
}

# Initialize aggregator
aggregator = SignalAggregator(strategy_weights, aggregation_config)

# Process signals (Discord alerts sent automatically)
aggregated_signals = aggregator.aggregate_signals(strategy_signals)
```

### 2. Manual Discord Alerts

You can also send alerts manually:

```python
from src.utils.discord_webhook import DiscordAlertManager

# Initialize alert manager
alert_manager = DiscordAlertManager(webhook_url, config)

# Send alerts for signals
results = await alert_manager.process_signals(signals)
print(f"Sent {results['sent']} alerts")
```

### 3. Test Discord Integration

Run the demonstration script:

```bash
python3 discord_alerts_demo.py
```

## 📊 Alert Format

Discord alerts include rich embeds with:

### Signal Information
- **Asset**: Bitcoin, Ethereum, etc.
- **Signal Type**: LONG/SHORT with color coding
- **Price**: Current market price
- **Confidence**: Signal confidence percentage
- **Strength**: WEAK/MODERATE/STRONG
- **Position Size**: Recommended position size

### Risk Management
- **Stop Loss**: Calculated stop loss price
- **Take Profit**: Calculated take profit price
- **Max Risk**: Maximum risk percentage

### Volatility Metrics
- **Current Volatility**: Current volatility percentage
- **Volatility Ratio**: Ratio to historical mean
- **Reason**: Why the signal was generated

### Example Alert
```
📈 LONG Signal: Bitcoin
💰 Price: $117,678.19
💪 Strength: STRONG
🎯 Confidence: 85.0%
📊 Position Size: 1.8%
🛑 Stop Loss: $110,000.00
🎯 Take Profit: $130,000.00
📈 Volatility: 10.67%
📊 Volatility Ratio: 6.03x
💡 Reason: Volatility breakout: 10.67% > 5.95% threshold
```

## 🔄 Integration Points

### 1. Signal Aggregator Integration

The Discord integration is built into the `SignalAggregator` class:

```python
class SignalAggregator:
    def __init__(self, strategy_weights, aggregation_config):
        # Initialize Discord manager if configured
        if config.get('discord_alerts') and config.get('discord_webhook_url'):
            self.discord_manager = DiscordAlertManager(
                config['discord_webhook_url'],
                config.get('discord_config')
            )
    
    def aggregate_signals(self, strategy_signals):
        # Process signals
        aggregated_signals = self._process_signals(strategy_signals)
        
        # Send Discord alerts automatically
        if self.discord_manager and aggregated_signals:
            asyncio.create_task(self._send_discord_alerts(aggregated_signals))
        
        return aggregated_signals
```

### 2. Multi-Strategy Generator Integration

The `MultiStrategyGenerator` automatically uses Discord alerts when configured:

```python
from src.services.multi_strategy_generator import MultiStrategyGenerator

# Configure with Discord alerts
aggregator_config = {
    'strategy_weights': {'volatility': 1.0},
    'aggregation_config': {
        'discord_alerts': True,
        'discord_webhook_url': 'YOUR_WEBHOOK_URL',
        'discord_config': config
    }
}

generator = MultiStrategyGenerator(strategy_configs, aggregator_config)
signals = generator.generate_aggregated_signals(days=30)
```

## 🛡️ Error Handling

The Discord integration includes comprehensive error handling:

### 1. Connection Errors
- Automatic retry with exponential backoff
- Configurable retry count and delay
- Graceful degradation if Discord is unavailable

### 2. Rate Limiting
- Built-in rate limiting per asset
- Prevents spam during high volatility periods
- Configurable time intervals

### 3. Configuration Validation
- Validates webhook URL format
- Checks required configuration fields
- Provides helpful error messages

## 📈 Performance Considerations

### 1. Async Processing
- Discord alerts are sent asynchronously
- Non-blocking signal processing
- Uses `asyncio.create_task()` for background processing

### 2. Batch Processing
- Multiple signals can be sent together
- Reduces Discord API calls
- Configurable batch size

### 3. Rate Limiting
- Prevents Discord rate limit issues
- Configurable per-asset limits
- Automatic throttling

## 🧪 Testing

### 1. Test Discord Configuration

```python
# Test webhook connection
webhook = DiscordWebhook(webhook_url, config)
success = await webhook.send_test_message()

# Test alert manager
alert_manager = DiscordAlertManager(webhook_url, config)
success = await alert_manager.send_test_alert()
```

### 2. Test with Real Signals

```python
# Generate real signals and test Discord alerts
strategy = VolatilityStrategy("config/strategies/volatility_strategy.json")
signals = strategy.generate_signals(analysis_results)

# Configure aggregator with Discord
aggregator = SignalAggregator(strategy_weights, aggregation_config)
aggregated_signals = aggregator.aggregate_signals({'volatility': signals})
```

## 🔧 Troubleshooting

### Common Issues

1. **Webhook URL Invalid**
   - Check the webhook URL format
   - Ensure the webhook is still active in Discord
   - Verify the webhook has proper permissions

2. **No Alerts Being Sent**
   - Check confidence and strength thresholds
   - Verify enabled assets and signal types
   - Check rate limiting settings

3. **Rate Limit Errors**
   - Increase `rate_limit` in configuration
   - Reduce signal frequency
   - Check Discord's rate limits

4. **Connection Errors**
   - Check internet connectivity
   - Verify Discord service status
   - Check firewall settings

### Debug Mode

Enable debug logging to troubleshoot:

```python
import logging
logging.getLogger('src.utils.discord_webhook').setLevel(logging.DEBUG)
```

## 📋 Best Practices

### 1. Configuration
- Use environment variables for webhook URLs in production
- Set appropriate confidence and strength thresholds
- Configure rate limits based on your trading frequency

### 2. Monitoring
- Monitor Discord alert delivery rates
- Track failed alert attempts
- Set up alerts for Discord integration failures

### 3. Security
- Keep webhook URLs secure
- Use dedicated Discord channels for alerts
- Regularly rotate webhook tokens

### 4. Performance
- Use batch alerts for multiple signals
- Set appropriate rate limits
- Monitor Discord API usage

## 🎉 Summary

The Discord webhook integration provides a robust, configurable solution for real-time trading signal alerts. With rich embed formatting, comprehensive error handling, and flexible configuration options, it seamlessly integrates with the MTS Pipeline's signal processing workflow.

Key benefits:
- ✅ **Real-time alerts** for immediate signal notification
- ✅ **Rich formatting** with comprehensive signal details
- ✅ **Configurable filtering** for personalized alerts
- ✅ **Reliable delivery** with error handling and retries
- ✅ **Easy integration** with existing signal processing
- ✅ **Production-ready** with monitoring and security features

The integration is now ready for production use and will automatically send Discord alerts whenever trading signals are generated by your MTS Pipeline! 🚀 