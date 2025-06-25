"""
Telemetry System for comfy2c4d ConfigurationManager

Provides comprehensive observability for configuration management,
tracking changes, access patterns, and performance metrics.
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict, deque
from threading import Lock
import hashlib
from loguru import logger


class TelemetryEventType(Enum):
    """Types of telemetry events"""
    CONFIG_READ = "config_read"
    CONFIG_WRITE = "config_write"
    CONFIG_DELETE = "config_delete"
    CONFIG_VALIDATION = "config_validation"
    CONFIG_MIGRATION = "config_migration"
    CONFIG_CONFLICT = "config_conflict"
    LAYER_ACCESS = "layer_access"
    OBSERVER_NOTIFICATION = "observer_notification"
    PERFORMANCE_METRIC = "performance_metric"
    ERROR = "error"


class ConfigLayer(Enum):
    """Configuration layers"""
    DEFAULT = "default"
    ENVIRONMENT = "environment"
    USER = "user"
    SESSION = "session"
    RUNTIME = "runtime"


@dataclass
class TelemetryEvent:
    """Base telemetry event"""
    timestamp: datetime
    event_type: TelemetryEventType
    component: str
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "component": self.component,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata
        }


@dataclass
class ConfigAccessEvent(TelemetryEvent):
    """Configuration access event"""
    config_path: str
    layer: ConfigLayer
    value: Any = None
    success: bool = True
    access_count: int = 1


@dataclass
class ConfigChangeEvent(TelemetryEvent):
    """Configuration change event"""
    config_path: str
    layer: ConfigLayer
    old_value: Any = None
    new_value: Any = None
    change_source: str = "unknown"
    
    def __post_init__(self):
        # Calculate value hash for tracking
        self.metadata["old_value_hash"] = self._hash_value(self.old_value)
        self.metadata["new_value_hash"] = self._hash_value(self.new_value)
    
    def _hash_value(self, value: Any) -> str:
        """Create hash of configuration value"""
        try:
            value_str = json.dumps(value, sort_keys=True)
            return hashlib.md5(value_str.encode()).hexdigest()[:8]
        except:
            return "unhashable"


@dataclass
class PerformanceMetric:
    """Performance metric for configuration operations"""
    operation: str
    duration_ms: float
    layer: Optional[ConfigLayer] = None
    cache_hit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigurationTelemetry:
    """
    Telemetry system for configuration management.
    
    Features:
    - Event tracking and aggregation
    - Access pattern analysis
    - Performance monitoring
    - Change tracking
    - Anomaly detection
    - Report generation
    """
    
    def __init__(self, buffer_size: int = 10000):
        self._events: deque = deque(maxlen=buffer_size)
        self._access_patterns: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._change_history: Dict[str, List[ConfigChangeEvent]] = defaultdict(list)
        self._performance_metrics: deque = deque(maxlen=1000)
        self._hot_paths: Dict[str, int] = defaultdict(int)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._lock = Lock()
        self._enabled = True
        
        # Anomaly detection thresholds
        self._anomaly_thresholds = {
            "access_rate_spike": 100,  # accesses per minute
            "error_rate": 0.1,  # 10% error rate
            "slow_operation": 100,  # ms
            "frequent_changes": 10  # changes per minute
        }
        
        logger.info("Configuration telemetry system initialized")
    
    def enable(self, enabled: bool = True):
        """Enable or disable telemetry collection"""
        self._enabled = enabled
        logger.info(f"Telemetry {'enabled' if enabled else 'disabled'}")
    
    def track_access(self, config_path: str, layer: ConfigLayer, value: Any = None, 
                    success: bool = True, duration_ms: Optional[float] = None):
        """Track configuration access"""
        if not self._enabled:
            return
        
        with self._lock:
            event = ConfigAccessEvent(
                timestamp=datetime.now(),
                event_type=TelemetryEventType.CONFIG_READ,
                component="ConfigurationManager",
                config_path=config_path,
                layer=layer,
                value=value,
                success=success,
                duration_ms=duration_ms
            )
            
            self._events.append(event)
            self._access_patterns[config_path].append(event.timestamp)
            
            # Track hot paths
            self._hot_paths[config_path] += 1
            
            # Track errors
            if not success:
                self._error_counts[config_path] += 1
    
    def track_change(self, config_path: str, layer: ConfigLayer, 
                    old_value: Any, new_value: Any, change_source: str = "unknown",
                    duration_ms: Optional[float] = None):
        """Track configuration change"""
        if not self._enabled:
            return
        
        with self._lock:
            event = ConfigChangeEvent(
                timestamp=datetime.now(),
                event_type=TelemetryEventType.CONFIG_WRITE,
                component="ConfigurationManager",
                config_path=config_path,
                layer=layer,
                old_value=old_value,
                new_value=new_value,
                change_source=change_source,
                duration_ms=duration_ms
            )
            
            self._events.append(event)
            self._change_history[config_path].append(event)
            
            # Check for rapid changes
            self._check_rapid_changes(config_path)
    
    def track_performance(self, operation: str, duration_ms: float, 
                         layer: Optional[ConfigLayer] = None, cache_hit: bool = False):
        """Track performance metric"""
        if not self._enabled:
            return
        
        with self._lock:
            metric = PerformanceMetric(
                operation=operation,
                duration_ms=duration_ms,
                layer=layer,
                cache_hit=cache_hit
            )
            
            self._performance_metrics.append(metric)
            
            # Check for slow operations
            if duration_ms > self._anomaly_thresholds["slow_operation"]:
                logger.warning(f"Slow configuration operation: {operation} took {duration_ms}ms")
    
    def track_error(self, config_path: str, error: Exception, operation: str):
        """Track configuration error"""
        if not self._enabled:
            return
        
        with self._lock:
            event = TelemetryEvent(
                timestamp=datetime.now(),
                event_type=TelemetryEventType.ERROR,
                component="ConfigurationManager",
                metadata={
                    "config_path": config_path,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "operation": operation
                }
            )
            
            self._events.append(event)
            self._error_counts[f"{config_path}:{operation}"] += 1
    
    def _check_rapid_changes(self, config_path: str):
        """Check for rapid configuration changes"""
        recent_changes = [
            event for event in self._change_history[config_path]
            if event.timestamp > datetime.now() - timedelta(minutes=1)
        ]
        
        if len(recent_changes) > self._anomaly_thresholds["frequent_changes"]:
            logger.warning(f"Rapid configuration changes detected for {config_path}: "
                         f"{len(recent_changes)} changes in last minute")
    
    def get_hot_paths(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently accessed configuration paths"""
        with self._lock:
            sorted_paths = sorted(self._hot_paths.items(), 
                                key=lambda x: x[1], reverse=True)
            return sorted_paths[:top_n]
    
    def get_access_pattern(self, config_path: str, 
                          time_window_minutes: int = 60) -> Dict[str, Any]:
        """Analyze access pattern for a configuration path"""
        with self._lock:
            accesses = self._access_patterns.get(config_path, deque())
            cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
            recent_accesses = [ts for ts in accesses if ts > cutoff]
            
            if not recent_accesses:
                return {"access_count": 0, "access_rate": 0.0}
            
            # Calculate access rate
            time_span = (recent_accesses[-1] - recent_accesses[0]).total_seconds() / 60
            access_rate = len(recent_accesses) / max(time_span, 1)
            
            return {
                "access_count": len(recent_accesses),
                "access_rate": access_rate,
                "first_access": recent_accesses[0].isoformat(),
                "last_access": recent_accesses[-1].isoformat(),
                "peak_minute": self._find_peak_minute(recent_accesses)
            }
    
    def _find_peak_minute(self, timestamps: List[datetime]) -> Optional[str]:
        """Find the minute with most accesses"""
        if not timestamps:
            return None
        
        minute_counts = defaultdict(int)
        for ts in timestamps:
            minute_key = ts.strftime("%Y-%m-%d %H:%M")
            minute_counts[minute_key] += 1
        
        peak_minute = max(minute_counts.items(), key=lambda x: x[1])
        return f"{peak_minute[0]} ({peak_minute[1]} accesses)"
    
    def get_change_history(self, config_path: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get change history for a configuration path"""
        with self._lock:
            changes = self._change_history.get(config_path, [])
            recent_changes = changes[-limit:] if changes else []
            
            return [
                {
                    "timestamp": change.timestamp.isoformat(),
                    "layer": change.layer.value,
                    "old_value_hash": change.metadata.get("old_value_hash"),
                    "new_value_hash": change.metadata.get("new_value_hash"),
                    "change_source": change.change_source
                }
                for change in recent_changes
            ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        with self._lock:
            if not self._performance_metrics:
                return {}
            
            metrics_by_operation = defaultdict(list)
            for metric in self._performance_metrics:
                metrics_by_operation[metric.operation].append(metric.duration_ms)
            
            summary = {}
            for operation, durations in metrics_by_operation.items():
                summary[operation] = {
                    "count": len(durations),
                    "avg_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "p95_ms": sorted(durations)[int(len(durations) * 0.95)]
                }
            
            # Cache statistics
            cache_hits = sum(1 for m in self._performance_metrics if m.cache_hit)
            total_cached_ops = sum(1 for m in self._performance_metrics 
                                 if m.metadata.get("cacheable", False))
            
            summary["cache"] = {
                "hit_rate": cache_hits / max(total_cached_ops, 1),
                "total_hits": cache_hits
            }
            
            return summary
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary"""
        with self._lock:
            total_errors = sum(self._error_counts.values())
            error_events = [e for e in self._events 
                          if e.event_type == TelemetryEventType.ERROR]
            
            # Group errors by type
            errors_by_type = defaultdict(int)
            for event in error_events:
                error_type = event.metadata.get("error_type", "Unknown")
                errors_by_type[error_type] += 1
            
            return {
                "total_errors": total_errors,
                "error_paths": dict(self._error_counts),
                "errors_by_type": dict(errors_by_type),
                "recent_errors": [
                    {
                        "timestamp": e.timestamp.isoformat(),
                        "path": e.metadata.get("config_path"),
                        "error": e.metadata.get("error_message"),
                        "operation": e.metadata.get("operation")
                    }
                    for e in error_events[-10:]
                ]
            }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive telemetry report"""
        return {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_events": len(self._events),
                "unique_paths": len(self._hot_paths),
                "total_changes": sum(len(changes) for changes in self._change_history.values()),
                "total_errors": sum(self._error_counts.values())
            },
            "hot_paths": dict(self.get_hot_paths()),
            "performance": self.get_performance_summary(),
            "errors": self.get_error_summary(),
            "anomalies": self._detect_anomalies()
        }
    
    def _detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in configuration usage"""
        anomalies = []
        
        # Check for high access rates
        for path, accesses in self._access_patterns.items():
            pattern = self.get_access_pattern(path, time_window_minutes=5)
            if pattern["access_rate"] > self._anomaly_thresholds["access_rate_spike"]:
                anomalies.append({
                    "type": "high_access_rate",
                    "path": path,
                    "access_rate": pattern["access_rate"],
                    "threshold": self._anomaly_thresholds["access_rate_spike"]
                })
        
        # Check for high error rates
        total_accesses = sum(self._hot_paths.values())
        total_errors = sum(self._error_counts.values())
        if total_accesses > 0:
            error_rate = total_errors / total_accesses
            if error_rate > self._anomaly_thresholds["error_rate"]:
                anomalies.append({
                    "type": "high_error_rate",
                    "error_rate": error_rate,
                    "threshold": self._anomaly_thresholds["error_rate"]
                })
        
        return anomalies
    
    def export_events(self, filepath: Path, format: str = "jsonl"):
        """Export telemetry events to file"""
        with self._lock:
            if format == "jsonl":
                with open(filepath, "w") as f:
                    for event in self._events:
                        f.write(json.dumps(event.to_dict()) + "\n")
            elif format == "json":
                with open(filepath, "w") as f:
                    json.dump([event.to_dict() for event in self._events], f, indent=2)
    
    def clear(self):
        """Clear all telemetry data"""
        with self._lock:
            self._events.clear()
            self._access_patterns.clear()
            self._change_history.clear()
            self._performance_metrics.clear()
            self._hot_paths.clear()
            self._error_counts.clear()


# Context manager for timing operations
class TelemetryTimer:
    """Context manager for timing configuration operations"""
    
    def __init__(self, telemetry: ConfigurationTelemetry, operation: str, 
                 layer: Optional[ConfigLayer] = None):
        self.telemetry = telemetry
        self.operation = operation
        self.layer = layer
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.telemetry.track_performance(
            self.operation, duration_ms, self.layer
        )


# Global instance
_config_telemetry = None


def get_configuration_telemetry() -> ConfigurationTelemetry:
    """Get the global configuration telemetry instance"""
    global _config_telemetry
    if _config_telemetry is None:
        _config_telemetry = ConfigurationTelemetry()
    return _config_telemetry