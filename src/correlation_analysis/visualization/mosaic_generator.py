"""
Mosaic generator for correlation analysis module.
Generates correlation matrices and daily mosaics for all monitored pairs.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np

from ..core.correlation_calculator import CorrelationCalculator
from ..core.correlation_engine import CorrelationEngine
from ..data.data_fetcher import DataFetcher
from ..data.data_normalizer import DataNormalizer
from ..storage.correlation_storage import CorrelationStorage


class MosaicGenerator:
    """
    Generates correlation mosaics for all monitored pairs.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the mosaic generator.
        
        Args:
            config_path: Path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config_path = config_path or "config/correlation_analysis/mosaic_settings.json"
        self.config = self._load_config()
        
        # Initialize components
        self.correlation_calculator = CorrelationCalculator()
        self.data_fetcher = DataFetcher()
        self.data_normalizer = DataNormalizer()
        self.storage = CorrelationStorage()
        
        # Ensure output directory exists
        self.output_directory = Path("data/correlation/mosaics")
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Mosaic generator initialized with output directory: {self.output_directory}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                self.logger.warning(f"Configuration file not found: {config_file}, using defaults")
                return self._get_default_config()
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            self.logger.info(f"Loaded mosaic configuration from {config_file}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load mosaic configuration: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "mosaic_generation": {
                "daily_enabled": True,
                "historical_enabled": False,
                "max_pairs_per_mosaic": 50,
                "correlation_windows": [7, 14, 30]
            },
            "visualization": {
                "heatmap_size": [12, 8],
                "color_scheme": "RdYlBu_r",
                "annotate_values": True,
                "include_significance": True
            },
            "export": {
                "formats": ["json"],
                "compression": False,
                "include_metadata": True
            }
        }
    
    def generate_correlation_matrix(self, pairs: Optional[List[str]] = None, 
                                  correlation_windows: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Generate correlation matrix for all monitored pairs.
        
        Args:
            pairs: List of pairs to include (defaults to all configured pairs)
            correlation_windows: List of correlation windows to use
            
        Returns:
            Dict[str, Any]: Correlation matrix data
        """
        try:
            start_time = time.time()
            self.logger.info("Starting correlation matrix generation")
            
            # Get pairs to analyze
            if pairs is None:
                engine = CorrelationEngine()
                pairs = engine.get_monitored_pairs()
            
            if not pairs:
                self.logger.warning("No pairs provided for correlation matrix generation")
                return self._create_empty_matrix()
            
            # Get correlation windows
            if correlation_windows is None:
                correlation_windows = self.config['mosaic_generation']['correlation_windows']
            
            self.logger.info(f"Generating correlation matrix for {len(pairs)} pairs with windows: {correlation_windows}")
            
            # Initialize matrix structure
            matrix_data = {
                'timestamp': int(datetime.now().timestamp() * 1000),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'pairs': pairs,
                'correlation_windows': correlation_windows,
                'matrix': {},
                'summary': {
                    'total_pairs': len(pairs),
                    'total_correlations': len(pairs) * len(correlation_windows),
                    'significant_correlations': 0,
                    'average_correlation_strength': 0.0,
                    'strong_correlations': 0,
                    'weak_correlations': 0,
                    'negative_correlations': 0
                },
                'metadata': {
                    'generation_time': datetime.now().isoformat(),
                    'config_used': self.config_path
                }
            }
            
            # Calculate correlations using batch processing for better performance
            correlations_data, failed_pairs = self._calculate_batch_correlations(pairs, correlation_windows)
            
            # Store correlation data
            matrix_data['matrix'] = correlations_data
            
            # Update summary statistics
            total_correlation = 0.0
            valid_correlations = 0
            significant_count = 0
            
            for pair_data in correlations_data.values():
                for window_data in pair_data.values():
                    correlation = window_data.get('correlation', np.nan)
                    if not np.isnan(correlation):
                        total_correlation += correlation
                        valid_correlations += 1
                        
                        if window_data.get('significance', False):
                            significant_count += 1
                        
                        # Categorize correlation strength
                        abs_corr = abs(correlation)
                        if abs_corr >= 0.7:
                            matrix_data['summary']['strong_correlations'] += 1
                        elif abs_corr < 0.3:
                            matrix_data['summary']['weak_correlations'] += 1
                        
                        if correlation < 0:
                            matrix_data['summary']['negative_correlations'] += 1
            
            # Update summary statistics
            if valid_correlations > 0:
                matrix_data['summary']['average_correlation_strength'] = total_correlation / valid_correlations
                matrix_data['summary']['significant_correlations'] = significant_count
            
            # Add failed pairs to metadata if any
            if failed_pairs:
                matrix_data['metadata']['failed_pairs'] = failed_pairs
                matrix_data['metadata']['partial_success'] = True
                self.logger.warning(f"Completed matrix with {len(failed_pairs)} failed pairs: {failed_pairs}")
            
            # Calculate generation time
            generation_time = time.time() - start_time
            matrix_data['metadata']['generation_time_seconds'] = generation_time
            
            self.logger.info(f"Correlation matrix generated in {generation_time:.2f}s")
            self.logger.info(f"Summary: {valid_correlations} valid correlations, {significant_count} significant")
            
            return matrix_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate correlation matrix: {e}")
            return self._create_empty_matrix()
    
    def _calculate_batch_correlations(self, pairs: List[str], correlation_windows: List[int]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Calculate correlations in batches for better performance.
        
        Args:
            pairs: List of pairs to analyze
            correlation_windows: List of correlation windows
            
        Returns:
            Tuple[Dict[str, Any], List[str]]: Correlation data and failed pairs
        """
        correlations_data = {}
        failed_pairs = []
        data_cache = {}
        
        # Group pairs by data requirements and cache data
        for pair in pairs:
            try:
                primary_asset, secondary_asset = self._parse_pair(pair)
                cache_key = f"{primary_asset}_{secondary_asset}"
                
                if cache_key not in data_cache:
                    # Load minimal data needed for maximum window
                    max_window = max(correlation_windows)
                    data = self.data_normalizer.normalize_for_correlation(
                        primary_asset, secondary_asset, max_window * 2
                    )
                    data_cache[cache_key] = data
                    self.logger.debug(f"Cached data for {cache_key}: {len(data)} rows")
                
                correlations_data[pair] = self._calculate_pair_correlations(
                    pair, data_cache[cache_key], correlation_windows
                )
                
            except Exception as e:
                self.logger.error(f"Failed to process pair {pair}: {e}")
                failed_pairs.append(pair)
                correlations_data[pair] = self._create_empty_pair_result(correlation_windows)
        
        # Clear cache to free memory
        data_cache.clear()
        
        return correlations_data, failed_pairs
    
    def _calculate_pair_correlations(self, pair: str, data: pd.DataFrame, correlation_windows: List[int]) -> Dict[str, Any]:
        """
        Calculate correlations for a single pair using cached data.
        
        Args:
            pair: Pair name
            data: Cached data for the pair
            correlation_windows: List of correlation windows
            
        Returns:
            Dict[str, Any]: Correlation data for the pair
        """
        pair_correlations = {}
        
        if data.empty:
            self.logger.warning(f"No data available for {pair}")
            return self._create_empty_pair_result(correlation_windows)
        
        primary_asset, secondary_asset = self._parse_pair(pair)
        
        for window in correlation_windows:
            try:
                # Calculate correlation
                correlation = self.correlation_calculator.calculate_correlation(
                    data, primary_asset, secondary_asset, window
                )
                
                # Calculate significance if correlation is valid
                significance = False
                p_value = np.nan
                sample_size = len(data)
                
                if not np.isnan(correlation):
                    # Calculate significance using correlation calculator
                    significance_result = self.correlation_calculator.calculate_correlation_with_significance(
                        data, primary_asset, secondary_asset, window
                    )
                    significance = significance_result.get('significant', False)
                    p_value = significance_result.get('p_value', np.nan)
                
                pair_correlations[f'{window}d'] = {
                    'correlation': float(correlation) if not np.isnan(correlation) else np.nan,
                    'significance': significance,
                    'p_value': float(p_value) if not np.isnan(p_value) else np.nan,
                    'sample_size': sample_size
                }
                
            except Exception as e:
                self.logger.error(f"Failed to calculate correlation for {pair} ({window}d): {e}")
                pair_correlations[f'{window}d'] = {
                    'correlation': np.nan,
                    'significance': False,
                    'p_value': np.nan,
                    'sample_size': 0
                }
        
        return pair_correlations
    
    def _create_empty_pair_result(self, correlation_windows: List[int]) -> Dict[str, Any]:
        """Create empty result structure for a pair."""
        result = {}
        for window in correlation_windows:
            result[f'{window}d'] = {
                'correlation': np.nan,
                'significance': False,
                'p_value': np.nan,
                'sample_size': 0
            }
        return result
    
    def _parse_pair(self, pair: str) -> Tuple[str, str]:
        """Parse pair string into primary and secondary assets."""
        if '_' in pair:
            parts = pair.split('_')
            if len(parts) >= 2:
                asset_mapping = {
                    # Crypto assets
                    'BTC': 'bitcoin',
                    'ETH': 'ethereum',
                    'USDT': 'tether',
                    'ADA': 'cardano',
                    'DOGE': 'dogecoin',
                    'XRP': 'ripple',
                    'LTC': 'litecoin',
                    'BCH': 'bitcoin-cash',
                    'SOL': 'solana',
                    'BTT': 'bittensor',
                    'FET': 'fetch-ai',
                    'OCEAN': 'ocean-protocol',
                    'RNDR': 'render-token',
                    'AGIX': 'singularitynet',
                    'SUI': 'sui',
                    'ENA': 'ethena',
                    
                    # Macro indicators
                    'VIX': 'VIXCLS',
                    'DXY': 'DEXCHUS',
                    'TREASURY': 'DGS10',
                    'FED': 'DFF',
                    'SOFR': 'SOFR',
                    'RRP': 'RRPONTSYD',
                    'BAML': 'BAMLH0A0HYM2',
                    'DEXUSEU': 'DEXUSEU',
                    'DTWEXBGS': 'DTWEXBGS'
                }
                primary = asset_mapping.get(parts[0].upper(), parts[0].lower())
                secondary = asset_mapping.get(parts[1].upper(), parts[1].lower())
                return primary, secondary
        
        return pair.lower(), pair.lower()
    
    def _create_empty_matrix(self) -> Dict[str, Any]:
        """Create empty correlation matrix structure."""
        return {
            'timestamp': int(datetime.now().timestamp() * 1000),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'pairs': [],
            'correlation_windows': [],
            'matrix': {},
            'summary': {
                'total_pairs': 0,
                'total_correlations': 0,
                'significant_correlations': 0,
                'average_correlation_strength': 0.0,
                'strong_correlations': 0,
                'weak_correlations': 0,
                'negative_correlations': 0
            },
            'metadata': {
                'generation_time': datetime.now().isoformat(),
                'config_used': self.config_path,
                'error': 'No data available'
            }
        }
    
    def save_correlation_matrix(self, matrix_data: Dict[str, Any], 
                              filename: Optional[str] = None) -> str:
        """
        Save correlation matrix to JSON file.
        
        Args:
            matrix_data: Correlation matrix data
            filename: Optional filename (defaults to auto-generated)
            
        Returns:
            str: Path to saved file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"correlation_matrix_{timestamp}.json"
            
            filepath = self.output_directory / filename
            
            # Save matrix data
            with open(filepath, 'w') as f:
                json.dump(matrix_data, f, indent=2, default=str)
            
            self.logger.info(f"Saved correlation matrix to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save correlation matrix: {e}")
            return ""
    
    def generate_daily_mosaic(self) -> Dict[str, Any]:
        """
        Generate daily correlation mosaic with summary and key findings.
        
        Returns:
            Dict[str, Any]: Daily mosaic data
        """
        try:
            self.logger.info("Generating daily correlation mosaic")
            
            # Generate correlation matrix
            matrix_data = self.generate_correlation_matrix()
            
            # Add mosaic-specific data
            mosaic_data = {
                'mosaic_type': 'daily',
                'generation_date': datetime.now().strftime('%Y-%m-%d'),
                'correlation_matrix': matrix_data,
                'key_findings': self._extract_key_findings(matrix_data),
                'recommendations': self._generate_recommendations(matrix_data),
                'file_locations': {}
            }
            
            # Save mosaic data
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f"daily_mosaic_{timestamp}.json"
            filepath = self.save_correlation_matrix(mosaic_data, filename)
            
            if filepath:
                mosaic_data['file_locations']['json_report'] = filepath
            
            self.logger.info(f"Daily mosaic generated: {len(mosaic_data['key_findings'])} key findings")
            return mosaic_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate daily mosaic: {e}")
            return {}
    
    def _extract_key_findings(self, matrix_data: Dict[str, Any]) -> List[str]:
        """Extract key findings from correlation matrix."""
        findings = []

        try:
            summary = matrix_data.get('summary', {})
            matrix = matrix_data.get('matrix', {})

            # Add summary findings
            total_pairs = summary.get('total_pairs', 0)
            significant_correlations = summary.get('significant_correlations', 0)
            average_correlation = summary.get('average_correlation_strength', 0.0)
            strong_correlations = summary.get('strong_correlations', 0)
            negative_correlations = summary.get('negative_correlations', 0)

            findings.append(f"Analyzed {total_pairs} asset pairs with correlation data")

            if significant_correlations > 0:
                findings.append(f"Found {significant_correlations} statistically significant correlations")

            if abs(average_correlation) > 0.5:
                findings.append(f"Average correlation strength: {average_correlation:.3f}")

            if strong_correlations > 0:
                findings.append(f"Identified {strong_correlations} strong correlations (|r| >= 0.7)")

            if negative_correlations > 0:
                findings.append(f"Found {negative_correlations} negative correlations")

            # Extract and rank specific pairs worth paying attention to
            notable_pairs = self._identify_notable_pairs(matrix)

            # Add top pairs to findings
            if notable_pairs['strong_positive']:
                strong_pos = notable_pairs['strong_positive'][:3]
                findings.append(f"🔥 Strong positive correlations: {', '.join(strong_pos)}")

            if notable_pairs['strong_negative']:
                strong_neg = notable_pairs['strong_negative'][:3]
                findings.append(f"🛡️ Strong negative correlations: {', '.join(strong_neg)}")

            if notable_pairs['high_significance']:
                high_sig = notable_pairs['high_significance'][:3]
                findings.append(f"📊 Highly significant pairs: {', '.join(high_sig)}")

            if notable_pairs['correlation_changes']:
                changes = notable_pairs['correlation_changes'][:2]
                findings.append(f"⚡ Notable correlation changes: {', '.join(changes)}")

        except Exception as e:
            self.logger.error(f"Failed to extract key findings: {e}")
            findings.append("Error extracting key findings")

        return findings

    def _identify_notable_pairs(self, matrix: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Identify notable pairs worth paying attention to based on correlation strength,
        significance, and changes over time.

        Returns:
            Dict with keys: strong_positive, strong_negative, high_significance, correlation_changes
        """
        notable_pairs = {
            'strong_positive': [],
            'strong_negative': [],
            'high_significance': [],
            'correlation_changes': []
        }

        try:
            # First pass: collect all correlation data
            pair_analysis = {}

            for pair, correlations in matrix.items():
                pair_analysis[pair] = {
                    'correlations': {},
                    'max_abs_corr': 0.0,
                    'min_p_value': 1.0,
                    'has_significant': False
                }

                for window, data in correlations.items():
                    correlation = data.get('correlation', np.nan)
                    p_value = data.get('p_value', np.nan)
                    significance = data.get('significance', False)

                    if not np.isnan(correlation):
                        pair_analysis[pair]['correlations'][window] = correlation
                        pair_analysis[pair]['max_abs_corr'] = max(pair_analysis[pair]['max_abs_corr'], abs(correlation))

                    if not np.isnan(p_value) and p_value < pair_analysis[pair]['min_p_value']:
                        pair_analysis[pair]['min_p_value'] = p_value

                    if significance:
                        pair_analysis[pair]['has_significant'] = True

            # Identify strong positive correlations (focus on most recent/important windows)
            for pair, analysis in pair_analysis.items():
                # Check 30d and 60d windows for strong correlations (longer-term more reliable)
                for window in ['60d', '30d']:
                    if window in analysis['correlations']:
                        corr = analysis['correlations'][window]
                        if not np.isnan(corr) and corr >= 0.7:
                            notable_pairs['strong_positive'].append(f"{pair} ({window}: {corr:.3f})")
                            break  # Only add once per pair

            # Identify strong negative correlations
            for pair, analysis in pair_analysis.items():
                for window in ['60d', '30d']:
                    if window in analysis['correlations']:
                        corr = analysis['correlations'][window]
                        if not np.isnan(corr) and corr <= -0.7:
                            notable_pairs['strong_negative'].append(f"{pair} ({window}: {corr:.3f})")
                            break

            # Identify highly significant correlations (very low p-values)
            for pair, analysis in pair_analysis.items():
                if analysis['has_significant'] and analysis['min_p_value'] < 1e-10:
                    # Find the strongest correlation for this pair
                    strongest_corr = None
                    strongest_window = None
                    for window, corr in analysis['correlations'].items():
                        if not np.isnan(corr) and (strongest_corr is None or abs(corr) > abs(strongest_corr)):
                            strongest_corr = corr
                            strongest_window = window

                    if strongest_corr is not None:
                        notable_pairs['high_significance'].append(f"{pair} ({strongest_window}: {strongest_corr:.3f})")

            # Identify pairs with notable correlation changes
            for pair, analysis in pair_analysis.items():
                correlations = analysis['correlations']

                # Need at least 2 time windows to detect changes
                if len(correlations) >= 2:
                    # Compare short-term vs long-term changes
                    short_term = correlations.get('7d', np.nan)
                    long_term = correlations.get('60d', np.nan)

                    if not np.isnan(short_term) and not np.isnan(long_term):
                        change = long_term - short_term
                        if abs(change) >= 0.3:  # Significant change threshold
                            notable_pairs['correlation_changes'].append(
                                f"{pair} ({short_term:+.3f}→{long_term:+.3f})"
                            )

            # Sort by correlation strength (strongest first)
            notable_pairs['strong_positive'].sort(key=lambda x: float(x.split(': ')[1]), reverse=True)
            notable_pairs['strong_negative'].sort(key=lambda x: float(x.split(': ')[1]))  # Most negative first
            notable_pairs['high_significance'].sort(key=lambda x: abs(float(x.split(': ')[1])), reverse=True)

            # For correlation changes, sort by magnitude of change
            try:
                def extract_change_magnitude(change_str):
                    # Extract values like "+0.376→+0.005)" from "BTC_ETH (+0.376→+0.005)"
                    values_part = change_str.split('(')[1].rstrip(')')
                    start_val, end_val = values_part.split('→')
                    return abs(float(end_val) - float(start_val))

                notable_pairs['correlation_changes'].sort(
                    key=extract_change_magnitude,
                    reverse=True
                )
            except (ValueError, IndexError) as e:
                self.logger.warning(f"Could not sort correlation changes: {e}")
                # Keep original order if sorting fails

        except Exception as e:
            self.logger.error(f"Failed to identify notable pairs: {e}")

        return notable_pairs

    def _generate_recommendations(self, matrix_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on correlation matrix."""
        recommendations = []
        
        try:
            summary = matrix_data.get('summary', {})
            average_correlation = summary.get('average_correlation_strength', 0.0)
            strong_correlations = summary.get('strong_correlations', 0)
            
            if strong_correlations > 0:
                recommendations.append("Consider correlation-based trading strategies for strongly correlated pairs")
            
            if abs(average_correlation) < 0.3:
                recommendations.append("Low average correlation suggests good diversification opportunities")
            
            if average_correlation > 0.5:
                recommendations.append("High average correlation - consider reducing portfolio concentration")
            
            recommendations.append("Monitor correlation breakdowns for trading opportunities")
            recommendations.append("Review correlation trends for portfolio rebalancing decisions")
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            recommendations.append("Error generating recommendations")
        
        return recommendations
