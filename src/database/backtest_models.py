from dataclasses import dataclass, field
from typing import List, Dict, Optional, TypedDict

class TradeRecord(TypedDict):
    date: str
    symbol: str
    action: str  # 'buy' or 'sell'
    price: float
    quantity: float
    pnl: float

@dataclass
class BacktestResult:
    """
    Structured results for a backtest run.
    Note: For large backtests, portfolio_values and trade_history may consume significant memory.
    For production, consider using decimal.Decimal for monetary values to avoid floating point errors.
    """
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    trade_count: int
    portfolio_values: List[float] = field(default_factory=list)
    trade_history: List[TradeRecord] = field(default_factory=list) 