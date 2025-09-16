#!/usr/bin/env python3
"""
Parameter sweep optimizer for the Enhanced VIX Correlation Strategy (BTC, ETH).
Searches over thresholds and filters using last 6 months and selects best config.
Saves summary and best config to backtest_results/.
"""

import os
import sys
import json
import itertools
from datetime import datetime, timedelta

sys.path.append('.')

from src.signals.strategies.vix_correlation_strategy import VIXCorrelationStrategy
from src.signals.backtest_interface import BacktestInterface


def set_strategy_params(strategy: VIXCorrelationStrategy, params: dict) -> None:
    # Core thresholds
    strategy.correlation_thresholds = {
        'strong_negative': params['neg'],
        'strong_positive': params['pos']
    }
    strategy.correlation_windows = params['windows']
    strategy.min_agreement_windows = params['agree']
    strategy.use_dynamic_thresholds = params['dynamic']
    strategy.vix_filters = {
        'min_vix_for_long': params['min_vix_long'],
        'min_vix_for_short': params['min_vix_short']
    }
    strategy.rsi_filter = {
        'enabled': params['rsi_enabled'],
        'long_max_rsi': params['long_max_rsi'],
        'short_min_rsi': params['short_min_rsi']
    }
    strategy.drawdown_filter = {
        'enabled': True,
        'min_drawdown_for_long': params['min_dd_long'],
        'min_drawup_for_short': params['min_du_short']
    }
    strategy.lag_range = params['lags']


def main():
    end_date = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
    start_date = (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(days=180)).strftime('%Y-%m-%d')

    # Parameter grid (kept modest to run quickly)
    negs = [-0.2, -0.3, -0.4, -0.5]
    poss = [0.2, 0.3, 0.4, 0.5]
    windows_list = [[7, 14, 21], [14, 21, 30]]
    agrees = [1, 2]
    dynamics = [False]
    min_vix_longs = [10.0, 12.0, 15.0]
    min_vix_shorts = [10.0, 12.0, 15.0]
    rsi_enableds = [False, True]
    long_max_rsis = [55, 60]
    short_min_rsis = [50, 55]
    min_dd_longs = [0.00, 0.02, 0.04]
    min_du_shorts = [0.00, 0.02, 0.04]
    lags_list = [[-2, -1, 0, 1, 2]]

    combos = list(itertools.product(
        negs, poss, windows_list, agrees, dynamics, min_vix_longs, min_vix_shorts,
        rsi_enableds, long_max_rsis, short_min_rsis, min_dd_longs, min_du_shorts, lags_list
    ))

    # Limit total combos to avoid long runtimes
    MAX_COMBOS = 60
    combos = combos[:MAX_COMBOS]

    backtester = BacktestInterface(initial_capital=100000.0, transaction_cost=0.001)
    base_strategy = VIXCorrelationStrategy('config/strategies/vix_correlation.json')

    results = []
    best = None

    for idx, c in enumerate(combos, 1):
        params = {
            'neg': c[0], 'pos': c[1], 'windows': c[2], 'agree': c[3], 'dynamic': c[4],
            'min_vix_long': c[5], 'min_vix_short': c[6],
            'rsi_enabled': c[7], 'long_max_rsi': c[8], 'short_min_rsi': c[9],
            'min_dd_long': c[10], 'min_du_short': c[11], 'lags': c[12]
        }

        # Clone by re-instantiation to avoid state carryover
        strategy = VIXCorrelationStrategy('config/strategies/vix_correlation.json')
        set_strategy_params(strategy, params)

        result = backtester.backtest_strategy(strategy, start_date, end_date)
        rd = result.to_dict()
        perf = rd.get('performance_metrics', {})
        stats = rd.get('trading_statistics', {})

        sharpe = perf.get('sharpe_ratio', 0.0)
        win_rate = perf.get('win_rate', 0.0)
        total_trades = stats.get('total_trades', 0)

        score = sharpe + (win_rate or 0) * 0.2 + (0.0 if total_trades < 5 else min(total_trades, 30) / 300.0)
        entry = {
            'params': params,
            'performance': perf,
            'stats': stats,
            'score': score
        }
        results.append(entry)

        # Keep best with a minimum trade count to avoid overfitting to zero signals
        min_trades = 5
        if (best is None and total_trades >= min_trades) or (total_trades >= min_trades and score > best['score']):
            best = entry

        print(f"[{idx}/{len(combos)}] sharpe={sharpe:.3f} win={win_rate:.2%} trades={total_trades} score={score:.3f}")

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs('backtest_results', exist_ok=True)
    out_path = f'backtest_results/vix_corr_opt_results_{ts}.json'
    with open(out_path, 'w') as f:
        json.dump({'start': start_date, 'end': end_date, 'results': results, 'best': best}, f, indent=2)

    if best:
        print('\nBest configuration found with score:', best['score'])
        best_cfg = best['params']
        # Persist to config file
        cfg_path = 'config/strategies/vix_correlation.json'
        with open(cfg_path, 'r') as f:
            cfg = json.load(f)
        cfg['correlation_thresholds'] = {
            'strong_negative': best_cfg['neg'],
            'strong_positive': best_cfg['pos']
        }
        cfg['correlation_windows'] = best_cfg['windows']
        cfg['min_agreement_windows'] = best_cfg['agree']
        cfg['use_dynamic_thresholds'] = best_cfg['dynamic']
        cfg['vix_filters'] = {
            'min_vix_for_long': best_cfg['min_vix_long'],
            'min_vix_for_short': best_cfg['min_vix_short']
        }
        cfg['rsi_filter'] = {
            'enabled': best_cfg['rsi_enabled'],
            'long_max_rsi': best_cfg['long_max_rsi'],
            'short_min_rsi': best_cfg['short_min_rsi']
        }
        cfg['drawdown_filter'] = {
            'enabled': True,
            'min_drawdown_for_long': best_cfg['min_dd_long'],
            'min_drawup_for_short': best_cfg['min_du_short']
        }
        cfg['lag_range'] = best_cfg['lags']
        with open(cfg_path, 'w') as f:
            json.dump(cfg, f, indent=2)
        print('Updated config/strategies/vix_correlation.json with best parameters.')
    else:
        print('\nNo configuration produced sufficient trades. See results for diagnostics:', out_path)


if __name__ == '__main__':
    main()


