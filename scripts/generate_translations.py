#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate translation files using pyside6-lupdate.
This script scans src/ (excluding subdirectories) and src/ui/ to generate .ts translation files.
"""

import os
import shutil
import subprocess
import sys

from scripts.common import PROJECT_ROOT


def check_pyside6_lupdate():
    """Check if pyside6-lupdate is available in the system."""
    lupdate_cmd = "pyside6-lupdate"
    if shutil.which(lupdate_cmd) is None:
        print(f"Error: {lupdate_cmd} not found. Please install PySide6 tools.")
        sys.exit(1)
    return lupdate_cmd


def generate_ts_files():
    """Generate .ts files from source code."""
    lupdate_cmd = check_pyside6_lupdate()

    # Ensure we run from the project root
    os.chdir(PROJECT_ROOT)

    # Create translations directory if it doesn't exist
    translations_dir = PROJECT_ROOT / "translations"
    translations_dir.mkdir(exist_ok=True)

    # Define languages to generate translation files for
    # Add more languages here as needed
    languages = ["en_US", "zh_CN"]

    # Define source directories to scan
    src_dir = "src"  # Main src directory
    src_ui_dir = "src/ui"  # src/ui directory (including subdirectories)

    for lang in languages:
        # Define output .ts file with language code
        output_ts = translations_dir / f"app_{lang}.ts"

        # Prepare the command to run
        command = [
            lupdate_cmd,
            # "-no-recursive",
            src_dir,
            src_ui_dir,
            "-ts", str(output_ts)
        ]

        print(f"Running for {lang}: {' '.join(command)}")

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"Translation file for {lang} generated successfully!")
            print(f"Output file: {output_ts}")
            if result.stdout:
                print(f"Output for {lang}:")
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error generating translation file for {lang}: {e}")
            if e.stdout:
                print("Standard output:")
                print(e.stdout)
            if e.stderr:
                print("Error output:")
                print(e.stderr)
            sys.exit(1)


if __name__ == "__main__":
    generate_ts_files()
