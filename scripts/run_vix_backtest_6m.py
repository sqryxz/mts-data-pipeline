#!/usr/bin/env python3
"""
Run 6-month backtest for the enhanced VIX Correlation Strategy on BTC and ETH.
Outputs results JSON and a brief markdown report in backtest_results/.
"""

import os
import sys
import json
from datetime import datetime, timedelta

sys.path.append('.')

from src.signals.strategies.vix_correlation_strategy import VIXCorrelationStrategy
from src.signals.backtest_interface import BacktestInterface


def main():
    end_date = datetime.now().date() - timedelta(days=1)
    start_date = end_date - timedelta(days=180)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    strategy = VIXCorrelationStrategy('config/strategies/vix_correlation.json')
    backtester = BacktestInterface(initial_capital=100000.0, transaction_cost=0.001)

    result = backtester.backtest_strategy(strategy, start_str, end_str)

    os.makedirs('backtest_results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_path = f'backtest_results/vix_corr_btc_eth_6m_{timestamp}.json'
    md_path = f'backtest_results/vix_corr_btc_eth_6m_{timestamp}.md'

    with open(json_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)

    perf = result.to_dict().get('performance_metrics', {})
    stats = result.to_dict().get('trading_statistics', {})
    with open(md_path, 'w') as f:
        f.write('# Enhanced VIX Correlation Strategy - 6M Backtest (BTC, ETH)\n\n')
        f.write(f'Period: {start_str} to {end_str}\n\n')
        f.write('## Performance\n')
        for k in ['total_return', 'annualized_return', 'sharpe_ratio', 'max_drawdown', 'volatility', 'calmar_ratio']:
            if k in perf:
                f.write(f'- {k}: {perf[k]}\n')
        f.write('\n## Trades\n')
        for k in ['total_trades', 'profitable_trades', 'losing_trades', 'win_rate', 'average_trade_return']:
            if k in stats:
                f.write(f'- {k}: {stats[k]}\n')
        f.write('\nSee JSON for full details.\n')

    print(f'Saved results to {json_path} and {md_path}')


if __name__ == '__main__':
    main()


