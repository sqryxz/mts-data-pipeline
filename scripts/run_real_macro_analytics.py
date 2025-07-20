#!/usr/bin/env python3
"""
Enhanced Real Macro Analytics Runner Script

This script runs macro analytics using real data with enhanced rate-of-change
calculations and z-score analysis for regime detection and high-conviction signals.
"""

import sys
import os
import json
import logging
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from enum import Enum

# Add src to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RegimeStatus(Enum):
    """Enum for regime status classification."""
    EXTREME_FEAR = "extreme_fear"
    FEAR = "fear"
    NEUTRAL = "neutral"
    GREED = "greed"
    EXTREME_GREED = "extreme_greed"
    BULLISH_ACCELERATION = "bullish_acceleration"
    BULLISH_DECELERATION = "bullish_deceleration"
    BEARISH_ACCELERATION = "bearish_acceleration"
    BEARISH_DECELERATION = "bearish_deceleration"
    COMPRESSED = "compressed"
    EXPANDING = "expanding"

class MomentumStatus(Enum):
    """Enum for momentum status classification."""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    WEAK_BULLISH = "weak_bullish"
    NEUTRAL = "neutral"
    WEAK_BEARISH = "weak_bearish"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"

def get_available_indicators_from_db(db_path: str = "data/crypto_data.db") -> List[str]:
    """
    Query SQLite database to get all available macro indicators.
    
    Args:
        db_path: Path to the SQLite database
        
    Returns:
        List of available indicator names
    """
    if not os.path.exists(db_path):
        logger.warning(f"Database not found at {db_path}")
        return []
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT indicator FROM macro_indicators ORDER BY indicator")
            indicators = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found {len(indicators)} indicators in database: {indicators}")
            return indicators
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return []

def load_macro_data_from_db(indicator: str, db_path: str = "data/crypto_data.db") -> pd.DataFrame:
    """
    Load macro data from SQLite database.
    
    Args:
        indicator: Indicator name
        db_path: Path to the SQLite database
        
    Returns:
        DataFrame with date and value columns
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    try:
        # Calculate date range for past 6 months (180 days)
        six_months_ago = datetime.now() - timedelta(days=180)
        start_date = six_months_ago.strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Query database
        with sqlite3.connect(db_path) as conn:
            query = """
            SELECT date, value
            FROM macro_indicators
            WHERE indicator = ? AND date >= ? AND date <= ?
            ORDER BY date ASC
            """
            df = pd.read_sql_query(query, conn, params=(indicator, start_date, end_date))
        
        if df.empty:
            logger.warning(f"No data found for {indicator} in the specified date range")
            return pd.DataFrame()
        
        # Convert date column
        df['date'] = pd.to_datetime(df['date'])
        
        # Handle missing values
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # Forward fill missing values
        df['value'] = df['value'].ffill()
        
        # Drop rows with still missing values
        df = df.dropna(subset=['value'])
        
        logger.info(f"Loaded {len(df)} records for {indicator} from {df['date'].min()} to {df['date'].max()}")
        
        return df[['date', 'value']].reset_index(drop=True)
        
    except sqlite3.Error as e:
        logger.error(f"Database error loading {indicator}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading {indicator}: {e}")
        return pd.DataFrame()

def load_macro_data(indicator: str) -> pd.DataFrame:
    """
    Load macro data from CSV files (legacy method).
    
    Args:
        indicator: Indicator name (VIX, DGS10, DTWEXBGS, DFF)
        
    Returns:
        DataFrame with date and value columns
    """
    # Map indicators to file names
    file_mapping = {
        'VIX': 'vixcls_2025.csv',
        'DGS10': 'dgs10_2025.csv',
        'DTWEXBGS': 'dtwexbgs_2025.csv',
        'DFF': 'dff_2025.csv'
    }
    
    if indicator not in file_mapping:
        raise ValueError(f"Unsupported indicator: {indicator}")
    
    file_path = os.path.join(project_root, 'data', 'raw', 'macro', file_mapping[indicator])
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    # Load CSV data
    df = pd.read_csv(file_path)
    
    # Convert date column
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter for past 6 months
    six_months_ago = datetime.now() - timedelta(days=180)
    df = df[df['date'] >= six_months_ago]
    
    # Sort by date
    df = df.sort_values('date')
    
    # Handle missing values
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    
    # Forward fill missing values
    df['value'] = df['value'].ffill()
    
    # Drop rows with still missing values
    df = df.dropna(subset=['value'])
    
    return df[['date', 'value']].reset_index(drop=True)

def calculate_roc(series: pd.Series, periods: int = 1) -> float:
    """
    Calculate Rate of Change.
    
    Args:
        series: Pandas Series with values
        periods: Number of periods to look back
        
    Returns:
        float: Rate of change
    """
    if len(series) < periods + 1:
        return 0.0
    
    current_value = series.iloc[-1]
    previous_value = series.iloc[-periods-1]
    
    if previous_value == 0:
        return 0.0
    
    return (current_value - previous_value) / previous_value

def calculate_z_score(series: pd.Series, window: int = 30) -> float:
    """
    Calculate Z-Score.
    
    Args:
        series: Pandas Series with values
        window: Rolling window size
        
    Returns:
        float: Z-Score
    """
    if len(series) < window:
        return 0.0
    
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    
    if len(rolling_mean) == 0 or rolling_std.iloc[-1] == 0:
        return 0.0
    
    current_value = series.iloc[-1]
    current_mean = rolling_mean.iloc[-1]
    current_std = rolling_std.iloc[-1]
    
    return (current_value - current_mean) / current_std

def classify_regime_status(indicator: str, z_score_30d: float, z_score_90d: float, 
                         roc_1d: float, roc_7d: float, roc_30d: float) -> Dict[str, str]:
    """
    Classify regime status based on indicator-specific thresholds.
    
    Args:
        indicator: Indicator name
        z_score_30d: 30-day z-score
        z_score_90d: 90-day z-score
        roc_1d: 1-day rate of change
        roc_7d: 7-day rate of change
        roc_30d: 30-day rate of change
        
    Returns:
        Dict with regime classifications
    """
    regime_info = {}
    
    # VIX-specific regime classification
    if indicator == 'VIXCLS':
        # VIX regime based on 30-day z-score
        if z_score_30d >= 2.0:
            regime_info['VIX_regime'] = RegimeStatus.EXTREME_FEAR.value
        elif z_score_30d >= 1.0:
            regime_info['VIX_regime'] = RegimeStatus.FEAR.value
        elif z_score_30d >= -1.0:
            regime_info['VIX_regime'] = RegimeStatus.NEUTRAL.value
        elif z_score_30d >= -2.0:
            regime_info['VIX_regime'] = RegimeStatus.GREED.value
        else:
            regime_info['VIX_regime'] = RegimeStatus.EXTREME_GREED.value
        
        # VIX momentum classification
        if roc_7d > 0.1:  # 10% weekly increase
            regime_info['VIX_momentum'] = MomentumStatus.STRONG_BULLISH.value
        elif roc_7d > 0.05:  # 5% weekly increase
            regime_info['VIX_momentum'] = MomentumStatus.BULLISH.value
        elif roc_7d > 0.02:  # 2% weekly increase
            regime_info['VIX_momentum'] = MomentumStatus.WEAK_BULLISH.value
        elif roc_7d > -0.02:  # -2% to 2% weekly change
            regime_info['VIX_momentum'] = MomentumStatus.NEUTRAL.value
        elif roc_7d > -0.05:  # -5% weekly decrease
            regime_info['VIX_momentum'] = MomentumStatus.WEAK_BEARISH.value
        elif roc_7d > -0.1:  # -10% weekly decrease
            regime_info['VIX_momentum'] = MomentumStatus.BEARISH.value
        else:
            regime_info['VIX_momentum'] = MomentumStatus.STRONG_BEARISH.value
    
    # DXY (DTWEXBGS) momentum classification
    elif indicator == 'DTWEXBGS':
        if roc_7d > 0.02:  # 2% weekly increase
            regime_info['DXY_momentum'] = MomentumStatus.BULLISH_ACCELERATION.value
        elif roc_7d > 0.01:  # 1% weekly increase
            regime_info['DXY_momentum'] = MomentumStatus.BULLISH.value
        elif roc_7d > -0.01:  # -1% to 1% weekly change
            regime_info['DXY_momentum'] = MomentumStatus.NEUTRAL.value
        elif roc_7d > -0.02:  # -2% weekly decrease
            regime_info['DXY_momentum'] = MomentumStatus.BEARISH.value
        else:
            regime_info['DXY_momentum'] = MomentumStatus.BEARISH_ACCELERATION.value
    
    # Treasury yields (DGS10) regime classification
    elif indicator == 'DGS10':
        if z_score_30d >= 1.5:
            regime_info['TREASURY_regime'] = RegimeStatus.EXPANDING.value
        elif z_score_30d <= -1.5:
            regime_info['TREASURY_regime'] = RegimeStatus.COMPRESSED.value
        else:
            regime_info['TREASURY_regime'] = RegimeStatus.NEUTRAL.value
    
    # Fed Funds Rate (DFF) regime classification
    elif indicator == 'DFF':
        if abs(roc_30d) < 0.001:  # Very stable
            regime_info['FED_regime'] = RegimeStatus.COMPRESSED.value
        else:
            regime_info['FED_regime'] = RegimeStatus.EXPANDING.value
    
    # Credit spreads (BAMLH0A0HYM2) regime classification
    elif indicator == 'BAMLH0A0HYM2':
        if z_score_30d >= 1.5:
            regime_info['CREDIT_regime'] = RegimeStatus.EXTREME_FEAR.value
        elif z_score_30d >= 0.5:
            regime_info['CREDIT_regime'] = RegimeStatus.FEAR.value
        elif z_score_30d >= -0.5:
            regime_info['CREDIT_regime'] = RegimeStatus.NEUTRAL.value
        else:
            regime_info['CREDIT_regime'] = RegimeStatus.GREED.value
    
    # SOFR regime classification
    elif indicator == 'SOFR':
        if abs(roc_7d) < 0.001:  # Very stable
            regime_info['SOFR_regime'] = RegimeStatus.COMPRESSED.value
        else:
            regime_info['SOFR_regime'] = RegimeStatus.EXPANDING.value
    
    return regime_info

def analyze_indicator_enhanced(indicator: str, use_db: bool = True) -> Dict[str, Any]:
    """
    Analyze an indicator using enhanced rate-of-change and z-score calculations.
    
    Args:
        indicator: Indicator name
        use_db: Whether to use database (True) or CSV files (False)
        
    Returns:
        Dict with enhanced analysis results
    """
    print(f"📊 Analyzing {indicator} with enhanced calculations...")
    
    try:
        # Load data
        if use_db:
            df = load_macro_data_from_db(indicator)
        else:
            df = load_macro_data(indicator)
        
        if len(df) == 0:
            print(f"   ❌ No data available for {indicator}")
            return None
        
        print(f"   📈 Loaded {len(df)} data points")
        print(f"   📅 Date range: {df['date'].min()} to {df['date'].max()}")
        
        # Calculate enhanced metrics
        values = df['value']
        
        # Rate of Change calculations (1d, 7d, 30d, 90d)
        roc_1d = calculate_roc(values, 1)
        roc_7d = calculate_roc(values, 7)
        roc_30d = calculate_roc(values, 30)
        roc_90d = calculate_roc(values, 90)
        
        # Z-Score calculations (30d, 90d)
        z_score_30d = calculate_z_score(values, 30)
        z_score_90d = calculate_z_score(values, 90)
        
        # Classify regime status
        regime_info = classify_regime_status(indicator, z_score_30d, z_score_90d, 
                                          roc_1d, roc_7d, roc_30d)
        
        # Create enhanced result structure
        indicator_aliases = {
            'VIXCLS': 'CBOE Volatility Index',
            'DGS10': '10-Year Treasury Constant Maturity Rate',
            'DTWEXBGS': 'Trade Weighted U.S. Dollar Index',
            'DFF': 'Federal Funds Effective Rate',
            'DEXUSEU': 'USD/EUR Exchange Rate',
            'DEXCHUS': 'China/US Exchange Rate',
            'BAMLH0A0HYM2': 'High Yield Credit Spreads',
            'RRPONTSYD': 'Overnight Reverse Repo',
            'SOFR': 'Secured Overnight Financing Rate'
        }
        
        result = {
            'indicator': indicator,
            'alias': indicator_aliases.get(indicator, indicator),
            'data_source': 'database' if use_db else 'csv',
            'analysis_time': datetime.now().isoformat(),
            'metrics': {
                'rate_of_change': {
                    '1d': round(roc_1d, 4),
                    '7d': round(roc_7d, 4),
                    '30d': round(roc_30d, 4),
                    '90d': round(roc_90d, 4)
                },
                'z_scores': {
                    '30d': round(z_score_30d, 4),
                    '90d': round(z_score_90d, 4)
                }
            },
            'regime_status': regime_info,
            'data_summary': {
                'total_data_points': len(df),
                'date_range_start': df['date'].min().isoformat(),
                'date_range_end': df['date'].max().isoformat(),
                'current_value': float(df['value'].iloc[-1]),
                'current_date': df['date'].iloc[-1].isoformat(),
                'min_value': float(df['value'].min()),
                'max_value': float(df['value'].max()),
                'mean_value': float(df['value'].mean()),
                'std_value': float(df['value'].std())
            },
            'signal_strength': calculate_signal_strength(indicator, z_score_30d, roc_7d, roc_30d)
        }
        
        print(f"   ✅ 1d ROC: {roc_1d:.4f}, 7d ROC: {roc_7d:.4f}, 30d ROC: {roc_30d:.4f}")
        print(f"   ✅ 30d Z-Score: {z_score_30d:.4f}, 90d Z-Score: {z_score_90d:.4f}")
        if regime_info:
            for key, value in regime_info.items():
                print(f"   ✅ {key}: {value}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Error analyzing {indicator}: {e}")
        logger.error(f"Error analyzing {indicator}: {e}")
        return None

def calculate_signal_strength(indicator: str, z_score_30d: float, roc_7d: float, roc_30d: float) -> Dict[str, Any]:
    """
    Calculate signal strength for high-conviction signals.
    
    Args:
        indicator: Indicator name
        z_score_30d: 30-day z-score
        roc_7d: 7-day rate of change
        roc_30d: 30-day rate of change
        
    Returns:
        Dict with signal strength information
    """
    signal_info = {
        'strength': 'low',
        'confidence': 0.0,
        'description': '',
        'timeframe': 'none'
    }
    
    # VIX-specific signal logic
    if indicator == 'VIXCLS':
        if z_score_30d >= 2.0 and roc_7d > 0.05:
            signal_info.update({
                'strength': 'high',
                'confidence': 0.9,
                'description': 'VIX extreme fear with accelerating momentum - potential crypto reversal signal',
                'timeframe': '1-2 weeks'
            })
        elif z_score_30d >= 1.5 and roc_7d > 0.02:
            signal_info.update({
                'strength': 'medium',
                'confidence': 0.7,
                'description': 'VIX elevated fear with positive momentum',
                'timeframe': '1 week'
            })
        elif z_score_30d <= -2.0 and roc_7d < -0.05:
            signal_info.update({
                'strength': 'high',
                'confidence': 0.8,
                'description': 'VIX extreme greed with accelerating decline - potential risk-on signal',
                'timeframe': '1-2 weeks'
            })
    
    # DXY-specific signal logic
    elif indicator == 'DTWEXBGS':
        if roc_7d > 0.02 and roc_30d > 0.05:
            signal_info.update({
                'strength': 'high',
                'confidence': 0.8,
                'description': 'DXY strong bullish acceleration - potential crypto headwind',
                'timeframe': '1-2 weeks'
            })
        elif roc_7d < -0.02 and roc_30d < -0.05:
            signal_info.update({
                'strength': 'high',
                'confidence': 0.8,
                'description': 'DXY strong bearish acceleration - potential crypto tailwind',
                'timeframe': '1-2 weeks'
            })
    
    # Treasury yields signal logic
    elif indicator == 'DGS10':
        if z_score_30d >= 1.5 and roc_30d > 0.02:
            signal_info.update({
                'strength': 'medium',
                'confidence': 0.6,
                'description': 'Treasury yields expanding - potential risk-off pressure',
                'timeframe': '1-3 weeks'
            })
        elif z_score_30d <= -1.5 and roc_30d < -0.02:
            signal_info.update({
                'strength': 'medium',
                'confidence': 0.6,
                'description': 'Treasury yields compressing - potential risk-on support',
                'timeframe': '1-3 weeks'
            })
    
    # Credit spreads signal logic
    elif indicator == 'BAMLH0A0HYM2':
        if z_score_30d >= 1.5:
            signal_info.update({
                'strength': 'high',
                'confidence': 0.8,
                'description': 'Credit spreads widening - significant risk-off signal',
                'timeframe': '1-2 weeks'
            })
        elif z_score_30d <= -1.0:
            signal_info.update({
                'strength': 'medium',
                'confidence': 0.6,
                'description': 'Credit spreads compressing - risk-on signal',
                'timeframe': '1-2 weeks'
            })
    
    return signal_info

def run_enhanced_macro_analytics(use_db: bool = True):
    """Run enhanced macro analytics with regime detection and signal strength."""
    
    print("=" * 80)
    print("ENHANCED MACRO ANALYTICS RUNNER")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data source: {'SQLite Database' if use_db else 'CSV Files'}")
    print()
    
    # Get available indicators
    if use_db:
        indicators = get_available_indicators_from_db()
        if not indicators:
            print("❌ No indicators found in database. Falling back to CSV files...")
            use_db = False
            indicators = ['VIX', 'DGS10', 'DTWEXBGS', 'DFF']  # Fallback to hardcoded list
    else:
        indicators = ['VIX', 'DGS10', 'DTWEXBGS', 'DFF']  # Legacy CSV indicators
    
    print("📊 Available indicators:")
    for indicator in indicators:
        print(f"   - {indicator}")
    
    print()
    print("⏱️  Enhanced Timeframes:")
    print("   - Rate of Change: 1d, 7d, 30d, 90d")
    print("   - Z-Scores: 30d, 90d")
    
    print()
    print("📈 Regime Detection:")
    print("   - VIX: Extreme Fear/Greed classification")
    print("   - DXY: Momentum acceleration/deceleration")
    print("   - Treasury: Yield curve compression/expansion")
    print("   - Credit: Spread widening/compression")
    
    print()
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    
    # Run analysis for each indicator
    all_results = {}
    high_conviction_signals = []
    
    for indicator in indicators:
        result = analyze_indicator_enhanced(indicator, use_db)
        
        if result is not None:
            all_results[indicator] = result
            
            # Track high-conviction signals
            signal_strength = result.get('signal_strength', {})
            if signal_strength.get('strength') in ['high', 'medium']:
                high_conviction_signals.append({
                    'indicator': indicator,
                    'strength': signal_strength.get('strength'),
                    'confidence': signal_strength.get('confidence'),
                    'description': signal_strength.get('description'),
                    'timeframe': signal_strength.get('timeframe')
                })
            
            print(f"   ✅ Analysis completed for {indicator}")
        else:
            print(f"   ❌ Analysis failed for {indicator}")
        
        print()
    
    # Generate summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    successful_indicators = list(all_results.keys())
    failed_indicators = [ind for ind in indicators if ind not in successful_indicators]
    
    print(f"✅ Successful analyses: {len(successful_indicators)}")
    if successful_indicators:
        print(f"   Indicators: {', '.join(successful_indicators)}")
    
    if failed_indicators:
        print(f"❌ Failed analyses: {len(failed_indicators)}")
        print(f"   Indicators: {', '.join(failed_indicators)}")
    
    print(f"🎯 High-conviction signals: {len(high_conviction_signals)}")
    for signal in high_conviction_signals:
        print(f"   - {signal['indicator']}: {signal['strength']} confidence ({signal['confidence']:.1%})")
        print(f"     {signal['description']} ({signal['timeframe']})")
    
    # Generate detailed report
    print()
    print("=" * 80)
    print("DETAILED REPORT")
    print("=" * 80)
    
    for indicator, result in all_results.items():
        print(f"\n📊 {indicator} Enhanced Analysis Report")
        print("-" * 50)
        
        alias = result.get('alias', indicator)
        data_source = result.get('data_source', 'unknown')
        print(f"Indicator: {indicator} ({alias})")
        print(f"Data Source: {data_source}")
        
        # Show metrics
        metrics = result.get('metrics', {})
        roc_metrics = metrics.get('rate_of_change', {})
        z_score_metrics = metrics.get('z_scores', {})
        
        print(f"\n📈 Rate of Change Metrics:")
        print(f"   1d ROC: {roc_metrics.get('1d', 'N/A')}")
        print(f"   7d ROC: {roc_metrics.get('7d', 'N/A')}")
        print(f"   30d ROC: {roc_metrics.get('30d', 'N/A')}")
        print(f"   90d ROC: {roc_metrics.get('90d', 'N/A')}")
        
        print(f"\n📊 Z-Score Metrics:")
        print(f"   30d Z-Score: {z_score_metrics.get('30d', 'N/A')}")
        print(f"   90d Z-Score: {z_score_metrics.get('90d', 'N/A')}")
        
        # Show regime status
        regime_status = result.get('regime_status', {})
        if regime_status:
            print(f"\n🎯 Regime Status:")
            for key, value in regime_status.items():
                print(f"   {key}: {value}")
        
        # Show signal strength
        signal_strength = result.get('signal_strength', {})
        if signal_strength.get('strength') != 'low':
            print(f"\n🚨 Signal Alert:")
            print(f"   Strength: {signal_strength.get('strength', 'N/A')}")
            print(f"   Confidence: {signal_strength.get('confidence', 0):.1%}")
            print(f"   Description: {signal_strength.get('description', 'N/A')}")
            print(f"   Timeframe: {signal_strength.get('timeframe', 'N/A')}")
        
        # Show data summary
        data_summary = result.get('data_summary', {})
        print(f"\n📋 Data Summary:")
        print(f"   Total data points: {data_summary.get('total_data_points', 'N/A')}")
        print(f"   Current value: {data_summary.get('current_value', 'N/A')}")
        print(f"   Current date: {data_summary.get('current_date', 'N/A')}")
        print(f"   Value range: {data_summary.get('min_value', 'N/A')} to {data_summary.get('max_value', 'N/A')}")
        print(f"   Mean: {data_summary.get('mean_value', 'N/A')}")
        print(f"   Std Dev: {data_summary.get('std_value', 'N/A')}")
    
    # Save results to JSON file
    output_file = f"enhanced_macro_analytics_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"\n💾 Saving results to: {output_file}")
    
    # Prepare final output structure
    final_output = {
        'metadata': {
            'analysis_time': datetime.now().isoformat(),
            'data_source': 'database' if use_db else 'csv',
            'total_indicators': len(successful_indicators),
            'high_conviction_signals': len(high_conviction_signals)
        },
        'results': all_results,
        'high_conviction_signals': high_conviction_signals
    }
    
    with open(output_file, 'w') as f:
        json.dump(final_output, f, indent=2, default=str)
    
    print(f"✅ Results saved to {output_file}")
    
    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True

def main():
    """Main entry point."""
    print("🚀 Starting Enhanced Macro Analytics Runner")
    print("📅 Analysis period: Past 6 months")
    print("📊 Data source: SQLite Database (with CSV fallback)")
    print("⏱️  Enhanced timeframes: 1d, 7d, 30d, 90d ROC + 30d, 90d Z-Scores")
    print("🎯 Focus: High-conviction regime detection signals")
    print()
    
    success = run_enhanced_macro_analytics(use_db=True)
    
    if success:
        print("✅ Enhanced macro analytics completed successfully!")
        sys.exit(0)
    else:
        print("❌ Enhanced macro analytics failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 