"""
Enhanced Alert Templates for generating actionable correlation alerts.
Provides detailed trading opportunities, market context, and specific recommendations.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json


class EnhancedAlertTemplates:
    """
    Enhanced alert templates for correlation analysis.
    Generates actionable, detailed alerts with trading opportunities and market context.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize enhanced alert templates."""
        self.logger = logging.getLogger(__name__)
        self.config = config or self._load_default_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration for alert templates."""
        return {
            'alert_expiration_hours': {
                'daily_correlation_mosaic': 24,
                'trading_opportunity': 6,
                'risk_alert': 12
            },
            'priority_levels': ['low', 'medium', 'high', 'critical'],
            'confidence_levels': ['low', 'medium', 'high'],
            'risk_levels': ['low', 'medium', 'high'],
            'timeframes': ['7d', '14d', '30d', '60d'],
            'opportunity_types': [
                'momentum_trade',
                'correlation_trade', 
                'divergence_trade',
                'breakdown_signal',
                'hedging_opportunity'
            ]
        }
    
    def create_enhanced_mosaic_alert(self, enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create enhanced daily correlation mosaic alert with actionable insights.
        
        Args:
            enhanced_analysis: Enhanced analysis from EnhancedMosaicAnalyzer
            
        Returns:
            Dict[str, Any]: Comprehensive alert with trading opportunities and insights
        """
        try:
            self.logger.info("Creating enhanced mosaic alert template")
            
            # Generate alert metadata
            alert_id = self._generate_alert_id('enhanced_mosaic', 'daily')
            timestamp = int(datetime.now().timestamp() * 1000)
            expires_at = int((datetime.now() + timedelta(hours=24)).timestamp() * 1000)
            
            # Extract key components from analysis
            market_regime = enhanced_analysis.get('market_regime', {})
            trading_opportunities = enhanced_analysis.get('trading_opportunities', [])
            market_insights = enhanced_analysis.get('market_insights', [])
            risk_analysis = enhanced_analysis.get('risk_analysis', {})
            portfolio_recommendations = enhanced_analysis.get('portfolio_recommendations', [])
            actionable_summary = enhanced_analysis.get('actionable_summary', {})
            priority_alerts = enhanced_analysis.get('priority_alerts', [])
            
            # Create comprehensive alert structure
            alert = {
                "timestamp": timestamp,
                "alert_type": "enhanced_daily_correlation_mosaic",
                "alert_id": alert_id,
                "date": datetime.now().strftime('%Y-%m-%d'),
                "version": "2.0",
                
                # Executive Summary - Most Important Info First
                "executive_summary": self._create_executive_summary(actionable_summary, market_regime, trading_opportunities),
                
                # Priority Alerts - Immediate Action Items
                "priority_alerts": self._format_priority_alerts(priority_alerts),
                
                # Market Context - Current Conditions
                "market_context": {
                    "regime": market_regime,
                    "conditions_summary": actionable_summary.get('market_conditions', 'Analysis unavailable'),
                    "regime_implications": market_regime.get('implications', []),
                    "key_metrics": enhanced_analysis.get('enhanced_metrics', {})
                },
                
                # Trading Opportunities - Specific Actionable Trades
                "trading_opportunities": {
                    "summary": {
                        "total_opportunities": len(trading_opportunities),
                        "high_confidence": len([op for op in trading_opportunities if op.get('confidence') == 'high']),
                        "immediate_action_required": len([op for op in trading_opportunities if op.get('risk_level') == 'low' and op.get('confidence') == 'high'])
                    },
                    "high_priority": self._filter_high_priority_opportunities(trading_opportunities),
                    "by_timeframe": self._group_opportunities_by_timeframe(trading_opportunities),
                    "by_type": self._group_opportunities_by_type(trading_opportunities)
                },
                
                # Risk Analysis - What to Watch Out For
                "risk_analysis": {
                    "overall_assessment": risk_analysis,
                    "risk_alerts": actionable_summary.get('risk_alerts', []),
                    "monitoring_priorities": actionable_summary.get('monitoring_priorities', []),
                    "risk_mitigation": self._extract_risk_mitigation(portfolio_recommendations)
                },
                
                # Portfolio Recommendations - Specific Actions
                "portfolio_recommendations": {
                    "immediate_actions": actionable_summary.get('immediate_actions', []),
                    "strategic_recommendations": self._categorize_recommendations(portfolio_recommendations),
                    "position_sizing_guidance": self._extract_position_sizing_guidance(portfolio_recommendations, risk_analysis),
                    "rebalancing_signals": self._extract_rebalancing_signals(portfolio_recommendations)
                },
                
                # Market Insights - Educational Context
                "market_insights": {
                    "key_insights": market_insights,
                    "correlation_breakdown_signals": enhanced_analysis.get('correlation_breakdown_signals', []),
                    "timeframe_analysis": enhanced_analysis.get('timeframe_analysis', {}),
                    "pair_rankings": enhanced_analysis.get('pair_rankings', [])
                },
                
                # Technical Details - For Advanced Users
                "technical_analysis": {
                    "correlation_matrix_summary": self._extract_matrix_summary(enhanced_analysis),
                    "statistical_significance": self._extract_significance_analysis(enhanced_analysis),
                    "confidence_intervals": self._calculate_confidence_intervals(enhanced_analysis),
                    "data_quality_metrics": self._assess_data_quality(enhanced_analysis)
                },
                
                # Next Steps - Clear Action Items
                "next_steps": {
                    "immediate_review": self._generate_immediate_review_items(trading_opportunities, priority_alerts),
                    "monitoring_schedule": self._generate_monitoring_schedule(actionable_summary),
                    "follow_up_analysis": self._generate_follow_up_items(enhanced_analysis),
                    "review_triggers": self._generate_review_triggers(market_regime, risk_analysis)
                },
                
                # Metadata
                "alert_metadata": {
                    "severity": self._determine_alert_severity(priority_alerts, risk_analysis),
                    "category": "enhanced_correlation_analysis",
                    "report_type": "daily_actionable_summary",
                    "confidence_score": self._calculate_overall_confidence(enhanced_analysis),
                    "expires_at": expires_at,
                    "generated_by": "EnhancedMosaicAnalyzer",
                    "analysis_timestamp": enhanced_analysis.get('timestamp', datetime.now().isoformat())
                }
            }
            
            # Add file references if available
            if 'file_locations' in enhanced_analysis:
                alert['file_references'] = enhanced_analysis['file_locations']
            
            self.logger.info(f"Enhanced mosaic alert created: {alert_id}")
            return alert
            
        except Exception as e:
            self.logger.error(f"Failed to create enhanced mosaic alert: {e}")
            return self._create_fallback_alert(enhanced_analysis)
    
    def _create_executive_summary(self, actionable_summary: Dict[str, Any], 
                                market_regime: Dict[str, Any], 
                                trading_opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create executive summary with key takeaways."""
        try:
            high_confidence_ops = len([op for op in trading_opportunities if op.get('confidence') == 'high'])
            
            # Determine overall market assessment
            regime_name = market_regime.get('regime', 'unknown')
            regime_confidence = market_regime.get('confidence', 'low')
            
            market_assessment = f"{regime_name.title()} market regime detected ({regime_confidence} confidence)"
            
            # Key statistics
            opportunity_count = actionable_summary.get('opportunity_count', 0)
            high_value_opportunities = actionable_summary.get('high_value_opportunities', 0)
            
            return {
                "market_assessment": market_assessment,
                "primary_recommendation": actionable_summary.get('top_recommendations', ['Monitor market conditions'])[0] if actionable_summary.get('top_recommendations') else 'Monitor market conditions',
                "opportunity_highlight": f"{high_confidence_ops} high-confidence trading opportunities identified from {opportunity_count} analyzed pairs",
                "risk_highlight": self._summarize_primary_risk(actionable_summary),
                "immediate_action_required": len(actionable_summary.get('immediate_actions', [])) > 0,
                "key_takeaways": self._generate_key_takeaways(actionable_summary, market_regime, trading_opportunities)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create executive summary: {e}")
            return {"market_assessment": "Analysis unavailable", "opportunity_highlight": "Unable to assess opportunities"}
    
    def _format_priority_alerts(self, priority_alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format priority alerts for immediate attention."""
        try:
            formatted_alerts = []
            
            for alert in priority_alerts:
                formatted_alert = {
                    "priority": alert.get('priority', 'medium'),
                    "type": alert.get('type', 'general'),
                    "message": alert.get('message', 'Alert message unavailable'),
                    "action_required": alert.get('action_required', False),
                    "timestamp": datetime.now().isoformat(),
                    "urgency_level": self._determine_urgency_level(alert)
                }
                formatted_alerts.append(formatted_alert)
            
            # Sort by priority and urgency
            formatted_alerts.sort(key=lambda x: (
                x['priority'] != 'high',
                x['urgency_level'] != 'immediate',
                x['action_required'] != True
            ))
            
            return formatted_alerts
            
        except Exception as e:
            self.logger.error(f"Failed to format priority alerts: {e}")
            return []
    
    def _filter_high_priority_opportunities(self, trading_opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and format high-priority trading opportunities."""
        try:
            high_priority = []
            
            for opportunity in trading_opportunities:
                confidence = opportunity.get('confidence', 'low')
                risk_level = opportunity.get('risk_level', 'high')
                
                # High priority: high confidence + low-medium risk
                if confidence == 'high' and risk_level in ['low', 'medium']:
                    formatted_opportunity = {
                        "pair": opportunity.get('pair', 'Unknown'),
                        "type": opportunity.get('opportunity_type', 'Unknown'),
                        "timeframe": opportunity.get('timeframe', 'Unknown'),
                        "correlation": opportunity.get('correlation', 0.0),
                        "confidence": confidence,
                        "risk_level": risk_level,
                        "entry_signal": opportunity.get('entry_signal', 'Monitor for entry'),
                        "expected_duration": opportunity.get('expected_duration', 'Unknown'),
                        "actionable_notes": opportunity.get('notes', 'No additional notes'),
                        "priority_score": self._calculate_priority_score(opportunity)
                    }
                    high_priority.append(formatted_opportunity)
            
            # Sort by priority score
            high_priority.sort(key=lambda x: x['priority_score'], reverse=True)
            return high_priority[:5]  # Top 5 high-priority opportunities
            
        except Exception as e:
            self.logger.error(f"Failed to filter high priority opportunities: {e}")
            return []
    
    def _group_opportunities_by_timeframe(self, trading_opportunities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group trading opportunities by timeframe."""
        try:
            grouped = {}
            
            for opportunity in trading_opportunities:
                timeframe = opportunity.get('timeframe', 'unknown')
                if timeframe not in grouped:
                    grouped[timeframe] = []
                
                grouped[timeframe].append({
                    "pair": opportunity.get('pair', 'Unknown'),
                    "type": opportunity.get('opportunity_type', 'Unknown'),
                    "correlation": opportunity.get('correlation', 0.0),
                    "confidence": opportunity.get('confidence', 'low'),
                    "entry_signal": opportunity.get('entry_signal', 'Monitor for entry')
                })
            
            # Sort each timeframe by confidence and correlation strength
            for timeframe in grouped:
                grouped[timeframe].sort(key=lambda x: (
                    x['confidence'] == 'high',
                    abs(x['correlation'])
                ), reverse=True)
            
            return grouped
            
        except Exception as e:
            self.logger.error(f"Failed to group opportunities by timeframe: {e}")
            return {}
    
    def _group_opportunities_by_type(self, trading_opportunities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group trading opportunities by type."""
        try:
            grouped = {}
            
            for opportunity in trading_opportunities:
                opp_type = opportunity.get('opportunity_type', 'unknown')
                if opp_type not in grouped:
                    grouped[opp_type] = []
                
                grouped[opp_type].append({
                    "pair": opportunity.get('pair', 'Unknown'),
                    "timeframe": opportunity.get('timeframe', 'Unknown'),
                    "correlation": opportunity.get('correlation', 0.0),
                    "confidence": opportunity.get('confidence', 'low'),
                    "entry_signal": opportunity.get('entry_signal', 'Monitor for entry')
                })
            
            return grouped
            
        except Exception as e:
            self.logger.error(f"Failed to group opportunities by type: {e}")
            return {}
    
    def _extract_risk_mitigation(self, portfolio_recommendations: List[Dict[str, Any]]) -> List[str]:
        """Extract risk mitigation recommendations."""
        try:
            risk_mitigation = []
            
            for rec in portfolio_recommendations:
                rec_type = rec.get('type', '')
                action = rec.get('action', '')
                
                if 'risk' in rec_type.lower() or 'concentration' in rec_type.lower():
                    risk_mitigation.append(action)
                elif 'reduce' in action.lower() or 'hedge' in action.lower():
                    risk_mitigation.append(action)
            
            # Add default recommendations if none found
            if not risk_mitigation:
                risk_mitigation = [
                    "Monitor correlation changes for risk concentration",
                    "Maintain appropriate position sizing",
                    "Review portfolio diversification regularly"
                ]
            
            return risk_mitigation[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to extract risk mitigation: {e}")
            return ["Monitor risk levels carefully"]
    
    def _categorize_recommendations(self, portfolio_recommendations: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Categorize portfolio recommendations by type."""
        try:
            categorized = {
                'allocation': [],
                'diversification': [],
                'rebalancing': [],
                'risk_management': [],
                'trading': [],
                'general': []
            }
            
            for rec in portfolio_recommendations:
                rec_type = rec.get('type', 'general').lower()
                action = rec.get('action', 'No action specified')
                
                if 'allocation' in rec_type or 'position' in rec_type:
                    categorized['allocation'].append(action)
                elif 'diversif' in rec_type:
                    categorized['diversification'].append(action)
                elif 'rebalanc' in rec_type:
                    categorized['rebalancing'].append(action)
                elif 'risk' in rec_type:
                    categorized['risk_management'].append(action)
                elif 'trading' in rec_type or 'trade' in rec_type:
                    categorized['trading'].append(action)
                else:
                    categorized['general'].append(action)
            
            # Remove empty categories
            return {k: v for k, v in categorized.items() if v}
            
        except Exception as e:
            self.logger.error(f"Failed to categorize recommendations: {e}")
            return {'general': ['Review portfolio allocation']}
    
    def _extract_position_sizing_guidance(self, portfolio_recommendations: List[Dict[str, Any]], 
                                         risk_analysis: Dict[str, Any]) -> List[str]:
        """Extract position sizing guidance."""
        try:
            guidance = []
            
            # From portfolio recommendations
            for rec in portfolio_recommendations:
                action = rec.get('action', '').lower()
                if 'position' in action or 'size' in action or 'allocation' in action:
                    guidance.append(rec.get('action', 'Review position sizes'))
            
            # From risk analysis
            overall_risk = risk_analysis.get('overall_risk_level', 'medium')
            if overall_risk == 'high':
                guidance.append("Reduce position sizes due to high risk environment")
            elif overall_risk == 'low':
                guidance.append("Consider increasing position sizes in low risk environment")
            
            concentration_risk = risk_analysis.get('concentration_risk', 'medium')
            if concentration_risk == 'high':
                guidance.append("Reduce positions in highly correlated assets")
            
            # Default guidance if none found
            if not guidance:
                guidance = [
                    "Maintain position sizes appropriate for current risk level",
                    "Monitor correlation changes that may affect position sizing"
                ]
            
            return guidance[:3]  # Limit to 3 items
            
        except Exception as e:
            self.logger.error(f"Failed to extract position sizing guidance: {e}")
            return ["Review position sizing based on current market conditions"]
    
    def _extract_rebalancing_signals(self, portfolio_recommendations: List[Dict[str, Any]]) -> List[str]:
        """Extract rebalancing signals."""
        try:
            signals = []
            
            for rec in portfolio_recommendations:
                rec_type = rec.get('type', '').lower()
                action = rec.get('action', '')
                
                if 'rebalanc' in rec_type:
                    signals.append(action)
                elif 'reduce' in action.lower() or 'increase' in action.lower():
                    signals.append(f"Rebalancing signal: {action}")
            
            if not signals:
                signals = ["No immediate rebalancing signals detected"]
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Failed to extract rebalancing signals: {e}")
            return ["Monitor for rebalancing opportunities"]
    
    def _extract_matrix_summary(self, enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract correlation matrix summary."""
        try:
            # Try to get from original mosaic data
            mosaic_data = enhanced_analysis.get('correlation_matrix', {})
            summary = mosaic_data.get('summary', {})
            
            return {
                "total_pairs": summary.get('total_pairs', 0),
                "significant_correlations": summary.get('significant_correlations', 0),
                "strong_correlations": summary.get('strong_correlations', 0),
                "weak_correlations": summary.get('weak_correlations', 0),
                "negative_correlations": summary.get('negative_correlations', 0),
                "average_correlation_strength": summary.get('average_correlation_strength', 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract matrix summary: {e}")
            return {"total_pairs": 0, "analysis_error": "Unable to extract correlation matrix summary"}
    
    def _extract_significance_analysis(self, enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract statistical significance analysis."""
        try:
            mosaic_data = enhanced_analysis.get('correlation_matrix', {})
            matrix = mosaic_data.get('matrix', {})
            
            total_correlations = 0
            significant_correlations = 0
            high_confidence_correlations = 0
            
            for pair, correlations in matrix.items():
                for timeframe, data in correlations.items():
                    if isinstance(data, dict):
                        total_correlations += 1
                        
                        significance = data.get('significance', False)
                        p_value = data.get('p_value', 1.0)
                        
                        if significance:
                            significant_correlations += 1
                        
                        if isinstance(p_value, (int, float)) and p_value < 0.01:
                            high_confidence_correlations += 1
            
            return {
                "total_correlations_tested": total_correlations,
                "statistically_significant": significant_correlations,
                "high_confidence": high_confidence_correlations,
                "significance_rate": significant_correlations / total_correlations if total_correlations > 0 else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract significance analysis: {e}")
            return {"analysis_error": "Unable to extract significance analysis"}
    
    def _calculate_confidence_intervals(self, enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confidence intervals for key metrics."""
        try:
            # This is a simplified implementation
            # In practice, you'd calculate actual confidence intervals
            
            mosaic_data = enhanced_analysis.get('correlation_matrix', {})
            summary = mosaic_data.get('summary', {})
            
            avg_correlation = summary.get('average_correlation_strength', 0.0)
            
            # Simplified confidence interval estimation
            # In practice, use proper statistical methods
            margin_of_error = 0.05  # Simplified
            
            return {
                "average_correlation": {
                    "point_estimate": avg_correlation,
                    "confidence_interval_95": [
                        max(-1.0, avg_correlation - margin_of_error),
                        min(1.0, avg_correlation + margin_of_error)
                    ]
                },
                "methodology": "Simplified estimation - use with caution"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate confidence intervals: {e}")
            return {"analysis_error": "Unable to calculate confidence intervals"}
    
    def _assess_data_quality(self, enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess data quality metrics."""
        try:
            mosaic_data = enhanced_analysis.get('correlation_matrix', {})
            matrix = mosaic_data.get('matrix', {})
            
            total_data_points = 0
            missing_data_points = 0
            nan_correlations = 0
            insufficient_sample_size = 0
            
            for pair, correlations in matrix.items():
                for timeframe, data in correlations.items():
                    if isinstance(data, dict):
                        total_data_points += 1
                        
                        correlation = data.get('correlation')
                        sample_size = data.get('sample_size', 0)
                        
                        if correlation is None:
                            missing_data_points += 1
                        elif str(correlation).lower() == 'nan':
                            nan_correlations += 1
                        
                        if sample_size < 100:  # Arbitrary threshold
                            insufficient_sample_size += 1
            
            data_completeness = (total_data_points - missing_data_points - nan_correlations) / total_data_points if total_data_points > 0 else 0.0
            
            return {
                "total_data_points": total_data_points,
                "data_completeness": data_completeness,
                "missing_correlations": missing_data_points,
                "nan_correlations": nan_correlations,
                "insufficient_sample_size": insufficient_sample_size,
                "quality_score": max(0.0, min(1.0, data_completeness - (insufficient_sample_size / total_data_points) if total_data_points > 0 else 0.0))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to assess data quality: {e}")
            return {"analysis_error": "Unable to assess data quality"}
    
    def _generate_immediate_review_items(self, trading_opportunities: List[Dict[str, Any]], 
                                       priority_alerts: List[Dict[str, Any]]) -> List[str]:
        """Generate immediate review items."""
        try:
            review_items = []
            
            # From priority alerts
            for alert in priority_alerts:
                if alert.get('action_required', False):
                    review_items.append(f"URGENT: {alert.get('message', 'Review required')}")
            
            # From high-confidence opportunities
            high_conf_ops = [op for op in trading_opportunities if op.get('confidence') == 'high']
            if len(high_conf_ops) >= 2:
                review_items.append(f"Review {len(high_conf_ops)} high-confidence trading opportunities")
            
            # Default items if none found
            if not review_items:
                review_items = ["Review daily correlation analysis for any immediate concerns"]
            
            return review_items[:5]  # Limit to 5 items
            
        except Exception as e:
            self.logger.error(f"Failed to generate immediate review items: {e}")
            return ["Review correlation analysis results"]
    
    def _generate_monitoring_schedule(self, actionable_summary: Dict[str, Any]) -> Dict[str, str]:
        """Generate monitoring schedule."""
        try:
            monitoring_priorities = actionable_summary.get('monitoring_priorities', [])
            
            schedule = {
                "immediate": "Review high-priority opportunities and risk alerts",
                "today": "Monitor correlation changes in key pairs",
                "this_week": "Assess portfolio positioning based on correlation regime",
                "ongoing": "Track correlation breakdowns and regime changes"
            }
            
            # Customize based on priorities
            if monitoring_priorities:
                schedule["immediate"] = f"Monitor: {monitoring_priorities[0]}" if monitoring_priorities else schedule["immediate"]
            
            return schedule
            
        except Exception as e:
            self.logger.error(f"Failed to generate monitoring schedule: {e}")
            return {"immediate": "Review correlation analysis"}
    
    def _generate_follow_up_items(self, enhanced_analysis: Dict[str, Any]) -> List[str]:
        """Generate follow-up analysis items."""
        try:
            follow_up = []
            
            # Based on breakdown signals
            breakdown_signals = enhanced_analysis.get('correlation_breakdown_signals', [])
            if len(breakdown_signals) >= 2:
                follow_up.append(f"Deep dive analysis on {len(breakdown_signals)} correlation breakdown signals")
            
            # Based on trading opportunities
            trading_opportunities = enhanced_analysis.get('trading_opportunities', [])
            medium_conf_ops = [op for op in trading_opportunities if op.get('confidence') == 'medium']
            if len(medium_conf_ops) >= 3:
                follow_up.append(f"Enhanced analysis of {len(medium_conf_ops)} medium-confidence opportunities")
            
            # Based on market regime
            market_regime = enhanced_analysis.get('market_regime', {})
            if market_regime.get('confidence') == 'medium':
                follow_up.append("Additional analysis to confirm market regime classification")
            
            # Default follow-up
            if not follow_up:
                follow_up = ["Continue monitoring correlation patterns for emerging trends"]
            
            return follow_up[:3]  # Limit to 3 items
            
        except Exception as e:
            self.logger.error(f"Failed to generate follow-up items: {e}")
            return ["Continue routine correlation monitoring"]
    
    def _generate_review_triggers(self, market_regime: Dict[str, Any], 
                                risk_analysis: Dict[str, Any]) -> List[str]:
        """Generate review triggers for when to revisit analysis."""
        try:
            triggers = []
            
            # Risk-based triggers
            overall_risk = risk_analysis.get('overall_risk_level', 'medium')
            if overall_risk == 'high':
                triggers.append("If average correlation drops below 0.5")
                triggers.append("If any strong correlation breaks down significantly")
            elif overall_risk == 'low':
                triggers.append("If average correlation increases above 0.4")
            
            # Regime-based triggers
            regime = market_regime.get('regime', 'unknown')
            if regime == 'diversified':
                triggers.append("If correlation concentration increases above 30%")
            elif regime == 'trending':
                triggers.append("If strong correlations drop below current levels")
            
            # General triggers
            triggers.extend([
                "Significant market events or volatility spikes",
                "Major changes in any monitored correlation pairs",
                "Weekly review scheduled for continued monitoring"
            ])
            
            return triggers[:5]  # Limit to 5 triggers
            
        except Exception as e:
            self.logger.error(f"Failed to generate review triggers: {e}")
            return ["Weekly review or significant market changes"]
    
    # Helper methods
    def _generate_alert_id(self, alert_type: str, frequency: str) -> str:
        """Generate unique alert ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        unique_id = str(uuid.uuid4())[:8]
        return f"enhanced_{alert_type}_{frequency}_{timestamp}_{unique_id}"
    
    def _summarize_primary_risk(self, actionable_summary: Dict[str, Any]) -> str:
        """Summarize primary risk from actionable summary."""
        try:
            risk_alerts = actionable_summary.get('risk_alerts', [])
            if risk_alerts:
                return risk_alerts[0]
            else:
                return "No significant risk alerts detected"
                
        except Exception as e:
            self.logger.error(f"Failed to summarize primary risk: {e}")
            return "Risk assessment unavailable"
    
    def _generate_key_takeaways(self, actionable_summary: Dict[str, Any], 
                               market_regime: Dict[str, Any], 
                               trading_opportunities: List[Dict[str, Any]]) -> List[str]:
        """Generate key takeaways for executive summary."""
        try:
            takeaways = []
            
            # From top recommendations
            top_recommendations = actionable_summary.get('top_recommendations', [])
            if top_recommendations:
                takeaways.append(top_recommendations[0])
            
            # From market regime
            regime_description = market_regime.get('description', '')
            if regime_description:
                takeaways.append(regime_description)
            
            # From opportunities
            high_conf_ops = len([op for op in trading_opportunities if op.get('confidence') == 'high'])
            if high_conf_ops > 0:
                takeaways.append(f"{high_conf_ops} high-confidence trading opportunities available")
            
            # From immediate actions
            immediate_actions = actionable_summary.get('immediate_actions', [])
            if len(immediate_actions) > 0 and "No immediate" not in immediate_actions[0]:
                takeaways.append("Immediate action required - review priority alerts")
            
            # Ensure we have at least 3 takeaways
            while len(takeaways) < 3:
                default_takeaways = [
                    "Monitor correlation patterns for changes",
                    "Maintain appropriate risk management",
                    "Review portfolio diversification effectiveness"
                ]
                for default in default_takeaways:
                    if default not in takeaways:
                        takeaways.append(default)
                        break
            
            return takeaways[:4]  # Limit to 4 key takeaways
            
        except Exception as e:
            self.logger.error(f"Failed to generate key takeaways: {e}")
            return ["Monitor market conditions", "Review correlation patterns", "Maintain risk management"]
    
    def _determine_urgency_level(self, alert: Dict[str, Any]) -> str:
        """Determine urgency level for an alert."""
        try:
            priority = alert.get('priority', 'medium')
            action_required = alert.get('action_required', False)
            alert_type = alert.get('type', 'general')
            
            if priority == 'high' and action_required:
                return 'immediate'
            elif priority == 'high' or (action_required and alert_type in ['risk', 'opportunity']):
                return 'urgent'
            elif priority == 'medium' and action_required:
                return 'moderate'
            else:
                return 'low'
                
        except Exception as e:
            self.logger.error(f"Failed to determine urgency level: {e}")
            return 'low'
    
    def _calculate_priority_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate priority score for an opportunity."""
        try:
            score = 0.0
            
            # Confidence scoring
            confidence = opportunity.get('confidence', 'low')
            if confidence == 'high':
                score += 3.0
            elif confidence == 'medium':
                score += 2.0
            else:
                score += 1.0
            
            # Risk scoring (lower risk = higher score)
            risk_level = opportunity.get('risk_level', 'high')
            if risk_level == 'low':
                score += 2.0
            elif risk_level == 'medium':
                score += 1.0
            
            # Correlation strength scoring
            correlation = abs(opportunity.get('correlation', 0.0))
            if correlation >= 0.8:
                score += 2.0
            elif correlation >= 0.6:
                score += 1.5
            elif correlation >= 0.4:
                score += 1.0
            
            return score
            
        except Exception as e:
            self.logger.error(f"Failed to calculate priority score: {e}")
            return 1.0
    
    def _determine_alert_severity(self, priority_alerts: List[Dict[str, Any]], 
                                 risk_analysis: Dict[str, Any]) -> str:
        """Determine overall alert severity."""
        try:
            # Check for high-priority alerts
            high_priority_count = len([alert for alert in priority_alerts if alert.get('priority') == 'high'])
            
            # Check overall risk level
            overall_risk = risk_analysis.get('overall_risk_level', 'medium')
            
            if high_priority_count >= 2 or overall_risk == 'high':
                return 'high'
            elif high_priority_count >= 1 or overall_risk == 'medium':
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            self.logger.error(f"Failed to determine alert severity: {e}")
            return 'medium'
    
    def _calculate_overall_confidence(self, enhanced_analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the analysis."""
        try:
            confidence_factors = []
            
            # Market regime confidence
            market_regime = enhanced_analysis.get('market_regime', {})
            regime_confidence = market_regime.get('confidence', 'low')
            
            confidence_map = {'high': 0.9, 'medium': 0.7, 'low': 0.4}
            confidence_factors.append(confidence_map.get(regime_confidence, 0.5))
            
            # Data quality
            enhanced_metrics = enhanced_analysis.get('enhanced_metrics', {})
            pairs_with_data = enhanced_metrics.get('pairs_with_data', 0)
            
            if pairs_with_data >= 20:
                confidence_factors.append(0.9)
            elif pairs_with_data >= 15:
                confidence_factors.append(0.7)
            elif pairs_with_data >= 10:
                confidence_factors.append(0.5)
            else:
                confidence_factors.append(0.3)
            
            # Trading opportunities confidence
            trading_opportunities = enhanced_analysis.get('trading_opportunities', [])
            high_conf_ops = len([op for op in trading_opportunities if op.get('confidence') == 'high'])
            
            if high_conf_ops >= 3:
                confidence_factors.append(0.8)
            elif high_conf_ops >= 1:
                confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.4)
            
            # Calculate weighted average
            if confidence_factors:
                return sum(confidence_factors) / len(confidence_factors)
            else:
                return 0.5
                
        except Exception as e:
            self.logger.error(f"Failed to calculate overall confidence: {e}")
            return 0.5
    
    def _create_fallback_alert(self, enhanced_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback alert if main creation fails."""
        try:
            alert_id = self._generate_alert_id('fallback_mosaic', 'daily')
            timestamp = int(datetime.now().timestamp() * 1000)
            
            return {
                "timestamp": timestamp,
                "alert_type": "enhanced_daily_correlation_mosaic_fallback",
                "alert_id": alert_id,
                "date": datetime.now().strftime('%Y-%m-%d'),
                "version": "2.0",
                "status": "partial_analysis",
                "executive_summary": {
                    "market_assessment": "Analysis partially completed",
                    "primary_recommendation": "Review correlation data manually",
                    "opportunity_highlight": "Unable to assess opportunities due to processing error",
                    "immediate_action_required": False,
                    "key_takeaways": ["Manual review required", "Check data quality", "Retry analysis"]
                },
                "error_info": {
                    "message": "Enhanced analysis failed - fallback alert generated",
                    "recommendation": "Review logs and retry analysis"
                },
                "alert_metadata": {
                    "severity": "medium",
                    "category": "enhanced_correlation_analysis",
                    "report_type": "fallback_summary",
                    "confidence_score": 0.2,
                    "expires_at": int((datetime.now() + timedelta(hours=6)).timestamp() * 1000)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create fallback alert: {e}")
            return {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "alert_type": "error",
                "message": "Critical error in alert generation"
            }
