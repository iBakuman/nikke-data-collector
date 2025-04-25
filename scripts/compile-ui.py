#!/usr/bin/env python
"""
UI Compiler Script

This script compiles all .ui files in the src/ui/design directory
to Python files in the src/ui directory using pyside6-uic.

It can also watch for changes to UI files and recompile them automatically.
"""
import subprocess
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
from watchdog.observers import Observer

from scripts.common import PROJECT_ROOT

design_dir = PROJECT_ROOT / "src" / "ui" / "design"
output_dir = PROJECT_ROOT / "src" / "ui"


def compile_single_ui_file(ui_file, output_dir):
    """Compile a single UI file."""
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
    Finds and compiles all .ui files from design folder to python files.
    """
    # Ensure directories exist
    if not design_dir.exists():
        print(f"Error: Design directory not found: {design_dir}")
        return False

    if not output_dir.exists():
        print(f"Error: Output directory not found: {output_dir}")
        return False

    # Find all .ui files in design directory
    ui_files = list(design_dir.glob("*.ui"))

    if not ui_files:
        print("No UI files found in design directory.")
        return False

    print(f"Found {len(ui_files)} UI file(s) to compile:")

    # Process each UI file
    success = True
    for ui_file in ui_files:
        if not compile_single_ui_file(ui_file, output_dir):
            success = False

    print("UI compilation completed.")
    return 0 if success else 1


class UIFileEventHandler(FileSystemEventHandler):
    """Event handler for UI file changes."""

    def __init__(self, _design_dir, _output_dir):
        self.design_dir = _design_dir
        self.output_dir = _output_dir
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
    if not design_dir.exists():
        print(f"Error: Design directory not found: {design_dir}")
        return False

    if not output_dir.exists():
        print(f"Error: Output directory not found: {output_dir}")
        return False

    # Compile all files first
    compile_ui()

    # Set up the event handler and observer
    event_handler = UIFileEventHandler(design_dir, output_dir)
    observer = Observer()
    observer.schedule(event_handler, str(design_dir), recursive=False)

    # Start watching
    observer.start()
    print(f"\nWatching for changes in {design_dir}")
    print("Press Ctrl+C to stop...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping file watcher...")
        observer.stop()

    observer.join()
    return True


if __name__ == "__main__":
    watch()
