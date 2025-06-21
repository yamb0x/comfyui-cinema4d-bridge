"""
Application Coordinator

New main application class using the decomposed architecture.
Coordinates between UIController, StateStore, WorkflowEngine, and IntegrationHub
to provide the same functionality as the monolithic application but with
clean separation of concerns.

Part of Phase 2 architectural decomposition - implements the multi-mind analysis
recommendation for composition-based architecture instead of monolithic inheritance.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..utils.advanced_logging import get_logger

logger = get_logger("app_coordinator")

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QCloseEvent

from ..utils.error_handling import handle_errors, error_context, ErrorHandler
from ..core.unified_config_manager import UnifiedConfigurationManager
from ..core.config_validation import ConfigurationValidationPipeline
from ..core.state_store import StateStore, StateObserver
from ..core.ui_controller import UIController
from ..core.workflow_engine import WorkflowEngine, WorkflowType
from ..core.integration_hub import IntegrationHub
from ..core.resource_manager import resource_manager, initialize_resource_management, cleanup_resources_on_exit


class ApplicationCoordinator(QMainWindow, StateObserver):
    """
    Main application coordinator using decomposed architecture
    
    Coordinates between specialized components instead of handling everything
    in a single monolithic class. Implements clean separation of concerns
    and dependency injection patterns.
    """
    
    # Application lifecycle signals
    startup_completed = Signal()
    shutdown_initiated = Signal()
    
    def __init__(self):
        super().__init__()
        
        # Error handling
        self.error_handler = ErrorHandler("app_coordinator")
        
        # Configuration system
        self.config_manager = None
        
        # Core components
        self.state_store = None
        self.ui_controller = None
        self.workflow_engine = None
        self.integration_hub = None
        
        # Application state
        self.is_initialized = False
        self.is_shutting_down = False
        
        # Startup timer
        self.startup_timer = QTimer()
        self.startup_timer.setSingleShot(True)
        self.startup_timer.timeout.connect(self._complete_startup)
    
    @handle_errors("app_coordinator", "initialize")
    async def initialize(self) -> bool:
        """Initialize application with decomposed architecture"""
        
        with error_context("app_coordinator", "initialize"):
            try:
                logger.info("Starting application initialization...")
                
                # Initialize resource management
                await initialize_resource_management()
                
                # Initialize configuration system
                self._initialize_configuration()
                
                # Validate configuration
                self._validate_configuration()
                
                # Initialize components in dependency order
                self._initialize_state_store()
                self._initialize_integration_hub()
                self._initialize_workflow_engine()
                self._initialize_ui_controller()
                
                # Setup component communications
                self._connect_components()
                
                # Create and setup UI
                self._setup_user_interface()
                
                # Start services
                await self._start_services()
                
                # Complete initialization
                self.is_initialized = True
                
                # Delay startup completion to allow UI to render
                self.startup_timer.start(100)
                
                logger.info("Application initialization completed successfully")
                return True
                
            except Exception as e:
                self.error_handler.handle_error(e, "initialize")
                await self._show_initialization_error(str(e))
                return False
    
    def _initialize_configuration(self):
        """Initialize configuration management"""
        config_dir = Path("config")
        self.config_manager = UnifiedConfigurationManager(config_dir)
        logger.debug("Configuration system initialized")
    
    def _validate_configuration(self):
        """Validate configuration and apply auto-fixes"""
        validator = ConfigurationValidationPipeline()
        report = validator.validate(self.config_manager, auto_fix=True)
        
        if report.errors:
            logger.warning(f"Configuration validation found {len(report.errors)} errors")
            for error in report.errors:
                logger.warning(f"Config error: {error.message}")
        
        if report.auto_fixes_applied:
            logger.info(f"Applied {len(report.auto_fixes_applied)} configuration auto-fixes")
    
    def _initialize_state_store(self):
        """Initialize centralized state management"""
        self.state_store = StateStore(self.config_manager)
        self.state_store.add_observer("selection", self)
        self.state_store.add_observer("workflow", self)
        logger.debug("State store initialized")
    
    def _initialize_integration_hub(self):
        """Initialize external service integrations"""
        self.integration_hub = IntegrationHub(self.config_manager)
        logger.debug("Integration hub initialized")
    
    def _initialize_workflow_engine(self):
        """Initialize workflow execution engine"""
        self.workflow_engine = WorkflowEngine(
            self.config_manager,
            self.state_store,
            self.integration_hub
        )
        logger.debug("Workflow engine initialized")
    
    def _initialize_ui_controller(self):
        """Initialize UI management"""
        self.ui_controller = UIController(self.config_manager)
        logger.debug("UI controller initialized")
    
    def _connect_components(self):
        """Setup communication between components"""
        
        # UI Controller → Application actions
        self.ui_controller.action_requested.connect(self._handle_ui_action)
        self.ui_controller.workflow_triggered.connect(self._handle_workflow_trigger)
        self.ui_controller.settings_changed.connect(self._handle_settings_change)
        
        # Integration Hub → UI updates
        self.integration_hub.service_connected.connect(self._on_service_connected)
        self.integration_hub.service_disconnected.connect(self._on_service_disconnected)
        self.integration_hub.service_error.connect(self._on_service_error)
        
        # Workflow Engine → UI updates
        self.workflow_engine.execution_started.connect(self._on_workflow_started)
        self.workflow_engine.execution_progress.connect(self._on_workflow_progress)
        self.workflow_engine.execution_completed.connect(self._on_workflow_completed)
        self.workflow_engine.execution_failed.connect(self._on_workflow_failed)
        
        # State Store → UI updates
        self.state_store.selection_changed.connect(self._on_selection_changed)
        self.state_store.workflow_changed.connect(self._on_workflow_state_changed)
        self.state_store.connection_changed.connect(self._on_connection_state_changed)
        
        logger.debug("Component communications configured")
    
    def _setup_user_interface(self):
        """Setup user interface using UI controller"""
        
        # Create main window
        main_window = self.ui_controller.create_main_window()
        
        # Create main interface
        main_interface = self.ui_controller.create_main_interface(main_window)
        main_window.setCentralWidget(main_interface)
        
        # Set this window as the main window
        self.setWindowTitle(main_window.windowTitle())
        self.resize(main_window.size())
        self.setCentralWidget(main_interface)
        
        # Apply theme
        theme = self.config_manager.get_setting("ui.theme", "dark")
        self.ui_controller.theme_manager.apply_theme(self, theme)
        
        logger.debug("User interface setup completed")
    
    async def _start_services(self):
        """Start external services and monitoring"""
        
        # Start integration monitoring
        self.integration_hub.start_monitoring()
        
        # Connect to services
        connection_results = await self.integration_hub.connect_all_services()
        
        connected_count = sum(1 for connected in connection_results.values() if connected)
        total_count = len(connection_results)
        
        logger.info(f"Service connections: {connected_count}/{total_count} successful")
        
        # Update UI with connection status
        for service_name, connected in connection_results.items():
            self.ui_controller.update_connection_status(service_name, connected)
    
    def _complete_startup(self):
        """Complete startup process"""
        self.startup_completed.emit()
        logger.info("Application startup completed")
    
    # Event Handlers - UI Actions
    
    @handle_errors("app_coordinator", "handle_ui_action")
    def _handle_ui_action(self, action_name: str, parameters: Dict[str, Any]):
        """Handle UI action requests"""
        
        with error_context("app_coordinator", "handle_ui_action", 
                          action=action_name, params=parameters):
            
            if action_name == "tab_changed":
                tab_index = parameters.get("index", 0)
                self.state_store.update_workflow(current_tab=tab_index)
            
            elif action_name == "workflow_changed":
                workflow = parameters.get("workflow", "")
                self.state_store.update_workflow(current_workflow=workflow)
            
            elif action_name == "clear_selection":
                self.state_store.clear_selection()
            
            elif action_name == "refresh_objects":
                asyncio.create_task(self._refresh_objects())
            
            elif action_name == "refresh_status":
                asyncio.create_task(self._refresh_service_status())
            
            else:
                logger.warning(f"Unknown UI action: {action_name}")
    
    @handle_errors("app_coordinator", "handle_workflow_trigger")
    def _handle_workflow_trigger(self, workflow_name: str, parameters: Dict[str, Any]):
        """Handle workflow execution trigger"""
        
        with error_context("app_coordinator", "handle_workflow_trigger",
                          workflow=workflow_name, params=parameters):
            
            # Determine workflow type based on current tab
            tab_index = parameters.get("tab_index", 0)
            workflow_types = [
                WorkflowType.IMAGE_GENERATION,
                WorkflowType.MODEL_3D_GENERATION,
                WorkflowType.TEXTURE_GENERATION,
                WorkflowType.CINEMA4D_AUTOMATION
            ]
            
            if 0 <= tab_index < len(workflow_types):
                workflow_type = workflow_types[tab_index]
                
                # Execute workflow
                asyncio.create_task(self._execute_workflow(workflow_type, workflow_name, parameters))
            else:
                logger.error(f"Invalid tab index for workflow: {tab_index}")
    
    def _handle_settings_change(self, setting_name: str, value: Any):
        """Handle settings changes"""
        self.config_manager.set_setting(setting_name, value)
        logger.debug(f"Setting changed: {setting_name} = {value}")
    
    # Event Handlers - Service Events
    
    def _on_service_connected(self, service_name: str, status: str):
        """Handle service connection"""
        self.ui_controller.update_connection_status(service_name, True)
        self.state_store.update_connection_status(service_name, True, status)
        logger.info(f"Service connected: {service_name}")
    
    def _on_service_disconnected(self, service_name: str, reason: str):
        """Handle service disconnection"""
        self.ui_controller.update_connection_status(service_name, False)
        self.state_store.update_connection_status(service_name, False, reason)
        logger.warning(f"Service disconnected: {service_name} - {reason}")
    
    def _on_service_error(self, service_name: str, error_message: str):
        """Handle service error"""
        self.ui_controller.update_connection_status(service_name, False)
        self.state_store.update_connection_status(service_name, False, error_message)
        logger.error(f"Service error: {service_name} - {error_message}")
    
    # Event Handlers - Workflow Events
    
    def _on_workflow_started(self, execution_id: str, workflow_type: str):
        """Handle workflow execution start"""
        self.ui_controller.show_progress("Workflow started...", 0)
        logger.info(f"Workflow started: {execution_id} ({workflow_type})")
    
    def _on_workflow_progress(self, execution_id: str, percentage: int, step: str):
        """Handle workflow progress update"""
        self.ui_controller.show_progress(step, percentage)
    
    def _on_workflow_completed(self, execution_id: str, success: bool, results: List[str]):
        """Handle workflow completion"""
        if success:
            self.ui_controller.show_progress("Workflow completed", 100)
            logger.info(f"Workflow completed: {execution_id} ({len(results)} results)")
            
            # TODO: Update UI with results
            # This would involve refreshing image/model grids, etc.
            
        else:
            self.ui_controller.show_progress("Workflow failed", 0)
            logger.error(f"Workflow failed: {execution_id}")
    
    def _on_workflow_failed(self, execution_id: str, error_message: str):
        """Handle workflow failure"""
        self.ui_controller.show_error("Workflow Failed", error_message)
        logger.error(f"Workflow failed: {execution_id} - {error_message}")
    
    # Event Handlers - State Changes
    
    def _on_selection_changed(self, selection_state):
        """Handle selection state changes"""
        selected_objects = selection_state.get_all_selected()
        self.ui_controller.update_object_list(selected_objects)
    
    def _on_workflow_state_changed(self, workflow_state):
        """Handle workflow state changes"""
        # Update UI based on workflow state
        pass
    
    def _on_connection_state_changed(self, connection_state):
        """Handle connection state changes"""
        # Update UI based on connection state
        pass
    
    # StateObserver implementation
    
    def on_state_changed(self, state_name: str, change_type: str, data: Any):
        """Handle state changes as observer"""
        logger.debug(f"State changed: {state_name} - {change_type}")
    
    # Async Operations
    
    async def _execute_workflow(self, 
                               workflow_type: WorkflowType,
                               workflow_name: str,
                               parameters: Dict[str, Any]):
        """Execute workflow using workflow engine"""
        try:
            # Get workflow file path
            workflows_dir = self.config_manager.get_setting("base.workflows_dir", "workflows")
            workflow_file = Path(workflows_dir) / workflow_type.value / f"{workflow_name}.json"
            
            if not workflow_file.exists():
                raise FileNotFoundError(f"Workflow file not found: {workflow_file}")
            
            # TODO: Collect UI widgets for dynamic parameters
            ui_widgets = {}  # This would be populated from UI controller
            
            # Execute workflow
            execution_id = await self.workflow_engine.execute_workflow(
                workflow_type=workflow_type,
                workflow_file=str(workflow_file),
                parameters=parameters,
                ui_widgets=ui_widgets
            )
            
            logger.info(f"Workflow execution initiated: {execution_id}")
            
        except Exception as e:
            self.error_handler.handle_error(e, "execute_workflow")
            self.ui_controller.show_error("Workflow Error", str(e))
    
    async def _refresh_objects(self):
        """Refresh object list from various sources"""
        try:
            # This would refresh objects from file system, state, etc.
            # For now, just log the action
            logger.info("Refreshing object list...")
            
        except Exception as e:
            self.error_handler.handle_error(e, "refresh_objects")
    
    async def _refresh_service_status(self):
        """Refresh service connection status"""
        try:
            # Force refresh of all service connections
            connection_results = await self.integration_hub.connect_all_services()
            
            for service_name, connected in connection_results.items():
                self.ui_controller.update_connection_status(service_name, connected)
            
            logger.info("Service status refreshed")
            
        except Exception as e:
            self.error_handler.handle_error(e, "refresh_service_status")
    
    # Error Handling
    
    async def _show_initialization_error(self, error_message: str):
        """Show initialization error to user"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Initialization Error")
        msg.setText("Failed to initialize application")
        msg.setDetailedText(error_message)
        msg.exec()
    
    # Lifecycle Methods
    
    def show(self):
        """Show application window"""
        super().show()
        logger.info("Application window shown")
    
    def closeEvent(self, event: QCloseEvent):
        """Handle application close"""
        if not self.is_shutting_down:
            self.is_shutting_down = True
            self.shutdown_initiated.emit()
            
            # Cleanup components
            asyncio.create_task(self._cleanup_application())
            
            # Accept close event
            event.accept()
            logger.info("Application closing...")
    
    async def _cleanup_application(self):
        """Cleanup application resources"""
        try:
            logger.info("Starting application cleanup...")
            
            # Stop services
            if self.integration_hub:
                self.integration_hub.cleanup()
            
            # Cleanup workflow engine
            if self.workflow_engine:
                self.workflow_engine.cleanup()
            
            # Save state
            if self.state_store:
                self.state_store.save_state()
            
            # Cleanup resources
            await cleanup_resources_on_exit()
            
            logger.info("Application cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Application Factory
def create_application() -> tuple[QApplication, ApplicationCoordinator]:
    """Create and configure application"""
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("ComfyUI to Cinema4D Bridge")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Studio Bridge")
    
    # Create application coordinator
    coordinator = ApplicationCoordinator()
    
    return app, coordinator


# Main entry point
async def run_application():
    """Run the application with new architecture"""
    
    try:
        # Create application
        app, coordinator = create_application()
        
        # Initialize coordinator
        success = await coordinator.initialize()
        
        if not success:
            logger.error("Application initialization failed")
            return 1
        
        # Show application
        coordinator.show()
        
        # Run event loop
        return app.exec()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(run_application())
    sys.exit(exit_code)