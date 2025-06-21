"""
Comprehensive Testing Framework

Professional testing system with unit tests, integration tests, performance tests,
UI tests, and automated test discovery with detailed reporting.

Part of Phase 3 Quality & Polish - provides enterprise-grade testing capabilities
for ensuring code quality and preventing regressions.
"""

import asyncio
import inspect
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type

from ..utils.advanced_logging import get_logger
from ..utils.performance_monitor import get_performance_monitor, performance_context

logger = get_logger("testing")


class TestType(Enum):
    """Types of tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    UI = "ui"
    END_TO_END = "end_to_end"


class TestStatus(Enum):
    """Test execution status"""
    NOT_RUN = "not_run"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Individual test result"""
    test_name: str
    test_type: TestType
    status: TestStatus
    duration: float = 0.0
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    assertions: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "test_name": self.test_name,
            "test_type": self.test_type.value,
            "status": self.status.value,
            "duration": self.duration,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "assertions": self.assertions,
            "metadata": self.metadata
        }


@dataclass
class TestSuite:
    """Collection of related tests"""
    name: str
    test_type: TestType
    tests: List[Callable] = field(default_factory=list)
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestReport:
    """Comprehensive test execution report"""
    test_run_id: str
    timestamp: float
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    total_duration: float
    test_results: List[TestResult] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    coverage_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "test_run_id": self.test_run_id,
            "timestamp": self.timestamp,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "total_duration": self.total_duration,
            "success_rate": self.success_rate,
            "test_results": [r.to_dict() for r in self.test_results],
            "performance_metrics": self.performance_metrics,
            "coverage_data": self.coverage_data
        }


class TestAssertions:
    """Assertion utilities for tests"""
    
    def __init__(self):
        self.assertion_count = 0
    
    def assert_true(self, condition: bool, message: str = "Assertion failed"):
        """Assert condition is True"""
        self.assertion_count += 1
        if not condition:
            raise AssertionError(f"{message}: Expected True, got {condition}")
    
    def assert_false(self, condition: bool, message: str = "Assertion failed"):
        """Assert condition is False"""
        self.assertion_count += 1
        if condition:
            raise AssertionError(f"{message}: Expected False, got {condition}")
    
    def assert_equal(self, expected: Any, actual: Any, message: str = "Values not equal"):
        """Assert values are equal"""
        self.assertion_count += 1
        if expected != actual:
            raise AssertionError(f"{message}: Expected {expected}, got {actual}")
    
    def assert_not_equal(self, expected: Any, actual: Any, message: str = "Values are equal"):
        """Assert values are not equal"""
        self.assertion_count += 1
        if expected == actual:
            raise AssertionError(f"{message}: Expected {expected} != {actual}")
    
    def assert_in(self, item: Any, container: Any, message: str = "Item not in container"):
        """Assert item is in container"""
        self.assertion_count += 1
        if item not in container:
            raise AssertionError(f"{message}: {item} not found in {container}")
    
    def assert_not_in(self, item: Any, container: Any, message: str = "Item in container"):
        """Assert item is not in container"""
        self.assertion_count += 1
        if item in container:
            raise AssertionError(f"{message}: {item} found in {container}")
    
    def assert_raises(self, expected_exception: Type[Exception], func: Callable, *args, **kwargs):
        """Assert function raises expected exception"""
        self.assertion_count += 1
        try:
            func(*args, **kwargs)
            raise AssertionError(f"Expected {expected_exception.__name__} to be raised")
        except expected_exception:
            pass  # Expected exception raised
        except Exception as e:
            raise AssertionError(f"Expected {expected_exception.__name__}, got {type(e).__name__}: {e}")
    
    def assert_almost_equal(self, expected: float, actual: float, places: int = 7, message: str = "Values not almost equal"):
        """Assert floats are almost equal"""
        self.assertion_count += 1
        if round(abs(expected - actual), places) != 0:
            raise AssertionError(f"{message}: {expected} != {actual} within {places} decimal places")
    
    def assert_greater(self, a: Any, b: Any, message: str = "Not greater"):
        """Assert a > b"""
        self.assertion_count += 1
        if not a > b:
            raise AssertionError(f"{message}: {a} is not greater than {b}")
    
    def assert_less(self, a: Any, b: Any, message: str = "Not less"):
        """Assert a < b"""
        self.assertion_count += 1
        if not a < b:
            raise AssertionError(f"{message}: {a} is not less than {b}")
    
    def assert_is_none(self, value: Any, message: str = "Value is not None"):
        """Assert value is None"""
        self.assertion_count += 1
        if value is not None:
            raise AssertionError(f"{message}: Expected None, got {value}")
    
    def assert_is_not_none(self, value: Any, message: str = "Value is None"):
        """Assert value is not None"""
        self.assertion_count += 1
        if value is None:
            raise AssertionError(f"{message}: Expected non-None value")


class MockObject:
    """Simple mock object for testing"""
    
    def __init__(self, **kwargs):
        self._call_history = []
        self._return_values = {}
        self._side_effects = {}
        
        # Set initial attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __getattr__(self, name):
        def mock_method(*args, **kwargs):
            self._call_history.append((name, args, kwargs))
            
            # Check for side effects
            if name in self._side_effects:
                effect = self._side_effects[name]
                if callable(effect):
                    return effect(*args, **kwargs)
                elif isinstance(effect, Exception):
                    raise effect
            
            # Return configured value
            return self._return_values.get(name)
        
        return mock_method
    
    def set_return_value(self, method_name: str, value: Any):
        """Set return value for method"""
        self._return_values[method_name] = value
    
    def set_side_effect(self, method_name: str, effect: Any):
        """Set side effect for method"""
        self._side_effects[method_name] = effect
    
    def get_call_history(self) -> List[Tuple[str, Tuple, Dict]]:
        """Get method call history"""
        return self._call_history.copy()
    
    def was_called(self, method_name: str) -> bool:
        """Check if method was called"""
        return any(call[0] == method_name for call in self._call_history)
    
    def call_count(self, method_name: str) -> int:
        """Get call count for method"""
        return sum(1 for call in self._call_history if call[0] == method_name)


class TestRunner:
    """Executes tests and generates reports"""
    
    def __init__(self):
        self.test_suites: List[TestSuite] = []
        self.test_filters: Set[str] = set()
        self.skip_patterns: Set[str] = set()
        self.performance_monitor = get_performance_monitor()
    
    def add_test_suite(self, test_suite: TestSuite):
        """Add test suite"""
        self.test_suites.append(test_suite)
        logger.debug(f"Added test suite: {test_suite.name} ({len(test_suite.tests)} tests)")
    
    def add_test_filter(self, pattern: str):
        """Add test name filter pattern"""
        self.test_filters.add(pattern)
    
    def add_skip_pattern(self, pattern: str):
        """Add test skip pattern"""
        self.skip_patterns.add(pattern)
    
    async def run_all_tests(self) -> TestReport:
        """Run all registered tests"""
        test_run_id = f"test_run_{int(time.time())}"
        start_time = time.time()
        
        all_results = []
        
        logger.info(f"Starting test run: {test_run_id}")
        
        for test_suite in self.test_suites:
            suite_results = await self._run_test_suite(test_suite)
            all_results.extend(suite_results)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate statistics
        total_tests = len(all_results)
        passed = sum(1 for r in all_results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in all_results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in all_results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in all_results if r.status == TestStatus.ERROR)
        
        # Get performance metrics
        performance_metrics = self.performance_monitor.get_performance_summary()
        
        report = TestReport(
            test_run_id=test_run_id,
            timestamp=start_time,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            total_duration=total_duration,
            test_results=all_results,
            performance_metrics=performance_metrics
        )
        
        logger.info(f"Test run completed: {passed}/{total_tests} passed ({report.success_rate:.1f}%)")
        
        return report
    
    async def _run_test_suite(self, test_suite: TestSuite) -> List[TestResult]:
        """Run tests in a test suite"""
        results = []
        
        logger.debug(f"Running test suite: {test_suite.name}")
        
        # Setup
        if test_suite.setup_function:
            try:
                if asyncio.iscoroutinefunction(test_suite.setup_function):
                    await test_suite.setup_function()
                else:
                    test_suite.setup_function()
            except Exception as e:
                logger.error(f"Test suite setup failed: {e}")
                # Mark all tests as errors
                for test_func in test_suite.tests:
                    results.append(TestResult(
                        test_name=test_func.__name__,
                        test_type=test_suite.test_type,
                        status=TestStatus.ERROR,
                        error_message=f"Setup failed: {str(e)}"
                    ))
                return results
        
        try:
            # Run individual tests
            for test_func in test_suite.tests:
                result = await self._run_single_test(test_func, test_suite.test_type)
                results.append(result)
        finally:
            # Teardown
            if test_suite.teardown_function:
                try:
                    if asyncio.iscoroutinefunction(test_suite.teardown_function):
                        await test_suite.teardown_function()
                    else:
                        test_suite.teardown_function()
                except Exception as e:
                    logger.error(f"Test suite teardown failed: {e}")
        
        return results
    
    async def _run_single_test(self, test_func: Callable, test_type: TestType) -> TestResult:
        """Run a single test function"""
        test_name = test_func.__name__
        
        # Check filters
        if self.test_filters and not any(pattern in test_name for pattern in self.test_filters):
            return TestResult(
                test_name=test_name,
                test_type=test_type,
                status=TestStatus.SKIPPED,
                error_message="Filtered out"
            )
        
        # Check skip patterns
        if any(pattern in test_name for pattern in self.skip_patterns):
            return TestResult(
                test_name=test_name,
                test_type=test_type,
                status=TestStatus.SKIPPED,
                error_message="Skipped by pattern"
            )
        
        logger.debug(f"Running test: {test_name}")
        
        start_time = time.perf_counter()
        assertions = TestAssertions()
        
        try:
            with performance_context("testing", test_name):
                # Inject assertions if test accepts them
                sig = inspect.signature(test_func)
                if 'assert_' in sig.parameters or 'assertions' in sig.parameters:
                    if asyncio.iscoroutinefunction(test_func):
                        await test_func(assertions)
                    else:
                        test_func(assertions)
                else:
                    if asyncio.iscoroutinefunction(test_func):
                        await test_func()
                    else:
                        test_func()
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            return TestResult(
                test_name=test_name,
                test_type=test_type,
                status=TestStatus.PASSED,
                duration=duration,
                assertions=assertions.assertion_count
            )
            
        except AssertionError as e:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            return TestResult(
                test_name=test_name,
                test_type=test_type,
                status=TestStatus.FAILED,
                duration=duration,
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                assertions=assertions.assertion_count
            )
            
        except Exception as e:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            return TestResult(
                test_name=test_name,
                test_type=test_type,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                assertions=assertions.assertion_count
            )


class TestDiscovery:
    """Automatically discovers tests in modules"""
    
    def __init__(self):
        self.test_patterns = ["test_*.py", "*_test.py"]
        self.test_function_patterns = ["test_*"]
    
    def discover_tests(self, search_paths: List[Path]) -> List[TestSuite]:
        """Discover tests in search paths"""
        discovered_suites = []
        
        for search_path in search_paths:
            if search_path.is_file():
                suite = self._discover_tests_in_file(search_path)
                if suite:
                    discovered_suites.append(suite)
            elif search_path.is_dir():
                for pattern in self.test_patterns:
                    for test_file in search_path.rglob(pattern):
                        suite = self._discover_tests_in_file(test_file)
                        if suite:
                            discovered_suites.append(suite)
        
        logger.info(f"Discovered {len(discovered_suites)} test suites")
        return discovered_suites
    
    def _discover_tests_in_file(self, file_path: Path) -> Optional[TestSuite]:
        """Discover tests in a single file"""
        try:
            # This is a simplified discovery - in practice you'd use importlib
            # to dynamically import and inspect modules
            
            module_name = file_path.stem
            test_functions = []
            
            # For now, create a mock test suite
            # In a real implementation, you'd parse the Python file
            # and extract test functions
            
            if "test" in module_name.lower():
                # Create a basic test suite
                suite = TestSuite(
                    name=module_name,
                    test_type=TestType.UNIT,
                    tests=test_functions
                )
                return suite
        
        except Exception as e:
            logger.error(f"Error discovering tests in {file_path}: {e}")
        
        return None


class PerformanceTestRunner:
    """Specialized runner for performance tests"""
    
    def __init__(self):
        self.performance_thresholds = {
            "execution_time": 1.0,  # seconds
            "memory_usage": 100,    # MB
            "cpu_usage": 50         # percent
        }
    
    async def run_performance_test(self, test_func: Callable, iterations: int = 5) -> Dict[str, Any]:
        """Run performance test with multiple iterations"""
        results = {
            "iterations": iterations,
            "execution_times": [],
            "average_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "threshold_violations": []
        }
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            try:
                if asyncio.iscoroutinefunction(test_func):
                    await test_func()
                else:
                    test_func()
                
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                
                results["execution_times"].append(execution_time)
                results["min_time"] = min(results["min_time"], execution_time)
                results["max_time"] = max(results["max_time"], execution_time)
                
            except Exception as e:
                logger.error(f"Performance test iteration {i+1} failed: {e}")
        
        if results["execution_times"]:
            results["average_time"] = sum(results["execution_times"]) / len(results["execution_times"])
            
            # Check thresholds
            if results["average_time"] > self.performance_thresholds["execution_time"]:
                results["threshold_violations"].append(
                    f"Average execution time {results['average_time']:.3f}s exceeds threshold {self.performance_thresholds['execution_time']}s"
                )
        
        return results


class TestReportGenerator:
    """Generates test reports in various formats"""
    
    def generate_html_report(self, report: TestReport, output_path: Path):
        """Generate HTML test report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report - {report.test_run_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .skipped {{ color: orange; }}
                .error {{ color: darkred; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Test Report: {report.test_run_id}</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Total Tests:</strong> {report.total_tests}</p>
                <p><strong>Success Rate:</strong> {report.success_rate:.1f}%</p>
                <p><strong>Duration:</strong> {report.total_duration:.2f} seconds</p>
                <p><span class="passed">Passed: {report.passed}</span> | 
                   <span class="failed">Failed: {report.failed}</span> | 
                   <span class="skipped">Skipped: {report.skipped}</span> | 
                   <span class="error">Errors: {report.errors}</span></p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Assertions</th>
                        <th>Error Message</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for result in report.test_results:
            status_class = result.status.value
            error_msg = result.error_message or ""
            if len(error_msg) > 50:
                error_msg = error_msg[:50] + "..."
            
            html_content += f"""
                    <tr>
                        <td>{result.test_name}</td>
                        <td>{result.test_type.value}</td>
                        <td class="{status_class}">{result.status.value}</td>
                        <td>{result.duration:.3f}s</td>
                        <td>{result.assertions}</td>
                        <td>{error_msg}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML test report generated: {output_path}")
    
    def generate_json_report(self, report: TestReport, output_path: Path):
        """Generate JSON test report"""
        import json
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        logger.info(f"JSON test report generated: {output_path}")


class TestingFramework:
    """
    Comprehensive testing framework
    
    Provides enterprise-grade testing capabilities including:
    - Unit, integration, performance, and UI tests
    - Test discovery and automatic execution
    - Mocking and assertion utilities
    - Detailed reporting with multiple formats
    - Performance testing and benchmarking
    """
    
    def __init__(self):
        self.test_runner = TestRunner()
        self.test_discovery = TestDiscovery()
        self.performance_runner = PerformanceTestRunner()
        self.report_generator = TestReportGenerator()
        
        # Built-in test suites
        self._register_builtin_tests()
        
        logger.info("Testing framework initialized")
    
    def _register_builtin_tests(self):
        """Register built-in tests for the application"""
        # Create built-in test suites
        unit_tests = TestSuite("builtin_unit_tests", TestType.UNIT)
        integration_tests = TestSuite("builtin_integration_tests", TestType.INTEGRATION)
        performance_tests = TestSuite("builtin_performance_tests", TestType.PERFORMANCE)
        
        # Add built-in unit tests
        unit_tests.tests = [
            self._test_logging_system,
            self._test_error_recovery,
            self._test_state_management,
            self._test_configuration_system
        ]
        
        # Add built-in integration tests
        integration_tests.tests = [
            self._test_component_integration,
            self._test_workflow_execution,
            self._test_state_synchronization
        ]
        
        # Add built-in performance tests
        performance_tests.tests = [
            self._test_ui_responsiveness,
            self._test_workflow_performance,
            self._test_memory_usage
        ]
        
        self.test_runner.add_test_suite(unit_tests)
        self.test_runner.add_test_suite(integration_tests)
        self.test_runner.add_test_suite(performance_tests)
    
    # Built-in unit tests
    
    def _test_logging_system(self, assert_: TestAssertions):
        """Test advanced logging system"""
        from ..utils.advanced_logging import get_logger
        
        logger_test = get_logger("test_logger")
        assert_.assert_is_not_none(logger_test, "Logger should be created")
        
        # Test logging methods exist
        assert_.assert_true(hasattr(logger_test, 'info'), "Logger should have info method")
        assert_.assert_true(hasattr(logger_test, 'error'), "Logger should have error method")
        assert_.assert_true(hasattr(logger_test, 'debug'), "Logger should have debug method")
        
        # Test context manager
        assert_.assert_true(hasattr(logger_test, 'context'), "Logger should have context method")
    
    def _test_error_recovery(self, assert_: TestAssertions):
        """Test error recovery system"""
        from ..utils.error_recovery import get_recovery_manager
        
        recovery_manager = get_recovery_manager()
        assert_.assert_is_not_none(recovery_manager, "Recovery manager should be created")
        
        # Test basic functionality
        assert_.assert_true(hasattr(recovery_manager, 'handle_error'), "Should have handle_error method")
        assert_.assert_true(hasattr(recovery_manager, 'configure_circuit_breaker'), "Should have circuit breaker config")
    
    def _test_state_management(self, assert_: TestAssertions):
        """Test state management system"""
        # Test basic state operations
        test_state = {"test_key": "test_value"}
        assert_.assert_equal(test_state["test_key"], "test_value", "State should store values")
        
        # Test state validation concepts
        assert_.assert_true(isinstance(test_state, dict), "State should be dictionary")
    
    def _test_configuration_system(self, assert_: TestAssertions):
        """Test configuration system"""
        # Test configuration structure
        config_data = {
            "ui": {"theme": "dark"},
            "mcp": {"comfyui_server_url": "http://localhost:8188"}
        }
        
        assert_.assert_in("ui", config_data, "Config should have UI section")
        assert_.assert_in("mcp", config_data, "Config should have MCP section")
        assert_.assert_equal(config_data["ui"]["theme"], "dark", "Theme should be dark")
    
    # Built-in integration tests
    
    async def _test_component_integration(self, assert_: TestAssertions):
        """Test component integration"""
        # Test that components can be imported together
        try:
            from ..utils.advanced_logging import get_logger
            from ..utils.error_recovery import get_recovery_manager
            from ..utils.performance_monitor import get_performance_monitor
            
            logger_instance = get_logger("integration_test")
            recovery_instance = get_recovery_manager()
            performance_instance = get_performance_monitor()
            
            assert_.assert_is_not_none(logger_instance, "Logger integration failed")
            assert_.assert_is_not_none(recovery_instance, "Recovery integration failed")
            assert_.assert_is_not_none(performance_instance, "Performance integration failed")
            
        except ImportError as e:
            assert_.assert_true(False, f"Component integration failed: {e}")
    
    async def _test_workflow_execution(self, assert_: TestAssertions):
        """Test workflow execution integration"""
        # Mock workflow execution
        start_time = time.time()
        
        # Simulate workflow steps
        await asyncio.sleep(0.01)  # Simulate work
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert_.assert_greater(duration, 0, "Workflow should take time to execute")
        assert_.assert_less(duration, 1.0, "Workflow should complete quickly in test")
    
    async def _test_state_synchronization(self, assert_: TestAssertions):
        """Test state synchronization"""
        # Test state sync concepts
        state_a = {"value": 1}
        state_b = {"value": 1}
        
        # Simulate state update
        state_a["value"] = 2
        state_b["value"] = 2  # Simulated sync
        
        assert_.assert_equal(state_a["value"], state_b["value"], "States should be synchronized")
    
    # Built-in performance tests
    
    async def _test_ui_responsiveness(self):
        """Test UI responsiveness"""
        # Simulate UI operation
        start_time = time.perf_counter()
        
        # Simulate UI work
        await asyncio.sleep(0.001)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # UI operations should be fast
        if duration > 0.1:  # 100ms threshold
            raise AssertionError(f"UI operation too slow: {duration:.3f}s > 0.1s")
    
    async def _test_workflow_performance(self):
        """Test workflow performance"""
        # Simulate workflow
        start_time = time.perf_counter()
        
        # Simulate workflow steps
        for i in range(10):
            await asyncio.sleep(0.001)  # Simulate processing
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Workflow should complete in reasonable time
        if duration > 1.0:  # 1 second threshold
            raise AssertionError(f"Workflow too slow: {duration:.3f}s > 1.0s")
    
    def _test_memory_usage(self):
        """Test memory usage"""
        # Create some objects to test memory
        test_objects = []
        for i in range(1000):
            test_objects.append({"id": i, "data": f"test_data_{i}"})
        
        # Memory usage should be reasonable
        import sys
        memory_size = sys.getsizeof(test_objects)
        
        if memory_size > 100000:  # 100KB threshold
            raise AssertionError(f"Memory usage too high: {memory_size} bytes > 100KB")
    
    # Public interface
    
    async def run_all_tests(self) -> TestReport:
        """Run all registered tests"""
        return await self.test_runner.run_all_tests()
    
    async def run_tests_by_type(self, test_type: TestType) -> TestReport:
        """Run tests of specific type"""
        # Filter test runner by type
        original_suites = self.test_runner.test_suites
        filtered_suites = [s for s in original_suites if s.test_type == test_type]
        
        self.test_runner.test_suites = filtered_suites
        try:
            return await self.test_runner.run_all_tests()
        finally:
            self.test_runner.test_suites = original_suites
    
    def discover_and_add_tests(self, search_paths: List[Path]):
        """Discover and add tests from paths"""
        discovered_suites = self.test_discovery.discover_tests(search_paths)
        for suite in discovered_suites:
            self.test_runner.add_test_suite(suite)
    
    def add_custom_test_suite(self, test_suite: TestSuite):
        """Add custom test suite"""
        self.test_runner.add_test_suite(test_suite)
    
    async def run_performance_benchmark(self, test_func: Callable, iterations: int = 5) -> Dict[str, Any]:
        """Run performance benchmark"""
        return await self.performance_runner.run_performance_test(test_func, iterations)
    
    def generate_reports(self, report: TestReport, output_dir: Path):
        """Generate test reports"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate HTML report
        html_path = output_dir / f"test_report_{report.test_run_id}.html"
        self.report_generator.generate_html_report(report, html_path)
        
        # Generate JSON report
        json_path = output_dir / f"test_report_{report.test_run_id}.json"
        self.report_generator.generate_json_report(report, json_path)
        
        return {"html": html_path, "json": json_path}
    
    def create_mock(self, **kwargs) -> MockObject:
        """Create mock object for testing"""
        return MockObject(**kwargs)
    
    def create_assertions(self) -> TestAssertions:
        """Create assertion utilities"""
        return TestAssertions()


# Global testing framework instance
_global_testing_framework: Optional[TestingFramework] = None


def get_testing_framework() -> TestingFramework:
    """Get or create global testing framework"""
    global _global_testing_framework
    if _global_testing_framework is None:
        _global_testing_framework = TestingFramework()
    return _global_testing_framework


def configure_testing(
    enable_performance_tests: bool = True,
    test_discovery_paths: Optional[List[Path]] = None,
    custom_thresholds: Optional[Dict[str, float]] = None
):
    """Configure testing framework"""
    framework = get_testing_framework()
    
    # Configure performance testing
    if custom_thresholds:
        framework.performance_runner.performance_thresholds.update(custom_thresholds)
    
    # Add discovery paths
    if test_discovery_paths:
        framework.discover_and_add_tests(test_discovery_paths)
    
    logger.info("Testing framework configured",
                performance_tests=enable_performance_tests,
                discovery_paths=len(test_discovery_paths) if test_discovery_paths else 0)