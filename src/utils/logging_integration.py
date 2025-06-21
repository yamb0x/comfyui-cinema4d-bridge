"""
Logging Integration Script

Updates all components to use the new advanced logging system
with structured output and performance tracking.
"""

import re
from pathlib import Path
from typing import List, Tuple

# Component files to update
COMPONENT_FILES = [
    "src/core/unified_config_manager.py",
    "src/core/config_validation.py", 
    "src/core/state_store.py",
    "src/core/ui_controller.py",
    "src/core/workflow_engine.py",
    "src/core/integration_hub.py",
    "src/core/app_coordinator.py",
    "src/utils/error_handling.py",
    "src/core/resource_manager.py"
]

# Mapping of old imports to new imports
IMPORT_REPLACEMENTS = [
    (r'from loguru import logger', 'from ..utils.advanced_logging import get_logger\n\nlogger = get_logger'),
    (r'import logging\nlogger = logging\.getLogger\(__name__\)', 'from ..utils.advanced_logging import get_logger\n\nlogger = get_logger'),
]

# Common logging pattern replacements
LOGGING_PATTERNS = [
    # Add contextual logging for key operations
    (r'logger\.debug\(f"Loading configuration from', 'with logger.context(operation="load_config"):\n            logger.debug(f"Loading configuration from'),
    (r'logger\.info\(f"Workflow execution started:', 'with logger.timed_operation("workflow_execution"):\n            logger.info(f"Workflow execution started:'),
    (r'logger\.error\(f"Failed to connect to', 'with logger.context(operation="service_connection"):\n            logger.error(f"Failed to connect to'),
    
    # Add performance tracking for critical operations
    (r'logger\.debug\(f"UI controller initialized', 'with logger.context(operation="ui_initialization"):\n            logger.debug(f"UI controller initialized'),
    (r'logger\.info\(f"State store initialized', 'with logger.context(operation="state_initialization"):\n            logger.info(f"State store initialized'),
]


def update_component_logging(file_path: Path, component_name: str) -> bool:
    """Update logging in a single component file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update imports
        for old_pattern, new_replacement in IMPORT_REPLACEMENTS:
            if 'loguru' in old_pattern:
                content = re.sub(old_pattern, f'{new_replacement}("{component_name}")', content)
            else:
                content = re.sub(old_pattern, f'{new_replacement}("{component_name}")', content)
        
        # Add contextual logging patterns
        for old_pattern, new_replacement in LOGGING_PATTERNS:
            content = re.sub(old_pattern, new_replacement, content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated logging in {file_path}")
            return True
        else:
            print(f"- No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to update {file_path}: {e}")
        return False


def integrate_advanced_logging():
    """Integrate advanced logging into all components"""
    print("🔧 Integrating Advanced Logging System...")
    
    project_root = Path(__file__).parent.parent.parent
    updated_files = []
    
    for file_path in COMPONENT_FILES:
        full_path = project_root / file_path
        if full_path.exists():
            # Extract component name from file path
            component_name = full_path.stem
            if component_name.endswith('_manager'):
                component_name = component_name[:-8]  # Remove '_manager' suffix
            elif component_name.endswith('_store'):
                component_name = component_name[:-6]   # Remove '_store' suffix
            elif component_name.endswith('_engine'):
                component_name = component_name[:-7]   # Remove '_engine' suffix
            elif component_name.endswith('_hub'):
                component_name = component_name[:-4]   # Remove '_hub' suffix
            elif component_name.endswith('_controller'):
                component_name = component_name[:-11] # Remove '_controller' suffix
            
            if update_component_logging(full_path, component_name):
                updated_files.append(str(file_path))
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print(f"\n📊 Integration Summary:")
    print(f"  • Updated {len(updated_files)} files")
    print(f"  • Advanced logging patterns applied")
    print(f"  • Performance tracking enabled")
    print(f"  • Structured output configured")
    
    if updated_files:
        print(f"\n✅ Files updated:")
        for file_path in updated_files:
            print(f"    - {file_path}")
    
    return len(updated_files)


if __name__ == "__main__":
    integrate_advanced_logging()