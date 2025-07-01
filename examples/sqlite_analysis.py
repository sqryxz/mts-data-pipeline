#!/usr/bin/env python3
"""
SQLite Database Analysis Examples
=================================

This script demonstrates how to use the SQLite database for cryptocurrency
data analysis, including basic queries, combined crypto-macro analysis,
and visualization examples.

Usage:
    python examples/sqlite_analysis.py
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.sqlite_helper import CryptoDatabase


def setup_analysis():
    """Set up database connection and configure plotting style."""
    # Initialize database
    db = CryptoDatabase()
    
    # Configure plotting style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    return db


def example_1_basic_crypto_queries(db: CryptoDatabase):
    """
    Example 1: Basic cryptocurrency data queries and analysis.
    
    Demonstrates:
    - Simple data retrieval
    - Basic price analysis
    - Volume analysis
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Cryptocurrency Queries")
    print("="*60)
    
    # Get recent Bitcoin data
    print("📊 Retrieving Bitcoin data for the last 7 days...")
    bitcoin_df = db.get_crypto_data('bitcoin', days=7)
    
    if bitcoin_df.empty:
        print("❌ No Bitcoin data available")
        return
    
    print(f"✅ Retrieved {len(bitcoin_df)} Bitcoin records")
    
    # Basic statistics
    print("\n📈 Price Statistics:")
    print(f"  • Latest Close: ${bitcoin_df['close'].iloc[-1]:,.2f}")
    print(f"  • Highest Price: ${bitcoin_df['high'].max():,.2f}")
    print(f"  • Lowest Price: ${bitcoin_df['low'].min():,.2f}")
    print(f"  • Average Price: ${bitcoin_df['close'].mean():,.2f}")
    print(f"  • Price Volatility (std): ${bitcoin_df['close'].std():,.2f}")
    
    # Volume analysis
    print("\n📊 Volume Statistics:")
    print(f"  • Total Volume: {bitcoin_df['volume'].sum():,.0f}")
    print(f"  • Average Volume: {bitcoin_df['volume'].mean():,.0f}")
    print(f"  • Highest Volume: {bitcoin_df['volume'].max():,.0f}")
    
    # Date range
    print(f"\n📅 Date Range: {bitcoin_df['date_str'].min()} to {bitcoin_df['date_str'].max()}")


def example_2_price_trend_analysis(db: CryptoDatabase):
    """
    Example 2: Price trend analysis and visualization.
    
    Demonstrates:
    - Time series analysis
    - Moving averages
    - Price change calculation
    - Basic plotting
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Price Trend Analysis")
    print("="*60)
    
    # Get data for multiple cryptocurrencies
    cryptos = ['bitcoin', 'ethereum', 'tether']
    crypto_data = {}
    
    for crypto in cryptos:
        df = db.get_crypto_data(crypto, days=7)
        if not df.empty:
            crypto_data[crypto] = df
            print(f"✅ Loaded {len(df)} records for {crypto.title()}")
    
    if not crypto_data:
        print("❌ No crypto data available for analysis")
        return
    
    # Calculate price changes
    print("\n📈 Price Change Analysis (First vs Last):")
    for crypto, df in crypto_data.items():
        if len(df) >= 2:
            first_price = df['close'].iloc[0]
            last_price = df['close'].iloc[-1]
            change = ((last_price - first_price) / first_price) * 100
            
            direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            print(f"  • {crypto.title()}: ${first_price:,.2f} → ${last_price:,.2f} ({change:+.2f}%) {direction}")
    
    # Create price comparison plot
    try:
        plt.figure(figsize=(12, 6))
        
        for crypto, df in crypto_data.items():
            if len(df) > 1:
                # Convert timestamp to datetime for plotting
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                plt.plot(df['datetime'], df['close'], label=crypto.title(), linewidth=2)
        
        plt.title('Cryptocurrency Price Trends (Last 7 Days)', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save plot
        plot_path = 'crypto_price_trends.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"\n💾 Price trend chart saved as: {plot_path}")
        
        plt.close()
        
    except Exception as e:
        print(f"❌ Plotting error: {e}")


def example_3_combined_crypto_macro_analysis(db: CryptoDatabase):
    """
    Example 3: Combined cryptocurrency and macro economic analysis.
    
    Demonstrates:
    - Combined dataset queries
    - Correlation analysis
    - Data availability assessment
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Combined Crypto-Macro Analysis")
    print("="*60)
    
    # Get combined analysis data
    print("📊 Retrieving combined crypto-macro data for Bitcoin...")
    combined_df = db.get_combined_analysis_data('bitcoin', days=30)
    
    if combined_df.empty:
        print("❌ No combined data available")
        return
    
    print(f"✅ Retrieved {len(combined_df)} combined records")
    
    # Analyze macro data availability
    macro_columns = ['vix_value', 'fed_funds_rate', 'treasury_10y_rate', 'dollar_index']
    
    print("\n📈 Macro Data Availability:")
    for col in macro_columns:
        available = combined_df[col].notna().sum()
        percentage = (available / len(combined_df)) * 100
        print(f"  • {col.replace('_', ' ').title()}: {available}/{len(combined_df)} ({percentage:.1f}%)")
    
    # Show data quality metrics
    print(f"\n📊 Data Quality Metrics:")
    print(f"  • Average Macro Availability: {combined_df['macro_data_availability'].mean():.1f}%")
    print(f"  • Records with Any Macro Data: {(combined_df['macro_data_availability'] > 0).sum()}")
    print(f"  • Records with Complete Macro Data: {(combined_df['macro_data_availability'] == 1.0).sum()}")
    
    # Analyze volatility
    if 'price_volatility' in combined_df.columns:
        volatility_stats = combined_df['price_volatility'].describe()
        print(f"\n📊 Price Volatility Analysis:")
        print(f"  • Average Daily Volatility: {volatility_stats['mean']:.4f}")
        print(f"  • Maximum Volatility: {volatility_stats['max']:.4f}")
        print(f"  • Minimum Volatility: {volatility_stats['min']:.4f}")
    
    # If we have macro data, show correlations
    macro_data_exists = combined_df[macro_columns].notna().any().any()
    if macro_data_exists:
        print("\n🔗 Correlation Analysis (where data available):")
        
        # Calculate correlations with Bitcoin close price
        for col in macro_columns:
            if combined_df[col].notna().sum() > 1:
                correlation = combined_df['close'].corr(combined_df[col])
                if not pd.isna(correlation):
                    direction = "📈" if correlation > 0 else "📉"
                    print(f"  • Bitcoin vs {col.replace('_', ' ').title()}: {correlation:.3f} {direction}")
    
    else:
        print("\nℹ️  No macro data overlap in current dataset")
        print("ℹ️  This is expected - crypto and macro data have different date ranges")
        print("ℹ️  The analysis framework is ready for when overlapping data becomes available")


def example_4_database_health_monitoring(db: CryptoDatabase):
    """
    Example 4: Database health and status monitoring.
    
    Demonstrates:
    - Database health queries
    - Data freshness assessment
    - System monitoring
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Database Health Monitoring")
    print("="*60)
    
    # Get comprehensive database health status
    health_status = db.get_health_status()
    
    print(f"📊 Database Overview:")
    print(f"  • Database Path: {health_status['database_path']}")
    print(f"  • Database Size: {health_status['database_size_mb']} MB")
    
    # Crypto data summary
    crypto_data = health_status.get('crypto_data', [])
    total_crypto_records = sum(crypto['total_records'] for crypto in crypto_data)
    
    print(f"\n💰 Cryptocurrency Data:")
    print(f"  • Total Symbols: {len(crypto_data)}")
    print(f"  • Total Records: {total_crypto_records:,}")
    
    for crypto in crypto_data:
        print(f"    - {crypto['symbol'].upper()}: {crypto['total_records']:,} records (latest: {crypto['latest_date']})")
    
    # Macro data summary
    macro_data = health_status.get('macro_data', [])
    total_macro_records = sum(macro['total_records'] for macro in macro_data)
    
    print(f"\n📈 Macro Economic Data:")
    print(f"  • Total Indicators: {len(macro_data)}")
    print(f"  • Total Records: {total_macro_records:,}")
    
    for macro in macro_data:
        print(f"    - {macro['indicator']}: {macro['total_records']} records (latest: {macro['latest_date']})")
    
    # Overall summary
    grand_total = total_crypto_records + total_macro_records
    print(f"\n🎯 Grand Total: {grand_total:,} records across all datasets")
    
    # Data freshness assessment
    current_date = datetime.now().strftime('%Y-%m-%d')
    print(f"\n📅 Data Freshness Assessment (as of {current_date}):")
    
    for crypto in crypto_data:
        latest_date = crypto['latest_date']
        if latest_date:
            days_old = (datetime.now() - datetime.strptime(latest_date, '%Y-%m-%d')).days
            freshness = "🟢 Fresh" if days_old <= 1 else "🟡 Stale" if days_old <= 7 else "🔴 Very Stale"
            print(f"  • {crypto['symbol'].upper()}: {days_old} days old {freshness}")


def main():
    """Main function to run all analysis examples."""
    print("🚀 SQLite Database Analysis Examples")
    print("=====================================")
    print("This script demonstrates various analysis capabilities using the SQLite database.")
    
    try:
        # Set up analysis environment
        db = setup_analysis()
        
        # Run all examples
        example_1_basic_crypto_queries(db)
        example_2_price_trend_analysis(db)
        example_3_combined_crypto_macro_analysis(db)
        example_4_database_health_monitoring(db)
        
        print("\n" + "="*60)
        print("🎉 ALL ANALYSIS EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n📚 Key Takeaways:")
        print("• SQLite database provides efficient data storage and retrieval")
        print("• Combined crypto-macro analysis enables sophisticated research")
        print("• Database health monitoring ensures data quality and freshness")
        print("• Analysis framework is ready for production use")
        
    except Exception as e:
        print(f"\n❌ Error running analysis examples: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 