"""
Production-ready FastAPI application for MTS Signal Generation API.

Provides endpoints for:
- Signal generation and retrieval
- Strategy backtesting
- System health monitoring
- Configuration management
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import asyncio
from contextlib import asynccontextmanager

# Setup path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis
import structlog

from config.settings import Config
from src.signals.strategies.strategy_registry import StrategyRegistry
from src.signals.signal_aggregator import SignalAggregator
from src.services.multi_strategy_generator import MultiStrategyGenerator
from src.signals.backtest_interface import BacktestInterface, BacktestResult, BacktestStatus
from src.data.signal_models import TradingSignal, SignalType, SignalStrength
from src.services.monitor import HealthChecker
from src.utils.exceptions import CryptoDataPipelineError

# Initialize configuration and logging
config = Config()
logger = structlog.get_logger(__name__)

# Redis connection for caching
try:
    redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None


# Pydantic Models for API
class SignalResponse(BaseModel):
    """Response model for trading signals"""
    signal_id: str
    asset: str
    signal_type: str
    timestamp: int
    price: float
    strategy_name: str
    signal_strength: str
    confidence: float
    position_size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_risk: Optional[float] = None
    analysis_data: Optional[Dict[str, Any]] = None
    correlation_value: Optional[float] = None
    created_at: str


class BacktestRequest(BaseModel):
    """Request model for backtesting"""
    strategy_name: str = Field(..., description="Name of strategy to backtest")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    use_aggregated: bool = Field(False, description="Use multi-strategy aggregation")


class BacktestResponse(BaseModel):
    """Response model for backtest results"""
    strategy_name: str
    start_date: str
    end_date: str
    status: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    execution_time: float
    
    # Optional detailed results
    daily_returns: Optional[List[float]] = None
    equity_curve: Optional[List[float]] = None
    trade_log: Optional[List[Dict[str, Any]]] = None


class SystemHealthResponse(BaseModel):
    """Response model for system health"""
    status: str
    healthy: bool
    timestamp: str
    components: Dict[str, Dict[str, Any]]
    uptime_seconds: float


class SignalGenerationRequest(BaseModel):
    """Request model for generating new signals"""
    strategies: Optional[List[str]] = Field(None, description="Specific strategies to run")
    assets: Optional[List[str]] = Field(None, description="Specific assets to analyze")
    force_refresh: bool = Field(False, description="Force refresh of cached data")
    days: int = Field(30, description="Number of days of data to analyze")


# Global variables for services
strategy_registry: Optional[StrategyRegistry] = None
signal_aggregator: Optional[SignalAggregator] = None
multi_strategy_generator: Optional[MultiStrategyGenerator] = None
backtest_interface: Optional[BacktestInterface] = None
health_checker: Optional[HealthChecker] = None
app_start_time: datetime = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application services"""
    global strategy_registry, signal_aggregator, multi_strategy_generator
    global backtest_interface, health_checker, app_start_time
    
    # Startup
    logger.info("Starting MTS Signal API...")
    app_start_time = datetime.now()
    
    try:
        # Initialize strategy registry
        strategy_registry = StrategyRegistry()
        strategy_registry.load_strategies_from_directory("src/signals/strategies")
        
        # Initialize backtest interface
        backtest_interface = BacktestInterface()
        
        # Initialize health checker
        health_checker = HealthChecker()
        
        # Create multi-strategy generator with default configuration
        strategy_configs = {}
        for strategy_name in config.ENABLED_STRATEGIES:
            strategy_configs[strategy_name] = {
                'config_path': f"{config.STRATEGY_CONFIG_DIR}/{strategy_name}.json"
            }
        
        aggregator_config = {
            'strategy_weights': config.STRATEGY_WEIGHTS,
            'aggregation_config': {
                'max_position_size': config.MAX_POSITION_SIZE,
                'conflict_resolution': 'weighted_average'
            }
        }
        
        multi_strategy_generator = MultiStrategyGenerator(strategy_configs, aggregator_config)
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down MTS Signal API...")
    if redis_client:
        redis_client.close()


# Create FastAPI application
app = FastAPI(
    title="MTS Signal Generation API",
    description="Production API for Multi-Trading Strategy Signal Generation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.is_development() else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency for caching
def get_cache_key(prefix: str, *args) -> str:
    """Generate cache key"""
    return f"{prefix}:{':'.join(map(str, args))}"


def cache_get(key: str) -> Optional[str]:
    """Get value from cache"""
    if redis_client:
        try:
            return redis_client.get(key)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
    return None


def cache_set(key: str, value: str, ttl: int = None) -> bool:
    """Set value in cache"""
    if redis_client:
        try:
            if ttl:
                return redis_client.setex(key, ttl, value)
            else:
                return redis_client.set(key, value)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    return False


# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "MTS Signal Generation API",
        "version": "1.0.0",
        "status": "operational",
        "environment": config.ENVIRONMENT.value,
        "documentation": "/docs"
    }


@app.get("/health", response_model=SystemHealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Get system health
        health_status = health_checker.get_system_health_status()
        
        # Calculate uptime
        uptime = (datetime.now() - app_start_time).total_seconds()
        
        return SystemHealthResponse(
            status=health_status['status'],
            healthy=health_status['healthy'],
            timestamp=health_status['checked_at'],
            components=health_status['components'],
            uptime_seconds=uptime
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/signals/generate", response_model=List[SignalResponse])
async def generate_signals(
    request: SignalGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate new trading signals"""
    try:
        # Check cache first (unless force refresh)
        cache_key = get_cache_key("signals", "latest", request.days)
        
        if not request.force_refresh:
            cached_signals = cache_get(cache_key)
            if cached_signals:
                logger.info("Returning cached signals")
                signals_data = json.loads(cached_signals)
                return [SignalResponse(**signal) for signal in signals_data]
        
        # Generate signals using multi-strategy generator
        signals = await asyncio.get_event_loop().run_in_executor(
            None, multi_strategy_generator.generate_aggregated_signals, request.days
        )
        
        # Convert to response format
        signal_responses = []
        for signal in signals:
            signal_data = signal.to_dict()
            signal_responses.append(SignalResponse(**signal_data))
        
        # Cache results
        cache_data = [signal.dict() for signal in signal_responses]
        background_tasks.add_task(
            cache_set, 
            cache_key, 
            json.dumps(cache_data), 
            config.REDIS_SIGNAL_TTL
        )
        
        logger.info(f"Generated {len(signal_responses)} signals")
        return signal_responses
        
    except Exception as e:
        logger.error(f"Signal generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Signal generation failed: {str(e)}")


@app.get("/signals/latest", response_model=List[SignalResponse])
async def get_latest_signals(
    asset: Optional[str] = Query(None, description="Filter by asset"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of signals")
):
    """Get latest generated signals with optional filtering"""
    try:
        # Try to get from cache first
        cache_key = get_cache_key("signals", "latest", 30)
        cached_signals = cache_get(cache_key)
        
        if not cached_signals:
            # Generate fresh signals if none cached
            request = SignalGenerationRequest()
            return await generate_signals(request, BackgroundTasks())
        
        signals_data = json.loads(cached_signals)
        signals = [SignalResponse(**signal) for signal in signals_data]
        
        # Apply filters
        if asset:
            signals = [s for s in signals if s.asset.lower() == asset.lower()]
        
        if strategy:
            signals = [s for s in signals if strategy.lower() in s.strategy_name.lower()]
        
        # Apply limit
        signals = signals[:limit]
        
        logger.info(f"Returning {len(signals)} filtered signals")
        return signals
        
    except Exception as e:
        logger.error(f"Failed to get latest signals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get signals: {str(e)}")


@app.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """Run strategy backtest"""
    try:
        # Check cache first
        cache_key = get_cache_key(
            "backtest", 
            request.strategy_name, 
            request.start_date, 
            request.end_date,
            request.use_aggregated
        )
        
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Returning cached backtest result")
            return BacktestResponse(**json.loads(cached_result))
        
        # Run backtest
        if request.use_aggregated:
            # Use multi-strategy generator
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                backtest_interface.backtest_aggregated_strategies,
                multi_strategy_generator,
                request.start_date,
                request.end_date
            )
        else:
            # Load single strategy
            config_path = f"{config.STRATEGY_CONFIG_DIR}/{request.strategy_name}.json"
            strategy = strategy_registry.get_strategy(request.strategy_name, config_path)
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                backtest_interface.backtest_strategy,
                strategy,
                request.start_date,
                request.end_date
            )
        
        # Convert to response format
        response_data = {
            'strategy_name': result.strategy_name,
            'start_date': result.start_date,
            'end_date': result.end_date,
            'status': result.status.value,
            'total_return': result.total_return,
            'annualized_return': result.annualized_return,
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown,
            'win_rate': result.win_rate,
            'total_trades': result.total_trades,
            'execution_time': result.execution_time
        }
        
        # Include detailed results for successful backtests
        if result.status == BacktestStatus.SUCCESS:
            response_data.update({
                'daily_returns': result.daily_returns,
                'equity_curve': result.equity_curve,
                'trade_log': result.trade_log
            })
        
        response = BacktestResponse(**response_data)
        
        # Cache successful results
        if result.status == BacktestStatus.SUCCESS:
            cache_set(cache_key, response.json(), 3600)  # Cache for 1 hour
        
        logger.info(f"Backtest completed: {request.strategy_name}")
        return response
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@app.get("/strategies", response_model=List[str])
async def list_strategies():
    """List available strategies"""
    try:
        strategies = list(strategy_registry.list_strategies().keys())
        return strategies
    except Exception as e:
        logger.error(f"Failed to list strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list strategies: {str(e)}")


@app.get("/config", response_model=Dict[str, Any])
async def get_configuration():
    """Get current system configuration (public settings only)"""
    try:
        public_config = {
            'environment': config.ENVIRONMENT.value,
            'enabled_strategies': config.ENABLED_STRATEGIES,
            'strategy_weights': config.STRATEGY_WEIGHTS,
            'signal_generation_interval_minutes': config.SIGNAL_GENERATION_INTERVAL_MINUTES,
            'max_position_size': config.MAX_POSITION_SIZE,
            'max_daily_trades': config.MAX_DAILY_TRADES,
            'api_version': "1.0.0",
            'features': {
                'caching_enabled': redis_client is not None,
                'monitoring_enabled': config.ENABLE_METRICS,
                'alerts_enabled': config.ENABLE_ALERTS
            }
        }
        return public_config
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


# Error handlers
@app.exception_handler(CryptoDataPipelineError)
async def pipeline_error_handler(request, exc):
    """Handle pipeline-specific errors"""
    logger.error(f"Pipeline error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": f"Pipeline error: {str(exc)}"}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle value errors"""
    logger.error(f"Value error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": f"Invalid value: {str(exc)}"}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.signal_api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        workers=config.API_WORKERS,
        log_level=config.LOG_LEVEL.lower(),
        reload=config.is_development()
    ) 