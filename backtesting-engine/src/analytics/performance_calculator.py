from typing import List, Optional, Dict
from datetime import datetime
import numpy as np
from decimal import Decimal

class PerformanceCalculator:
    """
    Tracks portfolio value and returns over time, and calculates total return and risk metrics.
    """
    def __init__(self):
        self.dates: List[datetime] = []
        self.portfolio_values: List[float] = []
        self.returns: List[float] = []

    def add_portfolio_value(self, date: datetime, value: float) -> None:
        """
        Add a portfolio value for a given date.
        """
        if self.portfolio_values:
            prev_value = self.portfolio_values[-1]
            if prev_value > 0:
                ret = (value - prev_value) / prev_value
            else:
                ret = 0.0
            self.returns.append(ret)
        self.dates.append(date)
        self.portfolio_values.append(value)

    def calculate_total_return(self) -> Optional[float]:
        """
        Calculate total return over the tracked period.
        Returns None if not enough data.
        """
        if not self.portfolio_values or len(self.portfolio_values) < 2:
            return None
        initial = self.portfolio_values[0]
        final = self.portfolio_values[-1]
        if initial == 0:
            return None
        return (final - initial) / initial

    def calculate_sharpe_ratio(self, returns: Optional[List[float]] = None, risk_free_rate: float = 0.02, periods_per_year: Optional[int] = None) -> Optional[float]:
        """
        Calculate annualized Sharpe ratio with edge case protection and input validation.
        Args:
            returns: List of periodic returns (if None, use self.returns)
            risk_free_rate: Annual risk-free rate (default 2%)
            periods_per_year: Number of periods per year (default: 252 for daily, 365 for crypto daily, 52 for weekly, 8760 for hourly)
        Returns:
            Sharpe ratio, or None if not enough data or invalid input
        """
        rets = np.array(returns if returns is not None else self.returns, dtype=np.float64)
        if len(rets) < 2:
            return None
        if np.any(np.isnan(rets)) or np.any(np.isinf(rets)):
            return None
        mean_ret = np.mean(rets)
        std_ret = np.std(rets, ddof=1)
        # Use a small epsilon to avoid near-zero volatility explosion
        EPSILON = 1e-8
        if std_ret < EPSILON:
            return None
        # Infer periods_per_year if not provided (default: 252)
        if periods_per_year is None:
            periods_per_year = 252
        rf_per_period = (1 + risk_free_rate) ** (1 / periods_per_year) - 1
        excess_ret = mean_ret - rf_per_period
        sharpe = (excess_ret / std_ret) * np.sqrt(periods_per_year)
        return sharpe

    def calculate_max_drawdown(self, portfolio_values: Optional[List[float]] = None) -> Optional[Dict[str, float]]:
        """
        Calculate maximum drawdown and related stats with edge case protection.
        Args:
            portfolio_values: List of portfolio values (if None, use self.portfolio_values)
        Returns:
            Dict with max_drawdown, peak, trough, and duration, or None if not enough data or invalid input
        """
        values = np.array(portfolio_values if portfolio_values is not None else self.portfolio_values, dtype=np.float64)
        if len(values) < 2:
            return None
        if np.any(np.isnan(values)) or np.any(np.isinf(values)) or np.any(values < 0):
            return None
        running_max = np.maximum.accumulate(values)
        drawdowns = (values - running_max) / running_max
        min_drawdown = np.min(drawdowns)
        trough_idx = np.argmin(drawdowns)
        # Find the last peak before the trough
        peak_idx = np.argmax(values[:trough_idx+1]) if trough_idx > 0 else 0
        # Duration is time from peak to trough; if never recovers, duration is till end
        duration = trough_idx - peak_idx if trough_idx > peak_idx else 0
        return {
            "max_drawdown": float(-min_drawdown),
            "peak": float(running_max[peak_idx]),
            "trough": float(values[trough_idx]),
            "duration": int(duration)
        } 