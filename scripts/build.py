# !/usr/bin/env python
"""
Build script for compiling the NIKKE Arena application with Nuitka.
Handles resource inclusion and proper packaging.
"""
import datetime
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """Get the project root directory"""
    # Start with the current script's directory
    current_dir = Path(__file__).resolve().parent

    # Navigate up to find project root (where src is)
    project_dir = current_dir
    while project_dir.name != "nikke-data-collector" and project_dir != Path("/"):
        project_dir = project_dir.parent

    if project_dir.name != "nikke-data-collector":
        raise Exception("Could not find project root directory")
    return project_dir


def build(output_dir=None, output_name=None, debug_mode=False, standalone=True, onefile=False) -> Optional[bool]:
    """
    Build the NIKKE Arena application with Nuitka

    Args:
        output_dir: Directory to place output files
        output_name: Name for the output executable
        debug_mode: Enable debug mode
        standalone: Create standalone executable
        onefile: Create a single executable file
    """
    project_root = get_project_root()
    src_dir = project_root / "src"
    dist_dir = project_root / "dist"

    # Determine output paths
    if not output_dir:
        output_dir = project_root
    else:
        output_dir = Path(output_dir)

    if debug_mode:
        output_dir /= "debug"
    else:
        output_dir /= "release"

    if not output_name:
        output_name = "nikke-data-collector"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Create a timestamp for the report file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{output_name}_{timestamp}_build_report.xml"
    report_path = dist_dir / report_filename

    # Build Nuitka command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--show-progress",
        f"--windows-icon-from-ico={os.path.join(src_dir, 'nikke_arena', 'resources', 'logo.ico')}",
        "--enable-plugin=pyside6",
        f"--output-dir={output_dir}",
        f"--output-filename={output_name}",
        f"--report={report_path}"
    ]

    # Critical: Include resources directory
    resources_dir = src_dir / "nikke_arena" / "resources"

    if not debug_mode:
        cmd.append("--windows-console-mode=disable")

    if onefile:
        # Onefile mode - package everything into a single executable
        cmd.append("--onefile")
    elif standalone:
        # Standalone mode - create a directory with the executable and dependencies
        cmd.append("--standalone")

    # Include all files in the resources directory
    cmd.append(f"--include-data-dir={resources_dir}=resources")
    # cmd.append(f"--include-data-files={resources_dir / '*.*'}=resources/")
    # Include files in the ref subdirectory - scan recursively with **/*
    # cmd.append(f"--include-data-files={resources_dir / 'ref' / '**/*.*'}=resources/ref/")
    # Include files in the detectable subdirectory - scan recursively with **/*
    # cmd.append(f"--include-data-files={resources_dir / 'detectable' / '**/*.*'}=resources/detectable/")

    # Add debug option if requested
    # if debug_mode:
    #     cmd.append("--enable-plugin=pylint-warnings")
    #     cmd.append("--include-module=faulthandler")
    #     cmd.append("--disable-console-hidden")
    # else:
    #     pass
    # For production build
    # cmd.append("--file-version=1.0.0")
    # cmd.append("--file-description=NIKKE Arena Data Collector")

    # Add main file
    main_file = src_dir / "main.py"
    cmd.append(str(main_file))

    # Print command
    print("Running Nuitka build with command:")
    print(" ".join(cmd))
    print(f"Build report will be saved to: {report_path}")

    # Execute Nuitka build
    result = subprocess.run(cmd)

    if result.returncode == 0:
        # Success
        if onefile:
            output_path = output_dir / f"{output_name}.exe"
        elif standalone:
            output_path = output_dir / f"{output_name}.dist" / f"{output_name}.exe"
        else:
            output_path = output_dir / f"{output_name}.pyd"  # Or .so on Linux/Mac

        print(f"Build successful! Output at: {output_path}")
        print(f"Build report saved to: {report_path}")
        return True
    else:
        # Failure
        print(f"Build failed with exit code {result.returncode}")
        print(f"Check build report at: {report_path} for details")
        return False


def build_release():
    """Build release version"""
    success = build(
        output_dir=os.path.join(get_project_root()),
        output_name="nikke-data-collector",
        debug_mode=False,
        standalone=False,
        onefile=True
    )
    return sys.exit(0 if success else 1)


def build_debug():
    success = build(
        output_dir=os.path.join(get_project_root()),
        output_name="nikke-data-collector-debug",
        debug_mode=True,
        standalone=False,
        onefile=True
    )
    return sys.exit(0 if success else 1)


if __name__ == "__main__":
    build_debug()
