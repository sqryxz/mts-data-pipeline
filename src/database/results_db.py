import sqlite3
from typing import List, Dict, Optional
from .backtest_models import BacktestResult, TradeRecord
import json

class ResultsDB:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def save_backtest_run(self, run_name: str, strategy_name: str, start_date: str, end_date: str, initial_capital: float, result: BacktestResult, config_json: Optional[dict] = None, status: str = 'COMPLETED', error_message: Optional[str] = None, completed_at: Optional[str] = None, portfolio_snapshots: Optional[List[Dict]] = None):
        """
        Save a backtest run, its trades, and optional portfolio snapshots to the database.
        Core metrics are stored in backtest_runs only. Robust validation and error handling included.
        """
        if not result:
            raise ValueError("BacktestResult cannot be None")
        if result.total_return is None or result.sharpe_ratio is None or result.max_drawdown is None or result.trade_count is None:
            raise ValueError("BacktestResult missing required core metrics")
        conn = self._connect()
        try:
            cur = conn.cursor()
            # Insert into backtest_runs
            cur.execute(
                """
                INSERT INTO backtest_runs (run_name, strategy_name, start_date, end_date, initial_capital, config_json, status, error_message, completed_at, total_return, sharpe_ratio, max_drawdown, trade_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_name,
                    strategy_name,
                    start_date,
                    end_date,
                    initial_capital,
                    json.dumps(config_json) if config_json else None,
                    status,
                    error_message,
                    completed_at,
                    result.total_return,
                    result.sharpe_ratio,
                    result.max_drawdown,
                    result.trade_count
                )
            )
            backtest_run_id = cur.lastrowid
            if not backtest_run_id:
                raise RuntimeError("Failed to get backtest_run_id after insert")

            # Insert trades with validation
            for i, trade in enumerate(result.trade_history):
                # Validate required fields
                required_fields = ['date', 'symbol', 'action', 'quantity', 'price']
                for field in required_fields:
                    if field not in trade or trade[field] is None:
                        raise ValueError(f"Trade {i} missing required field '{field}': {trade}")
                action = trade['action']
                if not isinstance(action, str) or not action:
                    raise ValueError(f"Trade {i} has invalid 'action': {trade}")
                # Insert trade
                cur.execute(
                    """
                    INSERT INTO trade_executions (backtest_run_id, timestamp, symbol, side, quantity, price, commission, strategy, signal_strength, order_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        backtest_run_id,
                        trade['date'],
                        trade['symbol'],
                        action.upper(),
                        trade['quantity'],
                        trade['price'],
                        trade.get('commission', 0),
                        strategy_name,
                        trade.get('signal_strength'),
                        trade.get('order_id')
                    )
                )

            # Insert portfolio snapshots if provided
            if portfolio_snapshots:
                for i, snap in enumerate(portfolio_snapshots):
                    if not all(k in snap and snap[k] is not None for k in ['timestamp', 'total_value', 'cash_balance']):
                        raise ValueError(f"Portfolio snapshot {i} missing required fields: {snap}")
                    cur.execute(
                        """
                        INSERT INTO portfolio_snapshots (backtest_run_id, timestamp, total_value, cash_balance)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            backtest_run_id,
                            snap['timestamp'],
                            snap['total_value'],
                            snap['cash_balance']
                        )
                    )

            conn.commit()
            return backtest_run_id
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to save backtest run: {e}")
        finally:
            conn.close()

    def load_backtest_run(self, backtest_run_id: int) -> BacktestResult:
        """
        Load a saved backtest run and reconstruct a BacktestResult object.
        Uses explicit column mapping and robust error handling.
        Maps DB 'side' field to 'action' in trade records.
        """
        if not isinstance(backtest_run_id, int) or backtest_run_id <= 0:
            raise ValueError(f"Invalid backtest_run_id: {backtest_run_id}")
        conn = self._connect()
        try:
            cur = conn.cursor()
            # Use static SQL string for safety
            cur.execute(
                """
                SELECT run_name, strategy_name, start_date, end_date, initial_capital,
                       config_json, status, error_message, completed_at, total_return,
                       sharpe_ratio, max_drawdown, trade_count
                FROM backtest_runs WHERE id = ?
                """,
                (backtest_run_id,)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"No backtest run found with id {backtest_run_id}")
            columns = [
                'run_name', 'strategy_name', 'start_date', 'end_date', 'initial_capital',
                'config_json', 'status', 'error_message', 'completed_at', 'total_return',
                'sharpe_ratio', 'max_drawdown', 'trade_count'
            ]
            run_data = dict(zip(columns, row))

            # Strictly validate and type core metrics
            for field in ['total_return', 'sharpe_ratio', 'max_drawdown']:
                val = run_data[field]
                if val is not None:
                    try:
                        run_data[field] = float(val)
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid {field} value in backtest {backtest_run_id}: {val}")
                else:
                    run_data[field] = 0.0
            # Handle trade_count
            if run_data['trade_count'] is not None:
                try:
                    run_data['trade_count'] = int(run_data['trade_count'])
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid trade_count in backtest {backtest_run_id}: {run_data['trade_count']}")
            else:
                run_data['trade_count'] = 0

            # Load trade history with strict validation
            cur.execute(
                """
                SELECT timestamp, symbol, side, quantity, price, commission,
                       strategy, signal_strength, order_id
                FROM trade_executions 
                WHERE backtest_run_id = ? 
                ORDER BY timestamp ASC
                """,
                (backtest_run_id,)
            )
            trades = []
            trade_columns = [
                'timestamp', 'symbol', 'side', 'quantity', 'price', 'commission',
                'strategy', 'signal_strength', 'order_id'
            ]
            for trade_row in cur.fetchall():
                if len(trade_row) != len(trade_columns):
                    raise ValueError(f"Unexpected trade data structure: expected {len(trade_columns)} columns, got {len(trade_row)}")
                trade_dict = dict(zip(trade_columns, trade_row))
                # Map 'side' to 'action' for BacktestResult
                trade_dict['action'] = trade_dict.pop('side')
                # Validate required fields
                if not trade_dict.get('symbol') or not trade_dict.get('action'):
                    raise ValueError(f"Missing required fields in trade: {trade_dict}")
                # Strictly type numeric fields
                numeric_fields = ['quantity', 'price', 'commission', 'signal_strength']
                for field in numeric_fields:
                    if trade_dict[field] is not None:
                        try:
                            trade_dict[field] = float(trade_dict[field])
                        except (ValueError, TypeError):
                            raise ValueError(f"Invalid {field} in trade {trade_dict.get('order_id', 'unknown')}: {trade_dict[field]}")
                    else:
                        trade_dict[field] = 0.0 if field == 'commission' else None
                trades.append(trade_dict)

            # Load portfolio values with strict validation
            cur.execute(
                """
                SELECT total_value 
                FROM portfolio_snapshots 
                WHERE backtest_run_id = ? 
                ORDER BY timestamp ASC
                """,
                (backtest_run_id,)
            )
            portfolio_values = []
            for snap_row in cur.fetchall():
                if snap_row[0] is not None:
                    try:
                        portfolio_values.append(float(snap_row[0]))
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid portfolio value in backtest {backtest_run_id}: {snap_row[0]}")

            # Reconstruct BacktestResult
            result = BacktestResult(
                total_return=run_data['total_return'],
                sharpe_ratio=run_data['sharpe_ratio'],
                max_drawdown=run_data['max_drawdown'],
                trade_count=run_data['trade_count'],
                portfolio_values=portfolio_values,
                trade_history=trades
            )
            return result
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error loading backtest {backtest_run_id}: {e}")
        except ValueError as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Unexpected error loading backtest {backtest_run_id}: {e}")
        finally:
            conn.close()

    def list_backtest_runs(self) -> List[Dict]:
        """
        List all backtest runs with summary info. Uses explicit column mapping and error handling.
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, run_name, strategy_name, start_date, end_date, status,
                       created_at, completed_at, total_return, sharpe_ratio, max_drawdown, trade_count
                FROM backtest_runs ORDER BY created_at DESC
                """
            )
            columns = [
                'id', 'run_name', 'strategy_name', 'start_date', 'end_date', 'status',
                'created_at', 'completed_at', 'total_return', 'sharpe_ratio', 'max_drawdown', 'trade_count'
            ]
            runs = []
            for row in cur.fetchall():
                if len(row) != len(columns):
                    continue  # Skip malformed rows
                run_dict = dict(zip(columns, row))
                # Strictly type numeric fields
                for field in ['total_return', 'sharpe_ratio', 'max_drawdown']:
                    if run_dict[field] is not None:
                        try:
                            run_dict[field] = float(run_dict[field])
                        except (ValueError, TypeError):
                            raise ValueError(f"Invalid {field} in run {run_dict['id']}: {run_dict[field]}")
                    else:
                        run_dict[field] = 0.0
                if run_dict['trade_count'] is not None:
                    try:
                        run_dict['trade_count'] = int(run_dict['trade_count'])
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid trade_count in run {run_dict['id']}: {run_dict['trade_count']}")
                else:
                    run_dict['trade_count'] = 0
                runs.append(run_dict)
            return runs
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error listing backtest runs: {e}")
        finally:
            conn.close() 