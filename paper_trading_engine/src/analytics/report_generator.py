#!/usr/bin/env python3
"""
JSON Report Generator for Paper Trading Engine
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .performance_calculator import PerformanceCalculator, PerformanceMetrics
from ..core.models import Trade, PortfolioState
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..portfolio.portfolio_manager import PortfolioManager


class ReportGenerator:
    """Generate comprehensive JSON performance reports"""
    
    def __init__(self, output_directory: str = "data/reports", 
                 include_metadata: bool = True,
                 decimal_precision: int = 4):
        """
        Initialize report generator
        
        Args:
            output_directory: Directory to save report files
            include_metadata: Whether to include report metadata
            decimal_precision: Number of decimal places for numeric values
        """
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.performance_calculator = PerformanceCalculator()
        self.include_metadata = include_metadata
        self.decimal_precision = decimal_precision
        self.logger = logging.getLogger(__name__)
    
    def generate_comprehensive_report(self, portfolio_manager: "PortfolioManager", 
                                   report_type: str = "performance_report") -> Dict[str, Any]:
        """
        Generate a comprehensive JSON performance report
        
        Args:
            portfolio_manager: Portfolio manager with trade history
            report_type: Type of report to generate
            
        Returns:
            Dictionary containing complete report data
            
        Raises:
            ValueError: If portfolio_manager is None
        """
        if portfolio_manager is None:
            raise ValueError("Portfolio manager cannot be None")
        
        try:
            # Get current portfolio state
            portfolio_state = portfolio_manager.get_state()
            
            # Calculate performance metrics
            performance_metrics = self.performance_calculator.calculate_metrics(portfolio_manager)
            performance_summary = self.performance_calculator.generate_summary_report(performance_metrics)
            
            # Generate trade history
            trade_history = self._serialize_trade_history(portfolio_manager.trade_history)
            
            # Create comprehensive report
            report = {
                "portfolio_summary": self._serialize_portfolio_summary(portfolio_state),
                "performance_metrics": performance_summary,
                "trade_history": trade_history,
                "risk_analysis": self._generate_risk_analysis(performance_metrics, portfolio_state),
                "trading_activity": self._generate_trading_activity_summary(portfolio_manager.trade_history)
            }
            
            # Add metadata if enabled
            if self.include_metadata:
                report["report_metadata"] = {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": report_type,
                    "period_start": self._get_period_start(portfolio_manager.trade_history),
                    "period_end": datetime.now().isoformat(),
                    "version": "1.0"
                }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            raise
    
    def generate_summary_report(self, portfolio_manager: "PortfolioManager") -> Dict[str, Any]:
        """
        Generate a summary report with key metrics only
        
        Args:
            portfolio_manager: Portfolio manager with trade history
            
        Returns:
            Dictionary containing summary report data
        """
        if portfolio_manager is None:
            raise ValueError("Portfolio manager cannot be None")
        
        try:
            portfolio_state = portfolio_manager.get_state()
            performance_metrics = self.performance_calculator.calculate_metrics(portfolio_manager)
            
            report = {
                "portfolio_summary": {
                    "total_value": portfolio_state.total_value,
                    "initial_capital": portfolio_state.initial_capital,
                    "total_pnl": portfolio_state.total_pnl,
                    "realized_pnl": portfolio_state.realized_pnl,
                    "unrealized_pnl": portfolio_state.unrealized_pnl,
                    "cash": portfolio_state.cash,
                    "position_count": len(portfolio_state.positions),
                    "trade_count": portfolio_state.trade_count,
                    "win_rate": portfolio_state.win_rate
                },
                "key_metrics": {
                    "total_return_percent": performance_metrics.total_return * 100,
                    "sharpe_ratio": performance_metrics.sharpe_ratio,
                    "max_drawdown_percent": performance_metrics.max_drawdown_percent,
                    "profit_factor": performance_metrics.profit_factor,
                    "win_rate_percent": performance_metrics.win_rate * 100
                }
            }
            
            # Add metadata if enabled
            if self.include_metadata:
                report["report_metadata"] = {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": "summary_report",
                    "version": "1.0"
                }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating summary report: {e}")
            raise
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """
        Save report to JSON file
        
        Args:
            report: Report dictionary to save
            filename: Optional filename, will generate timestamped name if not provided
            
        Returns:
            Path to saved report file
            
        Raises:
            ValueError: If report validation fails
        """
        try:
            # Validate report before saving
            if not self._validate_report_data(report):
                raise ValueError("Report validation failed")
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_type = report.get("report_metadata", {}).get("report_type", "report")
                filename = f"{report_type}_{timestamp}.json"
            
            file_path = self.output_directory / filename
            
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Report saved to: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            raise
    
    def generate_and_save_report(self, portfolio_manager: "PortfolioManager", 
                               report_type: str = "performance_report",
                               filename: Optional[str] = None) -> Path:
        """
        Generate and save a comprehensive report
        
        Args:
            portfolio_manager: Portfolio manager with trade history
            report_type: Type of report to generate
            filename: Optional filename for the report
            
        Returns:
            Path to saved report file
        """
        report = self.generate_comprehensive_report(portfolio_manager, report_type)
        return self.save_report(report, filename)
    
    def _serialize_portfolio_summary(self, portfolio_state: PortfolioState) -> Dict[str, Any]:
        """Serialize portfolio state to dictionary"""
        return {
            "current_value": portfolio_state.total_value,
            "initial_capital": portfolio_state.initial_capital,
            "cash": portfolio_state.cash,
            "total_pnl": portfolio_state.total_pnl,
            "realized_pnl": portfolio_state.realized_pnl,
            "unrealized_pnl": portfolio_state.unrealized_pnl,
            "position_count": len(portfolio_state.positions),
            "trade_count": portfolio_state.trade_count,
            "win_count": portfolio_state.win_count,
            "loss_count": portfolio_state.loss_count,
            "win_rate": portfolio_state.win_rate,
            "positions": portfolio_state.positions
        }
    
    def _serialize_trade_history(self, trade_history: List[Trade]) -> List[Dict[str, Any]]:
        """Serialize trade history to list of dictionaries"""
        serialized_trades = []
        
        for trade in trade_history:
            # Use entry_price as the primary price, fallback to exit_price if available
            price = trade.entry_price if trade.entry_price is not None else (trade.exit_price or 0.0)
            
            trade_dict = {
                "timestamp": trade.timestamp.isoformat(),
                "asset": trade.asset,
                "side": trade.side.value,
                "quantity": trade.quantity,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "price": price,  # For backward compatibility
                "pnl": trade.pnl,
                "fees": trade.fees,
                "execution_id": str(trade.execution_id),
                "order_id": str(trade.order_id),
                "signal_id": str(trade.signal_id),
                "trade_id": str(trade.id),
                "metadata": getattr(trade, 'metadata', {})
            }
            serialized_trades.append(trade_dict)
        
        return serialized_trades
    
    def _generate_risk_analysis(self, metrics: PerformanceMetrics, 
                               portfolio_state: PortfolioState) -> Dict[str, Any]:
        """Generate risk analysis section"""
        return {
            "risk_metrics": {
                "sharpe_ratio": metrics.sharpe_ratio,
                "max_drawdown": metrics.max_drawdown,
                "max_drawdown_percent": metrics.max_drawdown_percent,
                "volatility": metrics.volatility
            },
            "position_risk": {
                "largest_position_value": self._calculate_largest_position_value(portfolio_state.positions),
                "cash_ratio": portfolio_state.cash / portfolio_state.total_value if portfolio_state.total_value > 0 else 0.0,
                "position_concentration": self._calculate_position_concentration(portfolio_state.positions)
            },
            "trade_risk": {
                "largest_win": metrics.largest_win,
                "largest_loss": metrics.largest_loss,
                "average_win": metrics.average_win,
                "average_loss": metrics.average_loss,
                "consecutive_wins": metrics.consecutive_wins,
                "consecutive_losses": metrics.consecutive_losses
            }
        }
    
    def _generate_trading_activity_summary(self, trade_history: List[Trade]) -> Dict[str, Any]:
        """Generate trading activity summary"""
        if not trade_history:
            return {
                "total_trades": 0,
                "trading_days": 0,
                "avg_trades_per_day": 0.0,
                "most_traded_asset": None,
                "trading_frequency": "No trades"
            }
        
        # Calculate trading days
        dates = [trade.timestamp.date() for trade in trade_history]
        unique_dates = set(dates)
        trading_days = len(unique_dates)
        
        # Find most traded asset
        asset_counts = {}
        for trade in trade_history:
            asset_counts[trade.asset] = asset_counts.get(trade.asset, 0) + 1
        
        most_traded_asset = max(asset_counts.items(), key=lambda x: x[1])[0] if asset_counts else None
        
        # Calculate trading frequency
        if trading_days > 0:
            avg_trades_per_day = len(trade_history) / trading_days
            if avg_trades_per_day >= 5:
                frequency = "High"
            elif avg_trades_per_day >= 2:
                frequency = "Medium"
            else:
                frequency = "Low"
        else:
            avg_trades_per_day = 0.0
            frequency = "No trades"
        
        return {
            "total_trades": len(trade_history),
            "trading_days": trading_days,
            "avg_trades_per_day": avg_trades_per_day,
            "most_traded_asset": most_traded_asset,
            "trading_frequency": frequency,
            "asset_distribution": asset_counts
        }
    
    def _get_period_start(self, trade_history: List[Trade]) -> str:
        """Get the start date of the trading period"""
        if not trade_history:
            return datetime.now().isoformat()
        
        earliest_trade = min(trade_history, key=lambda t: t.timestamp)
        return earliest_trade.timestamp.isoformat()
    
    def _calculate_largest_position_value(self, positions: Dict[str, Dict]) -> float:
        """Calculate the value of the largest position"""
        if not positions:
            return 0.0
        
        position_values = []
        for asset, pos_data in positions.items():
            try:
                quantity = float(pos_data.get('quantity', 0))
                current_price = float(pos_data.get('current_price', 0))
                position_value = abs(quantity * current_price)
                position_values.append(position_value)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Invalid position data for {asset}: {e}")
                continue
        
        return max(position_values) if position_values else 0.0
    
    def _calculate_position_concentration(self, positions: Dict[str, Dict]) -> Dict[str, float]:
        """Calculate position concentration metrics"""
        if not positions:
            return {}
        
        total_position_value = 0.0
        position_values = {}
        
        for asset, pos_data in positions.items():
            try:
                quantity = float(pos_data.get('quantity', 0))
                current_price = float(pos_data.get('current_price', 0))
                position_value = abs(quantity * current_price)
                position_values[asset] = position_value
                total_position_value += position_value
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Invalid position data for {asset}: {e}")
                continue
        
        if total_position_value == 0:
            return {}
        
        # Calculate concentration percentages
        concentration = {}
        for asset, value in position_values.items():
            concentration[asset] = (value / total_position_value) * 100
        
        return concentration
    
    def _validate_report_data(self, report: Dict[str, Any]) -> bool:
        """Validate report structure and data integrity"""
        try:
            # Check required sections based on report type
            required_sections = ["portfolio_summary"]
            
            # Comprehensive reports should have performance_metrics
            if "performance_metrics" in report:
                required_sections.append("performance_metrics")
            # Summary reports should have key_metrics
            elif "key_metrics" in report:
                required_sections.append("key_metrics")
            
            if self.include_metadata:
                required_sections.append("report_metadata")
            
            if not all(section in report for section in required_sections):
                self.logger.error(f"Missing required report sections. Found: {list(report.keys())}")
                return False
            
            # Validate portfolio summary
            portfolio_summary = report["portfolio_summary"]
            
            # Different report types have different required fields
            if "performance_metrics" in report:
                # Comprehensive report
                required_portfolio_fields = [
                    "current_value", "initial_capital", "total_pnl", 
                    "realized_pnl", "unrealized_pnl", "cash"
                ]
            else:
                # Summary report
                required_portfolio_fields = [
                    "total_value", "initial_capital", "total_pnl", 
                    "realized_pnl", "unrealized_pnl", "cash"
                ]
            
            if not all(field in portfolio_summary for field in required_portfolio_fields):
                self.logger.error(f"Missing required portfolio summary fields. Found: {list(portfolio_summary.keys())}")
                return False
            
            # Validate numeric fields
            for field in required_portfolio_fields:
                if not isinstance(portfolio_summary[field], (int, float)):
                    self.logger.error(f"Invalid data type for portfolio field: {field}")
                    return False
            
            # Validate trade history is a list (if present)
            if "trade_history" in report and not isinstance(report["trade_history"], list):
                self.logger.error("Trade history must be a list")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating report data: {e}")
            return False 