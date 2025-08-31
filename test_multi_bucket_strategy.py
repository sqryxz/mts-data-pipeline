#!/usr/bin/env python3
"""
Test script for Multi-Bucket Portfolio Strategy

This script demonstrates the functionality of the comprehensive multi-bucket
crypto portfolio strategy with momentum, residual, mean-reversion, and pair trading.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.signals.strategies.multi_bucket_portfolio_strategy import MultiBucketPortfolioStrategy

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_sample_market_data():
    """Generate sample market data for testing."""
    np.random.seed(42)
    
    # Generate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=200)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    market_data = {}
    
    # Generate data for each asset
    assets = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana', 'ripple', 'polkadot', 'chainlink', 'litecoin', 'uniswap']
    
    for asset in assets:
        # Generate price data with some correlation to BTC
        if asset == 'bitcoin':
            # BTC as base
            base_price = 50000
            returns = np.random.normal(0.001, 0.03, len(dates))  # Daily returns
        else:
            # Other assets with correlation to BTC
            btc_returns = np.random.normal(0.001, 0.03, len(dates))
            correlation = np.random.uniform(0.3, 0.8)  # Random correlation
            idiosyncratic = np.random.normal(0.001, 0.02, len(dates))
            returns = correlation * btc_returns + (1 - correlation) * idiosyncratic
        
        # Generate price series
        prices = [base_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLCV data
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000000, 10000000, len(dates))
        })
        
        market_data[asset] = df
    
    return market_data

def test_momentum_analysis():
    """Test momentum analysis functionality."""
    logger.info("Testing momentum analysis...")
    
    # Generate sample data
    market_data = generate_sample_market_data()
    
    # Initialize strategy
    config_path = 'config/strategies/multi_bucket_portfolio.json'
    strategy = MultiBucketPortfolioStrategy(config_path)
    
    # Run analysis
    analysis_results = strategy.analyze(market_data)
    
    # Check momentum analysis
    momentum_analysis = analysis_results.get('momentum_analysis', {})
    logger.info(f"Momentum analysis completed for {len(momentum_analysis)} assets")
    
    # Print sample results
    for asset, analysis in list(momentum_analysis.items())[:3]:
        logger.info(f"{asset}:")
        logger.info(f"  Composite Momentum: {analysis.get('composite_momentum', 0):.3f}")
        logger.info(f"  Acceleration: {analysis.get('acceleration', 0):.3f}")
        logger.info(f"  Momentum Strength: {analysis.get('momentum_strength', 0):.3f}")
        logger.info(f"  Trend Alignment: {analysis.get('trend_alignment', False)}")
    
    return analysis_results

def test_residual_analysis():
    """Test residual analysis functionality."""
    logger.info("Testing residual analysis...")
    
    # Generate sample data
    market_data = generate_sample_market_data()
    
    # Initialize strategy
    config_path = 'config/strategies/multi_bucket_portfolio.json'
    strategy = MultiBucketPortfolioStrategy(config_path)
    
    # Run analysis
    analysis_results = strategy.analyze(market_data)
    
    # Check residual analysis
    residual_analysis = analysis_results.get('residual_analysis', {})
    logger.info(f"Residual analysis completed for {len(residual_analysis)} assets")
    
    # Print sample results
    for asset, analysis in list(residual_analysis.items())[:3]:
        logger.info(f"{asset}:")
        logger.info(f"  Beta: {analysis.get('beta', 0):.3f}")
        logger.info(f"  Residual Z-Score: {analysis.get('residual_zscore', 0):.3f}")
        logger.info(f"  Residual Mean: {analysis.get('residual_mean', 0):.6f}")
        logger.info(f"  Residual Std: {analysis.get('residual_std', 0):.6f}")
    
    return analysis_results

def test_correlation_analysis():
    """Test correlation analysis functionality."""
    logger.info("Testing correlation analysis...")
    
    # Generate sample data
    market_data = generate_sample_market_data()
    
    # Initialize strategy
    config_path = 'config/strategies/multi_bucket_portfolio.json'
    strategy = MultiBucketPortfolioStrategy(config_path)
    
    # Run analysis
    analysis_results = strategy.analyze(market_data)
    
    # Check correlation analysis
    correlation_analysis = analysis_results.get('correlation_analysis', {})
    logger.info(f"Correlation analysis completed for {len(correlation_analysis)} timeframes")
    
    # Print average correlation
    avg_correlation = correlation_analysis.get('average_correlation', 0)
    logger.info(f"Average Correlation: {avg_correlation:.3f}")
    
    # Print correlation matrices for different timeframes
    for timeframe in ['7d', '30d']:
        if timeframe in correlation_analysis:
            corr_matrix = correlation_analysis[timeframe]
            if not corr_matrix.empty:
                logger.info(f"{timeframe} correlation matrix shape: {corr_matrix.shape}")
    
    return analysis_results

def test_pair_trading_analysis():
    """Test pair trading analysis functionality."""
    logger.info("Testing pair trading analysis...")
    
    # Generate sample data
    market_data = generate_sample_market_data()
    
    # Initialize strategy
    config_path = 'config/strategies/multi_bucket_portfolio.json'
    strategy = MultiBucketPortfolioStrategy(config_path)
    
    # Run analysis
    analysis_results = strategy.analyze(market_data)
    
    # Check pair analysis
    pair_analysis = analysis_results.get('pair_analysis', {})
    logger.info(f"Pair analysis completed for {len(pair_analysis)} pairs")
    
    # Print sample results
    for pair_name, analysis in pair_analysis.items():
        logger.info(f"{pair_name}:")
        logger.info(f"  Spread: {analysis.get('spread', 0):.2f}")
        logger.info(f"  Spread Z-Score: {analysis.get('spread_zscore', 0):.3f}")
        logger.info(f"  Long Price: {analysis.get('long_price', 0):.2f}")
        logger.info(f"  Short Price: {analysis.get('short_price', 0):.2f}")
        
        # Print correlation metrics
        corr_metrics = analysis.get('correlation_metrics', {})
        for timeframe, corr in corr_metrics.items():
            logger.info(f"  {timeframe} Correlation: {corr:.3f}")
    
    return analysis_results

def test_signal_generation():
    """Test signal generation functionality."""
    logger.info("Testing signal generation...")
    
    # Generate sample data
    market_data = generate_sample_market_data()
    
    # Initialize strategy
    config_path = 'config/strategies/multi_bucket_portfolio.json'
    strategy = MultiBucketPortfolioStrategy(config_path)
    
    # Run analysis
    analysis_results = strategy.analyze(market_data)
    
    # Generate signals
    signals = strategy.generate_signals(analysis_results)
    
    logger.info(f"Generated {len(signals)} trading signals")
    
    # Print sample signals
    for i, signal in enumerate(signals[:5]):
        logger.info(f"Signal {i+1}:")
        logger.info(f"  Symbol: {signal.symbol}")
        logger.info(f"  Type: {signal.signal_type.value}")
        logger.info(f"  Direction: {signal.direction.value}")
        logger.info(f"  Strength: {signal.signal_strength.value}")
        logger.info(f"  Confidence: {signal.confidence:.3f}")
        logger.info(f"  Position Size: {signal.position_size:.3f}")
        logger.info(f"  Price: {signal.price:.2f}")
        logger.info(f"  Stop Loss: {signal.stop_loss:.2f}" if signal.stop_loss else "  Stop Loss: None")
        logger.info(f"  Bucket: {signal.metadata.get('bucket', 'unknown')}")
    
    return signals

def test_risk_summary():
    """Test risk summary functionality."""
    logger.info("Testing risk summary...")
    
    # Generate sample data
    market_data = generate_sample_market_data()
    
    # Initialize strategy
    config_path = 'config/strategies/multi_bucket_portfolio.json'
    strategy = MultiBucketPortfolioStrategy(config_path)
    
    # Run analysis
    analysis_results = strategy.analyze(market_data)
    
    # Check risk summary
    risk_summary = analysis_results.get('risk_summary', {})
    
    logger.info("Risk Summary:")
    logger.info(f"  Total Exposure: {risk_summary.get('total_exposure', 0):.3f}")
    logger.info(f"  Portfolio Beta: {risk_summary.get('portfolio_beta', 0):.3f}")
    logger.info(f"  Leverage Factor: {risk_summary.get('leverage_factor', 1.0):.3f}")
    logger.info(f"  Risk-Off Mode: {risk_summary.get('risk_off_mode', False)}")
    logger.info(f"  Average Correlation: {risk_summary.get('average_correlation', 0.5):.3f}")
    logger.info(f"  Opportunity Count: {risk_summary.get('opportunity_count', 0)}")
    
    # Print bucket distribution
    bucket_distribution = risk_summary.get('bucket_distribution', {})
    logger.info("  Bucket Distribution:")
    for bucket, percentage in bucket_distribution.items():
        logger.info(f"    {bucket}: {percentage:.1%}")
    
    return risk_summary

def test_strategy_parameters():
    """Test strategy parameters."""
    logger.info("Testing strategy parameters...")
    
    # Initialize strategy
    config_path = 'config/strategies/multi_bucket_portfolio.json'
    strategy = MultiBucketPortfolioStrategy(config_path)
    
    # Get parameters
    parameters = strategy.get_parameters()
    
    logger.info("Strategy Parameters:")
    logger.info(f"  Strategy Name: {parameters.get('strategy_name', 'Unknown')}")
    logger.info(f"  Version: {parameters.get('version', 'Unknown')}")
    
    # Print momentum parameters
    momentum_params = parameters.get('momentum_parameters', {})
    logger.info("  Momentum Parameters:")
    logger.info(f"    Horizons: {momentum_params.get('horizons', [])}")
    logger.info(f"    Weights: {momentum_params.get('weights', [])}")
    logger.info(f"    Composite Threshold: {momentum_params.get('composite_threshold', 0)}")
    
    # Print correlation parameters
    correlation_params = parameters.get('correlation_parameters', {})
    logger.info("  Correlation Parameters:")
    logger.info(f"    Windows: {correlation_params.get('correlation_windows', [])}")
    logger.info(f"    Low Threshold: {correlation_params.get('low_correlation_threshold', 0)}")
    logger.info(f"    High Threshold: {correlation_params.get('high_correlation_threshold', 0)}")
    
    return parameters

def main():
    """Main test function."""
    logger.info("Starting Multi-Bucket Portfolio Strategy Tests")
    logger.info("=" * 60)
    
    try:
        # Test momentum analysis
        test_momentum_analysis()
        logger.info("-" * 40)
        
        # Test residual analysis
        test_residual_analysis()
        logger.info("-" * 40)
        
        # Test correlation analysis
        test_correlation_analysis()
        logger.info("-" * 40)
        
        # Test pair trading analysis
        test_pair_trading_analysis()
        logger.info("-" * 40)
        
        # Test signal generation
        test_signal_generation()
        logger.info("-" * 40)
        
        # Test risk summary
        test_risk_summary()
        logger.info("-" * 40)
        
        # Test strategy parameters
        test_strategy_parameters()
        logger.info("-" * 40)
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
