from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

@dataclass
class BacktestConfig:
    start_date: datetime
    end_date: datetime
    symbols: List[str]
    initial_capital: float = 100000.0
    max_duration_years: float = 10.0
    min_capital: float = 1.0

    def __post_init__(self):
        # Date validation
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        duration = self.end_date - self.start_date
        max_duration = timedelta(days=365.25 * self.max_duration_years)
        if duration > max_duration:
            raise ValueError(f"backtest duration cannot exceed {self.max_duration_years} years")
        # Capital validation
        if self.initial_capital < self.min_capital:
            raise ValueError(f"initial_capital must be at least ${self.min_capital}")
        if self.initial_capital > 1e12:
            raise ValueError("initial_capital cannot exceed $1 trillion")
        # Symbol validation and cleaning
        if not self.symbols:
            raise ValueError("at least one symbol must be provided")
        self.symbols = self._clean_symbols(self.symbols)

    def _clean_symbols(self, symbols: List[str]) -> List[str]:
        cleaned = []
        seen = set()
        for symbol in symbols:
            if not isinstance(symbol, str):
                raise ValueError("all symbols must be strings")
            symbol = symbol.strip().upper()
            if not symbol:
                continue
            if len(symbol) > 20:
                raise ValueError(f"symbol '{symbol}' exceeds 20 character limit")
            if symbol not in seen:
                seen.add(symbol)
                cleaned.append(symbol)
        if not cleaned:
            raise ValueError("no valid symbols provided after cleaning")
        return cleaned

    def get_duration_days(self) -> int:
        return (self.end_date - self.start_date).days

    def get_duration_years(self) -> float:
        return self.get_duration_days() / 365.25 