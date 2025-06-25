"""
Reliability Integration Module for comfy2c4d

Integrates all reliability patterns and provides a unified interface
for the application to use fault-tolerant components.
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from loguru import logger
from PySide6.QtCore import QObject, Signal

from .health_monitoring import get_health_monitor, HealthCheck, HealthStatus, MetricType
from .circuit_breaker import get_observer_chain_breaker, CircuitBreakerConfig
from .telemetry import get_configuration_telemetry, ConfigLayer
from .parameter_rules_engine import get_parameter_rules_engine
from ..testing.fault_injection import get_fault_injection_manager, FaultScenarios


class ReliabilityManager(QObject):
    """
    Central manager for all reliability features.
    
    Provides:
    - Unified initialization and configuration
    - Cross-component health checks
    - Coordinated fault handling
    - System-wide reliability metrics
    """
    
    # Signals
    system_health_changed = Signal(str)  # health_status
    reliability_event = Signal(str, str)  # component, event
    
    def __init__(self):
        super().__init__()
        self._health_monitor = get_health_monitor()
        self._observer_breaker = get_observer_chain_breaker()
        self._config_telemetry = get_configuration_telemetry()
        self._rules_engine = get_parameter_rules_engine()
        self._fault_manager = get_fault_injection_manager()
        
        self._initialized = False
        logger.info("Reliability manager initialized")
    
    def initialize(self, enable_fault_injection: bool = False):
        """Initialize all reliability components"""
        if self._initialized:
            return
        
        # Register core components for health monitoring
        self._register_health_checks()
        
        # Configure observer chain breakers
        self._configure_circuit_breakers()
        
        # Enable telemetry
        self._config_telemetry.enable(True)
        
        # Enable fault injection if requested (testing only)
        if enable_fault_injection:
            self._fault_manager.enable(True)
            self._configure_fault_scenarios()
        
        # Start health monitoring
        asyncio.create_task(self._health_monitor.start_cleanup_task())
        
        self._initialized = True
        logger.info("Reliability system fully initialized")
    
    def _register_health_checks(self):
        """Register health checks for core components"""
        
        # Configuration Manager health checks
        self._health_monitor.register_component(
            "ConfigurationManager",
            [
                HealthCheck(
                    name="config_access",
                    check_function=self._check_config_access,
                    interval_seconds=30,
                    failure_threshold=3
                ),
                HealthCheck(
                    name="config_consistency",
                    check_function=self._check_config_consistency,
                    interval_seconds=60,
                    failure_threshold=2
                )
            ]
        )
        
        # Parameter Rules Engine health checks
        self._health_monitor.register_component(
            "ParameterRulesEngine",
            [
                HealthCheck(
                    name="rule_extraction",
                    check_function=self._check_rule_extraction,
                    interval_seconds=45,
                    failure_threshold=3
                )
            ]
        )
        
        # Observer Chain health checks
        self._health_monitor.register_component(
            "ObserverChains",
            [
                HealthCheck(
                    name="chain_integrity",
                    check_function=self._check_observer_chains,
                    interval_seconds=30,
                    failure_threshold=5
                )
            ]
        )
    
    def _configure_circuit_breakers(self):
        """Configure circuit breakers for critical paths"""
        
        # UI update observer chain
        self._observer_breaker.configure_chain(
            "ui_updates",
            CircuitBreakerConfig(
                failure_threshold=3,
                success_threshold=2,
                timeout_seconds=10,
                half_open_requests=1
            )
        )
        
        # Configuration change observer chain
        self._observer_breaker.configure_chain(
            "config_changes",
            CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=3,
                timeout_seconds=30,
                half_open_requests=2
            )
        )
        
        # Parameter sync observer chain
        self._observer_breaker.configure_chain(
            "parameter_sync",
            CircuitBreakerConfig(
                failure_threshold=4,
                success_threshold=2,
                timeout_seconds=20,
                half_open_requests=1
            )
        )
    
    def _configure_fault_scenarios(self):
        """Configure fault injection scenarios for testing"""
        
        # Parameter extraction faults
        for fault_config in FaultScenarios.parameter_extraction_faults():
            self._fault_manager.configure_fault(
                "ParameterRulesEngine",
                "extract_parameters",
                fault_config
            )
        
        # UI synchronization faults
        for fault_config in FaultScenarios.ui_sync_faults():
            self._fault_manager.configure_fault(
                "UIController",
                "sync_parameters",
                fault_config
            )
        
        # Observer pattern faults
        for fault_config in FaultScenarios.observer_pattern_faults():
            self._fault_manager.configure_fault(
                "ObserverManager",
                "notify",
                fault_config
            )
    
    # Health check implementations
    async def _check_config_access(self) -> bool:
        """Check configuration access health"""
        try:
            # Simulate config access
            telemetry_report = self._config_telemetry.get_performance_summary()
            
            # Check for high error rates
            error_summary = self._config_telemetry.get_error_summary()
            total_errors = error_summary.get("total_errors", 0)
            
            # Record metrics
            self._health_monitor.record_metric(
                "ConfigurationManager",
                MetricType.ERROR_RATE,
                total_errors / max(len(telemetry_report), 1)
            )
            
            return total_errors < 100  # Threshold for unhealthy
            
        except Exception as e:
            logger.error(f"Config access health check failed: {e}")
            return False
    
    async def _check_config_consistency(self) -> bool:
        """Check configuration consistency"""
        try:
            # Check for rapid configuration changes
            anomalies = self._config_telemetry._detect_anomalies()
            
            rapid_changes = [a for a in anomalies 
                           if a.get("type") == "frequent_changes"]
            
            return len(rapid_changes) == 0
            
        except Exception as e:
            logger.error(f"Config consistency check failed: {e}")
            return False
    
    async def _check_rule_extraction(self) -> bool:
        """Check parameter rule extraction health"""
        try:
            # Test with minimal workflow
            test_workflow = {
                "nodes": [
                    {
                        "id": "1",
                        "class_type": "KSampler",
                        "inputs": {"seed": 123, "steps": 20}
                    }
                ]
            }
            
            params = self._rules_engine.extract_parameters(test_workflow)
            return len(params) > 0
            
        except Exception as e:
            logger.error(f"Rule extraction health check failed: {e}")
            return False
    
    async def _check_observer_chains(self) -> bool:
        """Check observer chain health"""
        try:
            stats = self._observer_breaker.get_all_stats()
            
            # Check for any open circuits
            for chain_id, chain_stats in stats.items():
                if chain_stats.failed_calls > chain_stats.successful_calls:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Observer chain health check failed: {e}")
            return False
    
    # Public API
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        component_health = self._health_monitor.get_all_health_status()
        
        # Determine overall health
        statuses = list(component_health.values())
        if any(s == HealthStatus.CRITICAL for s in statuses):
            overall = HealthStatus.CRITICAL
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY
        
        return {
            "overall_status": overall.value,
            "components": {k: v.value for k, v in component_health.items()},
            "metrics": self._gather_system_metrics()
        }
    
    def _gather_system_metrics(self) -> Dict[str, Any]:
        """Gather system-wide reliability metrics"""
        return {
            "config_telemetry": self._config_telemetry.generate_report(),
            "circuit_breakers": {
                chain_id: {
                    "state": stats.state_changes[-1][1].value if stats.state_changes else "unknown",
                    "success_rate": stats.successful_calls / max(stats.total_calls, 1)
                }
                for chain_id, stats in self._observer_breaker.get_all_stats().items()
            },
            "rules_engine": self._rules_engine.get_rule_statistics(),
            "fault_injection": self._fault_manager.get_statistics() if self._fault_manager._enabled else {}
        }
    
    def wrap_config_access(self, func: Callable) -> Callable:
        """Wrap configuration access with telemetry"""
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Track successful access
                if "path" in kwargs:
                    self._config_telemetry.track_access(
                        kwargs["path"], 
                        ConfigLayer.USER,
                        result,
                        True,
                        duration_ms
                    )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Track failed access
                if "path" in kwargs:
                    self._config_telemetry.track_access(
                        kwargs["path"],
                        ConfigLayer.USER,
                        None,
                        False,
                        duration_ms
                    )
                    self._config_telemetry.track_error(
                        kwargs["path"],
                        e,
                        "config_access"
                    )
                
                raise
        
        return wrapper
    
    def notify_observers_safely(self, chain_id: str, observers: List[Callable], 
                               *args, **kwargs):
        """Safely notify observers with circuit breaker protection"""
        self._observer_breaker.notify_observers(chain_id, observers, *args, **kwargs)
    
    async def notify_observers_safely_async(self, chain_id: str, observers: List[Callable],
                                          *args, **kwargs):
        """Async version of safe observer notification"""
        await self._observer_breaker.notify_observers_async(chain_id, observers, *args, **kwargs)
    
    def extract_parameters_safely(self, workflow: Dict[str, Any]) -> List[Any]:
        """Safely extract parameters with fault tolerance"""
        return self._rules_engine.extract_parameters(workflow)
    
    def record_metric(self, component: str, metric_type: MetricType, value: float,
                     metadata: Optional[Dict[str, Any]] = None):
        """Record a reliability metric"""
        self._health_monitor.record_metric(component, metric_type, value, metadata)
    
    def shutdown(self):
        """Shutdown reliability systems"""
        logger.info("Shutting down reliability systems...")
        
        # Shutdown health monitoring
        asyncio.create_task(self._health_monitor.shutdown())
        
        # Disable telemetry
        self._config_telemetry.enable(False)
        
        # Export telemetry data
        try:
            from pathlib import Path
            telemetry_path = Path("logs/telemetry_export.jsonl")
            telemetry_path.parent.mkdir(exist_ok=True)
            self._config_telemetry.export_events(telemetry_path)
            logger.info(f"Telemetry exported to {telemetry_path}")
        except Exception as e:
            logger.error(f"Failed to export telemetry: {e}")
        
        logger.info("Reliability systems shut down")


# Global instance
_reliability_manager = None


def get_reliability_manager() -> ReliabilityManager:
    """Get the global reliability manager"""
    global _reliability_manager
    if _reliability_manager is None:
        _reliability_manager = ReliabilityManager()
    return _reliability_manager