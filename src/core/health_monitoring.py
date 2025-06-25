"""
Health Monitoring System for comfy2c4d MVVM Components

Provides comprehensive health checking, performance monitoring,
and fault detection for all application components.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set
import asyncio
import time
from collections import deque
from loguru import logger
from PySide6.QtCore import QObject, Signal, QTimer


class HealthStatus(Enum):
    """Component health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Types of metrics to track"""
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    QUEUE_DEPTH = "queue_depth"
    CONNECTION_STATUS = "connection_status"


@dataclass
class HealthCheck:
    """Health check configuration"""
    name: str
    check_function: Callable[[], bool]
    interval_seconds: int = 30
    timeout_seconds: int = 5
    failure_threshold: int = 3
    recovery_threshold: int = 2
    severity: str = "warning"  # info, warning, error, critical


@dataclass
class HealthMetric:
    """Health metric data point"""
    timestamp: datetime
    metric_type: MetricType
    value: float
    component: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentHealth:
    """Health status for a component"""
    component_name: str
    status: HealthStatus
    last_check: datetime
    consecutive_failures: int = 0
    metrics: Dict[MetricType, deque] = field(default_factory=dict)
    active_issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HealthMonitor(QObject):
    """
    Centralized health monitoring for all application components.
    
    Features:
    - Component health checks with configurable intervals
    - Performance metric tracking
    - Anomaly detection
    - Automatic recovery triggers
    - Integration with telemetry system
    """
    
    # Signals
    health_changed = Signal(str, HealthStatus)  # component, status
    metric_recorded = Signal(str, MetricType, float)  # component, type, value
    anomaly_detected = Signal(str, str)  # component, description
    recovery_triggered = Signal(str, str)  # component, action
    
    def __init__(self):
        super().__init__()
        self._components: Dict[str, ComponentHealth] = {}
        self._health_checks: Dict[str, List[HealthCheck]] = {}
        self._check_timers: Dict[str, QTimer] = {}
        self._metric_retention = timedelta(hours=1)
        self._anomaly_detectors: List[Callable] = []
        self._recovery_actions: Dict[str, List[Callable]] = {}
        self._monitoring_enabled = True
        
        # Performance thresholds
        self._thresholds = {
            MetricType.LATENCY: {"warning": 1000, "critical": 5000},  # ms
            MetricType.ERROR_RATE: {"warning": 0.05, "critical": 0.20},  # percentage
            MetricType.MEMORY_USAGE: {"warning": 500, "critical": 1000},  # MB
            MetricType.QUEUE_DEPTH: {"warning": 100, "critical": 500},  # items
        }
        
        logger.info("Health monitoring system initialized")
    
    def register_component(self, component_name: str, health_checks: List[HealthCheck] = None):
        """Register a component for health monitoring"""
        if component_name not in self._components:
            self._components[component_name] = ComponentHealth(
                component_name=component_name,
                status=HealthStatus.UNKNOWN,
                last_check=datetime.now(),
                metrics={metric_type: deque(maxlen=1000) for metric_type in MetricType}
            )
            
        if health_checks:
            self._health_checks[component_name] = health_checks
            self._start_health_checks(component_name)
            
        logger.debug(f"Registered component for monitoring: {component_name}")
    
    def record_metric(self, component: str, metric_type: MetricType, value: float, 
                     metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric"""
        if not self._monitoring_enabled:
            return
            
        if component not in self._components:
            self.register_component(component)
        
        metric = HealthMetric(
            timestamp=datetime.now(),
            metric_type=metric_type,
            value=value,
            component=component,
            metadata=metadata or {}
        )
        
        self._components[component].metrics[metric_type].append(metric)
        self.metric_recorded.emit(component, metric_type, value)
        
        # Check for anomalies
        self._check_anomalies(component, metric_type, value)
        
        # Update component health based on metrics
        self._update_health_from_metrics(component)
    
    def _check_anomalies(self, component: str, metric_type: MetricType, value: float):
        """Check for anomalies in metrics"""
        if metric_type in self._thresholds:
            thresholds = self._thresholds[metric_type]
            
            if value >= thresholds.get("critical", float('inf')):
                self.anomaly_detected.emit(
                    component, 
                    f"Critical {metric_type.value}: {value}"
                )
                self._trigger_recovery(component, "critical_threshold")
                
            elif value >= thresholds.get("warning", float('inf')):
                self.anomaly_detected.emit(
                    component, 
                    f"Warning {metric_type.value}: {value}"
                )
    
    def _update_health_from_metrics(self, component: str):
        """Update component health based on recent metrics"""
        comp_health = self._components[component]
        issues = []
        
        # Analyze recent metrics
        for metric_type, metrics in comp_health.metrics.items():
            if not metrics:
                continue
                
            recent_metrics = [m for m in metrics 
                            if m.timestamp > datetime.now() - timedelta(minutes=5)]
            
            if not recent_metrics:
                continue
            
            avg_value = sum(m.value for m in recent_metrics) / len(recent_metrics)
            
            if metric_type in self._thresholds:
                thresholds = self._thresholds[metric_type]
                if avg_value >= thresholds.get("critical", float('inf')):
                    issues.append(f"{metric_type.value} critical: {avg_value:.2f}")
                elif avg_value >= thresholds.get("warning", float('inf')):
                    issues.append(f"{metric_type.value} warning: {avg_value:.2f}")
        
        # Determine health status
        old_status = comp_health.status
        if not issues:
            new_status = HealthStatus.HEALTHY
        elif any("critical" in issue for issue in issues):
            new_status = HealthStatus.CRITICAL
        elif len(issues) > 2:
            new_status = HealthStatus.UNHEALTHY
        else:
            new_status = HealthStatus.DEGRADED
        
        # Update component health
        comp_health.status = new_status
        comp_health.active_issues = issues
        
        if old_status != new_status:
            self.health_changed.emit(component, new_status)
            logger.info(f"Component {component} health changed: {old_status.value} -> {new_status.value}")
    
    def _start_health_checks(self, component: str):
        """Start health check timers for a component"""
        for check in self._health_checks.get(component, []):
            timer = QTimer()
            timer.timeout.connect(lambda c=check, comp=component: self._run_health_check(comp, c))
            timer.start(check.interval_seconds * 1000)
            
            timer_key = f"{component}_{check.name}"
            self._check_timers[timer_key] = timer
    
    def _run_health_check(self, component: str, check: HealthCheck):
        """Execute a health check"""
        try:
            # Run check with timeout
            result = asyncio.run(asyncio.wait_for(
                asyncio.coroutine(check.check_function)(),
                timeout=check.timeout_seconds
            ))
            
            comp_health = self._components[component]
            
            if result:
                # Check passed
                comp_health.consecutive_failures = 0
                if check.name in comp_health.active_issues:
                    comp_health.active_issues.remove(check.name)
            else:
                # Check failed
                comp_health.consecutive_failures += 1
                if comp_health.consecutive_failures >= check.failure_threshold:
                    if check.name not in comp_health.active_issues:
                        comp_health.active_issues.append(check.name)
                    self._trigger_recovery(component, f"health_check_failed:{check.name}")
            
            comp_health.last_check = datetime.now()
            
        except asyncio.TimeoutError:
            logger.error(f"Health check timeout: {component}/{check.name}")
            self._handle_check_failure(component, check, "timeout")
        except Exception as e:
            logger.error(f"Health check error: {component}/{check.name} - {e}")
            self._handle_check_failure(component, check, str(e))
    
    def _handle_check_failure(self, component: str, check: HealthCheck, reason: str):
        """Handle health check failure"""
        comp_health = self._components[component]
        comp_health.consecutive_failures += 1
        
        if comp_health.consecutive_failures >= check.failure_threshold:
            comp_health.status = HealthStatus.UNHEALTHY
            self.health_changed.emit(component, HealthStatus.UNHEALTHY)
            self.anomaly_detected.emit(component, f"Health check failed: {check.name} - {reason}")
            self._trigger_recovery(component, "health_check_failure")
    
    def _trigger_recovery(self, component: str, trigger: str):
        """Trigger recovery actions for a component"""
        if component in self._recovery_actions:
            for action in self._recovery_actions[component]:
                try:
                    action(component, trigger)
                    self.recovery_triggered.emit(component, f"Recovery action executed: {trigger}")
                except Exception as e:
                    logger.error(f"Recovery action failed: {component} - {e}")
    
    def register_recovery_action(self, component: str, action: Callable):
        """Register a recovery action for a component"""
        if component not in self._recovery_actions:
            self._recovery_actions[component] = []
        self._recovery_actions[component].append(action)
    
    def register_anomaly_detector(self, detector: Callable):
        """Register a custom anomaly detector"""
        self._anomaly_detectors.append(detector)
    
    def get_component_health(self, component: str) -> Optional[ComponentHealth]:
        """Get current health status for a component"""
        return self._components.get(component)
    
    def get_all_health_status(self) -> Dict[str, HealthStatus]:
        """Get health status for all components"""
        return {name: comp.status for name, comp in self._components.items()}
    
    def get_recent_metrics(self, component: str, metric_type: MetricType, 
                          minutes: int = 60) -> List[HealthMetric]:
        """Get recent metrics for a component"""
        if component not in self._components:
            return []
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        metrics = self._components[component].metrics.get(metric_type, [])
        return [m for m in metrics if m.timestamp > cutoff]
    
    def calculate_sla_metrics(self, component: str, hours: int = 24) -> Dict[str, float]:
        """Calculate SLA metrics for a component"""
        if component not in self._components:
            return {}
        
        comp_health = self._components[component]
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Calculate uptime percentage
        total_checks = 0
        healthy_checks = 0
        
        # This is simplified - in production, you'd track state changes
        # For now, we'll use current status as proxy
        uptime = 100.0 if comp_health.status == HealthStatus.HEALTHY else 0.0
        
        # Calculate average latency
        latency_metrics = [m for m in comp_health.metrics.get(MetricType.LATENCY, [])
                          if m.timestamp > cutoff]
        avg_latency = sum(m.value for m in latency_metrics) / len(latency_metrics) if latency_metrics else 0
        
        # Calculate error rate
        error_metrics = [m for m in comp_health.metrics.get(MetricType.ERROR_RATE, [])
                        if m.timestamp > cutoff]
        avg_error_rate = sum(m.value for m in error_metrics) / len(error_metrics) if error_metrics else 0
        
        return {
            "uptime_percentage": uptime,
            "average_latency_ms": avg_latency,
            "error_rate": avg_error_rate,
            "health_status": comp_health.status.value
        }
    
    def enable_monitoring(self, enabled: bool = True):
        """Enable or disable monitoring"""
        self._monitoring_enabled = enabled
        logger.info(f"Health monitoring {'enabled' if enabled else 'disabled'}")
    
    def shutdown(self):
        """Shutdown health monitoring"""
        # Stop all timers
        for timer in self._check_timers.values():
            timer.stop()
        
        self._check_timers.clear()
        self._components.clear()
        logger.info("Health monitoring system shut down")


# Singleton instance
_health_monitor = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor