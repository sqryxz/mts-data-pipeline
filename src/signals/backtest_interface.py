"""
Backtest Interface - Task 10
Interface for backtesting strategies against historical data from SQLite database.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

from src.data.sqlite_helper import CryptoDatabase
from src.signals.strategies.base_strategy import SignalStrategy
# MultiStrategyGenerator import removed to avoid circular dependency - import when needed
from src.data.signal_models import TradingSignal, SignalType
from src.utils.exceptions import DataProcessingError, ConfigurationError


class BacktestStatus(Enum):
    """Backtest execution status."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class BacktestResult:
    """Results from backtesting a strategy."""
    
    # Basic info
    strategy_name: str
    start_date: str
    end_date: str
    status: BacktestStatus
    
    # Performance metrics
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    
    # Trading statistics
    total_trades: int
    profitable_trades: int
    losing_trades: int
    average_trade_return: float
    average_winning_trade: float
    average_losing_trade: float
    
    # Risk metrics
    volatility: float
    var_95: float  # Value at Risk at 95% confidence
    calmar_ratio: float  # Annualized return / Max drawdown
    
    # Signal statistics
    total_signals: int
    long_signals: int
    short_signals: int
    hold_signals: int
    
    # Detailed data
    daily_returns: List[float]
    equity_curve: List[float]
    drawdown_series: List[float]
    trade_log: List[Dict[str, Any]]
    signals_generated: List[TradingSignal]
    
    # Metadata
    execution_time: float
    data_quality: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            'strategy_name': self.strategy_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': self.status.value,
            'performance_metrics': {
                'total_return': self.total_return,
                'annualized_return': self.annualized_return,
                'sharpe_ratio': self.sharpe_ratio,
                'max_drawdown': self.max_drawdown,
                'win_rate': self.win_rate,
                'volatility': self.volatility,
                'var_95': self.var_95,
                'calmar_ratio': self.calmar_ratio
            },
            'trading_statistics': {
                'total_trades': self.total_trades,
                'profitable_trades': self.profitable_trades,
                'losing_trades': self.losing_trades,
                'win_rate': self.win_rate,
                'average_trade_return': self.average_trade_return,
                'average_winning_trade': self.average_winning_trade,
                'average_losing_trade': self.average_losing_trade
            },
            'signal_statistics': {
                'total_signals': self.total_signals,
                'long_signals': self.long_signals,
                'short_signals': self.short_signals,
                'hold_signals': self.hold_signals
            },
            'daily_returns': self.daily_returns,
            'equity_curve': self.equity_curve,
            'drawdown_series': self.drawdown_series,
            'trade_log': self.trade_log,
            'execution_time': self.execution_time,
            'data_quality': self.data_quality
        }


class BacktestInterface:
    """
    Task 10: Backtest Interface
    
    Interface for backtesting strategies against historical SQLite data.
    Supports both individual strategy backtesting and multi-strategy system backtesting.
    """
    
    def __init__(self, initial_capital: float = 100000.0, transaction_cost: float = 0.001):
        """
        Initialize the backtest interface.
        
        Args:
            initial_capital: Starting capital for backtesting
            transaction_cost: Transaction cost as percentage (0.001 = 0.1%)
        """
        self.logger = logging.getLogger(__name__)
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.db = CryptoDatabase()
    
    def backtest_strategy(self, strategy: SignalStrategy, start_date: str, end_date: str) -> BacktestResult:
        """
        Backtest a single strategy against historical data.
        
        Args:
            strategy: Strategy instance to backtest
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            BacktestResult containing performance metrics and detailed results
        """
        self.logger.info(f"Starting backtest for strategy: {strategy.get_name()}")
        
        start_time = datetime.now()
        
        try:
            # Validate date range
            self._validate_date_range(start_date, end_date)
            
            # Get strategy parameters
            strategy_params = strategy.get_parameters()
            assets = strategy_params.get('assets', [])
            
            if not assets:
                raise ConfigurationError("Strategy must specify assets to backtest")
            
            # Get historical data
            historical_data = self._get_historical_data(assets, start_date, end_date)
            
            # Generate signals over the backtest period
            signals = self._generate_historical_signals(strategy, historical_data, start_date, end_date)
            
            # Execute backtest simulation
            backtest_results = self._execute_backtest_simulation(
                signals, historical_data, start_date, end_date
            )
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                backtest_results['daily_returns'],
                backtest_results['equity_curve'],
                backtest_results['trade_log']
            )
            
            # Calculate signal statistics
            signal_stats = self._calculate_signal_statistics(signals)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create result object
            result = BacktestResult(
                strategy_name=strategy.get_name(),
                start_date=start_date,
                end_date=end_date,
                status=BacktestStatus.SUCCESS,
                total_return=performance_metrics['total_return'],
                annualized_return=performance_metrics['annualized_return'],
                sharpe_ratio=performance_metrics['sharpe_ratio'],
                max_drawdown=performance_metrics['max_drawdown'],
                win_rate=performance_metrics['win_rate'],
                total_trades=performance_metrics['total_trades'],
                profitable_trades=performance_metrics['profitable_trades'],
                losing_trades=performance_metrics['losing_trades'],
                average_trade_return=performance_metrics['average_trade_return'],
                average_winning_trade=performance_metrics['average_winning_trade'],
                average_losing_trade=performance_metrics['average_losing_trade'],
                volatility=performance_metrics['volatility'],
                var_95=performance_metrics['var_95'],
                calmar_ratio=performance_metrics['calmar_ratio'],
                total_signals=signal_stats['total_signals'],
                long_signals=signal_stats['long_signals'],
                short_signals=signal_stats['short_signals'],
                hold_signals=signal_stats['hold_signals'],
                daily_returns=backtest_results['daily_returns'],
                equity_curve=backtest_results['equity_curve'],
                drawdown_series=backtest_results['drawdown_series'],
                trade_log=backtest_results['trade_log'],
                signals_generated=signals,
                execution_time=execution_time,
                data_quality=backtest_results['data_quality']
            )
            
            self.logger.info(f"Backtest completed successfully for {strategy.get_name()}")
            self.logger.info(f"Total return: {performance_metrics['total_return']:.2%}")
            self.logger.info(f"Sharpe ratio: {performance_metrics['sharpe_ratio']:.3f}")
            self.logger.info(f"Max drawdown: {performance_metrics['max_drawdown']:.2%}")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Backtest failed for strategy {strategy.get_name()}: {e}")
            
            # Return failed result
            return self._create_failed_result(strategy.get_name(), start_date, end_date, execution_time)
    
    def backtest_aggregated_strategies(self, generator, 
                                     start_date: str, end_date: str) -> BacktestResult:
        """
        Backtest a multi-strategy system with signal aggregation.
        
        Args:
            generator: MultiStrategyGenerator instance
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            BacktestResult containing performance metrics for the aggregated system
        """
        self.logger.info(f"Starting multi-strategy backtest with {len(generator.strategies)} strategies")
        
        start_time = datetime.now()
        
        try:
            # Validate date range
            self._validate_date_range(start_date, end_date)
            
            # Get all assets from all strategies
            all_assets = generator._get_all_assets()
            
            # Get historical data
            historical_data = self._get_historical_data(all_assets, start_date, end_date)
            
            # Generate aggregated signals over the backtest period
            aggregated_signals = self._generate_aggregated_historical_signals(
                generator, historical_data, start_date, end_date
            )
            
            # Execute backtest simulation
            backtest_results = self._execute_backtest_simulation(
                aggregated_signals, historical_data, start_date, end_date
            )
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                backtest_results['daily_returns'],
                backtest_results['equity_curve'],
                backtest_results['trade_log']
            )
            
            # Calculate signal statistics
            signal_stats = self._calculate_signal_statistics(aggregated_signals)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create result object
            result = BacktestResult(
                strategy_name="Multi-Strategy_Aggregated",
                start_date=start_date,
                end_date=end_date,
                status=BacktestStatus.SUCCESS,
                total_return=performance_metrics['total_return'],
                annualized_return=performance_metrics['annualized_return'],
                sharpe_ratio=performance_metrics['sharpe_ratio'],
                max_drawdown=performance_metrics['max_drawdown'],
                win_rate=performance_metrics['win_rate'],
                total_trades=performance_metrics['total_trades'],
                profitable_trades=performance_metrics['profitable_trades'],
                losing_trades=performance_metrics['losing_trades'],
                average_trade_return=performance_metrics['average_trade_return'],
                average_winning_trade=performance_metrics['average_winning_trade'],
                average_losing_trade=performance_metrics['average_losing_trade'],
                volatility=performance_metrics['volatility'],
                var_95=performance_metrics['var_95'],
                calmar_ratio=performance_metrics['calmar_ratio'],
                total_signals=signal_stats['total_signals'],
                long_signals=signal_stats['long_signals'],
                short_signals=signal_stats['short_signals'],
                hold_signals=signal_stats['hold_signals'],
                daily_returns=backtest_results['daily_returns'],
                equity_curve=backtest_results['equity_curve'],
                drawdown_series=backtest_results['drawdown_series'],
                trade_log=backtest_results['trade_log'],
                signals_generated=aggregated_signals,
                execution_time=execution_time,
                data_quality=backtest_results['data_quality']
            )
            
            self.logger.info(f"Multi-strategy backtest completed successfully")
            self.logger.info(f"Total return: {performance_metrics['total_return']:.2%}")
            self.logger.info(f"Sharpe ratio: {performance_metrics['sharpe_ratio']:.3f}")
            self.logger.info(f"Max drawdown: {performance_metrics['max_drawdown']:.2%}")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Multi-strategy backtest failed: {e}")
            
            # Return failed result
            return self._create_failed_result("Multi-Strategy_Aggregated", start_date, end_date, execution_time)
    
    def _validate_date_range(self, start_date: str, end_date: str) -> None:
        """Validate the date range for backtesting."""
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start_dt >= end_dt:
                raise ConfigurationError("Start date must be before end date")
            
            # Check if date range is reasonable (not too far in the past or future)
            today = datetime.now()
            if end_dt > today:
                raise ConfigurationError("End date cannot be in the future")
            
            if start_dt < datetime(2020, 1, 1):
                raise ConfigurationError("Start date cannot be before 2020-01-01")
            
        except ValueError as e:
            raise ConfigurationError(f"Invalid date format. Use YYYY-MM-DD: {e}")
    
    def _get_historical_data(self, assets: List[str], start_date: str, end_date: str) -> Dict[str, Any]:
        """Get historical data for backtesting."""
        try:
            # Calculate days between start and end date
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            days = (end_dt - start_dt).days + 30  # Add buffer for calculations
            
            # Get market data using our enhanced provider
            market_data = self.db.get_strategy_market_data(assets, days)
            
            # Filter data to exact date range
            filtered_data = self._filter_data_by_date_range(market_data, start_date, end_date)
            
            return filtered_data
            
        except Exception as e:
            raise DataProcessingError(f"Failed to get historical data: {e}")
    
    def _filter_data_by_date_range(self, market_data: Dict[str, Any], 
                                  start_date: str, end_date: str) -> Dict[str, Any]:
        """Filter market data to specific date range."""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        filtered_data = market_data.copy()
        
        # Filter VIX data
        if 'vix_data' in filtered_data:
            vix_data = []
            for record in filtered_data['vix_data']:
                record_date = datetime.strptime(record['date'], '%Y-%m-%d')
                if start_dt <= record_date <= end_dt:
                    vix_data.append(record)
            filtered_data['vix_data'] = vix_data
        
        # Filter crypto data
        if 'crypto_data' in filtered_data:
            for asset in filtered_data['crypto_data']:
                if 'price_data' in filtered_data['crypto_data'][asset]:
                    price_data = []
                    for record in filtered_data['crypto_data'][asset]['price_data']:
                        record_date = datetime.strptime(record['date'], '%Y-%m-%d')
                        if start_dt <= record_date <= end_dt:
                            price_data.append(record)
                    filtered_data['crypto_data'][asset]['price_data'] = price_data
        
        return filtered_data
    
    def _generate_historical_signals(self, strategy: SignalStrategy, 
                                   historical_data: Dict[str, Any],
                                   start_date: str, end_date: str) -> List[TradingSignal]:
        """Generate signals for the backtest period."""
        signals = []
        
        # Get date range
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Generate signals weekly to reduce computation
        current_date = start_dt
        while current_date <= end_dt:
            try:
                # Get data up to current date
                current_data = self._get_data_up_to_date(historical_data, current_date)
                
                # Run strategy analysis
                analysis_results = strategy.analyze(current_data)
                
                # Generate signals
                daily_signals = strategy.generate_signals(analysis_results)
                
                # Add timestamp to signals
                for signal in daily_signals:
                    signal.timestamp = current_date.timestamp()
                
                signals.extend(daily_signals)
                
            except Exception as e:
                self.logger.warning(f"Failed to generate signals for {current_date}: {e}")
            
            current_date += timedelta(days=7)  # Weekly generation for performance
        
        return signals
    
    def _generate_aggregated_historical_signals(self, generator,
                                              historical_data: Dict[str, Any],
                                              start_date: str, end_date: str) -> List[TradingSignal]:
        """Generate aggregated signals for the backtest period."""
        signals = []
        
        # Get date range
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Generate signals weekly to reduce computation
        current_date = start_dt
        while current_date <= end_dt:
            try:
                # Get data up to current date
                current_data = self._get_data_up_to_date(historical_data, current_date)
                
                # Generate individual signals from each strategy
                strategy_signals = generator._generate_individual_signals(current_data)
                
                # Aggregate signals
                daily_aggregated_signals = generator.aggregator.aggregate_signals(strategy_signals)
                
                # Add timestamp to signals
                for signal in daily_aggregated_signals:
                    signal.timestamp = current_date.timestamp()
                
                signals.extend(daily_aggregated_signals)
                
            except Exception as e:
                self.logger.warning(f"Failed to generate aggregated signals for {current_date}: {e}")
            
            current_date += timedelta(days=7)  # Weekly generation for performance
        
        return signals
    
    def _get_data_up_to_date(self, historical_data: Dict[str, Any], target_date: datetime) -> Dict[str, Any]:
        """Get data up to a specific date (for point-in-time analysis)."""
        filtered_data = historical_data.copy()
        
        # Filter VIX data
        if 'vix_data' in filtered_data:
            vix_data = []
            for record in filtered_data['vix_data']:
                record_date = datetime.strptime(record['date'], '%Y-%m-%d')
                if record_date <= target_date:
                    vix_data.append(record)
            filtered_data['vix_data'] = vix_data
        
        # Filter crypto data
        if 'crypto_data' in filtered_data:
            for asset in filtered_data['crypto_data']:
                if 'price_data' in filtered_data['crypto_data'][asset]:
                    price_data = []
                    for record in filtered_data['crypto_data'][asset]['price_data']:
                        record_date = datetime.strptime(record['date'], '%Y-%m-%d')
                        if record_date <= target_date:
                            price_data.append(record)
                    filtered_data['crypto_data'][asset]['price_data'] = price_data
        
        return filtered_data
    
    def _execute_backtest_simulation(self, signals: List[TradingSignal], 
                                   historical_data: Dict[str, Any],
                                   start_date: str, end_date: str) -> Dict[str, Any]:
        """Execute the backtest simulation with position management."""
        
        # Initialize portfolio
        portfolio = {
            'cash': self.initial_capital,
            'positions': {},  # asset -> {'shares': float, 'entry_price': float, 'entry_date': str}
            'equity_history': [],
            'daily_returns': [],
            'trade_log': []
        }
        
        # Get price data for all assets
        price_data = self._prepare_price_data(historical_data)
        
        # Process signals day by day
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        current_date = start_dt
        prev_portfolio_value = self.initial_capital
        
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Get signals for this date
            date_signals = [s for s in signals if datetime.fromtimestamp(s.timestamp).date() == current_date.date()]
            
            # Execute trades based on signals
            for signal in date_signals:
                self._execute_trade(signal, portfolio, price_data, date_str)
            
            # Calculate portfolio value
            portfolio_value = self._calculate_portfolio_value(portfolio, price_data, date_str)
            
            # Calculate daily return
            if prev_portfolio_value > 0:
                daily_return = (portfolio_value - prev_portfolio_value) / prev_portfolio_value
            else:
                daily_return = 0.0
            
            portfolio['daily_returns'].append(daily_return)
            portfolio['equity_history'].append(portfolio_value)
            
            prev_portfolio_value = portfolio_value
            current_date += timedelta(days=1)
        
        # Calculate drawdown series
        drawdown_series = self._calculate_drawdown_series(portfolio['equity_history'])
        
        # Assess data quality
        data_quality = self._assess_data_quality(historical_data, start_date, end_date)
        
        return {
            'daily_returns': portfolio['daily_returns'],
            'equity_curve': portfolio['equity_history'],
            'drawdown_series': drawdown_series,
            'trade_log': portfolio['trade_log'],
            'data_quality': data_quality
        }
    
    def _prepare_price_data(self, historical_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Prepare price data for easy lookup during simulation."""
        price_data = {}
        
        if 'crypto_data' in historical_data:
            for asset in historical_data['crypto_data']:
                price_data[asset] = {}
                if 'price_data' in historical_data['crypto_data'][asset]:
                    for record in historical_data['crypto_data'][asset]['price_data']:
                        price_data[asset][record['date']] = record['close']
        
        return price_data
    
    def _execute_trade(self, signal: TradingSignal, portfolio: Dict[str, Any], 
                      price_data: Dict[str, Dict[str, float]], date_str: str) -> None:
        """Execute a trade based on a signal."""
        
        asset = signal.asset
        signal_type = signal.signal_type
        position_size = signal.position_size
        
        # Get current price
        if asset not in price_data or date_str not in price_data[asset]:
            return  # Skip if no price data
        
        current_price = price_data[asset][date_str]
        
        # Calculate position value
        portfolio_value = self._calculate_portfolio_value(portfolio, price_data, date_str)
        position_value = portfolio_value * position_size
        
        # Handle different signal types
        if signal_type == SignalType.LONG:
            # Buy signal
            shares_to_buy = position_value / current_price
            transaction_cost = position_value * self.transaction_cost
            
            if portfolio['cash'] >= position_value + transaction_cost:
                portfolio['cash'] -= position_value + transaction_cost
                
                if asset not in portfolio['positions']:
                    portfolio['positions'][asset] = {
                        'shares': shares_to_buy,
                        'entry_price': current_price,
                        'entry_date': date_str
                    }
                else:
                    # Average up/down
                    existing_shares = portfolio['positions'][asset]['shares']
                    if existing_shares > 0:  # Adding to long position
                        existing_value = existing_shares * portfolio['positions'][asset]['entry_price']
                        new_avg_price = (existing_value + position_value) / (existing_shares + shares_to_buy)
                        
                        portfolio['positions'][asset]['shares'] += shares_to_buy
                        portfolio['positions'][asset]['entry_price'] = new_avg_price
                
                # Log trade
                portfolio['trade_log'].append({
                    'date': date_str,
                    'asset': asset,
                    'action': 'BUY',
                    'shares': shares_to_buy,
                    'price': current_price,
                    'value': position_value,
                    'transaction_cost': transaction_cost,
                    'signal_confidence': signal.confidence
                })
        
        elif signal_type == SignalType.SHORT:
            # Short signal - sell if we have a position
            if asset in portfolio['positions'] and portfolio['positions'][asset]['shares'] > 0:
                position = portfolio['positions'][asset]
                shares_to_sell = position['shares']
                sale_value = shares_to_sell * current_price
                transaction_cost = sale_value * self.transaction_cost
                
                portfolio['cash'] += sale_value - transaction_cost
                
                # Log trade
                portfolio['trade_log'].append({
                    'date': date_str,
                    'asset': asset,
                    'action': 'SELL',
                    'shares': shares_to_sell,
                    'price': current_price,
                    'value': sale_value,
                    'transaction_cost': transaction_cost,
                    'signal_confidence': signal.confidence,
                    'entry_price': position['entry_price'],
                    'pnl': (current_price - position['entry_price']) * shares_to_sell
                })
                
                # Remove position
                del portfolio['positions'][asset]
    
    def _calculate_portfolio_value(self, portfolio: Dict[str, Any], 
                                 price_data: Dict[str, Dict[str, float]], 
                                 date_str: str) -> float:
        """Calculate total portfolio value."""
        total_value = portfolio['cash']
        
        for asset, position in portfolio['positions'].items():
            if asset in price_data and date_str in price_data[asset]:
                current_price = price_data[asset][date_str]
                position_value = position['shares'] * current_price
                total_value += position_value
        
        return total_value
    
    def _calculate_drawdown_series(self, equity_curve: List[float]) -> List[float]:
        """Calculate drawdown series."""
        if not equity_curve:
            return []
        
        drawdown_series = []
        running_max = equity_curve[0]
        
        for value in equity_curve:
            running_max = max(running_max, value)
            drawdown = (value - running_max) / running_max if running_max > 0 else 0
            drawdown_series.append(drawdown)
        
        return drawdown_series
    
    def _calculate_performance_metrics(self, daily_returns: List[float], 
                                     equity_curve: List[float], 
                                     trade_log: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate comprehensive performance metrics."""
        if not daily_returns or not equity_curve:
            return self._get_empty_metrics()
        
        # Convert to numpy arrays for easier calculations
        returns = np.array(daily_returns)
        equity = np.array(equity_curve)
        
        # Basic returns
        if len(equity) > 1 and equity[0] > 0:
            total_return = (equity[-1] - equity[0]) / equity[0]
            annualized_return = (1 + total_return) ** (365 / len(equity)) - 1
        else:
            total_return = 0.0
            annualized_return = 0.0
        
        # Volatility
        volatility = np.std(returns) * np.sqrt(365) if len(returns) > 1 else 0.0
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        drawdown_series = self._calculate_drawdown_series(equity_curve)
        max_drawdown = abs(min(drawdown_series)) if drawdown_series else 0
        
        # Calmar ratio
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0
        
        # Trade statistics
        trades_with_pnl = [trade for trade in trade_log if 'pnl' in trade]
        
        total_trades = len(trade_log)
        profitable_trades = len([t for t in trades_with_pnl if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in trades_with_pnl if t.get('pnl', 0) < 0])
        
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        average_trade_return = np.mean([t.get('pnl', 0) for t in trades_with_pnl]) if trades_with_pnl else 0
        average_winning_trade = np.mean([t['pnl'] for t in trades_with_pnl if t.get('pnl', 0) > 0]) if profitable_trades > 0 else 0
        average_losing_trade = np.mean([t['pnl'] for t in trades_with_pnl if t.get('pnl', 0) < 0]) if losing_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'var_95': var_95,
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'average_trade_return': average_trade_return,
            'average_winning_trade': average_winning_trade,
            'average_losing_trade': average_losing_trade
        }
    
    def _calculate_signal_statistics(self, signals: List[TradingSignal]) -> Dict[str, int]:
        """Calculate signal statistics."""
        total_signals = len(signals)
        long_signals = len([s for s in signals if s.signal_type == SignalType.LONG])
        short_signals = len([s for s in signals if s.signal_type == SignalType.SHORT])
        hold_signals = len([s for s in signals if s.signal_type == SignalType.HOLD])
        
        return {
            'total_signals': total_signals,
            'long_signals': long_signals,
            'short_signals': short_signals,
            'hold_signals': hold_signals
        }
    
    def _assess_data_quality(self, historical_data: Dict[str, Any], 
                           start_date: str, end_date: str) -> Dict[str, Any]:
        """Assess the quality of historical data."""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        expected_days = (end_dt - start_dt).days + 1
        
        quality_metrics = {
            'expected_days': expected_days,
            'vix_data_completeness': 0.0,
            'crypto_data_completeness': {},
            'missing_dates': []
        }
        
        # Check VIX data completeness
        if 'vix_data' in historical_data:
            vix_days = len(historical_data['vix_data'])
            quality_metrics['vix_data_completeness'] = vix_days / expected_days if expected_days > 0 else 0
        
        # Check crypto data completeness
        if 'crypto_data' in historical_data:
            for asset in historical_data['crypto_data']:
                if 'price_data' in historical_data['crypto_data'][asset]:
                    crypto_days = len(historical_data['crypto_data'][asset]['price_data'])
                    quality_metrics['crypto_data_completeness'][asset] = crypto_days / expected_days if expected_days > 0 else 0
        
        return quality_metrics
    
    def _get_empty_metrics(self) -> Dict[str, float]:
        """Get empty metrics for failed backtests."""
        return {
            'total_return': 0.0,
            'annualized_return': 0.0,
            'volatility': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'calmar_ratio': 0.0,
            'var_95': 0.0,
            'total_trades': 0,
            'profitable_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'average_trade_return': 0.0,
            'average_winning_trade': 0.0,
            'average_losing_trade': 0.0
        }
    
    def _create_failed_result(self, strategy_name: str, start_date: str, 
                             end_date: str, execution_time: float) -> BacktestResult:
        """Create a failed backtest result."""
        return BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            status=BacktestStatus.FAILED,
            total_return=0.0,
            annualized_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            total_trades=0,
            profitable_trades=0,
            losing_trades=0,
            average_trade_return=0.0,
            average_winning_trade=0.0,
            average_losing_trade=0.0,
            volatility=0.0,
            var_95=0.0,
            calmar_ratio=0.0,
            total_signals=0,
            long_signals=0,
            short_signals=0,
            hold_signals=0,
            daily_returns=[],
            equity_curve=[],
            drawdown_series=[],
            trade_log=[],
            signals_generated=[],
            execution_time=execution_time,
            data_quality={}
        )
