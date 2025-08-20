#!/usr/bin/env python3
"""Display today's expanded correlation mosaic analysis."""

import json
import math

def display_expanded_mosaic():
    """Display today's expanded mosaic analysis."""
    try:
        # Load the mosaic data
        with open('data/correlation/mosaics/daily_mosaic_20250810.json', 'r') as f:
            data = json.load(f)
        
        # Display header
        print("🎨 EXPANDED CORRELATION MOSAIC - 2025-08-10")
        print("=" * 60)
        
        # Display summary
        summary = data['correlation_matrix']['summary']
        print(f"📊 Total Pairs Analyzed: {summary['total_pairs']}")
        print(f"🔍 Total Correlations: {summary['total_correlations']}")
        print(f"⭐ Significant Correlations: {summary['significant_correlations']}")
        print(f"📈 Average Correlation Strength: {summary['average_correlation_strength']:.3f}")
        print(f"🔴 Strong Correlations: {summary['strong_correlations']}")
        print(f"🟡 Weak Correlations: {summary['weak_correlations']}")
        print(f"🔵 Negative Correlations: {summary['negative_correlations']}")
        print()
        
        # Display correlations by time window
        print("🔍 CORRELATION BREAKDOWN BY TIME WINDOW:")
        matrix = data['correlation_matrix']['matrix']
        
        # Group by success/failure
        successful_pairs = []
        failed_pairs = []
        
        for pair, windows in matrix.items():
            pair_data = {"pair": pair, "windows": windows}
            has_valid_data = False
            
            for window, stats in windows.items():
                if not math.isnan(stats.get('correlation', float('nan'))):
                    has_valid_data = True
                    break
            
            if has_valid_data:
                successful_pairs.append(pair_data)
            else:
                failed_pairs.append(pair_data)
        
        print(f"✅ Successful pairs ({len(successful_pairs)}):")
        for pair_data in successful_pairs[:5]:  # Show first 5
            pair = pair_data['pair']
            windows = pair_data['windows']
            print(f"  {pair}:")
            for window, stats in windows.items():
                correlation = stats.get('correlation', float('nan'))
                if not math.isnan(correlation):
                    significance = "✅" if stats.get('significance') == "True" else "❌"
                    print(f"    {window}: {correlation:.3f} {significance}")
        
        if len(successful_pairs) > 5:
            print(f"    ... and {len(successful_pairs) - 5} more successful pairs")
        
        if failed_pairs:
            print(f"\n❌ Failed pairs ({len(failed_pairs)}):")
            for pair_data in failed_pairs:
                print(f"  • {pair_data['pair']} (no data available)")
        
        print()
        
        # Display key findings
        print("🎯 KEY FINDINGS:")
        for finding in data['key_findings']:
            print(f"  • {finding}")
        print()
        
        # Display recommendations
        print("💡 RECOMMENDATIONS:")
        for rec in data['recommendations']:
            print(f"  • {rec}")
        print()
        
        # Display metadata
        metadata = data['correlation_matrix']['metadata']
        print("📋 METADATA:")
        print(f"  • Generation Time: {metadata['generation_time']}")
        print(f"  • Processing Time: {metadata['generation_time_seconds']:.3f}s")
        print(f"  • Config Used: {metadata['config_used']}")
        
    except FileNotFoundError:
        print("❌ Mosaic file not found. Please generate a mosaic first:")
        print("   python3 -m src.correlation_analysis --daily")
    except Exception as e:
        print(f"❌ Error reading mosaic: {e}")

if __name__ == "__main__":
    display_expanded_mosaic()
