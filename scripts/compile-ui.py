#!/usr/bin/env python
"""
UI Compiler Script

This script automatically scans the project for .ui files in any directory,
and compiles them to Python files in a 'generated' subdirectory within each
parent directory using pyside6-uic.

It can also watch for changes to UI files and recompile them automatically.
"""
import subprocess
import time
from pathlib import Path

from watchdog.events import (FileCreatedEvent, FileModifiedEvent,
                             FileSystemEventHandler)
from watchdog.observers import Observer

from scripts.common import PROJECT_ROOT


def find_ui_directories():
    """Find all directories containing .ui files in the project."""
    ui_dirs = []

    # Skip these directories for performance reasons
    skip_dirs = ['.git', '__pycache__', 'venv', 'env', '.venv', '.env', 'node_modules']

    # Walk through all subdirectories in the project
    for path in PROJECT_ROOT.glob('**/'):
        # Skip directories we want to exclude
        if any(skip_name in str(path) for skip_name in skip_dirs):
            continue

        # Check if this directory contains .ui files
        ui_files = list(path.glob('*.ui'))
        if ui_files:
            # Create corresponding output directory path
            output_dir = path.parent
            ui_dirs.append({
                "design_dir": path,
                "output_dir": output_dir
            })

    return ui_dirs


def compile_single_ui_file(ui_file, output_dir):
    """Compile a single UI file."""
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True, parents=True)

    ui_name = ui_file.stem
    py_file = output_dir / f"{ui_name}.py"

    print(f"Compiling {ui_file.name} -> {py_file.name}...")

    try:
        result = subprocess.run(
            ["pyside6-uic", str(ui_file), "-o", str(py_file)],
            check=True,
            capture_output=True,
            text=True
        )

        if result.stderr:
            print(f"Warning during compilation: {result.stderr}")

        # Check if output file was created
        if py_file.exists():
            print(f"Successfully compiled {ui_file.name}")
            return True
        else:
            print(f"Error: Output file not created for {ui_file.name}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Error compiling {ui_file.name}: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: pyside6-uic not found. Make sure PySide6 is installed.")
        print("Install with: pip install PySide6")
        return False


def compile_ui():
    """
    Finds and compiles all .ui files to python files.
    """
    ui_dirs = find_ui_directories()

    if not ui_dirs:
        print("No directories with UI files found in the project.")
        return False

    print(f"Found {len(ui_dirs)} directories containing UI files.")

    success = True
    total_files = 0

    for dir_config in ui_dirs:
        design_dir = dir_config["design_dir"]
        output_dir = dir_config["output_dir"]

        # Find all .ui files in design directory
        ui_files = list(design_dir.glob("*.ui"))
        total_files += len(ui_files)

        print(f"Found {len(ui_files)} UI file(s) in {design_dir}:")

        # Process each UI file
        for ui_file in ui_files:
            if not compile_single_ui_file(ui_file, output_dir):
                success = False

    print(f"Total UI files compiled: {total_files}")
    print("UI compilation completed.")
    return 0 if success else 1


class UIFileEventHandler(FileSystemEventHandler):
    """Event handler for UI file changes."""

    def __init__(self, design_dir, output_dir):
        self.design_dir = design_dir
        self.output_dir = output_dir
        super().__init__()

    def on_modified(self, event):
        """Handle file modification events."""
        if isinstance(event, FileModifiedEvent):
            self._process_ui_file_event(event)

    def on_created(self, event):
        """Handle file creation events."""
        if isinstance(event, FileCreatedEvent):
            self._process_ui_file_event(event)

    def on_moved(self, event):
        """Handle file rename/move events."""
        # This catches the final rename operation that many editors use when saving files
        dest_path = Path(event.dest_path)
        if dest_path.suffix.lower() == '.ui' and dest_path.parent == self.design_dir:
            print(f"\nDetected save of {dest_path.name} (via rename)")
            compile_single_ui_file(dest_path, self.output_dir)

    def _process_ui_file_event(self, event):
        """Process UI file events and compile if needed."""
        # Check if it's a .ui file
        path = Path(event.src_path)

        # Only process files that end with exactly '.ui' (not '.ui.something')
        if path.suffix.lower() == '.ui' and path.parent == self.design_dir:
            print(f"\nDetected change to {path.name}")
            compile_single_ui_file(path, self.output_dir)


def watch():
    """Watch for changes to UI files and recompile them automatically."""
    # First scan for all UI directories
    ui_dirs = find_ui_directories()

    if not ui_dirs:
        print("No directories with UI files found in the project. Nothing to watch.")
        return False

    # Compile all files first
    compile_ui()

    # Set up observers for each directory
    observers = []

    for dir_config in ui_dirs:
        design_dir = dir_config["design_dir"]
        output_dir = dir_config["output_dir"]

        # Set up the event handler and observer
        event_handler = UIFileEventHandler(design_dir, output_dir)
        observer = Observer()
        observer.schedule(event_handler, str(design_dir), recursive=False)
        observer.start()
        observers.append(observer)

        print(f"Watching for changes in {design_dir}")

    print(f"\nWatching {len(ui_dirs)} directories for UI file changes.")
    print("Press Ctrl+C to stop...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping file watchers...")
        for observer in observers:
            observer.stop()

    for observer in observers:
        observer.join()

    return True


if __name__ == "__main__":
    watch()
