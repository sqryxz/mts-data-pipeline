"""
State manager for correlation analysis module.
Handles saving and loading correlation state to/from JSON files.
"""

import json
import logging
import os
import shutil
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

import numpy as np


class CorrelationStateManager:
    """
    Manages correlation analysis state persistence.
    """
    
    def __init__(self, state_directory: str = "data/correlation/state", config: Optional[Dict] = None):
        """
        Initialize the correlation state manager.
        
        Args:
            state_directory: Directory to store state files
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.state_directory = Path(state_directory)
        self.state_file = self.state_directory / "correlation_state.json"
        
        # Configuration with defaults
        self.config = {
            'max_correlation_history': 1000,
            'max_breakout_history': 500,
            'backup_count': 3,
            'compression_enabled': False,
            'encryption_enabled': False,
            'validate_schema': True,
            'enable_file_locking': True
        }
        if config:
            self.config.update(config)
        
        # Ensure state directory exists
        self.state_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"State manager initialized with directory: {self.state_directory}")
    
    def save_correlation_state(self, state: Dict[str, Any]) -> bool:
        """
        Save correlation state to JSON file with backup and validation.
        
        Args:
            state: Correlation state dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate state schema
            if self.config.get('validate_schema', True):
                if not self._validate_state_schema(state):
                    self.logger.error("Invalid state schema")
                    return False
            
            # Create backup before writing
            if self.state_file.exists():
                self._create_backup()
            
            # Add metadata to state
            state_with_metadata = {
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'version': '1.0',
                    'state_manager': 'CorrelationStateManager'
                },
                'state': self._make_json_serializable(state)
            }
            
            # Write to temporary file first for atomic operation
            temp_file = self.state_file.with_suffix('.tmp')
            
            # Use file locking if enabled
            if self.config.get('enable_file_locking', True):
                with open(temp_file, 'w') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
                    json.dump(state_with_metadata, f, indent=2, default=str)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
            else:
                with open(temp_file, 'w') as f:
                    json.dump(state_with_metadata, f, indent=2, default=str)
            
            # Atomic rename
            temp_file.rename(self.state_file)
            
            # Rotate backups
            self._rotate_backups()
            
            self.logger.info(f"Correlation state saved to {self.state_file}")
            return True
            
        except PermissionError as e:
            self.logger.error(f"Permission denied writing state: {e}")
            return self._try_alternative_location(state)
        except OSError as e:
            self.logger.error(f"Disk full or I/O error: {e}")
            return self._cleanup_and_retry(state)
        except json.JSONEncodeError as e:
            self.logger.error(f"JSON serialization failed: {e}")
            return self._validate_and_fix_data(state)
        except Exception as e:
            self.logger.error(f"Failed to save correlation state: {e}")
            return False
    
    def load_correlation_state(self) -> Dict[str, Any]:
        """
        Load correlation state from JSON file with error recovery.
        
        Returns:
            Dict[str, Any]: Loaded correlation state
        """
        try:
            if not self.state_file.exists():
                self.logger.info(f"State file not found: {self.state_file}, returning empty state")
                return self._get_default_state()
            
            # Try to load from main file
            try:
                with open(self.state_file, 'r') as f:
                    if self.config.get('enable_file_locking', True):
                        fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock
                    
                    state_data = json.load(f)
                    
                    if self.config.get('enable_file_locking', True):
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
                
            except (json.JSONDecodeError, FileNotFoundError) as e:
                self.logger.warning(f"Failed to load from main file: {e}, trying backup")
                return self._load_from_backup()
            
            # Extract state from metadata wrapper
            if 'state' in state_data:
                state = state_data['state']
            else:
                # Handle legacy format (no metadata wrapper)
                state = state_data
            
            # Validate loaded state
            if self.config.get('validate_schema', True):
                if not self._validate_state_schema(state):
                    self.logger.warning("Loaded state has invalid schema, trying backup")
                    return self._load_from_backup()
            
            # Restore objects from JSON format
            restored_state = self._restore_from_json(state)
            
            self.logger.info(f"Correlation state loaded from {self.state_file}")
            return restored_state
            
        except Exception as e:
            self.logger.error(f"Failed to load correlation state: {e}")
            return self._get_default_state()
    
    def save_pair_state(self, pair: str, pair_state: Dict[str, Any]) -> bool:
        """
        Save state for a specific pair with optimized partial update.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            pair_state: State data for the pair
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load current state
            current_state = self.load_correlation_state()
            
            # Update pair state
            current_state['pairs'] = current_state.get('pairs', {})
            current_state['pairs'][pair] = self._make_json_serializable(pair_state)
            
            # Save updated state
            return self.save_correlation_state(current_state)
            
        except Exception as e:
            self.logger.error(f"Failed to save pair state for {pair}: {e}")
            return False
    
    def load_pair_state(self, pair: str) -> Dict[str, Any]:
        """
        Load state for a specific pair.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            
        Returns:
            Dict[str, Any]: Pair state data
        """
        try:
            state = self.load_correlation_state()
            pairs = state.get('pairs', {})
            return pairs.get(pair, {})
            
        except Exception as e:
            self.logger.error(f"Failed to load pair state for {pair}: {e}")
            return {}
    
    def save_correlation_history(self, pair: str, correlation_data: Dict[str, Any]) -> bool:
        """
        Save correlation history for a pair with configurable limits.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            correlation_data: Correlation data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load current state
            current_state = self.load_correlation_state()
            
            # Initialize correlation history if not exists
            if 'correlation_history' not in current_state:
                current_state['correlation_history'] = {}
            
            if pair not in current_state['correlation_history']:
                current_state['correlation_history'][pair] = []
            
            # Add timestamp if not present
            if 'timestamp' not in correlation_data:
                correlation_data['timestamp'] = int(datetime.now().timestamp() * 1000)
            
            # Add to history
            current_state['correlation_history'][pair].append(correlation_data)
            
            # Keep only last N entries (configurable)
            max_history = self.config.get('max_correlation_history', 1000)
            if len(current_state['correlation_history'][pair]) > max_history:
                current_state['correlation_history'][pair] = current_state['correlation_history'][pair][-max_history:]
            
            # Save updated state
            return self.save_correlation_state(current_state)
            
        except Exception as e:
            self.logger.error(f"Failed to save correlation history for {pair}: {e}")
            return False
    
    def load_correlation_history(self, pair: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Load correlation history for a pair.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            limit: Maximum number of entries to return
            
        Returns:
            List[Dict[str, Any]]: Correlation history
        """
        try:
            state = self.load_correlation_state()
            history = state.get('correlation_history', {}).get(pair, [])
            
            # Return last N entries
            return history[-limit:] if limit > 0 else history
            
        except Exception as e:
            self.logger.error(f"Failed to load correlation history for {pair}: {e}")
            return []
    
    def save_breakout_history(self, pair: str, breakout_data: Dict[str, Any]) -> bool:
        """
        Save breakout history for a pair with configurable limits.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            breakout_data: Breakout data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load current state
            current_state = self.load_correlation_state()
            
            # Initialize breakout history if not exists
            if 'breakout_history' not in current_state:
                current_state['breakout_history'] = {}
            
            if pair not in current_state['breakout_history']:
                current_state['breakout_history'][pair] = []
            
            # Add timestamp if not present
            if 'timestamp' not in breakout_data:
                breakout_data['timestamp'] = int(datetime.now().timestamp() * 1000)
            
            # Add to history
            current_state['breakout_history'][pair].append(breakout_data)
            
            # Keep only last N entries (configurable)
            max_history = self.config.get('max_breakout_history', 500)
            if len(current_state['breakout_history'][pair]) > max_history:
                current_state['breakout_history'][pair] = current_state['breakout_history'][pair][-max_history:]
            
            # Save updated state
            return self.save_correlation_state(current_state)
            
        except Exception as e:
            self.logger.error(f"Failed to save breakout history for {pair}: {e}")
            return False
    
    def load_breakout_history(self, pair: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Load breakout history for a pair.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            limit: Maximum number of entries to return
            
        Returns:
            List[Dict[str, Any]]: Breakout history
        """
        try:
            state = self.load_correlation_state()
            history = state.get('breakout_history', {}).get(pair, [])
            
            # Return last N entries
            return history[-limit:] if limit > 0 else history
            
        except Exception as e:
            self.logger.error(f"Failed to load breakout history for {pair}: {e}")
            return []
    
    def clear_state(self) -> bool:
        """
        Clear all correlation state.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.state_file.exists():
                self.state_file.unlink()
                self.logger.info(f"Correlation state cleared: {self.state_file}")
            
            # Clear backups
            self._clear_backups()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear correlation state: {e}")
            return False
    
    def get_state_info(self) -> Dict[str, Any]:
        """
        Get information about the current state.
        
        Returns:
            Dict[str, Any]: State information
        """
        try:
            if not self.state_file.exists():
                return {
                    'exists': False,
                    'file_size': 0,
                    'last_modified': None,
                    'pairs_count': 0,
                    'correlation_history_count': 0,
                    'breakout_history_count': 0,
                    'backup_count': 0
                }
            
            # Get file info
            stat = self.state_file.stat()
            
            # Load state for counts
            state = self.load_correlation_state()
            
            pairs_count = len(state.get('pairs', {}))
            correlation_history_count = sum(len(history) for history in state.get('correlation_history', {}).values())
            breakout_history_count = sum(len(history) for history in state.get('breakout_history', {}).values())
            
            # Count backups
            backup_count = len(list(self.state_directory.glob("*.backup")))
            
            return {
                'exists': True,
                'file_size': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'pairs_count': pairs_count,
                'correlation_history_count': correlation_history_count,
                'breakout_history_count': breakout_history_count,
                'backup_count': backup_count
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get state info: {e}")
            return {'exists': False, 'error': str(e)}
    
    def _validate_state_schema(self, state: Dict[str, Any]) -> bool:
        """
        Validate state schema.
        
        Args:
            state: State dictionary to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            required_fields = ['pairs', 'correlation_history', 'breakout_history']
            for field in required_fields:
                if field not in state:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate pairs structure
            if not isinstance(state.get('pairs', {}), dict):
                self.logger.error("Pairs must be a dictionary")
                return False
            
            # Validate correlation_history structure
            if not isinstance(state.get('correlation_history', {}), dict):
                self.logger.error("Correlation history must be a dictionary")
                return False
            
            # Validate breakout_history structure
            if not isinstance(state.get('breakout_history', {}), dict):
                self.logger.error("Breakout history must be a dictionary")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Schema validation failed: {e}")
            return False
    
    def _create_backup(self) -> bool:
        """
        Create backup of current state file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.state_file.exists():
                return True
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.state_directory / f"correlation_state_{timestamp}.backup"
            
            shutil.copy2(self.state_file, backup_file)
            self.logger.debug(f"Backup created: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
    
    def _rotate_backups(self) -> None:
        """
        Rotate backups to keep only the most recent ones.
        """
        try:
            backup_files = sorted(self.state_directory.glob("*.backup"), key=lambda x: x.stat().st_mtime)
            max_backups = self.config.get('backup_count', 3)
            
            # Remove old backups
            while len(backup_files) > max_backups:
                old_backup = backup_files.pop(0)
                old_backup.unlink()
                self.logger.debug(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            self.logger.error(f"Failed to rotate backups: {e}")
    
    def _clear_backups(self) -> None:
        """
        Clear all backup files.
        """
        try:
            for backup_file in self.state_directory.glob("*.backup"):
                backup_file.unlink()
                self.logger.debug(f"Removed backup: {backup_file}")
        except Exception as e:
            self.logger.error(f"Failed to clear backups: {e}")
    
    def _load_from_backup(self) -> Dict[str, Any]:
        """
        Load state from backup file.
        
        Returns:
            Dict[str, Any]: State from backup or default state
        """
        try:
            backup_files = sorted(self.state_directory.glob("*.backup"), key=lambda x: x.stat().st_mtime, reverse=True)
            
            for backup_file in backup_files:
                try:
                    with open(backup_file, 'r') as f:
                        state_data = json.load(f)
                    
                    # Extract state from metadata wrapper
                    if 'state' in state_data:
                        state = state_data['state']
                    else:
                        state = state_data
                    
                    # Validate loaded state
                    if self.config.get('validate_schema', True):
                        if not self._validate_state_schema(state):
                            continue
                    
                    restored_state = self._restore_from_json(state)
                    self.logger.info(f"State loaded from backup: {backup_file}")
                    return restored_state
                    
                except Exception as e:
                    self.logger.warning(f"Failed to load from backup {backup_file}: {e}")
                    continue
            
            self.logger.warning("No valid backup found, returning default state")
            return self._get_default_state()
            
        except Exception as e:
            self.logger.error(f"Failed to load from backup: {e}")
            return self._get_default_state()
    
    def _try_alternative_location(self, state: Dict[str, Any]) -> bool:
        """
        Try to save state to alternative location.
        
        Args:
            state: State to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Try to save to a different directory
            alt_directory = Path("/tmp/correlation_state")
            alt_directory.mkdir(parents=True, exist_ok=True)
            alt_file = alt_directory / "correlation_state.json"
            
            state_with_metadata = {
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'version': '1.0',
                    'state_manager': 'CorrelationStateManager',
                    'location': 'alternative'
                },
                'state': self._make_json_serializable(state)
            }
            
            with open(alt_file, 'w') as f:
                json.dump(state_with_metadata, f, indent=2, default=str)
            
            self.logger.info(f"State saved to alternative location: {alt_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save to alternative location: {e}")
            return False
    
    def _cleanup_and_retry(self, state: Dict[str, Any]) -> bool:
        """
        Clean up disk space and retry saving.
        
        Args:
            state: State to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Clear old backups to free space
            self._clear_backups()
            
            # Try saving again
            return self.save_correlation_state(state)
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup and retry: {e}")
            return False
    
    def _validate_and_fix_data(self, state: Dict[str, Any]) -> bool:
        """
        Validate and fix data before saving.
        
        Args:
            state: State to validate and fix
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Remove any non-serializable objects
            cleaned_state = self._clean_state_data(state)
            
            # Try saving cleaned state
            return self.save_correlation_state(cleaned_state)
            
        except Exception as e:
            self.logger.error(f"Failed to validate and fix data: {e}")
            return False
    
    def _clean_state_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean state data by removing non-serializable objects.
        
        Args:
            state: State to clean
            
        Returns:
            Dict[str, Any]: Cleaned state
        """
        try:
            return self._make_json_serializable(state)
        except Exception as e:
            self.logger.error(f"Failed to clean state data: {e}")
            return self._get_default_state()
    
    def _get_default_state(self) -> Dict[str, Any]:
        """
        Get default state structure.
        
        Returns:
            Dict[str, Any]: Default state
        """
        return {
            'pairs': {},
            'correlation_history': {},
            'breakout_history': {},
            'settings': {
                'last_analysis_time': None,
                'total_pairs_analyzed': 0,
                'total_breakouts_detected': 0
            }
        }
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """
        Convert objects to JSON-serializable format.
        
        Args:
            obj: Object to convert
            
        Returns:
            Any: JSON-serializable object
        """
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            # Handle dataclass objects
            return self._make_json_serializable(obj.__dict__)
        else:
            return obj
    
    def _restore_from_json(self, obj: Any) -> Any:
        """
        Restore objects from JSON format with validation.
        
        Args:
            obj: JSON object to restore
            
        Returns:
            Any: Restored object
        """
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key == 'timestamp' and isinstance(value, str):
                    try:
                        result[key] = datetime.fromisoformat(value)
                    except ValueError:
                        result[key] = value
                elif key == 'last_updated' and isinstance(value, str):
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
