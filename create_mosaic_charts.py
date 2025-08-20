#!/usr/bin/env python3
"""Create visual charts from correlation mosaic data."""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

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

def create_correlation_heatmap(mosaic_data, output_dir='charts'):
    """Create a correlation heatmap."""
    if not mosaic_data:
        return None
    
    matrix = mosaic_data.get('correlation_matrix', {}).get('matrix', {})
    correlation_windows = mosaic_data.get('correlation_matrix', {}).get('correlation_windows', [])
    
    # Prepare data for heatmap
    pairs = list(matrix.keys())
    windows = [f'{w}d' for w in correlation_windows]
    
    # Create correlation matrix
    corr_data = []
    for pair in pairs:
        row = []
        for window in windows:
            if window in matrix[pair]:
                correlation = matrix[pair][window].get('correlation', np.nan)
                row.append(correlation if not np.isnan(correlation) else 0)
            else:
                row.append(0)
        corr_data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(corr_data, index=pairs, columns=windows)
    
    # Create the plot
    plt.figure(figsize=(12, 10))
    sns.set(font_scale=0.8)
    
    # Create heatmap
    mask = np.isnan(df) | (df == 0)
    heatmap = sns.heatmap(df, 
                         annot=True, 
                         fmt='.2f', 
                         cmap='RdBu_r', 
                         center=0,
                         mask=mask,
                         cbar_kws={'label': 'Correlation Coefficient'},
                         square=True,
                         linewidths=0.5)
    
    plt.title('Correlation Matrix Heatmap - All Pairs and Time Windows', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Time Windows', fontsize=12, fontweight='bold')
    plt.ylabel('Asset Pairs', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    filename = f'{output_dir}/correlation_heatmap_{datetime.now().strftime("%Y%m%d")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    return filename

def create_correlation_strength_chart(mosaic_data, output_dir='charts'):
    """Create a bar chart showing correlation strengths."""
    if not mosaic_data:
        return None
    
    matrix = mosaic_data.get('correlation_matrix', {}).get('matrix', {})
    correlation_windows = mosaic_data.get('correlation_matrix', {}).get('correlation_windows', [])
    
    # Collect all correlations
    correlations = []
    for pair, windows in matrix.items():
        for window in correlation_windows:
            window_key = f'{window}d'
            if window_key in windows:
                correlation = windows[window_key].get('correlation', np.nan)
                significance = windows[window_key].get('significance', False)
                if not np.isnan(correlation):
                    correlations.append({
                        'pair': pair,
                        'window': window_key,
                        'correlation': correlation,
                        'abs_correlation': abs(correlation),
                        'significance': significance
                    })
    
    # Sort by absolute correlation strength
    correlations.sort(key=lambda x: x['abs_correlation'], reverse=True)
    
    # Take top 20 correlations for visualization
    top_correlations = correlations[:20]
    
    # Create the plot
    plt.figure(figsize=(14, 8))
    
    pairs_windows = [f"{corr['pair']} ({corr['window']})" for corr in top_correlations]
    corr_values = [corr['correlation'] for corr in top_correlations]
    colors = ['red' if corr < 0 else 'blue' for corr in corr_values]
    
    bars = plt.barh(range(len(pairs_windows)), corr_values, color=colors, alpha=0.7)
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, corr_values)):
        plt.text(value + (0.02 if value >= 0 else -0.02), 
                bar.get_y() + bar.get_height()/2, 
                f'{value:.3f}', 
                ha='left' if value >= 0 else 'right',
                va='center',
                fontweight='bold')
    
    plt.yticks(range(len(pairs_windows)), pairs_windows)
    plt.xlabel('Correlation Coefficient', fontsize=12, fontweight='bold')
    plt.title('Top 20 Strongest Correlations', fontsize=16, fontweight='bold', pad=20)
    plt.grid(axis='x', alpha=0.3)
    plt.axvline(x=0, color='black', linestyle='-', alpha=0.5)
    plt.axvline(x=0.7, color='green', linestyle='--', alpha=0.7, label='Strong Correlation (0.7)')
    plt.axvline(x=-0.7, color='green', linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    
    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    filename = f'{output_dir}/correlation_strength_{datetime.now().strftime("%Y%m%d")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    return filename

def create_significance_chart(mosaic_data, output_dir='charts'):
    """Create a chart showing significant vs non-significant correlations."""
    if not mosaic_data:
        return None
    
    summary = mosaic_data.get('correlation_matrix', {}).get('summary', {})
    
    # Prepare data
    significant = summary.get('significant_correlations', 0)
    non_significant = summary.get('total_correlations', 0) - significant
    
    labels = ['Significant', 'Non-Significant']
    sizes = [significant, non_significant]
    colors = ['#2ecc71', '#e74c3c']
    
    # Create pie chart
    plt.figure(figsize=(10, 8))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('Distribution of Significant vs Non-Significant Correlations', 
              fontsize=16, fontweight='bold', pad=20)
    plt.axis('equal')
    plt.tight_layout()
    
    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    filename = f'{output_dir}/significance_distribution_{datetime.now().strftime("%Y%m%d")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    return filename

def create_time_window_comparison(mosaic_data, output_dir='charts'):
    """Create a chart comparing correlations across time windows."""
    if not mosaic_data:
        return None
    
    matrix = mosaic_data.get('correlation_matrix', {}).get('matrix', {})
    correlation_windows = mosaic_data.get('correlation_matrix', {}).get('correlation_windows', [])
    
    # Collect data for each time window
    window_data = {}
    for window in correlation_windows:
        window_key = f'{window}d'
        correlations = []
        for pair, windows_data in matrix.items():
            if window_key in windows_data:
                correlation = windows_data[window_key].get('correlation', np.nan)
                if not np.isnan(correlation):
                    correlations.append(correlation)
        window_data[window_key] = correlations
    
    # Create box plot
    plt.figure(figsize=(12, 8))
    
    data_to_plot = [window_data[f'{w}d'] for w in correlation_windows]
    labels = [f'{w}d' for w in correlation_windows]
    
    box_plot = plt.boxplot(data_to_plot, labels=labels, patch_artist=True)
    
    # Color the boxes
    colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow']
    for patch, color in zip(box_plot['boxes'], colors):
        patch.set_facecolor(color)
    
    plt.title('Correlation Distribution Across Time Windows', 
              fontsize=16, fontweight='bold', pad=20)
    plt.ylabel('Correlation Coefficient', fontsize=12, fontweight='bold')
    plt.xlabel('Time Windows', fontsize=12, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    plt.tight_layout()
    
    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    filename = f'{output_dir}/time_window_comparison_{datetime.now().strftime("%Y%m%d")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    return filename

def create_mosaic_charts(file_path='data/correlation/mosaics/daily_mosaic_20250810.json'):
    """Create all mosaic charts."""
    print("🎨 Creating Correlation Mosaic Charts...")
    print("=" * 50)
    
    # Load mosaic data
    mosaic_data = load_mosaic_data(file_path)
    if not mosaic_data:
        return
    
    # Set style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create charts
    charts_created = []
    
    print("📊 Creating correlation heatmap...")
    heatmap_file = create_correlation_heatmap(mosaic_data)
    if heatmap_file:
        charts_created.append(heatmap_file)
        print(f"✅ Heatmap saved: {heatmap_file}")
    
    print("📈 Creating correlation strength chart...")
    strength_file = create_correlation_strength_chart(mosaic_data)
    if strength_file:
        charts_created.append(strength_file)
        print(f"✅ Strength chart saved: {strength_file}")
    
    print("🍰 Creating significance distribution...")
    significance_file = create_significance_chart(mosaic_data)
    if significance_file:
        charts_created.append(significance_file)
        print(f"✅ Significance chart saved: {significance_file}")
    
    print("⏰ Creating time window comparison...")
    time_window_file = create_time_window_comparison(mosaic_data)
    if time_window_file:
        charts_created.append(time_window_file)
        print(f"✅ Time window chart saved: {time_window_file}")
    
    print(f"\n🎯 Created {len(charts_created)} charts:")
    for chart in charts_created:
        print(f"  📁 {chart}")
    
    return charts_created

def main():
    """Main function to run chart creation."""
    import sys
    
    # Check if file path is provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = 'data/correlation/mosaics/daily_mosaic_20250810.json'
    
    create_mosaic_charts(file_path)

if __name__ == "__main__":
    main()
