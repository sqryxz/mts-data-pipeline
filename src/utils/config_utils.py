"""
Configuration utilities for resolving environment variables in JSON files.
"""

import os
import re
import json
from typing import Any, Dict, Union
from pathlib import Path


def resolve_env_vars(value: Any) -> Any:
    """
    Recursively resolve environment variables in a value.
    
    Args:
        value: The value to process (can be string, dict, list, or primitive)
        
    Returns:
        The value with environment variables resolved
    """
    if isinstance(value, str):
        # Check if the string contains environment variable placeholders
        if '${' in value and '}' in value:
            # Replace ${VAR_NAME} with actual environment variable values
            def replace_env_var(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))  # Return original if not found
            
            return re.sub(r'\$\{([^}]+)\}', replace_env_var, value)
        return value
    elif isinstance(value, dict):
        return {k: resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_env_vars(item) for item in value]
    else:
        return value


def load_config_with_env_vars(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON configuration file and resolve environment variables.
    
    Args:
        config_path: Path to the JSON configuration file
        
    Returns:
        Dict with resolved configuration
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        json.JSONDecodeError: If the JSON is invalid
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Resolve environment variables
        resolved_config = resolve_env_vars(config)
        
        return resolved_config
        
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {config_path}: {e}", e.doc, e.pos)


def validate_discord_config(config: Dict[str, Any]) -> bool:
    """
    Validate Discord configuration.
    
    Args:
        config: Discord configuration dictionary
        
    Returns:
        bool: True if configuration is valid
    """
    required_fields = ['webhook_url', 'min_confidence', 'min_strength', 'rate_limit']
    
    for field in required_fields:
        if field not in config:
            return False
    
    # Check if webhook URL is properly configured
    webhook_url = config.get('webhook_url', '')
    if not webhook_url or webhook_url == 'YOUR_DISCORD_WEBHOOK_URL_HERE':
        return False
    
    # Validate numeric fields
    try:
        min_confidence = float(config.get('min_confidence', 0))
        if not (0 <= min_confidence <= 1):
            return False
    except (ValueError, TypeError):
        return False
    
    try:
        rate_limit = int(config.get('rate_limit', 0))
        if rate_limit <= 0:
            return False
    except (ValueError, TypeError):
        return False
    
    return True


def get_discord_config_from_env() -> Dict[str, Any]:
    """
    Get Discord configuration from environment variables.
    
    Returns:
        Dict with Discord configuration
    """
    return {
        'webhook_url': os.getenv('DISCORD_WEBHOOK_URL', ''),
        'username': 'MTS Signal Bot',
        'avatar_url': None,
        'embed_color': 16711680,
        'include_risk_metrics': True,
        'include_volatility_metrics': True,
        'max_retries': 3,
        'retry_delay': 1.0,
        'min_confidence': float(os.getenv('DISCORD_MIN_CONFIDENCE', '0.6')),
        'min_strength': os.getenv('DISCORD_MIN_STRENGTH', 'WEAK'),
        'enabled_assets': ['bitcoin', 'ethereum'],
        'enabled_signal_types': ['LONG', 'SHORT'],
        'rate_limit': int(os.getenv('DISCORD_RATE_LIMIT_SECONDS', '60')),
        'batch_alerts': True,
        'description': 'Discord alert configuration for MTS Pipeline signal notifications'
    }


def merge_configs(default_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two configuration dictionaries.
    
    Args:
        default_config: Default configuration
        override_config: Configuration to override defaults
        
    Returns:
        Merged configuration dictionary
    """
    result = default_config.copy()
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result 