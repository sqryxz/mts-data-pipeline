#!/usr/bin/env python3
"""Display today's correlation mosaic analysis."""

import json
from datetime import datetime

def display_mosaic():
    """Display today's mosaic analysis."""
    try:
        # Load the mosaic data
        with open('data/correlation/mosaics/daily_mosaic_20250810.json', 'r') as f:
            data = json.load(f)
        
        # Display header
        print("🎨 TODAY'S CORRELATION MOSAIC - 2025-08-10")
        print("=" * 50)
        
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
        for pair, windows in data['correlation_matrix']['matrix'].items():
            print(f"  {pair}:")
            for window, stats in windows.items():
                significance = "✅" if stats['significance'] == "True" else "❌"
                correlation = stats['correlation']
                p_value = stats['p_value']
                print(f"    {window}: {correlation:.3f} {significance} (p={p_value:.3e})")
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
    display_mosaic()
