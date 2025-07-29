#!/usr/bin/env python3
"""
Macro Analytics Runner Script

This script runs macro analytics for the past 6 months and generates
scores for all supported indicators across multiple timeframes.
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

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

def run_macro_analytics():
    """Run macro analytics for the past 6 months."""
    
    print("=" * 80)
    print("MACRO ANALYTICS RUNNER")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Import the service
        from services.macro_analytics_service import MacroAnalyticsService
        
        # Initialize the service
        print("Initializing Macro Analytics Service...")
        service = MacroAnalyticsService()
        
        # Get supported indicators
        indicators = service.get_supported_indicators()
        print(f"Supported indicators: {indicators}")
        
        # Get default timeframes
        timeframes = service.get_default_timeframes()
        print(f"Default timeframes: {timeframes}")
        
        # Get calculation settings
        roc_settings = service.get_calculation_settings('roc')
        z_score_settings = service.get_calculation_settings('z_score')
        print(f"ROC settings: {roc_settings}")
        print(f"Z-Score settings: {z_score_settings}")
        
        print()
        print("=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        
        # Run analysis for each indicator
        all_results = {}
        
        for indicator in indicators:
            print(f"\n📊 Analyzing {indicator}...")
            
            try:
                # Get indicator alias
                alias = service.get_indicator_alias(indicator)
                print(f"   Indicator: {indicator} ({alias})")
                
                # Run analysis
                result = service.analyze_indicator(
                    indicator=indicator,
                    timeframes=timeframes,
                    save_results=True  # Save to database
                )
                
                if result is not None:
                    all_results[indicator] = result
                    
                    # Display results
                    print(f"   ✅ Analysis completed successfully")
                    
                    # Show timeframe results
                    results = result.get('results', {})
                    for timeframe, timeframe_result in results.items():
                        calculations = timeframe_result.get('calculations', {})
                        
                        print(f"   📈 {timeframe}:")
                        for metric, metric_data in calculations.items():
                            value = metric_data.get('data', 'N/A')
                            print(f"      {metric}: {value}")
                    
                    # Show service metadata
                    service_info = result.get('service_info', {})
                    if service_info:
                        print(f"   📋 Analysis time: {service_info.get('analysis_time', 'N/A')}")
                        print(f"   📋 Config version: {service_info.get('config_version', 'N/A')}")
                        print(f"   📋 Saved to database: {result.get('saved_to_database', False)}")
                
                else:
                    print(f"   ❌ Analysis failed for {indicator}")
                    
            except Exception as e:
                print(f"   ❌ Error analyzing {indicator}: {e}")
                logger.error(f"Error analyzing {indicator}: {e}")
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        # Generate summary
        successful_indicators = list(all_results.keys())
        failed_indicators = [ind for ind in indicators if ind not in successful_indicators]
        
        print(f"✅ Successful analyses: {len(successful_indicators)}")
        if successful_indicators:
            print(f"   Indicators: {', '.join(successful_indicators)}")
        
        if failed_indicators:
            print(f"❌ Failed analyses: {len(failed_indicators)}")
            print(f"   Indicators: {', '.join(failed_indicators)}")
        
        # Generate detailed report
        print()
        print("=" * 80)
        print("DETAILED REPORT")
        print("=" * 80)
        
        for indicator, result in all_results.items():
            print(f"\n📊 {indicator} Analysis Report")
            print("-" * 40)
            
            alias = service.get_indicator_alias(indicator)
            print(f"Indicator: {indicator} ({alias})")
            
            results = result.get('results', {})
            for timeframe, timeframe_result in results.items():
                print(f"\n  📈 {timeframe} Timeframe:")
                calculations = timeframe_result.get('calculations', {})
                
                for metric, metric_data in calculations.items():
                    value = metric_data.get('data', 'N/A')
                    print(f"    {metric.upper()}: {value}")
            
            # Show metadata
            service_info = result.get('service_info', {})
            if service_info:
                print(f"\n  📋 Metadata:")
                print(f"    Analysis time: {service_info.get('analysis_time', 'N/A')}")
                print(f"    Requested timeframes: {service_info.get('requested_timeframes', [])}")
                print(f"    Config version: {service_info.get('config_version', 'N/A')}")
                print(f"    Saved to database: {result.get('saved_to_database', False)}")
        
        # Save results to JSON file
        output_file = f"macro_analytics_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        print(f"\n💾 Saving results to: {output_file}")
        
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"✅ Results saved to {output_file}")
        
        print()
        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Fatal error in macro analytics runner: {e}")
        return False


def main():
    """Main entry point."""
    print("🚀 Starting Macro Analytics Runner")
    print("📅 Analysis period: Past 6 months")
    print("📊 Indicators: VIX, DGS10, DTWEXBGS, DFF")
    print("⏱️  Timeframes: 1h, 4h, 1d, 1w, 1m")
    print("📈 Metrics: ROC, Z-Score")
    print()
    
    success = run_macro_analytics()
    
    if success:
        print("✅ Macro analytics completed successfully!")
        sys.exit(0)
    else:
        print("❌ Macro analytics failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 