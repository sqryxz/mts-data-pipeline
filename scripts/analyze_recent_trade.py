#!/usr/bin/env python3
"""
Recent Trade Analysis Script
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.sqlite_helper import CryptoDatabase

def analyze_recent_performance():
    """Analyze recent crypto performance"""
    print('=== RECENT PERFORMANCE ANALYSIS (Last 60 days) ===')
    
    db = CryptoDatabase('data/crypto_data.db')
    crypto_symbols = ['bitcoin', 'ethereum', 'solana', 'ripple']
    recent_data = {}
    
    for crypto in crypto_symbols:
        try:
            data = db.get_crypto_data(crypto, days=60)
            
            if not data.empty and 'close' in data.columns:
                prices = data['close'].dropna()
                
                if len(prices) > 10:
                    returns_60d = (prices.iloc[-1] / prices.iloc[0]) - 1
                    returns_30d = (prices.iloc[-1] / prices.iloc[-30]) - 1 if len(prices) >= 30 else 0
                    returns_14d = (prices.iloc[-1] / prices.iloc[-14]) - 1 if len(prices) >= 14 else 0
                    returns_7d = (prices.iloc[-1] / prices.iloc[-7]) - 1 if len(prices) >= 7 else 0
                    
                    momentum_7d = returns_7d
                    momentum_14d = returns_14d - returns_7d
                    momentum_30d = returns_30d - returns_14d
                    
                    daily_returns = prices.pct_change().dropna()
                    volatility = daily_returns.std() * (252 ** 0.5)
                    
                    recent_data[crypto] = {
                        'current_price': prices.iloc[-1],
                        'returns_60d': returns_60d,
                        'returns_30d': returns_30d,
                        'returns_14d': returns_14d,
                        'returns_7d': returns_7d,
                        'momentum_7d': momentum_7d,
                        'momentum_14d': momentum_14d,
                        'momentum_30d': momentum_30d,
                        'volatility': volatility,
                        'data_points': len(prices)
                    }
                    
                    print(f'{crypto.upper()}:')
                    print(f'  Current Price: ${prices.iloc[-1]:,.2f}')
                    print(f'  60d: {returns_60d:.2%} | 30d: {returns_30d:.2%} | 14d: {returns_14d:.2%} | 7d: {returns_7d:.2%}')
                    print(f'  Momentum: 7d: {momentum_7d:.2%} | 14d: {momentum_14d:.2%} | 30d: {momentum_30d:.2%}')
                    print(f'  Volatility: {volatility:.2%}')
                    print()
                    
        except Exception as e:
            print(f'Error analyzing {crypto}: {e}')
    
    return recent_data

def analyze_macro_environment():
    """Analyze recent macro environment"""
    print('=== RECENT MACRO ENVIRONMENT ===')
    
    db = CryptoDatabase('data/crypto_data.db')
    macro_indicators = ['VIXCLS', 'DGS10', 'DTWEXBGS']
    
    macro_data = {}
    
    for indicator in macro_indicators:
        try:
            query = f"""
            SELECT date, value 
            FROM macro_indicators 
            WHERE indicator = ? 
            AND date >= DATE('now', '-60 days')
            ORDER BY date ASC
            """
            
            df = db.query_to_dataframe(query, (indicator,))
            
            if not df.empty:
                values = pd.to_numeric(df['value'], errors='coerce').dropna()
                
                if len(values) > 10:
                    current = values.iloc[-1]
                    avg_60d = values.mean()
                    change_30d = (values.iloc[-1] / values.iloc[-30]) - 1 if len(values) >= 30 else 0
                    change_14d = (values.iloc[-1] / values.iloc[-14]) - 1 if len(values) >= 14 else 0
                    change_7d = (values.iloc[-1] / values.iloc[-7]) - 1 if len(values) >= 7 else 0
                    
                    macro_data[indicator] = {
                        'current': current,
                        'avg_60d': avg_60d,
                        'change_30d': change_30d,
                        'change_14d': change_14d,
                        'change_7d': change_7d
                    }
                    
                    print(f'{indicator}:')
                    print(f'  Current: {current:.4f}')
                    print(f'  60d Avg: {avg_60d:.4f}')
                    print(f'  Changes: 30d: {change_30d:.2%} | 14d: {change_14d:.2%} | 7d: {change_7d:.2%}')
                    print()
                    
        except Exception as e:
            print(f'Error analyzing {indicator}: {e}')
    
    return macro_data

def generate_recommendation(recent_data, macro_data):
    """Generate trade recommendation"""
    print('=== TRADE RECOMMENDATION ===')
    
    if not recent_data:
        print('No recent data available for analysis')
        return
    
    # Find best performers
    best_momentum = max(recent_data.items(), key=lambda x: x[1]['momentum_7d'])
    best_60d = max(recent_data.items(), key=lambda x: x[1]['returns_60d'])
    best_30d = max(recent_data.items(), key=lambda x: x[1]['returns_30d'])
    
    print(f'Best 7-day momentum: {best_momentum[0].upper()} ({best_momentum[1]["momentum_7d"]:.2%})')
    print(f'Best 60-day performance: {best_60d[0].upper()} ({best_60d[1]["returns_60d"]:.2%})')
    print(f'Best 30-day performance: {best_30d[0].upper()} ({best_30d[1]["returns_30d"]:.2%})')
    
    # Analyze VIX environment
    vix_data = macro_data.get('VIXCLS', {})
    if vix_data:
        vix_current = vix_data['current']
        vix_avg = vix_data['avg_60d']
        vix_change = vix_data['change_30d']
        
        print(f'\nVIX Environment:')
        print(f'  Current: {vix_current:.2f}')
        print(f'  60-day Avg: {vix_avg:.2f}')
        print(f'  30-day Change: {vix_change:.2%}')
        
        if vix_current < vix_avg:
            print(f'  Market sentiment: Low fear environment (bullish for crypto)')
        else:
            print(f'  Market sentiment: Elevated fear environment')
    
    # Generate recommendation
    print(f'\n🎯 RECOMMENDATION:')
    
    # Check for strong momentum
    if best_momentum[1]['momentum_7d'] > 0.02:  # 2% weekly momentum
        print(f'  LONG {best_momentum[0].upper()} - Strong recent momentum')
        print(f'  Rationale: Best 7-day momentum at {best_momentum[1]["momentum_7d"]:.2%}')
    elif best_60d[1]['returns_60d'] > 0.20:  # 20% 60-day return
        print(f'  LONG {best_60d[0].upper()} - Strong 60-day performance')
        print(f'  Rationale: Best 60-day return at {best_60d[1]["returns_60d"]:.2%}')
    elif best_30d[1]['returns_30d'] > 0.10:  # 10% 30-day return
        print(f'  LONG {best_30d[0].upper()} - Strong 30-day performance')
        print(f'  Rationale: Best 30-day return at {best_30d[1]["returns_30d"]:.2%}')
    else:
        print(f'  WAIT - No clear momentum signals')
        print(f'  Best momentum: {best_momentum[0].upper()} at {best_momentum[1]["momentum_7d"]:.2%}')
    
    print(f'\nRisk Management:')
    print(f'  - Position size: 5-10% of portfolio')
    print(f'  - Stop loss: 15-20% below entry')
    print(f'  - Take profit: 30-50% gains')
    
    # Additional insights
    print(f'\nAdditional Insights:')
    for crypto, data in recent_data.items():
        if data['momentum_7d'] > 0.01:  # 1% weekly momentum
            print(f'  - {crypto.upper()}: Positive momentum ({data["momentum_7d"]:.2%})')
        elif data['momentum_7d'] < -0.01:  # -1% weekly momentum
            print(f'  - {crypto.upper()}: Negative momentum ({data["momentum_7d"]:.2%})')

def main():
    """Main execution function"""
    print('=== RECENT TRADE ANALYSIS ===')
    print(f'Analysis Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 60)
    
    # Analyze recent performance
    recent_data = analyze_recent_performance()
    
    # Analyze macro environment
    macro_data = analyze_macro_environment()
    
    # Generate recommendation
    generate_recommendation(recent_data, macro_data)
    
    print('\n' + '=' * 60)
    print('Analysis complete!')

if __name__ == "__main__":
    main()
