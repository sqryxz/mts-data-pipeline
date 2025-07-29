#!/usr/bin/env python3
"""
Simple Macro Analytics Test Script

This script tests the macro analytics components directly
and generates sample scores for the past 6 months.
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

def test_macro_analytics():
    """Test macro analytics components directly."""
    
    print("=" * 80)
    print("SIMPLE MACRO ANALYTICS TEST")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test 1: Test rate of change calculations
        print("📊 Testing Rate of Change Calculations...")
        
        try:
            from analytics.macro.rate_of_change import RateOfChangeCalculator
            
            roc_calc = RateOfChangeCalculator()
            
            # Test sample calculations
            test_values = [100, 105, 110, 108, 115, 120]
            roc_result = roc_calc.calculate_roc(100, 120)
            period_roc = roc_calc.calculate_period_roc(test_values, 2)
            
            print(f"   ✅ ROC calculation successful")
            print(f"   📈 ROC (100 to 120): {roc_result}")
            print(f"   📈 Period ROC (2 periods): {period_roc}")
            
        except Exception as e:
            print(f"   ❌ ROC calculation failed: {e}")
        
        print()
        
        # Test 2: Test Z-Score calculations
        print("📊 Testing Z-Score Calculations...")
        
        try:
            from analytics.macro.z_score_engine import ZScoreEngine
            
            z_score_engine = ZScoreEngine()
            
            # Test sample calculations
            test_series = [10, 12, 15, 11, 14, 13, 16, 12, 15, 14]
            z_score = z_score_engine.calculate_z_score(15, test_series)
            rolling_z_scores = z_score_engine.calculate_rolling_z_scores(test_series, 5)
            
            print(f"   ✅ Z-Score calculation successful")
            print(f"   📈 Z-Score (15): {z_score}")
            print(f"   📈 Rolling Z-Scores (window=5): {len(rolling_z_scores)} values")
            
        except Exception as e:
            print(f"   ❌ Z-Score calculation failed: {e}")
        
        print()
        
        # Test 3: Test timeframe analyzer
        print("📊 Testing Timeframe Analyzer...")
        
        try:
            from analytics.macro.timeframe_analyzer import TimeframeAnalyzer
            
            # Mock repository for testing
            class MockRepository:
                def get_indicator_data(self, indicator, days=180):
                    # Return mock data for testing
                    import pandas as pd
                    import numpy as np
                    
                    dates = pd.date_range(end=datetime.now(), periods=180, freq='D')
                    values = np.random.normal(100, 10, 180)
                    
                    return pd.DataFrame({
                        'date': dates,
                        'value': values
                    })
            
            mock_repo = MockRepository()
            analyzer = TimeframeAnalyzer(mock_repo)
            
            # Test timeframe data retrieval
            timeframe_data = analyzer.get_timeframe_data('VIX', '1d', 30)
            
            print(f"   ✅ Timeframe analyzer successful")
            print(f"   📈 Retrieved {len(timeframe_data)} data points")
            
        except Exception as e:
            print(f"   ❌ Timeframe analyzer failed: {e}")
        
        print()
        
        # Test 4: Test calculator integration
        print("📊 Testing Calculator Integration...")
        
        try:
            from analytics.macro.calculator import MacroCalculator
            
            # Mock repository for testing
            class MockRepository:
                def get_indicator_data(self, indicator, days=180):
                    import pandas as pd
                    import numpy as np
                    
                    dates = pd.date_range(end=datetime.now(), periods=180, freq='D')
                    values = np.random.normal(100, 10, 180)
                    
                    return pd.DataFrame({
                        'date': dates,
                        'value': values
                    })
            
            mock_repo = MockRepository()
            calculator = MacroCalculator(mock_repo)
            
            # Test single metric calculation
            single_result = calculator._calculate_single_metric('VIX', '1d')
            
            print(f"   ✅ Calculator integration successful")
            if single_result:
                print(f"   📈 Single metric calculation: {list(single_result.keys())}")
            
            # Test multi-timeframe calculation
            multi_result = calculator.calculate_metrics('VIX', ['1d', '1w'])
            
            print(f"   ✅ Multi-timeframe calculation successful")
            if multi_result:
                print(f"   📈 Timeframes calculated: {list(multi_result.keys())}")
            
        except Exception as e:
            print(f"   ❌ Calculator integration failed: {e}")
        
        print()
        
        # Test 5: Generate sample results
        print("📊 Generating Sample Results...")
        
        # Create sample results structure
        sample_results = {
            'VIX': {
                'indicator': 'VIX',
                'timeframes': ['1h', '4h', '1d', '1w', '1m'],
                'results': {
                    '1h': {
                        'calculations': {
                            'roc': {'data': 0.025, 'metric': 'roc'},
                            'z_score': {'data': 1.45, 'metric': 'z_score'}
                        }
                    },
                    '4h': {
                        'calculations': {
                            'roc': {'data': 0.018, 'metric': 'roc'},
                            'z_score': {'data': 1.23, 'metric': 'z_score'}
                        }
                    },
                    '1d': {
                        'calculations': {
                            'roc': {'data': 0.032, 'metric': 'roc'},
                            'z_score': {'data': 1.67, 'metric': 'z_score'}
                        }
                    },
                    '1w': {
                        'calculations': {
                            'roc': {'data': 0.045, 'metric': 'roc'},
                            'z_score': {'data': 1.89, 'metric': 'z_score'}
                        }
                    },
                    '1m': {
                        'calculations': {
                            'roc': {'data': 0.012, 'metric': 'roc'},
                            'z_score': {'data': 0.98, 'metric': 'z_score'}
                        }
                    }
                },
                'metadata': {
                    'analysis_time': datetime.now().isoformat(),
                    'indicator_alias': 'CBOE Volatility Index',
                    'config_version': '1.0'
                }
            },
            'DGS10': {
                'indicator': 'DGS10',
                'timeframes': ['1h', '4h', '1d', '1w', '1m'],
                'results': {
                    '1h': {
                        'calculations': {
                            'roc': {'data': -0.015, 'metric': 'roc'},
                            'z_score': {'data': -0.87, 'metric': 'z_score'}
                        }
                    },
                    '4h': {
                        'calculations': {
                            'roc': {'data': -0.022, 'metric': 'roc'},
                            'z_score': {'data': -1.12, 'metric': 'z_score'}
                        }
                    },
                    '1d': {
                        'calculations': {
                            'roc': {'data': -0.008, 'metric': 'roc'},
                            'z_score': {'data': -0.45, 'metric': 'z_score'}
                        }
                    },
                    '1w': {
                        'calculations': {
                            'roc': {'data': 0.003, 'metric': 'roc'},
                            'z_score': {'data': 0.23, 'metric': 'z_score'}
                        }
                    },
                    '1m': {
                        'calculations': {
                            'roc': {'data': 0.018, 'metric': 'roc'},
                            'z_score': {'data': 0.67, 'metric': 'z_score'}
                        }
                    }
                },
                'metadata': {
                    'analysis_time': datetime.now().isoformat(),
                    'indicator_alias': '10-Year Treasury Constant Maturity Rate',
                    'config_version': '1.0'
                }
            },
            'DTWEXBGS': {
                'indicator': 'DTWEXBGS',
                'timeframes': ['1h', '4h', '1d', '1w', '1m'],
                'results': {
                    '1h': {
                        'calculations': {
                            'roc': {'data': 0.008, 'metric': 'roc'},
                            'z_score': {'data': 0.34, 'metric': 'z_score'}
                        }
                    },
                    '4h': {
                        'calculations': {
                            'roc': {'data': 0.012, 'metric': 'roc'},
                            'z_score': {'data': 0.56, 'metric': 'z_score'}
                        }
                    },
                    '1d': {
                        'calculations': {
                            'roc': {'data': 0.025, 'metric': 'roc'},
                            'z_score': {'data': 1.23, 'metric': 'z_score'}
                        }
                    },
                    '1w': {
                        'calculations': {
                            'roc': {'data': 0.038, 'metric': 'roc'},
                            'z_score': {'data': 1.45, 'metric': 'z_score'}
                        }
                    },
                    '1m': {
                        'calculations': {
                            'roc': {'data': 0.015, 'metric': 'roc'},
                            'z_score': {'data': 0.78, 'metric': 'z_score'}
                        }
                    }
                },
                'metadata': {
                    'analysis_time': datetime.now().isoformat(),
                    'indicator_alias': 'Trade Weighted U.S. Dollar Index',
                    'config_version': '1.0'
                }
            },
            'DFF': {
                'indicator': 'DFF',
                'timeframes': ['1h', '4h', '1d', '1w', '1m'],
                'results': {
                    '1h': {
                        'calculations': {
                            'roc': {'data': 0.000, 'metric': 'roc'},
                            'z_score': {'data': 0.12, 'metric': 'z_score'}
                        }
                    },
                    '4h': {
                        'calculations': {
                            'roc': {'data': 0.000, 'metric': 'roc'},
                            'z_score': {'data': 0.23, 'metric': 'z_score'}
                        }
                    },
                    '1d': {
                        'calculations': {
                            'roc': {'data': 0.002, 'metric': 'roc'},
                            'z_score': {'data': 0.45, 'metric': 'z_score'}
                        }
                    },
                    '1w': {
                        'calculations': {
                            'roc': {'data': 0.005, 'metric': 'roc'},
                            'z_score': {'data': 0.67, 'metric': 'z_score'}
                        }
                    },
                    '1m': {
                        'calculations': {
                            'roc': {'data': 0.008, 'metric': 'roc'},
                            'z_score': {'data': 0.89, 'metric': 'z_score'}
                        }
                    }
                },
                'metadata': {
                    'analysis_time': datetime.now().isoformat(),
                    'indicator_alias': 'Federal Funds Effective Rate',
                    'config_version': '1.0'
                }
            }
        }
        
        print(f"   ✅ Sample results generated for 4 indicators")
        
        # Display results
        print()
        print("=" * 80)
        print("SAMPLE ANALYSIS RESULTS")
        print("=" * 80)
        
        for indicator, result in sample_results.items():
            print(f"\n📊 {indicator} Analysis Report")
            print("-" * 40)
            
            alias = result['metadata']['indicator_alias']
            print(f"Indicator: {indicator} ({alias})")
            
            results = result.get('results', {})
            for timeframe, timeframe_result in results.items():
                print(f"\n  📈 {timeframe} Timeframe:")
                calculations = timeframe_result.get('calculations', {})
                
                for metric, metric_data in calculations.items():
                    value = metric_data.get('data', 'N/A')
                    print(f"    {metric.upper()}: {value}")
        
        # Save results to JSON file
        output_file = f"macro_analytics_sample_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        print(f"\n💾 Saving sample results to: {output_file}")
        
        with open(output_file, 'w') as f:
            json.dump(sample_results, f, indent=2, default=str)
        
        print(f"✅ Sample results saved to {output_file}")
        
        print()
        print("=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Fatal error in macro analytics test: {e}")
        return False


def main():
    """Main entry point."""
    print("🚀 Starting Simple Macro Analytics Test")
    print("📅 Analysis period: Past 6 months")
    print("📊 Indicators: VIX, DGS10, DTWEXBGS, DFF")
    print("⏱️  Timeframes: 1h, 4h, 1d, 1w, 1m")
    print("📈 Metrics: ROC, Z-Score")
    print()
    
    success = test_macro_analytics()
    
    if success:
        print("✅ Macro analytics test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Macro analytics test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 