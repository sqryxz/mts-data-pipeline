#!/usr/bin/env python3
"""Visualize correlation mosaic data in table format."""

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

def create_correlation_table(mosaic_data):
    """Create a correlation table from mosaic data."""
    if not mosaic_data:
        return None
    
    # Extract correlation matrix
    matrix = mosaic_data.get('correlation_matrix', {}).get('matrix', {})
    correlation_windows = mosaic_data.get('correlation_matrix', {}).get('correlation_windows', [])
    
    # Create table data
    table_data = []
    
    for pair, windows in matrix.items():
        row = {'Pair': pair}
        
        for window in correlation_windows:
            window_key = f'{window}d'
            if window_key in windows:
                correlation = windows[window_key].get('correlation', np.nan)
                significance = windows[window_key].get('significance', False)
                
                # Format correlation with significance indicator
                if np.isnan(correlation):
                    row[window_key] = 'N/A'
                else:
                    significance_symbol = '✅' if significance == "True" else '❌'
                    row[window_key] = f"{correlation:.3f} {significance_symbol}"
            else:
                row[window_key] = 'N/A'
        
        table_data.append(row)
    
    return pd.DataFrame(table_data)

def create_summary_table(mosaic_data):
    """Create a summary table from mosaic data."""
    if not mosaic_data:
        return None
    
    summary = mosaic_data.get('correlation_matrix', {}).get('summary', {})
    
    summary_data = [
        ['Total Pairs Analyzed', summary.get('total_pairs', 0)],
        ['Total Correlations', summary.get('total_correlations', 0)],
        ['Significant Correlations', summary.get('significant_correlations', 0)],
        ['Average Correlation Strength', f"{summary.get('average_correlation_strength', 0):.3f}"],
        ['Strong Correlations', summary.get('strong_correlations', 0)],
        ['Weak Correlations', summary.get('weak_correlations', 0)],
        ['Negative Correlations', summary.get('negative_correlations', 0)]
    ]
    
    return pd.DataFrame(summary_data, columns=['Metric', 'Value'])

def visualize_mosaic(file_path='data/correlation/mosaics/daily_mosaic_20250810.json'):
    """Visualize mosaic data in table format."""
    print("🎨 CORRELATION MOSAIC VISUALIZATION")
    print("=" * 50)
    
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
    print("-" * 30)
    summary_table = create_summary_table(mosaic_data)
    if summary_table is not None:
        print(tabulate(summary_table, headers='keys', tablefmt='grid', showindex=False))
        print()
    
    # Create and display correlation table
    print("🔍 CORRELATION MATRIX")
    print("-" * 30)
    correlation_table = create_correlation_table(mosaic_data)
    if correlation_table is not None:
        # Reorder columns for better readability
        columns = ['Pair'] + [col for col in correlation_table.columns if col != 'Pair']
        correlation_table = correlation_table[columns]
        
        print(tabulate(correlation_table, headers='keys', tablefmt='grid', showindex=False))
        print()
    
    # Display key findings
    print("🎯 KEY FINDINGS")
    print("-" * 30)
    key_findings = mosaic_data.get('key_findings', [])
    for i, finding in enumerate(key_findings, 1):
        print(f"{i}. {finding}")
    print()
    
    # Display recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 30)
    recommendations = mosaic_data.get('recommendations', [])
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    print()
    
    # Display metadata
    print("📋 METADATA")
    print("-" * 30)
    metadata = mosaic_data.get('correlation_matrix', {}).get('metadata', {})
    if metadata:
        for key, value in metadata.items():
            if key == 'generation_time':
                # Format timestamp
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
    """Main function to run visualization."""
    import sys
    
    # Check if file path is provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = 'data/correlation/mosaics/daily_mosaic_20250810.json'
    
    visualize_mosaic(file_path)

if __name__ == "__main__":
    main()
