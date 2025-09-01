#!/usr/bin/env python3
"""
Fix for VIX correlation strategy to use current prices even when VIX data is stale
"""

import sys
sys.path.append('.')
from src.signals.strategies.vix_correlation_strategy import VIXCorrelationStrategy
from src.data.sqlite_helper import CryptoDatabase
import pandas as pd
from datetime import datetime

def fix_vix_strategy_pricing():
    """
    Patch the VIX correlation strategy to use current prices when VIX data is stale.
    """
    print("🔧 Fixing VIX Strategy Price Issue")
    print("=" * 50)
    
    # Read the current VIX strategy file
    strategy_file = "src/signals/strategies/vix_correlation_strategy.py"
    
    with open(strategy_file, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if "# PRICE FIX:" in content:
        print("✅ VIX strategy already patched")
        return
    
    # Find the _calculate_correlations method and add price fix
    old_latest_price_line = "'latest_price': clean_df['close'].iloc[-1] if not clean_df.empty else None"
    
    new_latest_price_section = """# PRICE FIX: Get current price from fresh crypto data if VIX data is stale
        current_price = None
        if not clean_df.empty:
            latest_vix_date = clean_df.iloc[-1]['date_str']
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # If VIX data is more than 2 days old, get fresh crypto price
            from datetime import datetime as dt
            vix_date = dt.strptime(latest_vix_date, '%Y-%m-%d')
            days_old = (dt.now() - vix_date).days
            
            if days_old > 2:
                # Get fresh crypto price from crypto_ohlcv table
                fresh_crypto = self.database.get_crypto_data(asset, days=3)
                if not fresh_crypto.empty:
                    current_price = fresh_crypto['close'].iloc[-1]
                    self.logger.info(f"Using fresh crypto price ${current_price:,.2f} (VIX data {days_old} days old)")
                else:
                    current_price = clean_df['close'].iloc[-1]
            else:
                current_price = clean_df['close'].iloc[-1]
        
        'latest_price': current_price"""
    
    if old_latest_price_line in content:
        # Replace the line
        new_content = content.replace(old_latest_price_line, new_latest_price_section)
        
        # Write back the fixed file
        with open(strategy_file, 'w') as f:
            f.write(new_content)
        
        print("✅ VIX strategy patched to use fresh crypto prices")
        print("📝 The strategy will now use current Bitcoin/Ethereum prices")
        print("   even when VIX data is stale (older than 2 days)")
    else:
        print("❌ Could not find the target line to patch")
        print(f"Looking for: {old_latest_price_line}")

def test_fixed_strategy():
    """Test the fixed strategy"""
    print("\n🧪 Testing Fixed VIX Strategy")
    print("=" * 50)
    
    try:
        config_path = 'config/strategies/vix_correlation.json'
        strategy = VIXCorrelationStrategy(config_path)
        
        results = strategy.analyze({})
        print(f"✅ Analysis completed")
        print(f"Signal opportunities: {len(results.get('signal_opportunities', []))}")
        
        for opp in results.get('signal_opportunities', [])[:2]:  # Show first 2
            print(f"🎯 {opp['asset']}: ${opp['latest_price']:,.2f} ({opp['signal_type']})")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    fix_vix_strategy_pricing()
    test_fixed_strategy()
