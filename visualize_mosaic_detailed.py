#!/usr/bin/env python3
"""Detailed visualization of correlation mosaic data with insights."""

import json
import pandas as pd
import numpy as np
from tabulate import tabulate
from datetime import datetime

def load_mosaic_data(file_path):
    """Load mosaic data from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Mosaic file not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error loading mosaic file: {e}")
        return None

def create_detailed_correlation_table(mosaic_data):
    """Create a detailed correlation table with insights."""
    if not mosaic_data:
        return None
    
    matrix = mosaic_data.get('correlation_matrix', {}).get('matrix', {})
    correlation_windows = mosaic_data.get('correlation_matrix', {}).get('correlation_windows', [])
    
    table_data = []
    
    for pair, windows in matrix.items():
        row = {'Pair': pair}
        
        # Track if this pair has any significant correlations
        has_significant = False
        strongest_correlation = 0.0
        strongest_window = ''
        
        for window in correlation_windows:
            window_key = f'{window}d'
            if window_key in windows:
                correlation = windows[window_key].get('correlation', np.nan)
                significance = windows[window_key].get('significance', False)
                
                if not np.isnan(correlation):
                    # Track strongest correlation
                    if abs(correlation) > abs(strongest_correlation):
                        strongest_correlation = correlation
                        strongest_window = window_key
                    
                    if significance == "True":
                        has_significant = True
                    
                    # Color code based on correlation strength
                    if abs(correlation) >= 0.7:
                        strength_indicator = "🔥"  # Strong
                    elif abs(correlation) >= 0.5:
                        strength_indicator = "⚡"  # Moderate
                    elif abs(correlation) >= 0.3:
                        strength_indicator = "⚪"  # Weak
                    else:
                        strength_indicator = "🔘"  # Very weak
                    
                    significance_symbol = "✅" if significance == "True" else "❌"
                    row[window_key] = f"{correlation:.3f} {strength_indicator}{significance_symbol}"
                else:
                    row[window_key] = 'N/A'
            else:
                row[window_key] = 'N/A'
        
        # Add strongest correlation info
        if strongest_correlation != 0.0:
            row['Strongest'] = f"{strongest_correlation:.3f} ({strongest_window})"
        else:
            row['Strongest'] = 'N/A'
        
        # Add significance indicator
        row['Significant'] = "✅" if has_significant else "❌"
        
        table_data.append(row)
    
    return pd.DataFrame(table_data)

def create_insights_table(mosaic_data):
    """Create insights table highlighting key findings."""
    if not mosaic_data:
        return None
    
    matrix = mosaic_data.get('correlation_matrix', {}).get('matrix', {})
    correlation_windows = mosaic_data.get('correlation_matrix', {}).get('correlation_windows', [])
    
    insights = []
    
    # Find strongest correlations
    all_correlations = []
    for pair, windows in matrix.items():
        for window in correlation_windows:
            window_key = f'{window}d'
            if window_key in windows:
                correlation = windows[window_key].get('correlation', np.nan)
                significance = windows[window_key].get('significance', False)
                if not np.isnan(correlation) and significance == "True":
                    all_correlations.append({
                        'pair': pair,
                        'window': window_key,
                        'correlation': correlation,
                        'abs_correlation': abs(correlation)
                    })
    
    # Sort by absolute correlation strength
    all_correlations.sort(key=lambda x: x['abs_correlation'], reverse=True)
    
    # Top 5 strongest correlations
    insights.append(['Top 5 Strongest Correlations', ''])
    for i, corr in enumerate(all_correlations[:5], 1):
        direction = "Positive" if corr['correlation'] > 0 else "Negative"
        insights.append([f"{i}. {corr['pair']} ({corr['window']})", f"{corr['correlation']:.3f} ({direction})"])
    
    insights.append(['', ''])  # Empty row for spacing
    
    # Strongest positive and negative correlations
    positive_corrs = [c for c in all_correlations if c['correlation'] > 0]
    negative_corrs = [c for c in all_correlations if c['correlation'] < 0]
    
    if positive_corrs:
        strongest_positive = positive_corrs[0]
        insights.append(['Strongest Positive Correlation', f"{strongest_positive['pair']} ({strongest_positive['window']}): {strongest_positive['correlation']:.3f}"])
    
    if negative_corrs:
        strongest_negative = negative_corrs[0]
        insights.append(['Strongest Negative Correlation', f"{strongest_negative['pair']} ({strongest_negative['window']}): {strongest_negative['correlation']:.3f}"])
    
    return pd.DataFrame(insights, columns=['Insight', 'Value'])

def visualize_mosaic_detailed(file_path='data/correlation/mosaics/daily_mosaic_20250810.json'):
    """Visualize mosaic data in detailed table format."""
    print("🎨 DETAILED CORRELATION MOSAIC VISUALIZATION")
    print("=" * 60)
    
    # Load mosaic data
    mosaic_data = load_mosaic_data(file_path)
    if not mosaic_data:
        return
    
    # Display basic info
    generation_date = mosaic_data.get('generation_date', 'Unknown')
    print(f"📅 Generation Date: {generation_date}")
    print()
    
    # Create and display summary table
    print("📊 SUMMARY STATISTICS")
    print("-" * 40)
    summary_data = [
        ['Total Pairs Analyzed', mosaic_data['correlation_matrix']['summary']['total_pairs']],
        ['Total Correlations', mosaic_data['correlation_matrix']['summary']['total_correlations']],
        ['Significant Correlations', mosaic_data['correlation_matrix']['summary']['significant_correlations']],
        ['Average Correlation Strength', f"{mosaic_data['correlation_matrix']['summary']['average_correlation_strength']:.3f}"],
        ['Strong Correlations (|r| ≥ 0.7)', mosaic_data['correlation_matrix']['summary']['strong_correlations']],
        ['Weak Correlations', mosaic_data['correlation_matrix']['summary']['weak_correlations']],
        ['Negative Correlations', mosaic_data['correlation_matrix']['summary']['negative_correlations']]
    ]
    summary_table = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
    print(tabulate(summary_table, headers='keys', tablefmt='grid', showindex=False))
    print()
    
    # Display insights table
    print("🎯 KEY INSIGHTS")
    print("-" * 40)
    insights_table = create_insights_table(mosaic_data)
    if insights_table is not None:
        print(tabulate(insights_table, headers='keys', tablefmt='grid', showindex=False))
        print()
    
    # Display detailed correlation table
    print("🔍 DETAILED CORRELATION MATRIX")
    print("-" * 40)
    print("Legend: 🔥 Strong (|r| ≥ 0.7) | ⚡ Moderate (|r| ≥ 0.5) | ⚪ Weak (|r| ≥ 0.3) | 🔘 Very Weak (|r| < 0.3)")
    print("       ✅ Significant | ❌ Not Significant")
    print()
    
    correlation_table = create_detailed_correlation_table(mosaic_data)
    if correlation_table is not None:
        # Reorder columns for better readability
        columns = ['Pair', '7d', '14d', '30d', '60d', 'Strongest', 'Significant']
        correlation_table = correlation_table[columns]
        
        print(tabulate(correlation_table, headers='keys', tablefmt='grid', showindex=False))
        print()
    
    # Display key findings
    print("🎯 KEY FINDINGS")
    print("-" * 40)
    key_findings = mosaic_data.get('key_findings', [])
    for i, finding in enumerate(key_findings, 1):
        print(f"{i}. {finding}")
    print()
    
    # Display recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 40)
    recommendations = mosaic_data.get('recommendations', [])
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    print()
    
    # Display metadata
    print("📋 METADATA")
    print("-" * 40)
    metadata = mosaic_data.get('correlation_matrix', {}).get('metadata', {})
    if metadata:
        for key, value in metadata.items():
            if key == 'generation_time':
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"• {key.replace('_', ' ').title()}: {formatted_time}")
                except:
                    print(f"• {key.replace('_', ' ').title()}: {value}")
            elif key == 'generation_time_seconds':
                print(f"• {key.replace('_', ' ').title()}: {value:.3f}s")
            else:
                print(f"• {key.replace('_', ' ').title()}: {value}")

def main():
    """Main function to run detailed visualization."""
    import sys
    
    # Check if file path is provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = 'data/correlation/mosaics/daily_mosaic_20250810.json'
    
    visualize_mosaic_detailed(file_path)

if __name__ == "__main__":
    main()
