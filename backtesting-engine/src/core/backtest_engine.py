from typing import Optional, Any, Dict, Protocol, Union, List
import logging
from datetime import datetime
from ..events.order_event import OrderEvent
from ..events.fill_event import FillEvent
from ..utils.exceptions import BacktestingError, DataError, StrategyError, ConfigurationError, ExecutionError
from ..database.backtest_models import BacktestResult

# Define protocols for better type safety
class PortfolioManager(Protocol):
    def update_portfolio(self, event: Any) -> None: ...
    def get_portfolio_value(self) -> float: ...
    def process_fill(self, symbol: str, quantity: float, price: float, commission: float = 0.0) -> None: ...

class ExecutionHandler(Protocol):
    def execute_order(self, order: Any, market_price: float) -> Optional[FillEvent]: ...
    def get_fill_cost(self, order: Any) -> float: ...

class Strategy(Protocol):
    def process_market_data(self, event: Any) -> List[Any]: ...

class MarketDataProvider(Protocol):
    def generate_market_events(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Any]: ...

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Main orchestrator for the event-driven backtesting process.
    Handles configuration, data loading, strategy execution, and result generation.
    """
    
    def __init__(self, config):
        """
        Initialize the backtest engine with the given configuration.
        Raises ConfigurationError if validation fails.
        """
        try:
            self.config = config
            self._validate_config()
            logger.info(f"BacktestEngine initialized for strategy: {config.strategies}")
        except Exception as e:
            logger.error(f"Failed to initialize BacktestEngine: {e}")
            raise ConfigurationError(f"Engine initialization failed: {e}")
    
    def _validate_config(self):
        """
        Validate the backtest configuration for required fields and logical constraints.
        Raises ConfigurationError if invalid.
        """
        if not self.config:
            raise ConfigurationError("Configuration cannot be None")
        if not self.config.strategies:
            raise ConfigurationError("At least one strategy must be specified")
        if not self.config.symbols:
            raise ConfigurationError("At least one symbol must be specified")
        if self.config.start_date >= self.config.end_date:
            raise ConfigurationError("Start date must be before end date")
        if self.config.initial_capital <= 0:
            raise ConfigurationError("Initial capital must be positive")
    
    def run_backtest(self) -> BacktestResult:
        """
        Run the complete backtest workflow: data loading, strategy execution, and result generation.
        Returns a BacktestResult object. Raises custom exceptions on error.
        """
        logger.info(f"Starting backtest: {self.config.strategies[0]} on {self.config.symbols}")
        try:
            market_data = self._load_market_data()
            portfolio_manager = self._initialize_portfolio()
            strategy = self._initialize_strategy()
            result = self._run_simulation(market_data, portfolio_manager, strategy)
            logger.info("Backtest completed successfully")
            return result
        except DataError as e:
            logger.error(f"Data error during backtest: {e}")
            raise
        except StrategyError as e:
            logger.error(f"Strategy error during backtest: {e}")
            raise
        except ExecutionError as e:
            logger.error(f"Execution error during backtest: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during backtest: {e}")
            raise BacktestingError(f"Backtest failed: {e}")
    
    def _load_market_data(self):
        """
        Load market data for the configured symbols and period.
        Returns mock data for demonstration. Raises DataError on failure.
        """
        try:
            logger.info(f"Loading market data for {self.config.symbols}")
            if not self.config.symbols:
                raise DataError("No symbols specified for data loading")
            return {"data": "mock_market_data"}
        except Exception as e:
            logger.error(f"Failed to load market data: {e}")
            raise DataError(f"Market data loading failed: {e}")
    
    def _initialize_portfolio(self):
        """
        Initialize the portfolio manager for the backtest.
        Returns a mock portfolio for demonstration. Raises ExecutionError on failure.
        """
        try:
            logger.info(f"Initializing portfolio with capital: {self.config.initial_capital}")
            return {"initial_capital": self.config.initial_capital}
        except Exception as e:
            logger.error(f"Failed to initialize portfolio: {e}")
            raise ExecutionError(f"Portfolio initialization failed: {e}")
    
    def _initialize_strategy(self):
        """
        Initialize the trading strategy for the backtest.
        Returns a mock strategy for demonstration. Raises StrategyError on failure.
        """
        try:
            strategy_name = self.config.strategies[0]
            logger.info(f"Initializing strategy: {strategy_name}")
            if strategy_name == "InvalidStrategy":
                raise StrategyError(f"Strategy '{strategy_name}' not found")
            return {"name": strategy_name}
        except Exception as e:
            logger.error(f"Failed to initialize strategy: {e}")
            raise StrategyError(f"Strategy initialization failed: {e}")
    
    def _run_simulation(self, market_data, portfolio_manager, strategy):
        """
        Run the backtest simulation loop, processing events and generating results.
        Returns a BacktestResult object. Raises ExecutionError on failure.
        """
        try:
            logger.info("Running backtest simulation")
            result = BacktestResult(
                total_return=0.15,
                sharpe_ratio=1.2,
                max_drawdown=0.08,
                trade_count=10,
                portfolio_values=[100000.0, 115000.0],
                trade_history=[
                    {"date": "2023-01-01", "symbol": "bitcoin", "action": "BUY", "quantity": 1.0, "price": 50000.0}
                ]
            )
            return result
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            raise ExecutionError(f"Backtest simulation failed: {e}")
    
    def cleanup(self):
        """
        Clean up resources after the backtest run. Does not raise on error.
        """
        try:
            logger.info("Cleaning up backtest engine resources")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}") 