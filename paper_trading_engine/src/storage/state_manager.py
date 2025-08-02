"""
State management for persistent JSON storage
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from config.settings import Config
from src.core.models import Position, Trade
from src.core.enums import OrderSide
from src.utils.logger import get_logger

logger = get_logger('storage')


class StateManager:
    """Handles saving and loading portfolio state and trade history to/from JSON files"""
    
    def __init__(self, config: Config):
        self.config = config
        self.portfolio_file = Path(config.PORTFOLIO_STATE_FILE)
        self.trade_history_file = Path(config.TRADE_HISTORY_FILE)
        
        # Ensure data directory exists
        self.portfolio_file.parent.mkdir(parents=True, exist_ok=True)
        self.trade_history_file.parent.mkdir(parents=True, exist_ok=True)
    
    def save_portfolio_state(self, state: Dict[str, Any]) -> bool:
        """
        Save portfolio state to JSON file
        
        Args:
            state: Portfolio state dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert datetime objects to ISO format strings
            serializable_state = self._make_json_serializable(state)
            
            # Write to temporary file first, then rename for atomic operation
            temp_file = self.portfolio_file.with_suffix('.tmp')
            
            with open(temp_file, 'w') as f:
                json.dump(serializable_state, f, indent=2, default=str)
            
            # Atomic rename
            temp_file.rename(self.portfolio_file)
            
            logger.info(f"Portfolio state saved to {self.portfolio_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save portfolio state: {e}")
            return False
    
    def load_portfolio_state(self) -> Optional[Dict[str, Any]]:
        """
        Load portfolio state from JSON file
        
        Returns:
            Portfolio state dictionary or None if not found/error
        """
        try:
            if not self.portfolio_file.exists():
                logger.info("No existing portfolio state file found")
                return None
            
            with open(self.portfolio_file, 'r') as f:
                state = json.load(f)
            
            # Convert ISO format strings back to datetime objects
            restored_state = self._restore_from_json(state)
            
            logger.info(f"Portfolio state loaded from {self.portfolio_file}")
            return restored_state
            
        except Exception as e:
            logger.error(f"Failed to load portfolio state: {e}")
            return None
    
    def save_trade_history(self, trades: List[Trade]) -> bool:
        """
        Save trade history to JSON file
        
        Args:
            trades: List of Trade objects
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert trades to serializable format
            trade_data = []
            for trade in trades:
                trade_dict = {
                    'id': trade.id,
                    'asset': trade.asset,
                    'side': trade.side.value,
                    'quantity': trade.quantity,
                    'entry_price': trade.entry_price,
                    'exit_price': trade.exit_price,
                    'pnl': trade.pnl,
                    'fees': trade.fees,
                    'timestamp': trade.timestamp.isoformat(),
                    'signal_id': trade.signal_id,
                    'order_id': trade.order_id,
                    'execution_id': trade.execution_id
                }
                trade_data.append(trade_dict)
            
            # Write to temporary file first, then rename for atomic operation
            temp_file = self.trade_history_file.with_suffix('.tmp')
            
            with open(temp_file, 'w') as f:
                json.dump(trade_data, f, indent=2)
            
            # Atomic rename
            temp_file.rename(self.trade_history_file)
            
            logger.info(f"Trade history saved: {len(trades)} trades to {self.trade_history_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save trade history: {e}")
            return False
    
    def load_trade_history(self) -> List[Trade]:
        """
        Load trade history from JSON file
        
        Returns:
            List of Trade objects (empty list if not found/error)
        """
        try:
            if not self.trade_history_file.exists():
                logger.info("No existing trade history file found")
                return []
            
            with open(self.trade_history_file, 'r') as f:
                trade_data = json.load(f)
            
            # Convert back to Trade objects
            trades = []
            for data in trade_data:
                trade = Trade(
                    id=data['id'],
                    asset=data['asset'],
                    side=OrderSide(data['side']),
                    quantity=data['quantity'],
                    entry_price=data['entry_price'],
                    exit_price=data.get('exit_price'),
                    pnl=data['pnl'],
                    fees=data['fees'],
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    signal_id=data['signal_id'],
                    order_id=data['order_id'],
                    execution_id=data['execution_id']
                )
                trades.append(trade)
            
            logger.info(f"Trade history loaded: {len(trades)} trades from {self.trade_history_file}")
            return trades
            
        except Exception as e:
            logger.error(f"Failed to load trade history: {e}")
            return []
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Handle dataclass objects
            return self._make_json_serializable(obj.__dict__)
        else:
            return obj
    
    def _restore_from_json(self, obj: Any) -> Any:
        """Restore objects from JSON format"""
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key == 'timestamp' and isinstance(value, str):
                    try:
                        result[key] = datetime.fromisoformat(value)
                    except ValueError:
                        result[key] = value
                elif key == 'last_update' and isinstance(value, str):
                    try:
                        result[key] = datetime.fromisoformat(value)
                    except ValueError:
                        result[key] = value
                else:
                    result[key] = self._restore_from_json(value)
            return result
        elif isinstance(obj, list):
            return [self._restore_from_json(item) for item in obj]
        else:
            return obj
    
    def backup_state(self, suffix: str = None) -> bool:
        """
        Create backup copies of state files
        
        Args:
            suffix: Optional suffix for backup files
            
        Returns:
            True if successful, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_suffix = suffix or timestamp
            
            # Backup portfolio state
            if self.portfolio_file.exists():
                backup_file = self.portfolio_file.with_suffix(f'.{backup_suffix}.bak')
                backup_file.write_bytes(self.portfolio_file.read_bytes())
                logger.info(f"Portfolio state backed up to {backup_file}")
            
            # Backup trade history
            if self.trade_history_file.exists():
                backup_file = self.trade_history_file.with_suffix(f'.{backup_suffix}.bak')
                backup_file.write_bytes(self.trade_history_file.read_bytes())
                logger.info(f"Trade history backed up to {backup_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup state: {e}")
            return False