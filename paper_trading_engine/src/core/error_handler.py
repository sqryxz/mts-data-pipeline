#!/usr/bin/env python3
"""
Error Handler for Paper Trading Engine
"""

import signal
import sys
import time
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorRecord:
    """Error record for tracking"""
    timestamp: datetime
    error_type: str
    message: str
    severity: ErrorSeverity
    stack_trace: str
    context: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class ErrorHandler:
    """Comprehensive error handling and recovery system"""
    
    def __init__(self, max_errors: int = 1000, error_threshold: int = 10):
        self.logger = logging.getLogger(__name__)
        self.errors: List[ErrorRecord] = []
        self.max_errors = max_errors
        self.error_threshold = error_threshold
        self.shutdown_callbacks: List[Callable] = []
        self.recovery_callbacks: List[Callable] = []
        self.is_shutting_down = False
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def register_shutdown_callback(self, callback: Callable) -> None:
        """Register a callback to be called during shutdown"""
        self.shutdown_callbacks.append(callback)
    
    def register_recovery_callback(self, callback: Callable) -> None:
        """Register a callback to be called during error recovery"""
        self.recovery_callbacks.append(callback)
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> None:
        """Handle an error with recovery logic"""
        try:
            # Create error record
            error_record = ErrorRecord(
                timestamp=datetime.now(),
                error_type=type(error).__name__,
                message=str(error),
                severity=severity,
                stack_trace=traceback.format_exc(),
                context=context or {}
            )
            
            # Add to error list
            self.errors.append(error_record)
            
            # Trim old errors if we exceed max_errors
            if len(self.errors) > self.max_errors:
                self.errors = self.errors[-self.max_errors:]
            
            # Log the error
            self.logger.error(f"Error handled: {error_record.error_type}: {error_record.message}")
            self.logger.debug(f"Error context: {error_record.context}")
            
            # Check if we should trigger recovery
            if self._should_trigger_recovery():
                self._trigger_recovery()
            
            # Check if we should trigger shutdown
            if self._should_trigger_shutdown():
                self._trigger_shutdown()
                
        except Exception as e:
            # If error handling itself fails, log and continue
            self.logger.critical(f"Error handler failed: {e}")
    
    def _should_trigger_recovery(self) -> bool:
        """Check if we should trigger recovery based on error patterns"""
        if len(self.errors) < 3:
            return False
        
        # Check for recent critical errors
        recent_errors = [e for e in self.errors[-10:] 
                        if e.severity == ErrorSeverity.CRITICAL and 
                        (datetime.now() - e.timestamp).seconds < 60]
        
        return len(recent_errors) >= 2
    
    def _should_trigger_shutdown(self) -> bool:
        """Check if we should trigger shutdown based on error patterns"""
        if len(self.errors) < self.error_threshold:
            return False
        
        # Check for too many critical errors
        critical_errors = [e for e in self.errors[-self.error_threshold:] 
                          if e.severity == ErrorSeverity.CRITICAL]
        
        return len(critical_errors) >= self.error_threshold // 2
    
    def _trigger_recovery(self) -> None:
        """Trigger error recovery procedures"""
        self.logger.warning("Triggering error recovery procedures")
        
        try:
            for callback in self.recovery_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"Recovery callback failed: {e}")
        except Exception as e:
            self.logger.error(f"Error recovery failed: {e}")
    
    def _trigger_shutdown(self) -> None:
        """Trigger graceful shutdown"""
        self.logger.critical("Triggering graceful shutdown due to error threshold")
        self._graceful_shutdown()
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals"""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received signal {signal_name}, initiating graceful shutdown")
        self._graceful_shutdown()
    
    def _graceful_shutdown(self) -> None:
        """Perform graceful shutdown"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        self.logger.info("Starting graceful shutdown...")
        
        try:
            # Call all shutdown callbacks
            for callback in self.shutdown_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"Shutdown callback failed: {e}")
            
            # Save final state
            self._save_final_state()
            
            # Log shutdown completion
            self.logger.info("Graceful shutdown completed")
            
        except Exception as e:
            self.logger.critical(f"Shutdown failed: {e}")
        finally:
            # Exit the program
            sys.exit(0)
    
    def _save_final_state(self) -> None:
        """Save final state before shutdown"""
        try:
            # This would save the current state to persistent storage
            # For now, just log the final state
            self.logger.info("Saving final state...")
            
            # Log error summary
            error_summary = self.get_error_summary()
            self.logger.info(f"Error summary: {error_summary}")
            
        except Exception as e:
            self.logger.error(f"Failed to save final state: {e}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of recent errors"""
        if not self.errors:
            return {"total_errors": 0, "recent_errors": []}
        
        # Count errors by severity
        severity_counts = {}
        for error in self.errors:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Get recent errors (last 10)
        recent_errors = []
        for error in self.errors[-10:]:
            recent_errors.append({
                "timestamp": error.timestamp.isoformat(),
                "type": error.error_type,
                "message": error.message,
                "severity": error.severity.value,
                "resolved": error.resolved
            })
        
        return {
            "total_errors": len(self.errors),
            "severity_counts": severity_counts,
            "recent_errors": recent_errors,
            "error_rate": self._calculate_error_rate()
        }
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate per minute"""
        if len(self.errors) < 2:
            return 0.0
        
        # Calculate time span of errors
        first_error = self.errors[0].timestamp
        last_error = self.errors[-1].timestamp
        time_span_minutes = (last_error - first_error).total_seconds() / 60
        
        if time_span_minutes == 0:
            return float(len(self.errors))
        
        return len(self.errors) / time_span_minutes
    
    def mark_error_resolved(self, error_index: int) -> None:
        """Mark an error as resolved"""
        if 0 <= error_index < len(self.errors):
            self.errors[error_index].resolved = True
            self.errors[error_index].resolution_time = datetime.now()
    
    def get_unresolved_errors(self) -> List[ErrorRecord]:
        """Get list of unresolved errors"""
        return [error for error in self.errors if not error.resolved]
    
    def clear_old_errors(self, days: int = 7) -> None:
        """Clear errors older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        self.errors = [error for error in self.errors if error.timestamp > cutoff_time]
    
    def is_system_healthy(self) -> bool:
        """Check if system is healthy based on error patterns"""
        if not self.errors:
            return True
        
        # Check for recent critical errors
        recent_critical = [e for e in self.errors[-10:] 
                          if e.severity == ErrorSeverity.CRITICAL and 
                          (datetime.now() - e.timestamp).seconds < 300]  # 5 minutes
        
        return len(recent_critical) == 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status"""
        error_summary = self.get_error_summary()
        unresolved_count = len(self.get_unresolved_errors())
        
        return {
            "healthy": self.is_system_healthy(),
            "total_errors": error_summary["total_errors"],
            "unresolved_errors": unresolved_count,
            "error_rate_per_minute": error_summary["error_rate"],
            "severity_distribution": error_summary["severity_counts"],
            "recent_errors": error_summary["recent_errors"][-5:]  # Last 5 errors
        }


class GracefulShutdown:
    """Context manager for graceful shutdown"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Handle any unhandled exceptions
            self.error_handler.handle_error(
                exc_val, 
                context={"type": "unhandled_exception"},
                severity=ErrorSeverity.CRITICAL
            )
        
        # Ensure graceful shutdown
        if not self.error_handler.is_shutting_down:
            self.error_handler._graceful_shutdown() 