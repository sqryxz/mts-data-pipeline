#!/usr/bin/env python3
"""
Performance Analytics Calculator
"""

import math
import numpy as np
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..core.models import Trade, PortfolioState

if TYPE_CHECKING:
    from ..portfolio.portfolio_manager import PortfolioManager


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    
    # Basic metrics
    total_return: float
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    
    # Trade metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Risk metrics
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_percent: float
    
    # Profitability metrics
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    
    # Volatility metrics
    volatility: float
    avg_trade_pnl: float
    
    # Time metrics
    trading_days: int
    avg_trades_per_day: float
    
    # Additional metrics
    best_day_pnl: float
    worst_day_pnl: float
    consecutive_wins: int
    consecutive_losses: int


class PerformanceCalculator:
    """Calculate comprehensive performance metrics"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize performance calculator
        
        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_metrics(self, portfolio_manager: "PortfolioManager") -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics
        
        Args:
            portfolio_manager: Portfolio manager with trade history
            
        Returns:
            PerformanceMetrics object with all calculated metrics
            
        Raises:
            ValueError: If portfolio_manager is None or initial capital is invalid
        """
        if portfolio_manager is None:
            raise ValueError("Portfolio manager cannot be None")
        
        trade_history = portfolio_manager.trade_history
        portfolio_state = portfolio_manager.get_state()
        
        if portfolio_state.initial_capital <= 0:
            raise ValueError("Initial capital must be positive")
        
        if not trade_history:
            return self._empty_metrics(portfolio_state)
        
        # Basic calculations
        total_pnl = portfolio_state.total_pnl
        realized_pnl = portfolio_state.realized_pnl
        unrealized_pnl = portfolio_state.unrealized_pnl
        total_return = (portfolio_state.total_value - portfolio_state.initial_capital) / portfolio_state.initial_capital
        
        # Get completed trades (SELL trades only) for consistent analysis
        completed_trades = [trade for trade in trade_history if trade.side.value == 'SELL']
        
        # Trade analysis using completed trades only
        winning_trades, losing_trades = self._analyze_trades(completed_trades)
        total_trades = len(completed_trades)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Profitability metrics using completed trades
        profit_factor, avg_win, avg_loss, largest_win, largest_loss = self._calculate_profitability(completed_trades)
        
        # Risk metrics using completed trades for consistency
        sharpe_ratio = self._calculate_sharpe_ratio(completed_trades, total_return, portfolio_state.initial_capital)
        max_drawdown, max_drawdown_percent = self._calculate_max_drawdown(completed_trades, portfolio_state.initial_capital)
        volatility = self._calculate_volatility(completed_trades)
        
        # Time metrics using all trades (for trading days calculation)
        trading_days, avg_trades_per_day = self._calculate_time_metrics(trade_history)
        
        # Additional metrics using completed trades for consistency
        best_day_pnl, worst_day_pnl = self._calculate_daily_extremes(completed_trades)
        consecutive_wins, consecutive_losses = self._calculate_consecutive_trades(completed_trades)
        
        # Calculate average trade P&L from completed trades
        completed_trades_pnl = sum(trade.pnl for trade in completed_trades)
        avg_trade_pnl = completed_trades_pnl / total_trades if total_trades > 0 else 0.0
        
        return PerformanceMetrics(
            total_return=total_return,
            total_pnl=total_pnl,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            profit_factor=profit_factor,
            average_win=avg_win,
            average_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            volatility=volatility,
            avg_trade_pnl=avg_trade_pnl,
            trading_days=trading_days,
            avg_trades_per_day=avg_trades_per_day,
            best_day_pnl=best_day_pnl,
            worst_day_pnl=worst_day_pnl,
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses
        )
    
    def _empty_metrics(self, portfolio_state: PortfolioState) -> PerformanceMetrics:
        """Return empty metrics for portfolio with no trades"""
        return PerformanceMetrics(
            total_return=0.0,
            total_pnl=portfolio_state.total_pnl,
            realized_pnl=portfolio_state.realized_pnl,
            unrealized_pnl=portfolio_state.unrealized_pnl,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            max_drawdown_percent=0.0,
            profit_factor=0.0,
            average_win=0.0,
            average_loss=0.0,
            largest_win=0.0,
            largest_loss=0.0,
            volatility=0.0,
            avg_trade_pnl=0.0,
            trading_days=0,
            avg_trades_per_day=0.0,
            best_day_pnl=0.0,
            worst_day_pnl=0.0,
            consecutive_wins=0,
            consecutive_losses=0
        )
    
    def _analyze_trades(self, completed_trades: List[Trade]) -> Tuple[int, int]:
        """Count winning and losing trades from completed trades only"""
        winning_trades = sum(1 for trade in completed_trades if trade.pnl > 0)
        losing_trades = sum(1 for trade in completed_trades if trade.pnl < 0)
        return winning_trades, losing_trades
    
    def _calculate_profitability(self, completed_trades: List[Trade]) -> Tuple[float, float, float, float, float]:
        """Calculate profitability metrics from completed trades only"""
        winning_pnls = [trade.pnl for trade in completed_trades if trade.pnl > 0]
        losing_pnls = [trade.pnl for trade in completed_trades if trade.pnl < 0]
        
        total_profit = sum(winning_pnls) if winning_pnls else 0.0
        total_loss = abs(sum(losing_pnls)) if losing_pnls else 0.0
        
        # Fix infinite profit factor - use a large finite value instead of infinity
        if total_loss > 0:
            profit_factor = total_profit / total_loss
        elif total_profit > 0:
            profit_factor = 1000.0  # Large finite value instead of infinity
        else:
            profit_factor = 0.0
        
        avg_win = total_profit / len(winning_pnls) if winning_pnls else 0.0
        avg_loss = total_loss / len(losing_pnls) if losing_pnls else 0.0
        largest_win = max(winning_pnls) if winning_pnls else 0.0
        largest_loss = min(losing_pnls) if losing_pnls else 0.0
        
        return profit_factor, avg_win, avg_loss, largest_win, largest_loss
    
    def _calculate_sharpe_ratio(self, completed_trades: List[Trade], total_return: float, initial_capital: float) -> float:
        """Calculate Sharpe ratio using completed trades and actual initial capital"""
        if len(completed_trades) < 2:
            return 0.0
        
        # Calculate daily returns using actual initial capital
        daily_returns = self._calculate_daily_returns(completed_trades, initial_capital)
        
        if not daily_returns:
            return 0.0
        
        # Calculate average daily return and standard deviation
        avg_daily_return = np.mean(daily_returns)
        daily_std = np.std(daily_returns, ddof=1)
        
        if daily_std == 0:
            return 0.0
        
        # Annualize (assuming 252 trading days)
        annualized_return = avg_daily_return * 252
        annualized_volatility = daily_std * math.sqrt(252)
        
        # Calculate Sharpe ratio
        sharpe_ratio = (annualized_return - self.risk_free_rate) / annualized_volatility
        
        return sharpe_ratio
    
    def _calculate_daily_returns(self, completed_trades: List[Trade], initial_capital: float) -> List[float]:
        """Calculate daily returns from completed trades using actual initial capital"""
        if not completed_trades:
            return []
        
        # Group trades by date
        daily_pnl = {}
        
        for trade in completed_trades:
            date = trade.timestamp.date()
            if date not in daily_pnl:
                daily_pnl[date] = 0.0
            daily_pnl[date] += trade.pnl
        
        # Calculate returns as percentage changes using running capital
        daily_returns = []
        running_capital = initial_capital
        
        for date in sorted(daily_pnl.keys()):
            pnl = daily_pnl[date]
            # Protect against negative or zero capital
            if running_capital <= 0:
                daily_returns.append(0.0)
                running_capital = max(0.01, running_capital + pnl)  # Prevent going to zero
            else:
                daily_return = pnl / running_capital
                daily_returns.append(daily_return)
                running_capital += pnl
        
        return daily_returns
    
    def _calculate_max_drawdown(self, completed_trades: List[Trade], initial_capital: float) -> Tuple[float, float]:
        """Calculate maximum drawdown using completed trades and actual portfolio values"""
        if not completed_trades:
            return 0.0, 0.0
        
        # Calculate cumulative portfolio values using actual initial capital
        portfolio_values = [initial_capital]
        cumulative_pnl = 0.0
        
        for trade in completed_trades:
            cumulative_pnl += trade.pnl
            portfolio_values.append(initial_capital + cumulative_pnl)
        
        # Calculate drawdown
        max_drawdown = 0.0
        peak = portfolio_values[0]
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        max_drawdown_percent = (max_drawdown / peak) * 100 if peak > 0 else 0.0
        
        return max_drawdown, max_drawdown_percent
    
    def _calculate_volatility(self, completed_trades: List[Trade]) -> float:
        """Calculate volatility of completed trade P&L"""
        if len(completed_trades) < 2:
            return 0.0
        
        pnls = [trade.pnl for trade in completed_trades]
        return np.std(pnls, ddof=1)
    
    def _calculate_time_metrics(self, trade_history: List[Trade]) -> Tuple[int, float]:
        """Calculate trading days and average trades per day using all trades"""
        if not trade_history:
            return 0, 0.0
        
        # Get date range from all trades (including BUY trades for trading days)
        dates = [trade.timestamp.date() for trade in trade_history]
        unique_dates = set(dates)
        trading_days = len(unique_dates)
        
        # Count completed trades for average calculation
        completed_trades = [trade for trade in trade_history if trade.side.value == 'SELL']
        avg_trades_per_day = len(completed_trades) / trading_days if trading_days > 0 else 0.0
        
        return trading_days, avg_trades_per_day
    
    def _calculate_daily_extremes(self, completed_trades: List[Trade]) -> Tuple[float, float]:
        """Calculate best and worst day P&L from completed trades only"""
        if not completed_trades:
            return 0.0, 0.0
        
        # Group trades by date
        daily_pnl = {}
        
        for trade in completed_trades:
            date = trade.timestamp.date()
            if date not in daily_pnl:
                daily_pnl[date] = 0.0
            daily_pnl[date] += trade.pnl
        
        if not daily_pnl:
            return 0.0, 0.0
        
        best_day_pnl = max(daily_pnl.values())
        worst_day_pnl = min(daily_pnl.values())
        
        return best_day_pnl, worst_day_pnl
    
    def _calculate_consecutive_trades(self, completed_trades: List[Trade]) -> Tuple[int, int]:
        """Calculate consecutive wins and losses from completed trades only"""
        if not completed_trades:
            return 0, 0
        
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in completed_trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            elif trade.pnl < 0:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
            else:  # pnl == 0, reset both counters
                current_wins = 0
                current_losses = 0
        
        return max_consecutive_wins, max_consecutive_losses
    
    def generate_summary_report(self, metrics: PerformanceMetrics) -> Dict:
        """Generate a summary report dictionary"""
        return {
            "summary": {
                "total_return_percent": metrics.total_return * 100,
                "total_pnl": metrics.total_pnl,
                "realized_pnl": metrics.realized_pnl,
                "unrealized_pnl": metrics.unrealized_pnl,
                "total_trades": metrics.total_trades,
                "win_rate_percent": metrics.win_rate * 100
            },
            "risk_metrics": {
                "sharpe_ratio": metrics.sharpe_ratio,
                "max_drawdown": metrics.max_drawdown,
                "max_drawdown_percent": metrics.max_drawdown_percent,
                "volatility": metrics.volatility
            },
            "profitability": {
                "profit_factor": metrics.profit_factor,
                "average_win": metrics.average_win,
                "average_loss": metrics.average_loss,
                "largest_win": metrics.largest_win,
                "largest_loss": metrics.largest_loss,
                "avg_trade_pnl": metrics.avg_trade_pnl
            },
            "trading_activity": {
                "trading_days": metrics.trading_days,
                "avg_trades_per_day": metrics.avg_trades_per_day,
                "best_day_pnl": metrics.best_day_pnl,
                "worst_day_pnl": metrics.worst_day_pnl,
                "consecutive_wins": metrics.consecutive_wins,
                "consecutive_losses": metrics.consecutive_losses
            }
        } 