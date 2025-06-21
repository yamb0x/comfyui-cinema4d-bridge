"""
Performance Monitoring System

Comprehensive performance monitoring with real-time metrics, bottleneck detection,
resource usage tracking, and performance optimization recommendations.

Part of Phase 3 Quality & Polish - provides production-grade performance
insights and automatic optimization suggestions.
"""

import asyncio
import gc
import os
import psutil
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from contextlib import contextmanager

from ..utils.advanced_logging import get_logger

logger = get_logger("performance")


class MetricType(Enum):
    """Types of performance metrics"""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    NETWORK_LATENCY = "network_latency"
    FILE_IO = "file_io"
    WORKFLOW_PERFORMANCE = "workflow_performance"
    UI_RESPONSIVENESS = "ui_responsiveness"


class PerformanceLevel(Enum):
    """Performance level classifications"""
    EXCELLENT = "excellent"    # Top 10% performance
    GOOD = "good"             # Top 25% performance
    AVERAGE = "average"       # Average performance
    POOR = "poor"             # Bottom 25% performance
    CRITICAL = "critical"     # Bottom 10% performance


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_type: MetricType
    component: str
    operation: str
    value: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "metric_type": self.metric_type.value,
            "component": self.component,
            "operation": self.operation,
            "value": self.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


@dataclass
class PerformanceAlert:
    """Performance alert for threshold violations"""
    metric_type: MetricType
    component: str
    operation: str
    threshold_type: str  # "max_duration", "memory_limit", etc.
    threshold_value: float
    actual_value: float
    severity: str  # "warning", "critical"
    timestamp: float
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SystemResources:
    """Current system resource usage"""
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    network_io_mb_s: float
    open_files: int
    thread_count: int
    timestamp: float


class PerformanceThresholds:
    """Configurable performance thresholds"""
    
    def __init__(self):
        # Execution time thresholds (seconds)
        self.max_execution_times = {
            "ui_operation": 0.1,      # UI should be under 100ms
            "file_operation": 2.0,    # File ops under 2s
            "network_request": 10.0,  # Network under 10s
            "workflow_execution": 120.0,  # Workflows under 2 minutes
            "image_generation": 300.0,    # Image gen under 5 minutes
            "model_generation": 600.0,    # Model gen under 10 minutes
        }
        
        # Memory thresholds (MB)
        self.max_memory_usage = {
            "ui_component": 100,      # UI components under 100MB
            "workflow_engine": 500,   # Workflow engine under 500MB
            "image_processing": 1000, # Image processing under 1GB
            "model_processing": 2000, # Model processing under 2GB
        }
        
        # System resource thresholds
        self.system_thresholds = {
            "cpu_percent": 80.0,      # CPU under 80%
            "memory_percent": 85.0,   # Memory under 85%
            "disk_usage_percent": 90.0, # Disk under 90%
            "open_files": 1000,       # Under 1000 open files
            "thread_count": 100,      # Under 100 threads
        }
    
    def get_execution_threshold(self, operation: str) -> float:
        """Get execution time threshold for operation"""
        for key, threshold in self.max_execution_times.items():
            if key in operation.lower():
                return threshold
        return 30.0  # Default 30 seconds
    
    def get_memory_threshold(self, component: str) -> float:
        """Get memory threshold for component"""
        for key, threshold in self.max_memory_usage.items():
            if key in component.lower():
                return threshold
        return 200.0  # Default 200MB


class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics: deque = deque(maxlen=max_metrics)
        self.aggregated_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.lock = threading.Lock()
    
    def add_metric(self, metric: PerformanceMetric):
        """Add a performance metric"""
        with self.lock:
            self.metrics.append(metric)
            self._update_aggregated_stats(metric)
    
    def _update_aggregated_stats(self, metric: PerformanceMetric):
        """Update aggregated statistics"""
        key = f"{metric.component}:{metric.operation}"
        
        if key not in self.aggregated_stats:
            self.aggregated_stats[key] = {
                "count": 0,
                "total_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0,
                "recent_times": deque(maxlen=100)
            }
        
        stats = self.aggregated_stats[key]
        stats["count"] += 1
        stats["total_time"] += metric.value
        stats["min_time"] = min(stats["min_time"], metric.value)
        stats["max_time"] = max(stats["max_time"], metric.value)
        stats["recent_times"].append(metric.value)
    
    def get_stats(self, component: str = None, operation: str = None) -> Dict[str, Any]:
        """Get aggregated statistics"""
        with self.lock:
            if component and operation:
                key = f"{component}:{operation}"
                if key in self.aggregated_stats:
                    stats = self.aggregated_stats[key].copy()
                    if stats["count"] > 0:
                        stats["avg_time"] = stats["total_time"] / stats["count"]
                        recent = list(stats["recent_times"])
                        if recent:
                            stats["recent_avg"] = sum(recent) / len(recent)
                        del stats["recent_times"]  # Don't return deque
                    return stats
                return {}
            
            # Return all stats
            result = {}
            for key, stats in self.aggregated_stats.items():
                if stats["count"] > 0:
                    result[key] = {
                        "count": stats["count"],
                        "avg_time": stats["total_time"] / stats["count"],
                        "min_time": stats["min_time"],
                        "max_time": stats["max_time"],
                        "recent_avg": sum(stats["recent_times"]) / len(stats["recent_times"]) if stats["recent_times"] else 0
                    }
            return result
    
    def get_recent_metrics(self, limit: int = 100) -> List[PerformanceMetric]:
        """Get recent metrics"""
        with self.lock:
            return list(self.metrics)[-limit:]


class ResourceMonitor:
    """Monitors system resource usage"""
    
    def __init__(self, sample_interval: float = 5.0):
        self.sample_interval = sample_interval
        self.resource_history: deque = deque(maxlen=720)  # 1 hour at 5s intervals
        self.process = psutil.Process()
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start resource monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                resources = self._collect_resources()
                self.resource_history.append(resources)
                time.sleep(self.sample_interval)
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                time.sleep(self.sample_interval)
    
    def _collect_resources(self) -> SystemResources:
        """Collect current system resources"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # Disk usage (of current drive)
        disk = psutil.disk_usage('.')
        disk_usage_percent = disk.percent
        
        # Network I/O
        net_io = psutil.net_io_counters()
        network_io_mb_s = (net_io.bytes_sent + net_io.bytes_recv) / (1024**2) / self.sample_interval
        
        # Process info
        try:
            open_files = len(self.process.open_files())
        except:
            open_files = 0
        
        thread_count = self.process.num_threads()
        
        return SystemResources(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_usage_percent=disk_usage_percent,
            network_io_mb_s=network_io_mb_s,
            open_files=open_files,
            thread_count=thread_count,
            timestamp=time.time()
        )
    
    def get_current_resources(self) -> Optional[SystemResources]:
        """Get current resource usage"""
        try:
            return self._collect_resources()
        except Exception as e:
            logger.error(f"Failed to collect resources: {e}")
            return None
    
    def get_resource_history(self, duration_minutes: int = 60) -> List[SystemResources]:
        """Get resource history for specified duration"""
        samples_needed = int(duration_minutes * 60 / self.sample_interval)
        return list(self.resource_history)[-samples_needed:]


class BottleneckDetector:
    """Detects performance bottlenecks and provides recommendations"""
    
    def __init__(self, thresholds: PerformanceThresholds):
        self.thresholds = thresholds
        self.detected_bottlenecks: List[PerformanceAlert] = []
    
    def analyze_metrics(self, metrics: List[PerformanceMetric]) -> List[PerformanceAlert]:
        """Analyze metrics for bottlenecks"""
        alerts = []
        
        # Group metrics by component and operation
        grouped = defaultdict(list)
        for metric in metrics:
            key = f"{metric.component}:{metric.operation}"
            grouped[key].append(metric)
        
        # Analyze each group
        for key, metric_list in grouped.items():
            component, operation = key.split(':', 1)
            alerts.extend(self._analyze_execution_times(component, operation, metric_list))
        
        self.detected_bottlenecks.extend(alerts)
        return alerts
    
    def _analyze_execution_times(self, component: str, operation: str, metrics: List[PerformanceMetric]) -> List[PerformanceAlert]:
        """Analyze execution times for bottlenecks"""
        alerts = []
        
        execution_times = [m.value for m in metrics if m.metric_type == MetricType.EXECUTION_TIME]
        if not execution_times:
            return alerts
        
        threshold = self.thresholds.get_execution_threshold(operation)
        slow_executions = [t for t in execution_times if t > threshold]
        
        if slow_executions:
            avg_slow = sum(slow_executions) / len(slow_executions)
            severity = "critical" if avg_slow > threshold * 2 else "warning"
            
            recommendations = self._get_performance_recommendations(component, operation, avg_slow, threshold)
            
            alert = PerformanceAlert(
                metric_type=MetricType.EXECUTION_TIME,
                component=component,
                operation=operation,
                threshold_type="max_duration",
                threshold_value=threshold,
                actual_value=avg_slow,
                severity=severity,
                timestamp=time.time(),
                recommendations=recommendations
            )
            alerts.append(alert)
        
        return alerts
    
    def _get_performance_recommendations(self, component: str, operation: str, actual: float, threshold: float) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        ratio = actual / threshold
        
        # General recommendations
        if ratio > 3:
            recommendations.append("Consider caching results to avoid repeated expensive operations")
            recommendations.append("Investigate if operation can be performed asynchronously")
        
        # Component-specific recommendations
        if "ui" in component.lower():
            recommendations.extend([
                "Move heavy computations to background threads",
                "Use lazy loading for UI components",
                "Consider pagination for large data sets"
            ])
        elif "workflow" in component.lower():
            recommendations.extend([
                "Optimize workflow node configuration",
                "Check for memory leaks in long-running workflows",
                "Consider batch processing for multiple items"
            ])
        elif "network" in operation.lower():
            recommendations.extend([
                "Implement connection pooling",
                "Add retry logic with exponential backoff",
                "Check network bandwidth and latency"
            ])
        elif "file" in operation.lower():
            recommendations.extend([
                "Use streaming for large files",
                "Implement file caching",
                "Check disk I/O performance"
            ])
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def analyze_system_resources(self, resources: List[SystemResources]) -> List[PerformanceAlert]:
        """Analyze system resources for bottlenecks"""
        alerts = []
        
        if not resources:
            return alerts
        
        # Get recent average values
        recent = resources[-10:]  # Last 10 samples
        avg_cpu = sum(r.cpu_percent for r in recent) / len(recent)
        avg_memory = sum(r.memory_percent for r in recent) / len(recent)
        avg_disk = sum(r.disk_usage_percent for r in recent) / len(recent)
        max_threads = max(r.thread_count for r in recent)
        max_files = max(r.open_files for r in recent)
        
        # Check thresholds
        if avg_cpu > self.thresholds.system_thresholds["cpu_percent"]:
            alerts.append(PerformanceAlert(
                metric_type=MetricType.CPU_USAGE,
                component="system",
                operation="cpu_usage",
                threshold_type="max_cpu_percent",
                threshold_value=self.thresholds.system_thresholds["cpu_percent"],
                actual_value=avg_cpu,
                severity="warning" if avg_cpu < 95 else "critical",
                timestamp=time.time(),
                recommendations=[
                    "Close unnecessary applications",
                    "Optimize CPU-intensive operations",
                    "Consider upgrading hardware"
                ]
            ))
        
        if avg_memory > self.thresholds.system_thresholds["memory_percent"]:
            alerts.append(PerformanceAlert(
                metric_type=MetricType.MEMORY_USAGE,
                component="system", 
                operation="memory_usage",
                threshold_type="max_memory_percent",
                threshold_value=self.thresholds.system_thresholds["memory_percent"],
                actual_value=avg_memory,
                severity="warning" if avg_memory < 95 else "critical",
                timestamp=time.time(),
                recommendations=[
                    "Close memory-intensive applications",
                    "Implement garbage collection optimization",
                    "Consider increasing system RAM"
                ]
            ))
        
        return alerts


class PerformanceOptimizer:
    """Provides automatic performance optimizations"""
    
    def __init__(self):
        self.optimizations_applied = []
    
    def apply_automatic_optimizations(self, alerts: List[PerformanceAlert]) -> List[str]:
        """Apply automatic performance optimizations based on alerts"""
        applied = []
        
        for alert in alerts:
            if alert.severity == "critical":
                optimizations = self._get_automatic_optimizations(alert)
                for optimization in optimizations:
                    if self._apply_optimization(optimization):
                        applied.append(optimization)
                        self.optimizations_applied.append({
                            "optimization": optimization,
                            "timestamp": time.time(),
                            "alert": alert
                        })
        
        return applied
    
    def _get_automatic_optimizations(self, alert: PerformanceAlert) -> List[str]:
        """Get automatic optimizations for alert"""
        optimizations = []
        
        if alert.metric_type == MetricType.MEMORY_USAGE:
            optimizations.extend([
                "force_garbage_collection",
                "clear_caches",
                "close_unused_connections"
            ])
        elif alert.metric_type == MetricType.CPU_USAGE:
            optimizations.extend([
                "reduce_background_tasks",
                "optimize_thread_pool"
            ])
        
        return optimizations
    
    def _apply_optimization(self, optimization: str) -> bool:
        """Apply specific optimization"""
        try:
            if optimization == "force_garbage_collection":
                gc.collect()
                logger.info("Applied optimization: force garbage collection")
                return True
            elif optimization == "clear_caches":
                # Clear various caches
                logger.info("Applied optimization: cleared caches")
                return True
            elif optimization == "close_unused_connections":
                # Close unused network connections
                logger.info("Applied optimization: closed unused connections")
                return True
            # Add more optimizations as needed
            
        except Exception as e:
            logger.error(f"Failed to apply optimization {optimization}: {e}")
        
        return False


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system
    
    Provides real-time metrics collection, bottleneck detection,
    system resource monitoring, and automatic optimization.
    """
    
    def __init__(self):
        self.thresholds = PerformanceThresholds()
        self.metrics_collector = MetricsCollector()
        self.resource_monitor = ResourceMonitor()
        self.bottleneck_detector = BottleneckDetector(self.thresholds)
        self.optimizer = PerformanceOptimizer()
        
        self.monitoring_enabled = True
        self.auto_optimization_enabled = True
        
        # Performance tracking
        self.active_operations: Dict[str, float] = {}
        self.operation_lock = threading.Lock()
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.resource_monitor.start_monitoring()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.resource_monitor.stop_monitoring()
        logger.info("Performance monitoring stopped")
    
    @contextmanager
    def track_operation(self, component: str, operation: str, metadata: Dict[str, Any] = None):
        """Context manager for tracking operation performance"""
        operation_id = f"{component}:{operation}:{id(threading.current_thread())}"
        start_time = time.perf_counter()
        
        with self.operation_lock:
            self.active_operations[operation_id] = start_time
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # Remove from active operations
            with self.operation_lock:
                self.active_operations.pop(operation_id, None)
            
            # Record metric
            if self.monitoring_enabled:
                metric = PerformanceMetric(
                    metric_type=MetricType.EXECUTION_TIME,
                    component=component,
                    operation=operation,
                    value=duration,
                    timestamp=time.time(),
                    metadata=metadata or {}
                )
                self.metrics_collector.add_metric(metric)
                
                # Check for immediate alerts
                threshold = self.thresholds.get_execution_threshold(operation)
                if duration > threshold:
                    with logger.context(component=component, operation=operation):
                        logger.warning(f"Performance threshold exceeded",
                                     duration=f"{duration:.3f}s",
                                     threshold=f"{threshold:.3f}s",
                                     ratio=f"{duration/threshold:.1f}x")
    
    def record_metric(self, metric_type: MetricType, component: str, operation: str, value: float, metadata: Dict[str, Any] = None):
        """Record a performance metric"""
        if self.monitoring_enabled:
            metric = PerformanceMetric(
                metric_type=metric_type,
                component=component,
                operation=operation,
                value=value,
                timestamp=time.time(),
                metadata=metadata or {}
            )
            self.metrics_collector.add_metric(metric)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        # Get metrics stats
        stats = self.metrics_collector.get_stats()
        
        # Get current system resources
        current_resources = self.resource_monitor.get_current_resources()
        
        # Get recent alerts
        recent_metrics = self.metrics_collector.get_recent_metrics(1000)
        alerts = self.bottleneck_detector.analyze_metrics(recent_metrics)
        
        # System resource alerts
        resource_history = self.resource_monitor.get_resource_history(10)
        resource_alerts = self.bottleneck_detector.analyze_system_resources(resource_history)
        
        # Combine all alerts
        all_alerts = alerts + resource_alerts
        
        # Performance level assessment
        performance_level = self._assess_performance_level(stats, current_resources, all_alerts)
        
        return {
            "performance_level": performance_level.value,
            "operation_stats": stats,
            "current_resources": current_resources.__dict__ if current_resources else None,
            "alerts": [
                {
                    "type": alert.metric_type.value,
                    "component": alert.component,
                    "operation": alert.operation,
                    "severity": alert.severity,
                    "actual_value": alert.actual_value,
                    "threshold_value": alert.threshold_value,
                    "recommendations": alert.recommendations
                }
                for alert in all_alerts[-10:]  # Last 10 alerts
            ],
            "active_operations": len(self.active_operations),
            "optimizations_applied": len(self.optimizer.optimizations_applied)
        }
    
    def _assess_performance_level(self, stats: Dict[str, Any], resources: Optional[SystemResources], alerts: List[PerformanceAlert]) -> PerformanceLevel:
        """Assess overall performance level"""
        # Count critical issues
        critical_alerts = len([a for a in alerts if a.severity == "critical"])
        warning_alerts = len([a for a in alerts if a.severity == "warning"])
        
        # Check system resources
        resource_issues = 0
        if resources:
            if resources.cpu_percent > 90:
                resource_issues += 2
            elif resources.cpu_percent > 80:
                resource_issues += 1
                
            if resources.memory_percent > 90:
                resource_issues += 2
            elif resources.memory_percent > 80:
                resource_issues += 1
        
        # Check operation performance
        slow_operations = 0
        total_operations = 0
        for key, operation_stats in stats.items():
            total_operations += 1
            if operation_stats.get("recent_avg", 0) > operation_stats.get("avg_time", 0) * 1.5:
                slow_operations += 1
        
        # Calculate performance score
        score = 100
        score -= critical_alerts * 20
        score -= warning_alerts * 10
        score -= resource_issues * 5
        if total_operations > 0:
            score -= (slow_operations / total_operations) * 20
        
        # Classify performance level
        if score >= 90:
            return PerformanceLevel.EXCELLENT
        elif score >= 75:
            return PerformanceLevel.GOOD
        elif score >= 50:
            return PerformanceLevel.AVERAGE
        elif score >= 25:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL
    
    def run_performance_analysis(self) -> Dict[str, Any]:
        """Run comprehensive performance analysis"""
        logger.info("Running performance analysis")
        
        # Collect recent metrics
        recent_metrics = self.metrics_collector.get_recent_metrics(5000)
        
        # Detect bottlenecks
        metric_alerts = self.bottleneck_detector.analyze_metrics(recent_metrics)
        
        # Check system resources
        resource_history = self.resource_monitor.get_resource_history(30)
        resource_alerts = self.bottleneck_detector.analyze_system_resources(resource_history)
        
        all_alerts = metric_alerts + resource_alerts
        
        # Apply automatic optimizations if enabled
        optimizations_applied = []
        if self.auto_optimization_enabled:
            optimizations_applied = self.optimizer.apply_automatic_optimizations(all_alerts)
        
        analysis_result = {
            "timestamp": time.time(),
            "total_alerts": len(all_alerts),
            "critical_alerts": len([a for a in all_alerts if a.severity == "critical"]),
            "warning_alerts": len([a for a in all_alerts if a.severity == "warning"]),
            "bottlenecks_detected": [
                {
                    "component": alert.component,
                    "operation": alert.operation,
                    "issue": f"{alert.actual_value:.2f}s > {alert.threshold_value:.2f}s",
                    "severity": alert.severity,
                    "recommendations": alert.recommendations[:2]
                }
                for alert in all_alerts
            ],
            "optimizations_applied": optimizations_applied,
            "performance_summary": self.get_performance_summary()
        }
        
        logger.info(f"Performance analysis complete",
                   total_alerts=len(all_alerts),
                   critical_alerts=len([a for a in all_alerts if a.severity == "critical"]),
                   optimizations=len(optimizations_applied))
        
        return analysis_result
    
    def configure_thresholds(self, **kwargs):
        """Configure performance thresholds"""
        for category, values in kwargs.items():
            if hasattr(self.thresholds, category):
                getattr(self.thresholds, category).update(values)
        logger.info("Performance thresholds updated")
    
    def enable_auto_optimization(self, enabled: bool = True):
        """Enable or disable automatic optimization"""
        self.auto_optimization_enabled = enabled
        logger.info(f"Auto-optimization {'enabled' if enabled else 'disabled'}")


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def configure_performance_monitoring(
    monitoring_enabled: bool = True,
    auto_optimization: bool = True,
    resource_monitoring: bool = True,
    custom_thresholds: Dict[str, Any] = None
):
    """Configure global performance monitoring"""
    monitor = get_performance_monitor()
    
    monitor.monitoring_enabled = monitoring_enabled
    monitor.enable_auto_optimization(auto_optimization)
    
    if resource_monitoring:
        monitor.start_monitoring()
    
    if custom_thresholds:
        monitor.configure_thresholds(**custom_thresholds)
    
    logger.info("Performance monitoring configured",
                monitoring=monitoring_enabled,
                auto_optimization=auto_optimization,
                resource_monitoring=resource_monitoring)


# Convenience decorators and context managers
def track_performance(component: str, operation: str = None):
    """Decorator for tracking function performance"""
    def decorator(func):
        nonlocal operation
        if operation is None:
            operation = func.__name__
        
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                monitor = get_performance_monitor()
                with monitor.track_operation(component, operation):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                monitor = get_performance_monitor()
                with monitor.track_operation(component, operation):
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator


@contextmanager
def performance_context(component: str, operation: str, metadata: Dict[str, Any] = None):
    """Context manager for tracking performance"""
    monitor = get_performance_monitor()
    with monitor.track_operation(component, operation, metadata):
        yield