#!/usr/bin/env python3
"""
Command-line interface for testing risk assessments.
"""

import sys
import os
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.risk_management.core.risk_orchestrator import RiskOrchestrator
from src.risk_management.models.risk_models import (
    TradingSignal, PortfolioState, SignalType, RiskLevel
)
from src.risk_management.utils.error_handler import ErrorType, ErrorSeverity


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def create_signal_from_args(args: argparse.Namespace) -> TradingSignal:
    """Create a trading signal from command line arguments."""
    try:
        # Validate signal type
        signal_type = SignalType(args.signal.upper())
        
        # Validate price
        if args.price <= 0:
            raise ValueError("Price must be positive")
        
        # Validate confidence
        if not 0 <= args.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        
        return TradingSignal(
            signal_id=f"cli-{args.asset.lower()}-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            asset=args.asset.upper(),
            signal_type=signal_type,
            price=float(args.price),
            confidence=float(args.confidence),
            timestamp=datetime.now()
        )
    except Exception as e:
        logging.error(f"Error creating signal: {e}")
        raise


def create_portfolio_from_args(args: argparse.Namespace) -> PortfolioState:
    """Create a portfolio state from command line arguments."""
    try:
        # Validate equity
        if args.equity <= 0:
            raise ValueError("Equity must be positive")
        
        # Validate drawdown
        if not 0 <= args.drawdown <= 1:
            raise ValueError("Drawdown must be between 0 and 1")
        
        return PortfolioState(
            total_equity=float(args.equity),
            current_drawdown=float(args.drawdown),
            daily_pnl=float(args.daily_pnl),
            positions={},
            cash=float(args.equity) * 0.2  # Assume 20% cash
        )
    except Exception as e:
        logging.error(f"Error creating portfolio: {e}")
        raise


def format_assessment_output(assessment: Any, output_format: str, pretty: bool = False) -> str:
    """Format assessment output based on specified format."""
    if output_format == 'json':
        if hasattr(assessment, 'to_dict'):
            data = assessment.to_dict()
        else:
            data = assessment.__dict__
        
        if pretty:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)
    
    elif output_format == 'summary':
        return f"""
Risk Assessment Summary:
======================
Signal: {assessment.asset} {assessment.signal_type.value} @ ${assessment.signal_price:,.2f}
Confidence: {assessment.signal_confidence:.1%}
Approved: {'✅ YES' if assessment.is_approved else '❌ NO'}
Risk Level: {assessment.risk_level.value if assessment.risk_level else 'UNKNOWN'}

Position Details:
----------------
Recommended Size: ${assessment.recommended_position_size:,.2f}
Position Risk: {assessment.position_risk_percent:.2%}
Stop Loss: ${assessment.stop_loss_price:,.2f}
Take Profit: ${assessment.take_profit_price:,.2f}
Risk/Reward Ratio: {assessment.risk_reward_ratio:.2f}

Risk Information:
----------------
Rejection Reason: {assessment.rejection_reason or 'N/A'}
Risk Warnings: {', '.join(assessment.risk_warnings) if assessment.risk_warnings else 'None'}
Processing Time: {assessment.processing_time_ms:.2f}ms
"""
    
    elif output_format == 'minimal':
        return f"{assessment.asset},{assessment.signal_type.value},{assessment.signal_price},{assessment.is_approved},{assessment.risk_level.value if assessment.risk_level else 'UNKNOWN'},{assessment.recommended_position_size:.2f},{assessment.stop_loss_price:.2f}"
    
    else:
        raise ValueError(f"Unknown output format: {output_format}")


def run_assessment(args: argparse.Namespace) -> None:
    """Run risk assessment with given arguments."""
    try:
        # Setup logging
        setup_logging(args.verbose)
        logger = logging.getLogger(__name__)
        
        logger.info("Initializing risk management orchestrator...")
        orchestrator = RiskOrchestrator()
        
        # Create signal and portfolio
        logger.info("Creating trading signal...")
        signal = create_signal_from_args(args)
        
        logger.info("Creating portfolio state...")
        portfolio = create_portfolio_from_args(args)
        
        # Log input parameters
        logger.info(f"Signal: {signal.asset} {signal.signal_type.value} @ ${signal.price:,.2f}")
        logger.info(f"Portfolio Equity: ${portfolio.total_equity:,.2f}")
        logger.info(f"Current Drawdown: {portfolio.current_drawdown:.1%}")
        
        # Perform risk assessment
        logger.info("Performing risk assessment...")
        assessment = orchestrator.assess_trade_risk(signal, portfolio)
        
        # Format and output result
        output = format_assessment_output(assessment, args.output, args.pretty)
        print(output)
        
        # Exit with appropriate code
        if assessment.is_approved:
            logger.info("Assessment completed successfully - trade approved")
            sys.exit(0)
        else:
            logger.warning("Assessment completed - trade rejected")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Error during assessment: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)


def run_batch_assessment(args: argparse.Namespace) -> None:
    """Run batch assessment from file."""
    try:
        # Setup logging
        setup_logging(args.verbose)
        logger = logging.getLogger(__name__)
        
        logger.info("Initializing risk management orchestrator...")
        orchestrator = RiskOrchestrator()
        
        # Read input file
        logger.info(f"Reading input file: {args.input_file}")
        with open(args.input_file, 'r') as f:
            if args.input_file.endswith('.json'):
                data = json.load(f)
            else:
                # Assume CSV format
                import csv
                reader = csv.DictReader(f)
                data = list(reader)
        
        results = []
        
        for i, item in enumerate(data):
            try:
                # Create signal and portfolio from data
                if isinstance(item, dict):
                    signal = TradingSignal(
                        signal_id=item.get('signal_id', f"batch-{i}"),
                        asset=item['asset'].upper(),
                        signal_type=SignalType(item['signal_type'].upper()),
                        price=float(item['price']),
                        confidence=float(item['confidence']),
                        timestamp=datetime.now()
                    )
                    
                    portfolio = PortfolioState(
                        total_equity=float(item['equity']),
                        current_drawdown=float(item.get('drawdown', 0.0)),
                        daily_pnl=float(item.get('daily_pnl', 0.0)),
                        positions={},
                        cash=float(item['equity']) * 0.2
                    )
                    
                    # Perform assessment
                    assessment = orchestrator.assess_trade_risk(signal, portfolio)
                    results.append(assessment)
                    
                    logger.info(f"Processed {i+1}/{len(data)}: {signal.asset} {signal.signal_type.value}")
                    
            except Exception as e:
                logger.error(f"Error processing item {i+1}: {e}")
                continue
        
        # Output results
        if args.output == 'json':
            output_data = []
            for assessment in results:
                if hasattr(assessment, 'to_dict'):
                    output_data.append(assessment.to_dict())
                else:
                    output_data.append(assessment.__dict__)
            
            if args.pretty:
                print(json.dumps(output_data, indent=2, default=str))
            else:
                print(json.dumps(output_data, default=str))
        
        else:
            for assessment in results:
                print(format_assessment_output(assessment, args.output, args.pretty))
        
        logger.info(f"Batch assessment completed: {len(results)}/{len(data)} successful")
        
    except Exception as e:
        logging.error(f"Error during batch assessment: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)


def create_sample_input_file(filename: str) -> None:
    """Create a sample input file for batch processing."""
    sample_data = [
        {
            "signal_id": "sample-1",
            "asset": "BTC",
            "signal_type": "LONG",
            "price": 50000.0,
            "confidence": 0.8,
            "equity": 100000.0,
            "drawdown": 0.05,
            "daily_pnl": 500.0
        },
        {
            "signal_id": "sample-2",
            "asset": "ETH",
            "signal_type": "SHORT",
            "price": 3000.0,
            "confidence": 0.7,
            "equity": 50000.0,
            "drawdown": 0.15,
            "daily_pnl": -1000.0
        },
        {
            "signal_id": "sample-3",
            "asset": "BTC",
            "signal_type": "LONG",
            "price": 52000.0,
            "confidence": 0.9,
            "equity": 200000.0,
            "drawdown": 0.02,
            "daily_pnl": 2000.0
        }
    ]
    
    with open(filename, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"Sample input file created: {filename}")
    print("You can modify this file and use it with --batch mode")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Risk Management CLI - Test risk assessments from command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single assessment
  python cli.py --asset BTC --signal LONG --price 50000 --confidence 0.8 --equity 100000

  # Batch assessment from JSON file
  python cli.py --batch --input-file signals.json --output json --pretty

  # Create sample input file
  python cli.py --create-sample sample_signals.json

  # CSV output format
  python cli.py --asset ETH --signal SHORT --price 3000 --confidence 0.7 --equity 50000 --output minimal
        """
    )
    
    # Create subparsers for different modes
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single assessment parser
    single_parser = subparsers.add_parser('assess', help='Run single risk assessment')
    single_parser.add_argument('--asset', required=True, help='Asset symbol (e.g., BTC, ETH)')
    single_parser.add_argument('--signal', required=True, choices=['LONG', 'SHORT'], help='Signal type')
    single_parser.add_argument('--price', required=True, type=float, help='Asset price')
    single_parser.add_argument('--confidence', required=True, type=float, help='Signal confidence (0-1)')
    single_parser.add_argument('--equity', required=True, type=float, help='Portfolio equity')
    single_parser.add_argument('--drawdown', type=float, default=0.05, help='Current drawdown (0-1, default: 0.05)')
    single_parser.add_argument('--daily-pnl', type=float, default=0.0, help='Daily P&L (default: 0.0)')
    single_parser.add_argument('--output', choices=['json', 'summary', 'minimal'], default='summary', help='Output format')
    single_parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    single_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    # Batch assessment parser
    batch_parser = subparsers.add_parser('batch', help='Run batch risk assessment')
    batch_parser.add_argument('--input-file', required=True, help='Input file (JSON or CSV)')
    batch_parser.add_argument('--output', choices=['json', 'summary', 'minimal'], default='json', help='Output format')
    batch_parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    batch_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    # Create sample parser
    sample_parser = subparsers.add_parser('create-sample', help='Create sample input file')
    sample_parser.add_argument('filename', help='Output filename')
    
    # Legacy support for direct arguments
    parser.add_argument('--asset', help='Asset symbol (e.g., BTC, ETH)')
    parser.add_argument('--signal', choices=['LONG', 'SHORT'], help='Signal type')
    parser.add_argument('--price', type=float, help='Asset price')
    parser.add_argument('--confidence', type=float, help='Signal confidence (0-1)')
    parser.add_argument('--equity', type=float, help='Portfolio equity')
    parser.add_argument('--drawdown', type=float, default=0.05, help='Current drawdown (0-1, default: 0.05)')
    parser.add_argument('--daily-pnl', type=float, default=0.0, help='Daily P&L (default: 0.0)')
    parser.add_argument('--output', choices=['json', 'summary', 'minimal'], default='summary', help='Output format')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    parser.add_argument('--batch', action='store_true', help='Batch mode')
    parser.add_argument('--input-file', help='Input file for batch mode')
    parser.add_argument('--create-sample', help='Create sample input file')
    
    args = parser.parse_args()
    
    # Handle different modes
    if args.command == 'create-sample' or args.create_sample:
        create_sample_input_file(args.filename or args.create_sample)
        return
    
    elif args.command == 'batch' or args.batch:
        run_batch_assessment(args)
        return
    
    elif args.command == 'assess' or (args.asset and args.signal and args.price and args.confidence and args.equity):
        run_assessment(args)
        return
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 