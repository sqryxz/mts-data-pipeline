from datetime import datetime, timezone
from typing import Iterator
from .data_loader import DataLoader
from ..events.market_event import MarketEvent
import math

class MarketDataProvider:
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader

    def generate_market_events(self, symbol: str, start_date: datetime, end_date: datetime) -> Iterator[MarketEvent]:
        # Input validation
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            raise ValueError("start_date and end_date must be datetime objects")
        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")

        df = self.data_loader.load_market_data(symbol, start_date, end_date)
        if df.empty:
            print(f"[MarketDataProvider] WARNING: No market data found for {symbol} between {start_date} and {end_date}")
            return

        events_generated = 0
        events_skipped = 0
        for row in df.itertuples():
            try:
                if not self._validate_row_data(row):
                    events_skipped += 1
                    continue
                ts = self._preserve_timezone(row.Index)
                event = MarketEvent(
                    timestamp=ts,
                    symbol=symbol,
                    open_price=float(row.open),
                    high_price=float(row.high),
                    low_price=float(row.low),
                    close_price=float(row.close),
                    volume=float(row.volume)
                )
                yield event
                events_generated += 1
            except Exception as e:
                print(f"[MarketDataProvider] ERROR: Failed to create MarketEvent for {symbol} at {row.Index}: {e}")
                events_skipped += 1
        print(f"[MarketDataProvider] {events_generated} events generated, {events_skipped} rows skipped for {symbol}")

    def _preserve_timezone(self, ts) -> datetime:
        # Ensure UTC timezone is preserved
        if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
            return ts
        return ts.replace(tzinfo=timezone.utc)

    def _validate_row_data(self, row) -> bool:
        try:
            prices = [row.open, row.high, row.low, row.close]
            if any(math.isnan(p) or math.isinf(p) for p in prices):
                return False
            if any(p <= 0 for p in prices):
                return False
            if not (row.low <= row.open <= row.high):
                return False
            if not (row.low <= row.close <= row.high):
                return False
            if math.isnan(row.volume) or row.volume < 0:
                return False
            return True
        except (AttributeError, TypeError):
            return False 