#!/usr/bin/env python3
"""
Health Checker for Paper Trading Engine
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Individual health metric"""
    name: str
    status: HealthStatus
    value: Any
    message: str
    timestamp: datetime
    threshold: Optional[float] = None


class HealthChecker:
    """System health monitoring and reporting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, HealthMetric] = {}
        self.start_time = datetime.now()
        self.last_check = None
        
        # Health thresholds
        self.thresholds = {
            'memory_usage_mb': 500.0,  # 500MB memory limit
            'cpu_usage_percent': 80.0,  # 80% CPU limit
            'disk_usage_percent': 90.0,  # 90% disk limit
            'api_response_time_ms': 5000.0,  # 5 second API timeout
            'error_rate_percent': 5.0,  # 5% error rate limit
            'trade_execution_time_ms': 1000.0,  # 1 second trade execution
        }
    
    def add_metric(self, name: str, status: HealthStatus, value: Any, 
                   message: str, threshold: Optional[float] = None) -> None:
        """Add or update a health metric"""
        self.metrics[name] = HealthMetric(
            name=name,
            status=status,
            value=value,
            message=message,
            timestamp=datetime.now(),
            threshold=threshold
        )
    
    def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        try:
            # Check memory usage
            self._check_memory_usage()
            
            # Check CPU usage
            self._check_cpu_usage()
            
            # Check disk usage
            self._check_disk_usage()
            
            # Check API connectivity
            self._check_api_connectivity()
            
            # Check error rates
            self._check_error_rates()
            
            # Check trade execution performance
            self._check_trade_performance()
            
            # Generate overall health status
            overall_status = self._calculate_overall_status()
            
            self.last_check = datetime.now()
            
            return {
                'status': overall_status.value,
                'timestamp': self.last_check.isoformat(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'metrics': {name: {
                    'status': metric.status.value,
                    'value': metric.value,
                    'message': metric.message,
                    'timestamp': metric.timestamp.isoformat(),
                    'threshold': metric.threshold
                } for name, metric in self.metrics.items()}
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                'status': HealthStatus.CRITICAL.value,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'metrics': {}
            }
    
    def _check_memory_usage(self) -> None:
        """Check system memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            usage_mb = memory.used / (1024 * 1024)
            threshold = self.thresholds['memory_usage_mb']
            
            if usage_mb > threshold:
                status = HealthStatus.CRITICAL
                message = f"Memory usage {usage_mb:.1f}MB exceeds threshold {threshold}MB"
            elif usage_mb > threshold * 0.8:
                status = HealthStatus.WARNING
                message = f"Memory usage {usage_mb:.1f}MB approaching threshold {threshold}MB"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage {usage_mb:.1f}MB is normal"
            
            self.add_metric('memory_usage_mb', status, usage_mb, message, threshold)
            
        except ImportError:
            self.add_metric('memory_usage_mb', HealthStatus.UNKNOWN, 0, 
                           "psutil not available", self.thresholds['memory_usage_mb'])
        except Exception as e:
            self.add_metric('memory_usage_mb', HealthStatus.CRITICAL, 0, 
                           f"Memory check failed: {e}", self.thresholds['memory_usage_mb'])
    
    def _check_cpu_usage(self) -> None:
        """Check system CPU usage"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            threshold = self.thresholds['cpu_usage_percent']
            
            if cpu_percent > threshold:
                status = HealthStatus.CRITICAL
                message = f"CPU usage {cpu_percent:.1f}% exceeds threshold {threshold}%"
            elif cpu_percent > threshold * 0.8:
                status = HealthStatus.WARNING
                message = f"CPU usage {cpu_percent:.1f}% approaching threshold {threshold}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage {cpu_percent:.1f}% is normal"
            
            self.add_metric('cpu_usage_percent', status, cpu_percent, message, threshold)
            
        except ImportError:
            self.add_metric('cpu_usage_percent', HealthStatus.UNKNOWN, 0, 
                           "psutil not available", self.thresholds['cpu_usage_percent'])
        except Exception as e:
            self.add_metric('cpu_usage_percent', HealthStatus.CRITICAL, 0, 
                           f"CPU check failed: {e}", self.thresholds['cpu_usage_percent'])
    
    def _check_disk_usage(self) -> None:
        """Check disk usage"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            threshold = self.thresholds['disk_usage_percent']
            
            if usage_percent > threshold:
                status = HealthStatus.CRITICAL
                message = f"Disk usage {usage_percent:.1f}% exceeds threshold {threshold}%"
            elif usage_percent > threshold * 0.8:
                status = HealthStatus.WARNING
                message = f"Disk usage {usage_percent:.1f}% approaching threshold {threshold}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage {usage_percent:.1f}% is normal"
            
            self.add_metric('disk_usage_percent', status, usage_percent, message, threshold)
            
        except ImportError:
            self.add_metric('disk_usage_percent', HealthStatus.UNKNOWN, 0, 
                           "psutil not available", self.thresholds['disk_usage_percent'])
        except Exception as e:
            self.add_metric('disk_usage_percent', HealthStatus.CRITICAL, 0, 
                           f"Disk check failed: {e}", self.thresholds['disk_usage_percent'])
    
    def _check_api_connectivity(self) -> None:
        """Check API connectivity and response time"""
        try:
            import requests
            start_time = time.time()
            
            # Test CoinGecko API connectivity
            response = requests.get('https://api.coingecko.com/api/v3/ping', timeout=5)
            response_time_ms = (time.time() - start_time) * 1000
            threshold = self.thresholds['api_response_time_ms']
            
            if response.status_code == 200:
                if response_time_ms > threshold:
                    status = HealthStatus.WARNING
                    message = f"API response time {response_time_ms:.0f}ms is slow"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"API response time {response_time_ms:.0f}ms is normal"
            else:
                status = HealthStatus.CRITICAL
                message = f"API returned status {response.status_code}"
            
            self.add_metric('api_response_time_ms', status, response_time_ms, message, threshold)
            
        except Exception as e:
            self.add_metric('api_response_time_ms', HealthStatus.CRITICAL, 0, 
                           f"API connectivity failed: {e}", self.thresholds['api_response_time_ms'])
    
    def _check_error_rates(self) -> None:
        """Check error rates (placeholder for now)"""
        # This would be implemented with actual error tracking
        error_rate = 0.0  # Placeholder
        threshold = self.thresholds['error_rate_percent']
        
        if error_rate > threshold:
            status = HealthStatus.CRITICAL
            message = f"Error rate {error_rate:.1f}% exceeds threshold {threshold}%"
        elif error_rate > threshold * 0.5:
            status = HealthStatus.WARNING
            message = f"Error rate {error_rate:.1f}% is elevated"
        else:
            status = HealthStatus.HEALTHY
            message = f"Error rate {error_rate:.1f}% is normal"
        
        self.add_metric('error_rate_percent', status, error_rate, message, threshold)
    
    def _check_trade_performance(self) -> None:
        """Check trade execution performance (placeholder)"""
        # This would be implemented with actual trade timing data
        avg_execution_time = 100.0  # Placeholder - 100ms
        threshold = self.thresholds['trade_execution_time_ms']
        
        if avg_execution_time > threshold:
            status = HealthStatus.WARNING
            message = f"Trade execution time {avg_execution_time:.0f}ms is slow"
        else:
            status = HealthStatus.HEALTHY
            message = f"Trade execution time {avg_execution_time:.0f}ms is normal"
        
        self.add_metric('trade_execution_time_ms', status, avg_execution_time, message, threshold)
    
    def _calculate_overall_status(self) -> HealthStatus:
        """Calculate overall system health status"""
        if not self.metrics:
            return HealthStatus.UNKNOWN
        
        status_counts = {
            HealthStatus.CRITICAL: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.HEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        for metric in self.metrics.values():
            status_counts[metric.status] += 1
        
        # If any critical, overall is critical
        if status_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        
        # If any warnings, overall is warning
        if status_counts[HealthStatus.WARNING] > 0:
            return HealthStatus.WARNING
        
        # If all healthy, overall is healthy
        if status_counts[HealthStatus.HEALTHY] > 0 and status_counts[HealthStatus.UNKNOWN] == 0:
            return HealthStatus.HEALTHY
        
        # Otherwise unknown
        return HealthStatus.UNKNOWN
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health"""
        health_data = self.check_system_health()
        
        # Count metrics by status
        status_counts = {}
        for metric_data in health_data['metrics'].values():
            status = metric_data['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'overall_status': health_data['status'],
            'timestamp': health_data['timestamp'],
            'uptime_seconds': health_data['uptime_seconds'],
            'metric_counts': status_counts,
            'total_metrics': len(health_data['metrics'])
        }
    
    def is_healthy(self) -> bool:
        """Check if system is overall healthy"""
        health_data = self.check_system_health()
        return health_data['status'] == HealthStatus.HEALTHY.value
    
    def get_critical_issues(self) -> List[str]:
        """Get list of critical health issues"""
        critical_issues = []
        
        for name, metric in self.metrics.items():
            if metric.status == HealthStatus.CRITICAL:
                critical_issues.append(f"{name}: {metric.message}")
        
        return critical_issues 