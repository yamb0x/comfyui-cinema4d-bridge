#!/usr/bin/env python3
"""
Script to improve logging by converting excessive INFO logs to DEBUG
Based on multi-mind analysis of debug patterns
"""

import re
import os
from pathlib import Path
from typing import List, Tuple

# Patterns that should be DEBUG level instead of INFO
DEBUG_PATTERNS = [
    # Parameter operations
    r'Validated parameters:',
    r'Injecting parameters',
    r'Collected \d+ parameters',
    r'Created/Loaded dynamic parameters',
    r'🎯.*Creating widget for',
    r'✅ Set \w+ =',
    r'🔧.*parameter',
    
    # File monitoring and loading
    r'Using configured directory:',
    r'Loading models from:',
    r'Found \d+ (models|files|images)',
    r'Checking directory:',
    r'Successfully loaded \d+ (session images|images|3D models)',
    r'Added 3D model to grid:',
    r'Loading model:',
    
    # UI state changes
    r'Testing selector visibility',
    r'selector visibility:',
    r'Font size changed to',
    r'Updated UI with \d+ parameter groups',
    r'Added parameter widget:',
    r'Created section for',
    r'✅ (Created|Added)',
    
    # Workflow processing details
    r'Converting workflow with \d+ nodes',
    r'Skipping node',
    r'🔧 CONVERSION FIX:',
    r'Workflow hint:',
    r'Parameter UI refresh:',
    r'Synchronized all workflow dropdowns',
    
    # Configuration details
    r'Loaded saved unified configuration',
    r'Configuration updated from unified manager',
    r'Loaded prompts from workflow:',
    r'Updating (positive|negative) prompt widget',
    
    # Server operations
    r'Started server for ThreeJS viewer on port',
    
    # Progress tracking
    r'💾 Saved workflow state:',
    r'✅ Added \d+ parameter widgets',
    r'🔄 Starting UI (update|refresh)',
]

# Patterns that should remain INFO (user-facing actions)
KEEP_INFO_PATTERNS = [
    r'Starting comfy2c4d Application',
    r'ComfyUI connection established',
    r'Cinema4D connection verified',
    r'Workflow execution (started|completed)',
    r'Generated (image|model|texture)',
    r'Export completed',
    r'Application initialized successfully',
    r'Window settings loaded successfully',
    r'Configuration saved',
    r'parameters configuration saved',
]

def should_convert_to_debug(line: str) -> bool:
    """Check if a logger.info line should be converted to debug"""
    # Check if it matches any KEEP_INFO patterns
    for pattern in KEEP_INFO_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return False
    
    # Check if it matches any DEBUG patterns
    for pattern in DEBUG_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    
    return False

def process_file(filepath: Path) -> Tuple[int, List[str]]:
    """Process a single file and convert appropriate logs"""
    changes_count = 0
    modified_lines = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            # Check for logger.info or self.logger.info
            if re.search(r'(self\.)?logger\.info\(', line):
                # Extract the log message
                log_match = re.search(r'logger\.info\((.*?)\)', line, re.DOTALL)
                if log_match and should_convert_to_debug(log_match.group(1)):
                    # Convert to debug
                    new_line = line.replace('logger.info(', 'logger.debug(')
                    lines[i] = new_line
                    changes_count += 1
                    modified_lines.append(f"Line {i+1}: {line.strip()} -> {new_line.strip()}")
        
        if changes_count > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    
    return changes_count, modified_lines

def main():
    """Main function to process all Python files"""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / 'src'
    
    total_changes = 0
    files_modified = 0
    
    print("🔍 Scanning Python files for logging improvements...")
    print(f"Project root: {project_root}")
    print()
    
    # Process all Python files in src directory
    for py_file in src_dir.rglob('*.py'):
        changes, modified_lines = process_file(py_file)
        if changes > 0:
            total_changes += changes
            files_modified += 1
            print(f"📝 {py_file.relative_to(project_root)}: {changes} changes")
            if len(modified_lines) <= 5:
                for line in modified_lines:
                    print(f"   {line}")
            else:
                for line in modified_lines[:3]:
                    print(f"   {line}")
                print(f"   ... and {len(modified_lines) - 3} more changes")
            print()
    
    print(f"\n✅ Summary:")
    print(f"   Files modified: {files_modified}")
    print(f"   Total log conversions: {total_changes}")
    
    # Create a report file
    report_path = project_root / 'logs' / 'logging_improvements.txt'
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write(f"Logging Improvements Report\n")
        f.write(f"==========================\n\n")
        f.write(f"Files modified: {files_modified}\n")
        f.write(f"Total conversions: {total_changes}\n\n")
        f.write(f"Patterns used for conversion:\n")
        for pattern in DEBUG_PATTERNS:
            f.write(f"  - {pattern}\n")
    
    print(f"\n📄 Report saved to: {report_path}")

if __name__ == "__main__":
    main()