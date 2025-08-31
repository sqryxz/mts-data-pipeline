"""
Discord Alert Database Logger
Logs Discord alert activity to SQLite database for tracking and analysis.
"""

import sqlite3
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager
from pathlib import Path

from src.data.signal_models import TradingSignal


class DiscordAlertLogger:
    """
    Database logger for Discord alert activity.
    Logs all Discord alert attempts, successes, and failures to SQLite database.
    """
    
    def __init__(self, db_path: str = "data/crypto_data.db"):
        """
        Initialize Discord alert logger.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        # FIX 1: Create directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure the discord_alerts table exists in the database."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS discord_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_type TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        price REAL NOT NULL,
                        confidence REAL NOT NULL,
                        strength TEXT,
                        position_size REAL,
                        stop_loss REAL,
                        take_profit REAL,
                        strategy_name TEXT,
                        webhook_url TEXT,
                        discord_message_id TEXT,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success BOOLEAN NOT NULL DEFAULT 0,
                        error_message TEXT,
                        alert_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better query performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_discord_alerts_symbol 
                    ON discord_alerts(symbol)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_discord_alerts_sent_at 
                    ON discord_alerts(sent_at)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_discord_alerts_signal_type 
                    ON discord_alerts(signal_type)
                """)
                
                conn.commit()
                self.logger.debug("Discord alerts table and indexes created/verified")
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to create discord_alerts table: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def log_alert_attempt(self, signal: TradingSignal, webhook_url: str, 
                         alert_type: str = "signal_alert", 
                         strategy_name: Optional[str] = None) -> Optional[int]:
        """
        Log a Discord alert attempt to the database.
        
        Args:
            signal: TradingSignal object
            webhook_url: Discord webhook URL used
            alert_type: Type of alert (signal_alert, test_alert, etc.)
            strategy_name: Name of the strategy that generated the signal
            
        Returns:
            Optional[int]: Database record ID, or None if failed
        """
        # FIX 9: Input validation
        if not signal:
            self.logger.error("Signal cannot be None")
            return None
        if not webhook_url:
            self.logger.error("Webhook URL cannot be empty")
            return None
        # FIX 5: Improved type safety for symbol validation
        if not hasattr(signal, 'symbol') or signal.symbol is None or signal.symbol == "":
            self.logger.error("Signal must have a valid symbol")
            return None
        
        # FIX 2: Additional required field validation
        if not hasattr(signal, 'price') or signal.price is None:
            self.logger.error("Signal must have a valid price")
            return None
        if not hasattr(signal, 'confidence') or signal.confidence is None:
            self.logger.error("Signal must have a valid confidence")
            return None
        if not hasattr(signal, 'signal_type') or signal.signal_type is None:
            self.logger.error("Signal must have a valid signal_type")
            return None
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # FIX 4: Safe timestamp handling
                timestamp = getattr(signal, 'timestamp', None)
                if timestamp and hasattr(timestamp, 'isoformat'):
                    timestamp = timestamp.isoformat()
                elif timestamp:
                    timestamp = str(timestamp)
                else:
                    timestamp = None
                
                # Extract data from signal
                alert_data = {
                    "signal_id": getattr(signal, 'id', None),
                    "timestamp": timestamp,
                    "analysis_data": getattr(signal, 'analysis_data', {}),
                    "test": getattr(signal, 'test', False),
                    "custom": getattr(signal, 'custom', False)
                }
                
                # FIX 3: Safe JSON serialization
                try:
                    alert_data_json = json.dumps(alert_data, default=str)
                except (TypeError, ValueError) as e:
                    self.logger.warning(f"Failed to serialize alert_data: {e}")
                    alert_data_json = json.dumps({})
                
                cursor.execute("""
                    INSERT INTO discord_alerts (
                        alert_type, symbol, signal_type, price, confidence, strength,
                        position_size, stop_loss, take_profit, strategy_name, webhook_url,
                        sent_at, success, alert_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert_type,
                    signal.symbol,
                    # FIX 1: Safe attribute access for signal_type
                    getattr(signal.signal_type, 'value', str(signal.signal_type)) if signal.signal_type else None,
                    signal.price,
                    signal.confidence,
                    # FIX 2: Safe attribute access
                    getattr(signal.signal_strength, 'value', None) if signal.signal_strength else None,
                    signal.position_size,
                    signal.stop_loss,
                    signal.take_profit,
                    strategy_name or getattr(signal, 'strategy_name', None),
                    webhook_url,
                    datetime.now(),
                    0,  # FIX 5: Start as failed, update to success
                    alert_data_json
                ))
                
                alert_id = cursor.lastrowid
                conn.commit()
                
                self.logger.debug(f"Logged Discord alert attempt: ID {alert_id} for {signal.symbol}")
                return alert_id
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to log Discord alert attempt: {e}")
            return None  # FIX 7: Return None instead of -1
    
    def update_alert_result(self, alert_id: Optional[int], success: bool, 
                           error_message: Optional[str] = None,
                           discord_message_id: Optional[str] = None):
        """
        Update the result of a Discord alert attempt.
        
        Args:
            alert_id: Database record ID from log_alert_attempt
            success: Whether the alert was sent successfully
            error_message: Error message if failed
            discord_message_id: Discord message ID if successful
        """
        # FIX 7: Handle None instead of -1
        if alert_id is None:
            return
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE discord_alerts 
                    SET success = ?, error_message = ?, discord_message_id = ?
                    WHERE id = ?
                """, (1 if success else 0, error_message, discord_message_id, alert_id))
                
                conn.commit()
                
                if success:
                    self.logger.debug(f"Updated Discord alert result: ID {alert_id} - SUCCESS")
                else:
                    self.logger.warning(f"Updated Discord alert result: ID {alert_id} - FAILED: {error_message}")
                    
        except sqlite3.Error as e:
            self.logger.error(f"Failed to update Discord alert result: {e}")
    
    def log_bulk_alert_results(self, alert_results: Dict[int, bool]):
        """
        Log results of bulk alert sending with individual tracking.
        
        Args:
            alert_results: Dict mapping alert_id -> success_status
        """
        if not alert_results:
            return
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # FIX 3: Individual result tracking with efficient bulk update
                cursor.executemany("""
                    UPDATE discord_alerts 
                    SET success = ? 
                    WHERE id = ?
                """, [(1 if success else 0, alert_id) for alert_id, success in alert_results.items()])
                
                conn.commit()
                success_count = sum(1 for success in alert_results.values() if success)
                self.logger.debug(f"Updated {len(alert_results)} Discord alerts: {success_count} successful, {len(alert_results) - success_count} failed")
                    
        except sqlite3.Error as e:
            self.logger.error(f"Failed to update bulk Discord alert results: {e}")
    
    def get_recent_alerts(self, limit: int = 50) -> list:
        """
        Get recent Discord alerts from the database.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of alert records
        """
        # FIX 10: Add limit validation
        if limit <= 0:
            self.logger.warning("Invalid limit provided, using default of 50")
            limit = 50
        elif limit > 1000:  # Prevent excessive memory usage
            self.logger.warning("Limit too large, capping at 1000")
            limit = 1000
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM discord_alerts 
                    ORDER BY sent_at DESC 
                    LIMIT ?
                """, (limit,))
                
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get recent Discord alerts: {e}")
            return []
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        Get Discord alert statistics.
        
        Returns:
            Dictionary with alert statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # FIX 4: Remove unnecessary transaction - context manager handles it
                # Total alerts
                cursor.execute("SELECT COUNT(*) FROM discord_alerts")
                total_alerts = cursor.fetchone()[0]
                
                # Successful alerts
                cursor.execute("SELECT COUNT(*) FROM discord_alerts WHERE success = 1")
                successful_alerts = cursor.fetchone()[0]
                
                # Failed alerts
                cursor.execute("SELECT COUNT(*) FROM discord_alerts WHERE success = 0")
                failed_alerts = cursor.fetchone()[0]
                
                # Alerts by symbol
                cursor.execute("""
                    SELECT symbol, COUNT(*) as count 
                    FROM discord_alerts 
                    GROUP BY symbol 
                    ORDER BY count DESC
                """)
                alerts_by_symbol = dict(cursor.fetchall())
                
                # Alerts by signal type
                cursor.execute("""
                    SELECT signal_type, COUNT(*) as count 
                    FROM discord_alerts 
                    GROUP BY signal_type 
                    ORDER BY count DESC
                """)
                alerts_by_signal_type = dict(cursor.fetchall())
                
                # Recent activity (last 24 hours)
                cursor.execute("""
                    SELECT COUNT(*) FROM discord_alerts 
                    WHERE sent_at >= datetime('now', '-1 day')
                """)
                recent_alerts = cursor.fetchone()[0]
                
                return {
                    'total_alerts': total_alerts,
                    'successful_alerts': successful_alerts,
                    'failed_alerts': failed_alerts,
                    'success_rate': (successful_alerts / total_alerts * 100) if total_alerts > 0 else 0,
                    'alerts_by_symbol': alerts_by_symbol,
                    'alerts_by_signal_type': alerts_by_signal_type,
                    'recent_alerts_24h': recent_alerts
                }
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get Discord alert statistics: {e}")
            # FIX 12: Return more informative error response
            return {
                'error': f"Database error: {str(e)}",
                'total_alerts': 0,
                'successful_alerts': 0,
                'failed_alerts': 0,
                'success_rate': 0,
                'alerts_by_symbol': {},
                'alerts_by_signal_type': {},
                'recent_alerts_24h': 0
            }
