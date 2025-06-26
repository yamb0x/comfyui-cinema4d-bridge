#!/usr/bin/env python3
"""
Convert verbose logger.info() calls to logger.debug() based on content patterns.
This script identifies and converts operational logs that should be at debug level.
"""

import re
import os
from pathlib import Path
from typing import List, Tuple, Dict

# Define patterns that indicate a log should be at debug level
DEBUG_PATTERNS = [
    # Parameter operations
    r'Validated parameters:',
    r'Injecting parameters',
    r'Collected \d+ parameters',
    r'Created dynamic.*parameters',
    r'Loaded dynamic.*parameters',
    r'_load_parameters_from_config called',
    r'UI Components status:',
    
    # File monitoring
    r'Using configured.*directory:',
    r'Loading.*models from:',
    r'Found \d+.*models',
    r'Checking.*directory:',
    r'Found \d+.*files in',
    r'Trying.*directory:',
    r'Models grid has \d+ models',
    r'Auto-detected textures',
    r'File monitor detected',
    
    # Workflow processing
    r'Workflow contains:',
    r'Converted.*workflow.*to API format',
    r'Converting.*workflow with \d+ nodes',
    r'All node IDs in.*workflow:',
    r'Skipping.*node',
    r'📐 MINIMAL:',
    r'🔧 CONVERSION FIX:',
    r'🔧 CAMERA FIX:',
    r'🎥 Camera Config Detection',
    r'🚀 SENDING TO COMFYUI:',
    
    # UI state testing
    r'Testing.*selector visibility',
    r'.*selector visibility:',
    r'.*selector parent:',
    r'Found \d+.*selector instances',
    
    # Object management
    r'Added.*to object pool',
    r'Added.*to workflow:',
    r'Removed.*from workflow:',
    r'Linked model.*to image',
    r'Created new workflow object',
    r'Model already exists',
    r'Added standalone.*model:',
    r'Removed standalone object:',
    r'Deselected workflow object:',
    r'Marked.*as textured',
    
    # ComfyUI details
    r'Loaded workflow:',
    r'📋 INSTRUCTIONS:',
    r'💾 Workflow saved to:',
    r'🔍 SAVED FINAL WORKFLOW',
    r'🔍 Compare this with',
    r'Found models from ComfyUI:',
    r'Checkpoints:.*models',
    r'LoRAs:.*models',
    r'VAE:.*models',
    
    # Settings changes
    r'Auto-save timer.*complete',
    r'Font size changed to',
    r'Accent color changed to',
    r'Console auto-scroll',
    r'Console buffer size changed',
    r'Timestamp format changed',
    r'Max concurrent operations changed',
    r'Memory limit changed',
    r'GPU acceleration',
    r'Cache size changed',
    r'Auto-clear cache',
    r'File logging',
    r'Log rotation',
    r'Max log file size changed',
    r'Debug mode',
    r'Telemetry',
    r'Auto-save interval',
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in DEBUG_PATTERNS]

def should_convert_to_debug(line: str) -> bool:
    """Check if a logger.info line should be converted to debug."""
    # Extract the log message content
    match = re.search(r'logger\.info\(["\'](.+?)["\']', line, re.IGNORECASE)
    if not match:
        match = re.search(r'logger\.info\(f["\'](.+?)["\']', line, re.IGNORECASE)
    
    if match:
        log_content = match.group(1)
        # Check against all patterns
        for pattern in COMPILED_PATTERNS:
            if pattern.search(log_content):
                return True
    
    return False

def process_file(file_path: Path) -> Tuple[int, List[str]]:
    """Process a single file and return count of changes and modified lines."""
    changes = 0
    modified_lines = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        for i, line in enumerate(lines):
            if 'logger.info(' in line.lower() and should_convert_to_debug(line):
                # Convert to debug
                new_line = re.sub(r'(logger|self\.logger|\.logger)\.info\(', r'\1.debug(', line, flags=re.IGNORECASE)
                new_lines.append(new_line)
                if new_line != line:
                    changes += 1
                    modified_lines.append(f"  Line {i+1}: {line.strip()} -> {new_line.strip()}")
            else:
                new_lines.append(line)
        
        # Write back if there were changes
        if changes > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        
        return changes, modified_lines
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, []

def main():
    """Main function to process all Python files."""
    # Get the project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    src_dir = project_root / 'src'
    
    print("Converting verbose logger.info() calls to logger.debug()...")
    print(f"Processing files in: {src_dir}")
    print("-" * 80)
    
    # Statistics
    total_files = 0
    total_changes = 0
    files_modified = {}
    
    # Process all Python files
    for py_file in src_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
            
        total_files += 1
        changes, modified_lines = process_file(py_file)
        
        if changes > 0:
            total_changes += changes
            files_modified[py_file] = (changes, modified_lines)
    
    # Report results
    print(f"\nProcessed {total_files} files")
    print(f"Total changes made: {total_changes}")
    print(f"Files modified: {len(files_modified)}")
    
    if files_modified:
        print("\nModified files:")
        for file_path, (changes, lines) in sorted(files_modified.items()):
            relative_path = file_path.relative_to(project_root)
            print(f"\n{relative_path}: {changes} changes")
            if len(lines) <= 5:  # Show details for files with few changes
                for line in lines:
                    print(line)
            else:
                print(f"  (showing first 3 of {len(lines)} changes)")
                for line in lines[:3]:
                    print(line)
                print("  ...")
    
    print("\nConversion complete!")
    print("Note: Review changes with 'git diff' before committing.")

if __name__ == "__main__":
    main()