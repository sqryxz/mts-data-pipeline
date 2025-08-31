#!/usr/bin/env python3
"""
Multi-Bucket Portfolio Strategy Backtesting Framework

Comprehensive backtesting of the multi-bucket crypto portfolio strategy
over the past year with detailed performance analysis and risk metrics.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os
import json
from typing import Dict, List, Any, Optional, Tuple

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.signals.strategies.multi_bucket_portfolio_strategy import MultiBucketPortfolioStrategy

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_sample_historical_data(start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
    """Generate sample historical data for backtesting."""
    logger.info("Generating sample historical data for backtesting...")
    
    # Generate date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Assets to simulate
    assets = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana', 'ripple', 'polkadot', 'chainlink', 'litecoin', 'uniswap']
    
    market_data = {}
    
    for asset in assets:
        # Generate realistic price data with some correlation to BTC
        np.random.seed(hash(asset) % 1000)  # Different seed for each asset
        
        if asset == 'bitcoin':
            # BTC as base with realistic volatility
            base_price = 50000
            returns = np.random.normal(0.0005, 0.03, len(date_range))  # Daily returns
        else:
            # Other assets with correlation to BTC
            btc_returns = np.random.normal(0.0005, 0.03, len(date_range))
            correlation = np.random.uniform(0.3, 0.8)  # Random correlation
            idiosyncratic = np.random.normal(0.0003, 0.025, len(date_range))
            returns = correlation * btc_returns + (1 - correlation) * idiosyncratic
        
        # Generate price series
        prices = [base_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLCV data
        df = pd.DataFrame({
            'timestamp': date_range,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000000, 10000000, len(date_range))
        })
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        market_data[asset] = df
    
    logger.info(f"Generated sample data for {len(market_data)} assets over {len(date_range)} days")
    return market_data

class MultiBucketBacktester:
    """
    Comprehensive backtesting framework for the multi-bucket portfolio strategy.
    """
    
    def __init__(self, config_path: str, start_date: str, end_date: str, initial_capital: float = 100000):
        """
        Initialize the backtester.
        
        Args:
            config_path: Path to strategy configuration
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            initial_capital: Initial portfolio capital
        """
        self.config_path = config_path
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.initial_capital = initial_capital
        
        # Initialize strategy
        self.strategy = MultiBucketPortfolioStrategy(config_path)
        
        # Portfolio state
        self.portfolio = {
            'cash': initial_capital,
            'positions': {},
            'equity_curve': [],
            'trades': [],
            'daily_returns': [],
            'risk_metrics': {}
        }
        
        # Performance tracking
        self.performance_metrics = {
            'total_return': 0.0,
            'annualized_return': 0.0,
            'volatility': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'calmar_ratio': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'bucket_performance': {},
            'regime_analysis': {}
        }
        
        logger.info(f"Backtester initialized for period {start_date} to {end_date} with ${initial_capital:,.0f} initial capital")
    
    def run_backtest(self) -> Dict[str, Any]:
        """Run the complete backtest."""
        logger.info("Starting backtest...")
        
        # Generate sample historical data
        market_data = generate_sample_historical_data(self.start_date, self.end_date)
        
        # Get date range
        all_dates = set()
        for asset, df in market_data.items():
            all_dates.update(df.index.date)
        
        trading_dates = sorted(list(all_dates))
        logger.info(f"Backtesting over {len(trading_dates)} trading days")
        
        # Initialize tracking
        daily_portfolio_values = []
        daily_positions = []
        daily_signals = []
        
        # Run daily analysis
        for i, date in enumerate(trading_dates):
            if i % 30 == 0:  # Log progress every 30 days
                logger.info(f"Processing day {i+1}/{len(trading_dates)}: {date}")
            
            # Get market data for current date
            current_market_data = self._get_market_data_for_date(market_data, date)
            
            if not current_market_data:
                continue
            
            # Run strategy analysis
            try:
                analysis_results = self.strategy.analyze(current_market_data)
                signals = self.strategy.generate_signals(analysis_results)
                
                # Execute trades
                self._execute_trades(signals, current_market_data, date)
                
                # Update portfolio value
                portfolio_value = self._calculate_portfolio_value(current_market_data, date)
                daily_portfolio_values.append({
                    'date': date,
                    'portfolio_value': portfolio_value,
                    'cash': self.portfolio['cash'],
                    'positions_value': portfolio_value - self.portfolio['cash']
                })
                
                # Track positions
                daily_positions.append({
                    'date': date,
                    'positions': self.portfolio['positions'].copy(),
                    'analysis': analysis_results
                })
                
                # Track signals
                if signals:
                    daily_signals.append({
                        'date': date,
                        'signals': signals,
                        'analysis': analysis_results
                    })
                
            except Exception as e:
                logger.error(f"Error processing {date}: {e}")
                continue
        
        # Calculate performance metrics
        self._calculate_performance_metrics(daily_portfolio_values, daily_positions, daily_signals)
        
        # Generate reports
        backtest_results = {
            'performance_metrics': self.performance_metrics,
            'daily_portfolio_values': daily_portfolio_values,
            'daily_positions': daily_positions,
            'daily_signals': daily_signals,
            'trades': self.portfolio['trades'],
            'market_data': market_data
        }
        
        logger.info("Backtest completed successfully")
        return backtest_results
    
    def _get_market_data_for_date(self, market_data: Dict[str, pd.DataFrame], date: datetime.date) -> Dict[str, pd.DataFrame]:
        """Get market data up to the specified date for each asset."""
        current_market_data = {}
        
        for asset, df in market_data.items():
            # Get data up to the current date
            current_data = df[df.index.date <= date]
            if not current_data.empty:
                current_market_data[asset] = current_data
        
        return current_market_data
    
    def _execute_trades(self, signals: List, market_data: Dict[str, pd.DataFrame], date: datetime.date):
        """Execute trading signals and update portfolio."""
        for signal in signals:
            try:
                symbol = signal.symbol
                signal_type = signal.signal_type.value
                direction = signal.direction.value
                position_size = signal.position_size
                price = signal.price
                
                # Calculate position value
                position_value = self.portfolio['cash'] * position_size
                
                if direction == 'BUY':
                    # Buy position
                    if position_value <= self.portfolio['cash']:
                        shares = position_value / price
                        
                        if symbol in self.portfolio['positions']:
                            # Add to existing position
                            self.portfolio['positions'][symbol]['shares'] += shares
                            self.portfolio['positions'][symbol]['avg_price'] = (
                                (self.portfolio['positions'][symbol]['avg_price'] * 
                                 self.portfolio['positions'][symbol]['shares'] + position_value) /
                                (self.portfolio['positions'][symbol]['shares'] + shares)
                            )
                        else:
                            # New position
                            self.portfolio['positions'][symbol] = {
                                'shares': shares,
                                'avg_price': price,
                                'entry_date': date,
                                'signal_type': signal_type,
                                'bucket': signal.metadata.get('bucket', 'unknown')
                            }
                        
                        self.portfolio['cash'] -= position_value
                        
                        # Record trade
                        self.portfolio['trades'].append({
                            'date': date,
                            'symbol': symbol,
                            'action': 'BUY',
                            'shares': shares,
                            'price': price,
                            'value': position_value,
                            'bucket': signal.metadata.get('bucket', 'unknown'),
                            'signal_strength': signal.signal_strength.value,
                            'confidence': signal.confidence
                        })
                
                elif direction == 'SELL':
                    # Sell position (for short signals, we'll track as negative shares)
                    if symbol in self.portfolio['positions']:
                        # Close existing long position
                        shares = self.portfolio['positions'][symbol]['shares']
                        exit_value = shares * price
                        
                        self.portfolio['cash'] += exit_value
                        
                        # Calculate P&L
                        entry_value = shares * self.portfolio['positions'][symbol]['avg_price']
                        pnl = exit_value - entry_value
                        
                        # Record trade
                        self.portfolio['trades'].append({
                            'date': date,
                            'symbol': symbol,
                            'action': 'SELL',
                            'shares': shares,
                            'price': price,
                            'value': exit_value,
                            'pnl': pnl,
                            'bucket': self.portfolio['positions'][symbol].get('bucket', 'unknown'),
                            'signal_strength': signal.signal_strength.value,
                            'confidence': signal.confidence
                        })
                        
                        del self.portfolio['positions'][symbol]
                    
                    # For short signals, we'll implement a simplified approach
                    if signal_type == 'SHORT':
                        # Track short position (simplified)
                        short_value = self.portfolio['cash'] * position_size
                        self.portfolio['cash'] += short_value  # Receive cash for short
                        
                        # Record short trade
                        self.portfolio['trades'].append({
                            'date': date,
                            'symbol': symbol,
                            'action': 'SHORT',
                            'value': short_value,
                            'price': price,
                            'bucket': signal.metadata.get('bucket', 'unknown'),
                            'signal_strength': signal.signal_strength.value,
                            'confidence': signal.confidence
                        })
                
            except Exception as e:
                logger.error(f"Error executing trade for {signal.symbol}: {e}")
    
    def _calculate_portfolio_value(self, market_data: Dict[str, pd.DataFrame], date: datetime.date) -> float:
        """Calculate total portfolio value including positions."""
        total_value = self.portfolio['cash']
        
        for symbol, position in self.portfolio['positions'].items():
            if symbol in market_data:
                # Get current price
                current_data = market_data[symbol][market_data[symbol].index.date == date]
                if not current_data.empty:
                    current_price = current_data['close'].iloc[-1]
                    position_value = position['shares'] * current_price
                    total_value += position_value
        
        return total_value
    
    def _calculate_performance_metrics(self, daily_portfolio_values: List[Dict], 
                                     daily_positions: List[Dict], 
                                     daily_signals: List[Dict]):
        """Calculate comprehensive performance metrics."""
        logger.info("Calculating performance metrics...")
        
        # Create portfolio value series
        df_portfolio = pd.DataFrame(daily_portfolio_values)
        df_portfolio['date'] = pd.to_datetime(df_portfolio['date'])
        df_portfolio.set_index('date', inplace=True)
        
        # Calculate returns
        df_portfolio['daily_return'] = df_portfolio['portfolio_value'].pct_change()
        df_portfolio['cumulative_return'] = (df_portfolio['portfolio_value'] / self.initial_capital) - 1
        
        # Basic metrics
        total_return = (df_portfolio['portfolio_value'].iloc[-1] / self.initial_capital) - 1
        annualized_return = ((1 + total_return) ** (252 / len(df_portfolio))) - 1
        volatility = df_portfolio['daily_return'].std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        cumulative_returns = df_portfolio['cumulative_return']
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / (running_max + 1)
        max_drawdown = drawdown.min()
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Win rate and profit factor
        trades_df = pd.DataFrame(self.portfolio['trades'])
        if not trades_df.empty and 'pnl' in trades_df.columns:
            winning_trades = trades_df[trades_df['pnl'] > 0]
            losing_trades = trades_df[trades_df['pnl'] < 0]
            
            win_rate = len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0
            profit_factor = (abs(winning_trades['pnl'].sum()) / abs(losing_trades['pnl'].sum()) 
                           if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else 0)
        else:
            win_rate = 0
            profit_factor = 0
        
        # Bucket performance analysis
        bucket_performance = self._analyze_bucket_performance(daily_positions, daily_signals)
        
        # Regime analysis
        regime_analysis = self._analyze_regime_performance(daily_positions)
        
        # Update performance metrics
        self.performance_metrics.update({
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'bucket_performance': bucket_performance,
            'regime_analysis': regime_analysis,
            'portfolio_data': df_portfolio
        })
    
    def _analyze_bucket_performance(self, daily_positions: List[Dict], daily_signals: List[Dict]) -> Dict[str, Any]:
        """Analyze performance by strategy bucket."""
        bucket_stats = {
            'momentum_long': {'signals': 0, 'trades': 0, 'pnl': 0.0},
            'residual_long': {'signals': 0, 'trades': 0, 'pnl': 0.0},
            'residual_short': {'signals': 0, 'trades': 0, 'pnl': 0.0},
            'mean_reversion_long': {'signals': 0, 'trades': 0, 'pnl': 0.0},
            'mean_reversion_short': {'signals': 0, 'trades': 0, 'pnl': 0.0},
            'pair_long_spread': {'signals': 0, 'trades': 0, 'pnl': 0.0},
            'pair_short_spread': {'signals': 0, 'trades': 0, 'pnl': 0.0}
        }
        
        # Count signals by bucket
        for signal_data in daily_signals:
            for signal in signal_data['signals']:
                bucket = signal.metadata.get('bucket', 'unknown')
                if bucket in bucket_stats:
                    bucket_stats[bucket]['signals'] += 1
        
        # Analyze trades by bucket
        trades_df = pd.DataFrame(self.portfolio['trades'])
        if not trades_df.empty and 'bucket' in trades_df.columns:
            for bucket in bucket_stats:
                bucket_trades = trades_df[trades_df['bucket'] == bucket]
                bucket_stats[bucket]['trades'] = len(bucket_trades)
                if 'pnl' in bucket_trades.columns:
                    bucket_stats[bucket]['pnl'] = bucket_trades['pnl'].sum()
        
        return bucket_stats
    
    def _analyze_regime_performance(self, daily_positions: List[Dict]) -> Dict[str, Any]:
        """Analyze performance across different correlation regimes."""
        regime_stats = {
            'low_correlation': {'days': 0, 'avg_return': 0.0},
            'medium_correlation': {'days': 0, 'avg_return': 0.0},
            'high_correlation': {'days': 0, 'avg_return': 0.0}
        }
        
        for position_data in daily_positions:
            analysis = position_data.get('analysis', {})
            regime_analysis = analysis.get('regime_analysis', {})
            avg_correlation = regime_analysis.get('average_correlation', 0.5)
            
            # Categorize regime
            if avg_correlation <= 0.15:
                regime = 'low_correlation'
            elif avg_correlation <= 0.50:
                regime = 'medium_correlation'
            else:
                regime = 'high_correlation'
            
            regime_stats[regime]['days'] += 1
        
        return regime_stats
    
    def generate_report(self, backtest_results: Dict[str, Any]) -> str:
        """Generate comprehensive backtest report."""
        logger.info("Generating backtest report...")
        
        metrics = self.performance_metrics
        portfolio_data = metrics['portfolio_data']
        
        report = f"""
# Multi-Bucket Portfolio Strategy Backtest Report

## Backtest Period
- Start Date: {self.start_date.strftime('%Y-%m-%d')}
- End Date: {self.end_date.strftime('%Y-%m-%d')}
- Duration: {(self.end_date - self.start_date).days} days
- Initial Capital: ${self.initial_capital:,.0f}

## Performance Summary
- Total Return: {metrics['total_return']:.2%}
- Annualized Return: {metrics['annualized_return']:.2%}
- Volatility: {metrics['volatility']:.2%}
- Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
- Maximum Drawdown: {metrics['max_drawdown']:.2%}
- Calmar Ratio: {metrics['calmar_ratio']:.2f}
- Win Rate: {metrics['win_rate']:.2%}
- Profit Factor: {metrics['profit_factor']:.2f}

## Final Portfolio Value
- Final Value: ${portfolio_data['portfolio_value'].iloc[-1]:,.0f}
- Total P&L: ${portfolio_data['portfolio_value'].iloc[-1] - self.initial_capital:,.0f}

## Trading Activity
- Total Trades: {len(self.portfolio['trades'])}
- Trading Days: {len(portfolio_data)}

## Bucket Performance
"""
        
        for bucket, stats in metrics['bucket_performance'].items():
            if stats['signals'] > 0 or stats['trades'] > 0:
                report += f"- {bucket}: {stats['signals']} signals, {stats['trades']} trades, ${stats['pnl']:,.0f} P&L\n"
        
        report += f"""
## Regime Analysis
"""
        
        for regime, stats in metrics['regime_analysis'].items():
            if stats['days'] > 0:
                report += f"- {regime}: {stats['days']} days\n"
        
        return report
    
    def save_results(self, backtest_results: Dict[str, Any], output_dir: str = "backtest_results"):
        """Save backtest results to files."""
        logger.info(f"Saving backtest results to {output_dir}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Save performance metrics
        with open(f"{output_dir}/performance_metrics.json", 'w') as f:
            # Convert numpy types to native Python types for JSON serialization
            metrics = self.performance_metrics.copy()
            if 'portfolio_data' in metrics:
                del metrics['portfolio_data']  # Remove DataFrame from JSON
            json.dump(metrics, f, indent=2, default=str)
        
        # Save portfolio data
        portfolio_data = self.performance_metrics['portfolio_data']
        portfolio_data.to_csv(f"{output_dir}/portfolio_data.csv")
        
        # Save trades
        trades_df = pd.DataFrame(self.portfolio['trades'])
        if not trades_df.empty:
            trades_df.to_csv(f"{output_dir}/trades.csv", index=False)
        
        # Save daily positions
        with open(f"{output_dir}/daily_positions.json", 'w') as f:
            json.dump(backtest_results['daily_positions'], f, indent=2, default=str)
        
        # Generate and save report
        report = self.generate_report(backtest_results)
        with open(f"{output_dir}/backtest_report.md", 'w') as f:
            f.write(report)
        
        logger.info(f"All results saved to {output_dir}/")


def main():
    """Main backtesting function."""
    logger.info("Starting Multi-Bucket Portfolio Strategy Backtest")
    
    # Set backtest parameters
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    initial_capital = 100000  # $100k initial capital
    
    logger.info(f"Backtest period: {start_date} to {end_date}")
    logger.info(f"Initial capital: ${initial_capital:,.0f}")
    
    try:
        # Initialize backtester
        backtester = MultiBucketBacktester(
            config_path='config/strategies/multi_bucket_portfolio.json',
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        
        # Run backtest
        backtest_results = backtester.run_backtest()
        
        if not backtest_results:
            logger.error("Backtest failed - no results generated")
            return
        
        # Generate and display report
        report = backtester.generate_report(backtest_results)
        print(report)
        
        # Save results
        backtester.save_results(backtest_results)
        
        # Display key metrics
        metrics = backtester.performance_metrics
        print(f"\n{'='*60}")
        print("KEY PERFORMANCE METRICS")
        print(f"{'='*60}")
        print(f"Total Return: {metrics['total_return']:.2%}")
        print(f"Annualized Return: {metrics['annualized_return']:.2%}")
        print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"Maximum Drawdown: {metrics['max_drawdown']:.2%}")
        print(f"Win Rate: {metrics['win_rate']:.2%}")
        print(f"Total Trades: {len(backtester.portfolio['trades'])}")
        
        logger.info("Backtest completed successfully!")
        
    except Exception as e:
        logger.error(f"Backtest failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
