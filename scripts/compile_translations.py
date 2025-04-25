#!/usr/bin/env python
"""
Compile Translation Files Script

This script compiles all .ts files in the src/ui/translations directory
to .qm files in the same directory using pyside6-lrelease.
"""
import os
import shutil
import subprocess
import sys

from scripts.common import PROJECT_ROOT


def check_pyside6_lrelease():
    """Check if pyside6-lrelease is available in the system."""
    lrelease_cmd = "pyside6-lrelease"
    if shutil.which(lrelease_cmd) is None:
        print(f"Error: {lrelease_cmd} not found. Please install PySide6 tools.")
        sys.exit(1)
    return lrelease_cmd

def compile_translations():
    """Compile .ts files to .qm files."""
    lrelease_cmd = check_pyside6_lrelease()

    # Ensure we run from the project root
    os.chdir(PROJECT_ROOT)

    # Define translations directory
    translations_dir = PROJECT_ROOT / "src" / "ui" / "translations"
    
    if not translations_dir.exists():
        print(f"Error: Translations directory not found: {translations_dir}")
        return False

    # Find all .ts files in translations directory
    ts_files = list(translations_dir.glob("*.ts"))
    
    if not ts_files:
        print("No .ts files found in translations directory.")
        return False
    
    print(f"Found {len(ts_files)} translation file(s) to compile:")
    
    # Process each .ts file
    success = True
    for ts_file in ts_files:
        qm_file = ts_file.with_suffix(".qm")
        print(f"Compiling {ts_file.name} -> {qm_file.name}...")
        
        try:
            result = subprocess.run(
                [lrelease_cmd, str(ts_file), "-qm", str(qm_file)],
                check=True,
                capture_output=True,
                text=True
            )
            
            if result.stderr:
                print(f"Warning during compilation: {result.stderr}")
            
            # Check if output file was created
            if qm_file.exists():
                print(f"Successfully compiled {ts_file.name}")
            else:
                print(f"Error: Output file not created for {ts_file.name}")
                success = False
                
        except subprocess.CalledProcessError as e:
            print(f"Error compiling {ts_file.name}: {e.stderr}")
            success = False
    
    print("Translation compilation completed.")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(compile_translations()) 
