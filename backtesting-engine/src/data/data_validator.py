import pandas as pd

class DataValidator:
    @staticmethod
    def validate_ohlcv(df: pd.DataFrame) -> bool:
        required_cols = ["open", "high", "low", "close", "volume"]
        # Check for required columns
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns in OHLCV data: {missing}")
        # Check for nulls
        if df[required_cols].isnull().any().any():
            raise ValueError("Null values found in OHLCV data")
        # Check for negative prices (allowing zero for volume)
        price_cols = ["open", "high", "low", "close"]
        if (df[price_cols] <= 0).any().any():
            raise ValueError("Non-positive values found in OHLC prices")
        if (df["volume"] < 0).any():
            raise ValueError("Negative values found in volume column")
        # Check high >= low
        if (df["high"] < df["low"]).any():
            raise ValueError("high < low found in OHLCV data")
        # Check open and close between low and high
        if not ((df["low"] <= df["open"]) & (df["open"] <= df["high"]) &
                (df["low"] <= df["close"]) & (df["close"] <= df["high"])) .all():
            raise ValueError("open/close not between low and high in OHLCV data")
        return True

    @staticmethod
    def validate_chronological(df: pd.DataFrame) -> bool:
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be a DatetimeIndex for chronological validation")
        if not df.index.is_monotonic_increasing:
            raise ValueError("Timestamps are not in chronological order")
        return True 