#!/usr/bin/env python3
"""
VIX Correlation Strategy Backtest Analysis for Bitcoin
"""

import sys
sys.path.append('.')

print('VIX CORRELATION STRATEGY BACKTEST FOR BITCOIN')
print('=' * 50)

from src.signals.strategies.vix_correlation_strategy import VIXCorrelationStrategy

try:
    print('Initializing VIX Correlation Strategy...')
    strategy = VIXCorrelationStrategy('config/strategies/vix_correlation.json')
    print('Strategy initialized successfully')

    # Get market data for backtest - use the correct method
    from src.data.sqlite_helper import CryptoDatabase
    db = CryptoDatabase()

    # Get combined analysis data (crypto + VIX)
    market_data = {
        'bitcoin': db.get_combined_analysis_data('bitcoin', days=30)
    }

    if market_data['bitcoin'].empty:
        print('No Bitcoin data available for backtest')
    else:
        print('Loaded Bitcoin price records:', len(market_data['bitcoin']))

        # Run strategy analysis
        analysis_results = strategy.analyze(market_data)

        # Generate signals
        signals = strategy.generate_signals(analysis_results)

        print('SIGNALS GENERATED:')
        print('Total Signals:', len(signals))

        # Analyze signal distribution
        long_signals = [s for s in signals if s.signal_type.value == 'LONG']
        short_signals = [s for s in signals if s.signal_type.value == 'SHORT']

        print('LONG Signals:', len(long_signals))
        print('SHORT Signals:', len(short_signals))

        if signals:
            # Calculate basic performance metrics
            confidences = [s.confidence for s in signals]
            avg_confidence = sum(confidences) / len(confidences)

            print('Average Confidence:', round(avg_confidence * 100, 1), '%')
            print('High Confidence (>80%):', len([s for s in signals if s.confidence > 0.8]))

            # Analyze position sizing
            position_sizes = [s.position_size for s in signals]
            avg_position_size = sum(position_sizes) / len(position_sizes)

            print('Average Position Size:', round(avg_position_size * 100, 1), '%')

            # Risk analysis
            total_signals = len(signals)
            avg_risk = sum([s.max_risk for s in signals]) / total_signals

            print('Average Risk per Trade:', round(avg_risk * 100, 1), '%')

            print('STRATEGY PERFORMANCE ASSESSMENT:')

            # Signal quality assessment
            if avg_confidence > 0.8:
                signal_quality = 'Excellent'
            elif avg_confidence > 0.6:
                signal_quality = 'Good'
            else:
                signal_quality = 'Needs Improvement'

            # Risk assessment
            if avg_risk < 0.03:
                risk_level = 'Conservative'
            elif avg_risk < 0.05:
                risk_level = 'Moderate'
            else:
                risk_level = 'Aggressive'

            print('Signal Quality:', signal_quality)
            print('Risk Management:', risk_level)
            print('Strategy Type: Correlation-based (VIX vs Crypto)')
            print('Best For: Extreme market conditions')

            print('STRATEGY SUMMARY:')
            print('- Signal generation based on VIX correlation strength')
            print('- Built-in position sizing and risk management')
            print('- Designed for extreme market volatility periods')

        # Market data analysis
        if 'bitcoin' in market_data and not market_data['bitcoin'].empty:
            btc_data = market_data['bitcoin']
            print('Market Data Available:', len(btc_data), 'records')

except Exception as e:
    print('Error running VIX Correlation backtest:', str(e))
    import traceback
    traceback.print_exc()
