"""
Main risk management coordinator.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Union
from pathlib import Path
from ..calculators.position_calculator import PositionCalculator
from ..calculators.risk_level_calculator import RiskLevelCalculator
from ..models.risk_models import RiskAssessment, TradingSignal, PortfolioState
from ..validators.trade_validator import TradeValidator
from ..utils.error_handler import (
    RiskManagementErrorHandler, ErrorType, ErrorSeverity,
    validate_input, create_error_assessment, handle_configuration_error
)

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    'risk_limits': {
        'max_drawdown_limit': 0.20,
        'daily_loss_limit': 0.05,
        'per_trade_stop_loss': 0.02,
        'max_position_size': 0.10,
        'max_single_asset_exposure': 0.15,
        'max_sector_exposure': 0.30,
        'max_correlation_risk': 0.80,
        'volatility_threshold': 0.05,
        'drawdown_warning_level': 0.15
    },
    'position_sizing': {
        'base_position_percent': 0.02,
        'min_position_size': 0.001
    },
    'risk_assessment': {
        'default_risk_reward_ratio': 2.0,
        'confidence_threshold': 0.5,
        'processing_timeout_ms': 5000
    }
}


class RiskOrchestrator:
    """
    Main risk management coordinator that processes trading signals
    and produces comprehensive risk assessments
    """
    
    def __init__(self, config_path: str = "src/risk_management/config/risk_config.json"):
        self.error_handler = RiskManagementErrorHandler()
        self.config = self._load_config_safely(config_path)
        
        # Load all risk limits with validation
        self._load_risk_limits()
        
        # Load position sizing parameters with validation
        self._load_position_sizing()
        
        # Load risk assessment parameters with validation
        self._load_risk_assessment()
        
        # Load market conditions (if available)
        self._load_market_conditions()
        
        # Initialize components with error handling
        self._initialize_components()
        
        self._log_initialization()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load and validate risk configuration from JSON file.
        
        Args:
            config_path: Path to the configuration JSON file
            
        Returns:
            Dictionary containing the configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
            ValueError: If required configuration keys are missing or invalid
        """
        try:
            # Check if file exists
            if not Path(config_path).exists():
                logger.warning(f"Configuration file not found: {config_path}, using defaults")
                return DEFAULT_CONFIG
            
            # Load JSON configuration
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate and merge with defaults
            config = self._validate_and_merge_config(config)
            
            logger.info("Configuration loaded and validated successfully")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            logger.info("Using default configuration")
            return DEFAULT_CONFIG
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {e}")
            logger.info("Using default configuration")
            return DEFAULT_CONFIG
    
    def _validate_and_merge_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration values and merge with defaults."""
        
        # Validate required sections exist
        required_sections = ['risk_limits', 'position_sizing', 'risk_assessment']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate risk limits
        risk_limits = config.get('risk_limits', {})
        required_limits = [
            'max_drawdown_limit', 'daily_loss_limit', 'per_trade_stop_loss', 
            'max_position_size', 'max_single_asset_exposure', 'max_sector_exposure'
        ]
        
        for limit in required_limits:
            if limit not in risk_limits:
                raise ValueError(f"Missing required risk limit: {limit}")
            
            # Validate percentage values
            value = risk_limits[limit]
            if not isinstance(value, (int, float)):
                raise ValueError(f"{limit} must be a number, got {type(value)}")
            if not 0 < value <= 1:
                raise ValueError(f"{limit} must be between 0 and 1, got {value}")
        
        # Validate position sizing
        position_sizing = config.get('position_sizing', {})
        if 'base_position_percent' not in position_sizing:
            raise ValueError("Missing required position sizing parameter: base_position_percent")
        
        base_pos = position_sizing['base_position_percent']
        if not isinstance(base_pos, (int, float)) or not 0 < base_pos <= 1:
            raise ValueError(f"base_position_percent must be between 0 and 1, got {base_pos}")
        
        # Merge with defaults for missing optional values
        merged_config = {}
        for section, defaults in DEFAULT_CONFIG.items():
            merged_config[section] = {**defaults, **config.get(section, {})}
        
        # Add any additional sections from config not in defaults
        for section, values in config.items():
            if section not in merged_config:
                merged_config[section] = values
        
        return merged_config
    
    def _load_config_safely(self, config_path: str) -> Dict[str, Any]:
        """Load configuration with comprehensive error handling."""
        try:
            return self._load_config(config_path)
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CONFIGURATION_ERROR,
                severity=ErrorSeverity.HIGH,
                context={'config_path': config_path}
            )
            return handle_configuration_error(config_path, e)
    
    def _load_risk_limits(self) -> None:
        """Load risk limits with validation."""
        try:
            risk_limits = self.config.get('risk_limits', {})
            
            # Validate and load each risk limit
            self.max_drawdown_limit = self._validate_risk_limit(
                risk_limits.get('max_drawdown_limit'), 'max_drawdown_limit', 0.0, 1.0
            )
            self.daily_loss_limit = self._validate_risk_limit(
                risk_limits.get('daily_loss_limit'), 'daily_loss_limit', 0.0, 1.0
            )
            self.per_trade_stop_loss = self._validate_risk_limit(
                risk_limits.get('per_trade_stop_loss'), 'per_trade_stop_loss', 0.0, 1.0
            )
            self.max_position_size = self._validate_risk_limit(
                risk_limits.get('max_position_size'), 'max_position_size', 0.0, 1.0
            )
            self.max_single_asset_exposure = self._validate_risk_limit(
                risk_limits.get('max_single_asset_exposure'), 'max_single_asset_exposure', 0.0, 1.0
            )
            self.max_sector_exposure = self._validate_risk_limit(
                risk_limits.get('max_sector_exposure'), 'max_sector_exposure', 0.0, 1.0
            )
            self.max_correlation_risk = self._validate_risk_limit(
                risk_limits.get('max_correlation_risk'), 'max_correlation_risk', 0.0, 1.0
            )
            self.volatility_threshold = self._validate_risk_limit(
                risk_limits.get('volatility_threshold'), 'volatility_threshold', 0.0, 1.0
            )
            self.drawdown_warning_level = self._validate_risk_limit(
                risk_limits.get('drawdown_warning_level'), 'drawdown_warning_level', 0.0, 1.0
            )
            
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CONFIGURATION_ERROR,
                severity=ErrorSeverity.HIGH,
                context={'section': 'risk_limits'}
            )
            # Use default values
            self.max_drawdown_limit = 0.20
            self.daily_loss_limit = 0.05
            self.per_trade_stop_loss = 0.02
            self.max_position_size = 0.10
            self.max_single_asset_exposure = 0.15
            self.max_sector_exposure = 0.30
            self.max_correlation_risk = 0.80
            self.volatility_threshold = 0.05
            self.drawdown_warning_level = 0.15
    
    def _validate_risk_limit(self, value: Any, name: str, min_val: float, max_val: float) -> float:
        """Validate a risk limit value."""
        try:
            validate_input(value, float, name, min_value=min_val, max_value=max_val)
            return float(value)
        except ValueError as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={'limit_name': name, 'value': value}
            )
            # Return default value
            return DEFAULT_CONFIG['risk_limits'].get(name, 0.0)
    
    def _load_position_sizing(self) -> None:
        """Load position sizing parameters with validation."""
        try:
            position_sizing = self.config.get('position_sizing', {})
            
            self.base_position_percent = self._validate_risk_limit(
                position_sizing.get('base_position_percent'), 'base_position_percent', 0.0, 1.0
            )
            self.min_position_size = self._validate_risk_limit(
                position_sizing.get('min_position_size'), 'min_position_size', 0.0, 1.0
            )
            
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CONFIGURATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={'section': 'position_sizing'}
            )
            # Use default values
            self.base_position_percent = 0.02
            self.min_position_size = 0.001
    
    def _load_risk_assessment(self) -> None:
        """Load risk assessment parameters with validation."""
        try:
            risk_assessment = self.config.get('risk_assessment', {})
            
            self.default_risk_reward_ratio = self._validate_risk_limit(
                risk_assessment.get('default_risk_reward_ratio'), 'default_risk_reward_ratio', 0.0, 10.0
            )
            self.confidence_threshold = self._validate_risk_limit(
                risk_assessment.get('confidence_threshold'), 'confidence_threshold', 0.0, 1.0
            )
            self.processing_timeout_ms = self._validate_risk_limit(
                risk_assessment.get('processing_timeout_ms'), 'processing_timeout_ms', 100, 60000
            )
            
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CONFIGURATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={'section': 'risk_assessment'}
            )
            # Use default values
            self.default_risk_reward_ratio = 2.0
            self.confidence_threshold = 0.5
            self.processing_timeout_ms = 5000
    
    def _load_market_conditions(self) -> None:
        """Load market conditions parameters."""
        try:
            market_conditions = self.config.get('market_conditions', {})
            
            self.volatility_warning_threshold = market_conditions.get('volatility_warning_threshold', 0.05)
            self.low_liquidity_threshold = market_conditions.get('low_liquidity_threshold', 0.01)
            self.correlation_lookback_days = market_conditions.get('correlation_lookback_days', 30)
            
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CONFIGURATION_ERROR,
                severity=ErrorSeverity.LOW,
                context={'section': 'market_conditions'}
            )
            # Use default values
            self.volatility_warning_threshold = 0.05
            self.low_liquidity_threshold = 0.01
            self.correlation_lookback_days = 30
    
    def _initialize_components(self) -> None:
        """Initialize components with error handling."""
        try:
            self.trade_validator = TradeValidator(self.config)
            self.risk_level_calculator = RiskLevelCalculator(self.config)
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.SYSTEM_ERROR,
                severity=ErrorSeverity.CRITICAL,
                context={'operation': 'component_initialization'}
            )
            raise
    
    def _log_initialization(self) -> None:
        """Log initialization parameters."""
        logger.info("Risk Orchestrator initialized successfully")
        logger.info(f"Max drawdown limit: {self.max_drawdown_limit}")
        logger.info(f"Daily loss limit: {self.daily_loss_limit}")
        logger.info(f"Per trade stop loss: {self.per_trade_stop_loss}")
        logger.info(f"Max position size: {self.max_position_size}")
        logger.info(f"Base position percent: {self.base_position_percent}")
    
    def _calculate_stop_loss_price(self, signal: 'TradingSignal', position_size: float) -> float:
        """
        Calculate stop loss price based on 2% position risk.
        
        Args:
            signal: Trading signal with price and signal type
            position_size: Position size in USD
            
        Returns:
            Stop loss price
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if signal is None:
            raise ValueError("Signal cannot be None")
        
        if position_size <= 0:
            raise ValueError(f"Position size must be positive, got {position_size}")
        
        # Validate required attributes
        required_attrs = ['price', 'signal_type', 'asset']
        for attr in required_attrs:
            if not hasattr(signal, attr):
                raise ValueError(f"Signal must have {attr} attribute")
        
        if signal.price <= 0:
            raise ValueError(f"Signal price must be positive, got {signal.price}")
        
        if signal.signal_type is None:
            raise ValueError("Signal type cannot be None")
        
        # Validate signal_type.value exists and is valid
        if not hasattr(signal.signal_type, 'value') or signal.signal_type.value is None:
            raise ValueError("Signal type must have a valid value")
        
        try:
            # Calculate maximum loss amount (2% of position)
            max_loss_amount = position_size * self.per_trade_stop_loss
            
            # Calculate number of shares/units
            units = position_size / signal.price
            
            # Calculate stop loss distance per unit
            stop_loss_distance_per_unit = max_loss_amount / units
            
            # Calculate stop loss price based on signal type
            signal_type_upper = str(signal.signal_type.value).upper()
            if signal_type_upper == 'LONG':
                stop_loss_price = signal.price - stop_loss_distance_per_unit
                # For LONG positions, ensure stop loss isn't negative
                if stop_loss_price < 0:
                    logger.warning(f"Calculated stop loss {stop_loss_price:.2f} is negative for LONG position. Using 0.01")
                    stop_loss_price = 0.01  # Minimal positive value instead of 0
            elif signal_type_upper == 'SHORT':
                stop_loss_price = signal.price + stop_loss_distance_per_unit
                # Defensive check for SHORT positions (edge case protection)
                if stop_loss_price < 0:
                    logger.warning(f"Calculated stop loss {stop_loss_price:.2f} is negative for SHORT position. Using 0.01")
                    stop_loss_price = 0.01
            else:
                raise ValueError(f"Invalid signal type: {signal.signal_type.value}")
            
            logger.info(f"Stop loss calculation for {signal.asset}:")
            logger.info(f"  Signal price: ${signal.price:.2f}")
            logger.info(f"  Position size: ${position_size:.2f}")
            logger.info(f"  Signal type: {signal.signal_type.value}")
            logger.info(f"  Max loss amount: ${max_loss_amount:.2f}")
            logger.info(f"  Units: {units:.4f}")
            logger.info(f"  Stop loss distance per unit: ${stop_loss_distance_per_unit:.4f}")
            logger.info(f"  Stop loss price: ${stop_loss_price:.2f}")
            
            return stop_loss_price
            
        except AttributeError as e:
            logger.error(f"Missing required attribute: {e}")
            raise ValueError(f"Invalid signal structure: {e}")
        except (TypeError, ZeroDivisionError) as e:
            logger.error(f"Calculation error: {e}")
            raise ValueError(f"Calculation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calculating stop loss: {e}")
            raise
    
    def _calculate_risk_reward_ratio(self, signal: 'TradingSignal', stop_loss_price: float) -> float:
        """
        Calculate basic risk/reward ratio using stop loss distance.
        
        Args:
            signal: Trading signal with price and signal type
            stop_loss_price: Calculated stop loss price
            
        Returns:
            Risk/reward ratio (reward per unit / risk per unit)
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if signal is None:
            raise ValueError("Signal cannot be None")
        
        if stop_loss_price <= 0:  # Changed from < 0
            raise ValueError(f"Stop loss price must be positive, got {stop_loss_price}")
        
        # Validate required attributes
        if not hasattr(signal, 'price'):
            raise ValueError("Signal must have price attribute")
        
        if not hasattr(signal, 'signal_type'):
            raise ValueError("Signal must have signal_type attribute")
        
        if signal.price <= 0:
            raise ValueError(f"Signal price must be positive, got {signal.price}")
        
        if signal.signal_type is None:
            raise ValueError("Signal type cannot be None")
        
        # Validate signal_type.value exists and is valid
        if not hasattr(signal.signal_type, 'value') or signal.signal_type.value is None:
            raise ValueError("Signal type must have a valid value")
        
        try:
            # Calculate risk per unit (distance from entry to stop loss)
            signal_type_upper = str(signal.signal_type.value).upper()
            
            if signal_type_upper == 'LONG':
                risk_per_unit = signal.price - stop_loss_price
            elif signal_type_upper == 'SHORT':
                risk_per_unit = stop_loss_price - signal.price
            else:
                raise ValueError(f"Invalid signal type: {signal.signal_type.value}")
            
            # Ensure risk per unit is positive
            if risk_per_unit <= 0:
                raise ValueError(f"Invalid risk calculation: risk per unit is {risk_per_unit}")
            
            # Calculate reward per unit (using take profit if available, otherwise default 2:1)
            if hasattr(signal, 'take_profit_price') and signal.take_profit_price is not None and signal.take_profit_price > 0:
                # Use provided take profit price
                if signal_type_upper == 'LONG':
                    reward_per_unit = signal.take_profit_price - signal.price
                else:  # SHORT
                    reward_per_unit = signal.price - signal.take_profit_price
            else:
                # Default to 2:1 reward/risk ratio
                reward_per_unit = risk_per_unit * 2
            
            # Ensure reward per unit is positive
            if reward_per_unit <= 0:
                raise ValueError(f"Invalid reward calculation: reward per unit is {reward_per_unit}")
            
            # Calculate risk/reward ratio
            risk_reward_ratio = reward_per_unit / risk_per_unit
            
            # Safe asset name access
            asset_name = getattr(signal, 'asset', 'Unknown')
            logger.info(f"Risk/reward calculation for {asset_name}:")
            logger.info(f"  Signal price: ${signal.price:.2f}")
            logger.info(f"  Stop loss price: ${stop_loss_price:.2f}")
            logger.info(f"  Signal type: {signal.signal_type.value}")
            logger.info(f"  Risk per unit: ${risk_per_unit:.4f}")
            logger.info(f"  Reward per unit: ${reward_per_unit:.4f}")
            logger.info(f"  Risk/reward ratio: {risk_reward_ratio:.2f}")
            
            return risk_reward_ratio
            
        except AttributeError as e:
            logger.error(f"Missing required attribute: {e}")
            raise ValueError(f"Invalid signal structure: {e}")
        except (TypeError, ZeroDivisionError) as e:
            logger.error(f"Calculation error: {e}")
            raise ValueError(f"Calculation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calculating risk/reward ratio: {e}")
            raise
    
    def assess_trade_risk(self, signal: 'TradingSignal', portfolio_state: 'PortfolioState') -> 'RiskAssessment':
        """
        Create basic risk assessment that combines all calculations.
        
        Args:
            signal: Trading signal to assess
            portfolio_state: Current portfolio state
            
        Returns:
            Comprehensive risk assessment
        """
        start_time = time.time()
        
        try:
            # Validate inputs with comprehensive error handling
            self._validate_assessment_inputs(signal, portfolio_state)
            
            logger.info(f"Starting risk assessment for {signal.asset} {signal.signal_type.value} signal")
            
            # Calculate position size with error handling
            recommended_position_size = self._calculate_position_size_safely(signal, portfolio_state)
            
            # Calculate stop loss price with error handling
            stop_loss_price = self._calculate_stop_loss_safely(signal, recommended_position_size)
            
            # Calculate risk/reward ratio with error handling
            risk_reward_ratio = self._calculate_risk_reward_safely(signal, stop_loss_price)
            
            # Calculate take profit price with error handling
            take_profit_price = self._calculate_take_profit_safely(signal, stop_loss_price, risk_reward_ratio)
            
            # Calculate position risk percent with error handling
            position_risk_percent = self._calculate_position_risk_safely(recommended_position_size, portfolio_state)
            
            # Calculate portfolio heat
            portfolio_heat = position_risk_percent  # Simplified for now
            
            # Validate trade against risk limits with error handling
            validation_result = self._validate_trade_safely(signal, portfolio_state, recommended_position_size)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Create risk assessment
            assessment = self._create_assessment_safely(
                signal, portfolio_state, recommended_position_size, stop_loss_price,
                take_profit_price, risk_reward_ratio, position_risk_percent,
                portfolio_heat, validation_result, processing_time_ms
            )
            
            # Calculate risk level with error handling
            risk_level = self._calculate_risk_level_safely(assessment)
            assessment.risk_level = risk_level
            
            # Get additional risk factors with error handling
            additional_risk_factors = self._get_risk_factors_safely(assessment)
            assessment.risk_warnings.extend(additional_risk_factors)
            
            logger.info(f"Risk assessment completed successfully:")
            logger.info(f"  Position size: ${recommended_position_size:.2f}")
            logger.info(f"  Stop loss: ${stop_loss_price:.2f}")
            logger.info(f"  Take profit: ${take_profit_price:.2f}")
            logger.info(f"  Risk/reward ratio: {risk_reward_ratio:.2f}")
            logger.info(f"  Processing time: {processing_time_ms:.2f}ms")
            
            return assessment
            
        except Exception as e:
            # Handle any unexpected errors
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.SYSTEM_ERROR,
                severity=ErrorSeverity.HIGH,
                context={
                    'signal_id': getattr(signal, 'signal_id', 'unknown') if signal else 'unknown',
                    'asset': getattr(signal, 'asset', 'unknown') if signal else 'unknown',
                    'operation': 'risk_assessment'
                }
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Return comprehensive error assessment
            return create_error_assessment(signal, portfolio_state, e, ErrorType.SYSTEM_ERROR)
    
    def _validate_assessment_inputs(self, signal: 'TradingSignal', portfolio_state: 'PortfolioState') -> None:
        """Validate assessment inputs with comprehensive error handling."""
        try:
            # Validate signal
            if signal is None:
                raise ValueError("Signal cannot be None")
            
            # Validate required signal attributes
            required_attrs = ['signal_id', 'asset', 'signal_type', 'price', 'confidence', 'timestamp']
            for attr in required_attrs:
                if not hasattr(signal, attr):
                    raise ValueError(f"Signal missing required attribute: {attr}")
            
            # Validate signal values
            validate_input(signal.price, float, 'signal.price', min_value=0.0)
            validate_input(signal.confidence, float, 'signal.confidence', min_value=0.0, max_value=1.0)
            
            # Validate portfolio state
            if portfolio_state is None:
                raise ValueError("Portfolio state cannot be None")
            
            if not hasattr(portfolio_state, 'total_equity'):
                raise ValueError("Portfolio state missing total_equity attribute")
            
            validate_input(portfolio_state.total_equity, float, 'portfolio_state.total_equity', min_value=0.0)
            
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={'operation': 'input_validation'}
            )
            raise
    
    def _calculate_position_size_safely(self, signal: 'TradingSignal', portfolio_state: 'PortfolioState') -> float:
        """Calculate position size with error handling."""
        try:
            position_calculator = PositionCalculator()
            return position_calculator.calculate_position_size(signal, portfolio_state)
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CALCULATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={'operation': 'position_size_calculation'}
            )
            # Return safe default
            return portfolio_state.total_equity * self.base_position_percent
    
    def _calculate_stop_loss_safely(self, signal: 'TradingSignal', position_size: float) -> float:
        """Calculate stop loss with error handling."""
        try:
            return self._calculate_stop_loss_price(signal, position_size)
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CALCULATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={'operation': 'stop_loss_calculation'}
            )
            # Return safe default based on signal type
            if signal.signal_type.value.upper() == 'LONG':
                return signal.price * 0.98  # 2% below entry
            else:
                return signal.price * 1.02  # 2% above entry
    
    def _calculate_risk_reward_safely(self, signal: 'TradingSignal', stop_loss_price: float) -> float:
        """Calculate risk/reward ratio with error handling."""
        try:
            return self._calculate_risk_reward_ratio(signal, stop_loss_price)
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CALCULATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={'operation': 'risk_reward_calculation'}
            )
            # Return safe default
            return self.default_risk_reward_ratio
    
    def _calculate_take_profit_safely(self, signal: 'TradingSignal', stop_loss_price: float, risk_reward_ratio: float) -> float:
        """Calculate take profit with error handling."""
        try:
            if hasattr(signal, 'take_profit_price') and signal.take_profit_price is not None:
                return signal.take_profit_price
            else:
                # Calculate take profit based on risk/reward ratio
                signal_type_upper = str(signal.signal_type.value).upper()
                if signal_type_upper == 'LONG':
                    risk_distance = signal.price - stop_loss_price
                    return signal.price + (risk_distance * risk_reward_ratio)
                elif signal_type_upper == 'SHORT':
                    risk_distance = stop_loss_price - signal.price
                    return signal.price - (risk_distance * risk_reward_ratio)
                else:
                    raise ValueError(f"Invalid signal type: {signal.signal_type.value}")
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CALCULATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={'operation': 'take_profit_calculation'}
            )
            # Return safe default
            if signal.signal_type.value.upper() == 'LONG':
                return signal.price * 1.04  # 4% above entry
            else:
                return signal.price * 0.96  # 4% below entry
    
    def _calculate_position_risk_safely(self, position_size: float, portfolio_state: 'PortfolioState') -> float:
        """Calculate position risk percent with error handling."""
        try:
            if portfolio_state.total_equity <= 0:
                raise ValueError(f"Portfolio total equity must be positive, got {portfolio_state.total_equity}")
            return position_size / portfolio_state.total_equity
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CALCULATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={'operation': 'position_risk_calculation'}
            )
            # Return safe default
            return 0.0
    
    def _validate_trade_safely(self, signal: 'TradingSignal', portfolio_state: 'PortfolioState', position_size: float):
        """Validate trade with error handling."""
        try:
            return self.trade_validator.validate_trade(signal, portfolio_state, position_size)
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={'operation': 'trade_validation'}
            )
            # Return safe default validation result
            from ..validators.trade_validator import ValidationResult
            return ValidationResult(
                is_valid=False,
                rejection_reason=f"Validation failed: {str(e)}",
                warnings=[f"Validation error: {str(e)}"]
            )
    
    def _create_assessment_safely(self, signal, portfolio_state, recommended_position_size, stop_loss_price,
                                 take_profit_price, risk_reward_ratio, position_risk_percent, portfolio_heat,
                                 validation_result, processing_time_ms):
        """Create assessment with error handling."""
        try:
            return RiskAssessment(
                signal_id=signal.signal_id,
                asset=signal.asset,
                signal_type=signal.signal_type,
                signal_price=signal.price,
                signal_confidence=signal.confidence,
                timestamp=signal.timestamp,
                
                # Position sizing
                recommended_position_size=recommended_position_size,
                position_size_method="Fixed Percentage",
                
                # Risk management
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                
                # Risk metrics
                risk_reward_ratio=risk_reward_ratio,
                position_risk_percent=position_risk_percent,
                portfolio_heat=portfolio_heat,
                
                # Validation results from trade validator
                is_approved=validation_result.is_valid,
                rejection_reason=validation_result.rejection_reason,
                risk_warnings=validation_result.warnings,
                
                # Market conditions (placeholder values)
                market_volatility=0.0,
                correlation_risk=0.0,
                
                # Portfolio impact
                portfolio_impact={
                    'drawdown_impact': 0.0,
                    'exposure_increase': position_risk_percent
                },
                current_drawdown=getattr(portfolio_state, 'current_drawdown', 0.0),
                daily_pnl_impact=0.0,
                
                # Configuration used
                risk_config_snapshot={
                    'max_drawdown_limit': self.max_drawdown_limit,
                    'daily_loss_limit': self.daily_loss_limit,
                    'per_trade_stop_loss': self.per_trade_stop_loss,
                    'max_position_size': self.max_position_size
                },
                
                # Processing metadata
                processing_time_ms=processing_time_ms
            )
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.SYSTEM_ERROR,
                severity=ErrorSeverity.HIGH,
                context={'operation': 'assessment_creation'}
            )
            raise
    
    def _calculate_risk_level_safely(self, assessment: 'RiskAssessment'):
        """Calculate risk level with error handling."""
        try:
            return self.risk_level_calculator.calculate_risk_level(assessment)
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CALCULATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={'operation': 'risk_level_calculation'}
            )
            # Return safe default
            from ..models.risk_models import RiskLevel
            return RiskLevel.CRITICAL
    
    def _get_risk_factors_safely(self, assessment: 'RiskAssessment'):
        """Get risk factors with error handling."""
        try:
            return self.risk_level_calculator.get_risk_factors(assessment)
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                error_type=ErrorType.CALCULATION_ERROR,
                severity=ErrorSeverity.LOW,
                context={'operation': 'risk_factors_calculation'}
            )
            # Return safe default
            return []
    
    def to_json(self, assessment: 'RiskAssessment') -> str:
        """
        Convert risk assessment to JSON string.
        
        Args:
            assessment: RiskAssessment object to convert
            
        Returns:
            JSON string representation of the assessment
        """
        try:
            # Convert assessment to dictionary
            assessment_dict = {
                'signal_id': assessment.signal_id,
                'asset': assessment.asset,
                'signal_type': assessment.signal_type.value if assessment.signal_type else None,
                'signal_price': assessment.signal_price,
                'signal_confidence': assessment.signal_confidence,
                'timestamp': assessment.timestamp.isoformat() if assessment.timestamp else None,
                
                # Assessment results
                'is_approved': assessment.is_approved,
                'risk_level': assessment.risk_level.value if assessment.risk_level else None,
                'rejection_reason': assessment.rejection_reason,
                'risk_warnings': assessment.risk_warnings,
                
                # Position sizing
                'recommended_position_size': assessment.recommended_position_size,
                'position_size_method': assessment.position_size_method,
                
                # Risk management
                'stop_loss_price': assessment.stop_loss_price,
                'take_profit_price': assessment.take_profit_price,
                
                # Risk metrics
                'risk_reward_ratio': assessment.risk_reward_ratio,
                'position_risk_percent': assessment.position_risk_percent,
                'portfolio_heat': assessment.portfolio_heat,
                
                # Market conditions
                'market_volatility': assessment.market_volatility,
                'correlation_risk': assessment.correlation_risk,
                
                # Portfolio impact
                'portfolio_impact': assessment.portfolio_impact,
                'current_drawdown': assessment.current_drawdown,
                'daily_pnl_impact': assessment.daily_pnl_impact,
                
                # Configuration
                'risk_config_snapshot': assessment.risk_config_snapshot,
                
                # Processing metadata
                'processing_time_ms': assessment.processing_time_ms
            }
            
            return json.dumps(assessment_dict, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error converting assessment to JSON: {e}")
            # Return error JSON
            error_dict = {
                'error': True,
                'error_message': str(e),
                'signal_id': getattr(assessment, 'signal_id', 'unknown'),
                'asset': getattr(assessment, 'asset', 'unknown'),
                'is_approved': False,
                'rejection_reason': f"JSON conversion failed: {str(e)}"
            }
            return json.dumps(error_dict, indent=2) 