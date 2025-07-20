"""
Macro Analytics API Endpoints

FastAPI router for macro indicator analytics endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import threading
import re
from functools import lru_cache

# Import Pydantic for response models
try:
    from pydantic import BaseModel, validator
except ImportError:
    # Fallback for older FastAPI versions
    BaseModel = object
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Import service
try:
    from services.macro_analytics_service import MacroAnalyticsService
except ImportError:
    # Fallback for when running as module
    from ...services.macro_analytics_service import MacroAnalyticsService

# Create router
router = APIRouter(prefix="/macro-analytics", tags=["macro-analytics"])

# Logger
logger = logging.getLogger(__name__)

# Thread-safe service instance management
_service_lock = threading.Lock()
_service_instance: Optional[MacroAnalyticsService] = None


# Response Models
class HealthCheckResponse(BaseModel):
    status: str
    service_type: str
    repository_available: bool
    calculator_available: bool
    configuration_loaded: bool
    timestamp: str
    endpoint: str


class IndicatorsResponse(BaseModel):
    indicators: List[str]
    count: int
    timestamp: str
    endpoint: str


class TimeframesResponse(BaseModel):
    timeframes: List[str]
    count: int
    timestamp: str
    endpoint: str


class ConfigResponse(BaseModel):
    configuration: Dict[str, Any]
    timestamp: str
    endpoint: str


class SummaryResponse(BaseModel):
    summary: Dict[str, Any]
    timestamp: str
    endpoint: str


class ValidationResponse(BaseModel):
    indicator: Optional[str] = None
    timeframe: Optional[str] = None
    valid: bool
    timestamp: str
    endpoint: str


class CalculateMetricsRequest(BaseModel):
    timeframes: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    save_results: bool = False
    
    @validator('timeframes', each_item=True)
    def validate_timeframe_format(cls, v):
        if v and not re.match(r'^[0-9]+[hdwm]$', v):
            raise ValueError(f"Invalid timeframe format: {v}")
        return v
    
    @validator('metrics', each_item=True)
    def validate_metric_format(cls, v):
        valid_metrics = ['roc', 'z_score']
        if v and v not in valid_metrics:
            raise ValueError(f"Invalid metric: {v}. Valid metrics: {valid_metrics}")
        return v


class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: str
    endpoint: str


def get_service() -> MacroAnalyticsService:
    """
    Thread-safe service getter with caching.
    
    Returns:
        MacroAnalyticsService: Service instance
    """
    global _service_instance
    
    if _service_instance is None:
        with _service_lock:
            if _service_instance is None:  # Double-check pattern
                try:
                    _service_instance = MacroAnalyticsService()
                    logger.info("MacroAnalyticsService initialized for API")
                except Exception as e:
                    logger.error(f"Failed to initialize MacroAnalyticsService: {e}")
                    raise HTTPException(status_code=500, detail="Service initialization failed")
    
    return _service_instance


def validate_indicator_format(indicator: str) -> bool:
    """
    Validate indicator format.
    
    Args:
        indicator: Indicator name to validate
        
    Returns:
        bool: True if valid format
    """
    if not indicator or not isinstance(indicator, str):
        return False
    
    # Allow alphanumeric and underscore characters
    return bool(re.match(r'^[A-Z0-9_]+$', indicator.strip()))


def sanitize_path_parameter(param: str) -> str:
    """
    Sanitize path parameters to prevent injection.
    
    Args:
        param: Parameter to sanitize
        
    Returns:
        str: Sanitized parameter
    """
    if not param:
        return ""
    
    # Remove any potentially dangerous characters
    sanitized = re.sub(r'[^A-Za-z0-9_-]', '', param)
    return sanitized.strip()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint for the macro analytics service.
    
    Returns:
        HealthCheckResponse: Health status information
    """
    try:
        service = get_service()
        service_info = service.get_service_info()
        
        return HealthCheckResponse(
            status="healthy",
            service_type=service_info.get("service_type", "unknown"),
            repository_available=service_info.get("repository_available", False),
            calculator_available=service_info.get("calculator_available", False),
            configuration_loaded=service_info.get("configuration_loaded", False),
            timestamp=datetime.now().isoformat(),
            endpoint="/macro-analytics/health"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/indicators", response_model=IndicatorsResponse)
async def get_supported_indicators():
    """
    Get list of supported macro indicators.
    
    Returns:
        IndicatorsResponse: List of supported indicators
    """
    try:
        service = get_service()
        indicators = service.get_supported_indicators()
        
        return IndicatorsResponse(
            indicators=indicators,
            count=len(indicators),
            timestamp=datetime.now().isoformat(),
            endpoint="/macro-analytics/indicators"
        )
        
    except Exception as e:
        logger.error(f"Failed to get supported indicators: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get indicators: {str(e)}")


@router.get("/timeframes", response_model=TimeframesResponse)
async def get_default_timeframes():
    """
    Get list of default timeframes for analysis.
    
    Returns:
        TimeframesResponse: List of default timeframes
    """
    try:
        service = get_service()
        timeframes = service.get_default_timeframes()
        
        return TimeframesResponse(
            timeframes=timeframes,
            count=len(timeframes),
            timestamp=datetime.now().isoformat(),
            endpoint="/macro-analytics/timeframes"
        )
        
    except Exception as e:
        logger.error(f"Failed to get default timeframes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get timeframes: {str(e)}")


@router.get("/config", response_model=ConfigResponse)
async def get_service_configuration():
    """
    Get current service configuration (filtered for security).
    
    Returns:
        ConfigResponse: Service configuration (safe version)
    """
    try:
        service = get_service()
        config = service.get_configuration()
        
        # Filter sensitive information
        safe_config = {
            "analytics": config.get("analytics", {}),
            "indicators": config.get("indicators", {}),
            "logging": {
                "level": config.get("logging", {}).get("level", "INFO")
            }
            # Exclude database paths and other sensitive data
        }
        
        return ConfigResponse(
            configuration=safe_config,
            timestamp=datetime.now().isoformat(),
            endpoint="/macro-analytics/config"
        )
        
    except Exception as e:
        logger.error(f"Failed to get service configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.get("/summary", response_model=SummaryResponse)
async def get_analysis_summary():
    """
    Get analysis summary and service status.
    
    Returns:
        SummaryResponse: Analysis summary
    """
    try:
        service = get_service()
        summary = service.get_analysis_summary()
        
        return SummaryResponse(
            summary=summary,
            timestamp=datetime.now().isoformat(),
            endpoint="/macro-analytics/summary"
        )
        
    except Exception as e:
        logger.error(f"Failed to get analysis summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/validate/{indicator}", response_model=ValidationResponse)
async def validate_indicator(indicator: str):
    """
    Validate if an indicator is supported.
    
    Args:
        indicator: Indicator name to validate
        
    Returns:
        ValidationResponse: Validation result
    """
    try:
        # Sanitize and validate input
        sanitized_indicator = sanitize_path_parameter(indicator)
        if not validate_indicator_format(sanitized_indicator):
            raise HTTPException(status_code=400, detail="Invalid indicator format")
        
        service = get_service()
        is_valid = service.validate_indicator(sanitized_indicator)
        
        return ValidationResponse(
            indicator=sanitized_indicator,
            valid=is_valid,
            timestamp=datetime.now().isoformat(),
            endpoint=f"/macro-analytics/validate/{sanitized_indicator}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate indicator {indicator}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate indicator: {str(e)}")


@router.get("/validate/timeframe/{timeframe}", response_model=ValidationResponse)
async def validate_timeframe(timeframe: str):
    """
    Validate if a timeframe is supported.
    
    Args:
        timeframe: Timeframe to validate
        
    Returns:
        ValidationResponse: Validation result
    """
    try:
        # Sanitize and validate input
        sanitized_timeframe = sanitize_path_parameter(timeframe)
        if not sanitized_timeframe:
            raise HTTPException(status_code=400, detail="Invalid timeframe format")
        
        service = get_service()
        is_valid = service.validate_timeframe(sanitized_timeframe)
        
        return ValidationResponse(
            timeframe=sanitized_timeframe,
            valid=is_valid,
            timestamp=datetime.now().isoformat(),
            endpoint=f"/macro-analytics/validate/timeframe/{sanitized_timeframe}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate timeframe {timeframe}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate timeframe: {str(e)}")


@router.post("/calculate/{indicator}")
async def calculate_metrics(
    indicator: str,
    request: CalculateMetricsRequest
):
    """
    Calculate metrics for a specific indicator.
    
    Args:
        indicator: Indicator name to analyze
        request: CalculateMetricsRequest with parameters
        
    Returns:
        Dict: Calculation results
    """
    try:
        # Validate indicator format
        sanitized_indicator = sanitize_path_parameter(indicator)
        if not validate_indicator_format(sanitized_indicator):
            raise HTTPException(status_code=400, detail="Invalid indicator format")
        
        service = get_service()
        
        # Perform analysis
        result = service.analyze_indicator(
            indicator=sanitized_indicator,
            timeframes=request.timeframes,
            metrics=request.metrics
        )
        
        if result is None:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to calculate metrics for indicator: {sanitized_indicator}"
            )
        
        # Save results if requested (using public method)
        if request.save_results:
            try:
                # Use public method if available, otherwise log intent
                if hasattr(service, 'save_analysis_results'):
                    save_success = service.save_analysis_results(result)
                else:
                    save_success = service._save_results(result)  # Fallback
                    logger.warning("Using private method _save_results - consider adding public method")
                result["saved_to_database"] = save_success
            except Exception as e:
                logger.error(f"Failed to save results: {e}")
                result["saved_to_database"] = False
        
        # Add API metadata
        result["api_metadata"] = {
            "endpoint": f"/macro-analytics/calculate/{sanitized_indicator}",
            "request_time": datetime.now().isoformat(),
            "timeframes_requested": request.timeframes,
            "metrics_requested": request.metrics,
            "save_results_requested": request.save_results
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate metrics for {indicator}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to calculate metrics: {str(e)}"
        )


# Request validation middleware
# Note: APIRouter doesn't support middleware decorators
# This would be implemented at the FastAPI app level instead
# @router.middleware("http")
# async def validate_requests(request: Request, call_next):
#     """Middleware for request validation and logging."""
#     start_time = datetime.now()
#     
#     # Log request
#     logger.info(f"Request: {request.method} {request.url.path}")
#     
#     # Add basic rate limiting check (simple implementation)
#     # In production, use proper rate limiting library
#     client_ip = request.client.host if request.client else "unknown"
#     
#     # Process request
#     response = await call_next(request)
#     
#     # Add processing time header
#     process_time = (datetime.now() - start_time).total_seconds()
#     response.headers["X-Process-Time"] = str(process_time)
#     
#     # Log response
#     logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
#     
#     return response


# Example usage
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    # Create FastAPI app
    app = FastAPI(title="Macro Analytics API", version="1.0.0")
    
    # Include router
    app.include_router(router)
    
    # Add global exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        return JSONResponse(
            status_code=400,
            content={
                "error": "validation_error",
                "message": str(exc),
                "timestamp": datetime.now().isoformat(),
                "endpoint": str(request.url.path)
            }
        )
    
    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "error": "runtime_error",
                "message": str(exc),
                "timestamp": datetime.now().isoformat(),
                "endpoint": str(request.url.path)
            }
        )
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8000) 