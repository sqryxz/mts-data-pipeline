"""
Risk level calculation components.
"""

import logging
import math
from typing import Dict, Any, List
from ..models.risk_models import RiskLevel, RiskAssessment

logger = logging.getLogger(__name__)


class RiskLevelCalculator:
    """
    Calculates risk levels based on various risk metrics.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize risk level calculator with configuration.
        
        Args:
            config: Risk management configuration
        """
        self.config = config
        self.risk_limits = config.get('risk_limits', {})
        
        # Risk level thresholds
        self.low_risk_threshold = 0.08      # 8% - below this is LOW
        self.medium_risk_threshold = 0.12    # 12% - below this is MEDIUM  
        self.high_risk_threshold = 0.18      # 18% - below this is HIGH
        # Above 18% is CRITICAL
        
        logger.info(f"Risk level calculator initialized:")
        logger.info(f"  Low risk threshold: {self.low_risk_threshold:.1%}")
        logger.info(f"  Medium risk threshold: {self.medium_risk_threshold:.1%}")
        logger.info(f"  High risk threshold: {self.high_risk_threshold:.1%}")
    
    def calculate_risk_level(self, assessment: RiskAssessment) -> RiskLevel:
        """
        Calculate overall risk level based on assessment metrics.
        
        Args:
            assessment: Risk assessment containing various metrics
            
        Returns:
            Calculated risk level
        """
        # Validate input
        if assessment is None:
            logger.error("Risk assessment cannot be None")
            return RiskLevel.HIGH  # Safe default
        
        # Validate required attributes exist
        required_attrs = [
            'position_risk_percent', 'portfolio_heat', 'current_drawdown',
            'market_volatility', 'correlation_risk'
        ]
        
        for attr in required_attrs:
            if not hasattr(assessment, attr):
                logger.error(f"Risk assessment missing required attribute: {attr}")
                return RiskLevel.HIGH
        
        # Validate data types and values
        try:
            for attr in required_attrs:
                value = getattr(assessment, attr)
                
                # Type check
                if not isinstance(value, (int, float)):
                    logger.error(f"{attr} must be numeric, got {type(value)}")
                    return RiskLevel.HIGH
                
                # NaN/Infinity check
                if not math.isfinite(value):
                    logger.error(f"{attr} contains invalid numeric value: {value}")
                    return RiskLevel.HIGH
                
                # Range check (most metrics should be 0-1)
                if value < 0:
                    logger.warning(f"{attr} is negative ({value}), may indicate data issue")
                
        except Exception as e:
            logger.error(f"Error validating assessment values: {e}")
            return RiskLevel.HIGH
        
        try:
            # Calculate composite risk score
            risk_score = self._calculate_composite_risk_score(assessment)
            
            # Determine risk level based on score
            if risk_score <= self.low_risk_threshold:
                risk_level = RiskLevel.LOW
            elif risk_score <= self.medium_risk_threshold:
                risk_level = RiskLevel.MEDIUM
            elif risk_score <= self.high_risk_threshold:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.CRITICAL
            
            logger.info(f"Risk level calculated: {risk_level.value} (score: {risk_score:.1%})")
            return risk_level
            
        except Exception as e:
            logger.error(f"Error calculating risk level: {e}")
            return RiskLevel.HIGH  # Default to HIGH on error
    
    def _calculate_composite_risk_score(self, assessment: RiskAssessment) -> float:
        """
        Calculate composite risk score from multiple metrics.
        
        Args:
            assessment: Risk assessment containing metrics
            
        Returns:
            Composite risk score (0.0 to 1.0)
        """
        try:
            # Validate required attributes
            required_attrs = [
                'position_risk_percent', 'portfolio_heat', 'current_drawdown',
                'market_volatility', 'correlation_risk'
            ]
            
            for attr in required_attrs:
                if not hasattr(assessment, attr):
                    logger.error(f"Risk assessment missing required attribute: {attr}")
                    return 0.5  # Default risk score
            
            # Safe attribute access with validation
            position_risk = self._validate_and_normalize_metric(
                getattr(assessment, 'position_risk_percent', 0.0), 'position_risk_percent'
            )
            portfolio_heat = self._validate_and_normalize_metric(
                getattr(assessment, 'portfolio_heat', 0.0), 'portfolio_heat'
            )
            drawdown_risk = self._validate_and_normalize_metric(
                getattr(assessment, 'current_drawdown', 0.0), 'current_drawdown'
            )
            volatility_risk = self._validate_and_normalize_metric(
                getattr(assessment, 'market_volatility', 0.0), 'market_volatility'
            )
            correlation_risk = self._validate_and_normalize_metric(
                getattr(assessment, 'correlation_risk', 0.0), 'correlation_risk'
            )
            
            # Weighted risk calculation
            weights = {
                'position_risk': 0.30,      # 30% weight
                'portfolio_heat': 0.25,      # 25% weight
                'drawdown_risk': 0.25,       # 25% weight
                'volatility_risk': 0.10,     # 10% weight
                'correlation_risk': 0.10     # 10% weight
            }
            
            # Calculate weighted score
            composite_score = (
                position_risk * weights['position_risk'] +
                portfolio_heat * weights['portfolio_heat'] +
                drawdown_risk * weights['drawdown_risk'] +
                volatility_risk * weights['volatility_risk'] +
                correlation_risk * weights['correlation_risk']
            )
            
            # Normalize to 0-1 range
            composite_score = min(composite_score, 1.0)
            composite_score = max(composite_score, 0.0)
            
            logger.debug(f"Composite risk score: {composite_score:.1%}")
            logger.debug(f"  Position risk: {position_risk:.1%}")
            logger.debug(f"  Portfolio heat: {portfolio_heat:.1%}")
            logger.debug(f"  Drawdown risk: {drawdown_risk:.1%}")
            logger.debug(f"  Volatility risk: {volatility_risk:.1%}")
            logger.debug(f"  Correlation risk: {correlation_risk:.1%}")
            
            return composite_score
            
        except Exception as e:
            logger.error(f"Error calculating composite risk score: {e}")
            return 0.5  # Default to 50% risk on error
    
    def get_risk_factors(self, assessment: RiskAssessment) -> List[str]:
        """
        Get list of contributing risk factors.
        
        Args:
            assessment: Risk assessment
            
        Returns:
            List of risk factor descriptions
        """
        # Validate input
        if assessment is None:
            logger.error("Risk assessment cannot be None")
            return ["Invalid assessment: None"]
        
        risk_factors = []
        
        try:
            # Check position risk
            position_risk = getattr(assessment, 'position_risk_percent', 0.0)
            if position_risk > 0.05:
                risk_factors.append(f"High position risk: {position_risk:.1%}")
            
            # Check portfolio heat
            portfolio_heat = getattr(assessment, 'portfolio_heat', 0.0)
            if portfolio_heat > 0.10:
                risk_factors.append(f"High portfolio heat: {portfolio_heat:.1%}")
            
            # Check drawdown
            current_drawdown = getattr(assessment, 'current_drawdown', 0.0)
            if current_drawdown > 0.10:
                risk_factors.append(f"High drawdown: {current_drawdown:.1%}")
            
            # Check volatility
            market_volatility = getattr(assessment, 'market_volatility', 0.0)
            if market_volatility > 0.05:
                risk_factors.append(f"High volatility: {market_volatility:.1%}")
            
            # Check correlation
            correlation_risk = getattr(assessment, 'correlation_risk', 0.0)
            if correlation_risk > 0.70:
                risk_factors.append(f"High correlation risk: {correlation_risk:.1%}")
            
            # Check risk/reward ratio
            risk_reward_ratio = getattr(assessment, 'risk_reward_ratio', 0.0)
            if risk_reward_ratio < 1.5:
                risk_factors.append(f"Poor risk/reward ratio: {risk_reward_ratio:.2f}")
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Error getting risk factors: {e}")
            return ["Error calculating risk factors"]
    
    def _validate_and_normalize_metric(self, value: Any, metric_name: str, default: float = 0.0) -> float:
        """
        Validate and normalize a risk metric value.
        
        Args:
            value: The metric value to validate
            metric_name: Name of the metric for logging
            default: Default value to use if validation fails
            
        Returns:
            Normalized metric value
        """
        if value is None:
            logger.warning(f"{metric_name} is None, using default: {default}")
            return default
        
        if not isinstance(value, (int, float)):
            logger.error(f"{metric_name} must be numeric, got {type(value)}, using default")
            return default
        
        if value < 0:
            logger.warning(f"{metric_name} is negative ({value}), using 0")
            return 0.0
        
        # Most metrics should be percentages (0-1), but some like risk_reward_ratio can be > 1
        if metric_name != 'risk_reward_ratio' and value > 1.0:
            logger.warning(f"{metric_name} > 100% ({value}), capping at 1.0")
            return 1.0
        
        return float(value) 