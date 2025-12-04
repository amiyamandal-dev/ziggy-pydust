"""
Development installation utilities for Pydust.

Similar to Maturin's develop functionality, this module provides
utilities for building and installing Pydust projects in development mode.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional


def develop_install(
    optimize: str = "Debug",
    verbose: bool = False,
    extras: Optional[list[str]] = None,
) -> None:
    """
    Build the extension and install the package in development mode.

    This is similar to `pip install -e .` but also builds the Zig extension
    modules first.

    Args:
        optimize: Optimization level (Debug, ReleaseSafe, ReleaseFast, ReleaseSmall)
        verbose: Enable verbose output
        extras: Optional list of extras to install
    """
    project_root = Path.cwd()
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print("❌ Error: pyproject.toml not found in current directory!")
        print("   Make sure you're in a Pydust project directory.")
        sys.exit(1)

    print(f"Building and installing in development mode (optimize={optimize})...")

    # Step 1: Build the extension modules using pydust build command
    print("\n[1/3] Building Zig extension modules...")
    try:
        # Import here to avoid circular imports
        from pydust import buildzig, config

        conf = config.load()

        # Use environment variable to set optimization level
        import os

        env = os.environ.copy()
        env["PYDUST_OPTIMIZE"] = optimize

        buildzig.zig_build(
            argv=["install", f"-Dpython-exe={sys.executable}", f"-Doptimize={optimize}"],
            conf=conf,
            env=env,
        )
        print("  ✓ Extension modules built successfully")
    except Exception as e:
        print(f"  ❌ Failed to build extension modules: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)

    # Step 2: Install the package in editable mode
    print("\n[2/3] Installing package in editable mode...")
    pip_cmd = [sys.executable, "-m", "pip", "install", "-e", "."]

    if extras:
        extras_str = ",".join(extras)
        pip_cmd[-1] = f".[{extras_str}]"

    if verbose:
        pip_cmd.append("-v")

    try:
        result = subprocess.run(
            pip_cmd,
            cwd=project_root,
            check=True,
            capture_output=not verbose,
            text=True,
        )
        print("  ✓ Package installed in editable mode")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to install package: {e}")
        if not verbose and e.stderr:
            print(f"     {e.stderr}")
        sys.exit(1)

    # Step 3: Verify installation
    print("\n[3/3] Verifying installation...")
    try:
        import tomllib

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        package_name = pyproject["tool"]["poetry"]["name"]

        # Try to import the package
        try:
            __import__(package_name.replace("-", "_"))
            print(f"  ✓ Package '{package_name}' is importable")
        except ImportError as e:
            print(f"  ⚠️  Warning: Could not import '{package_name}': {e}")
            print("     The package is installed but may have import issues.")

    except Exception as e:
        print(f"  ⚠️  Warning: Could not verify installation: {e}")

    print("\n✅ Development installation complete!\n")
    print("You can now:")
    print("  - Import your package in Python")
    print("  - Run tests with: pytest")
    print("  - Make changes to Zig code and rebuild with: pydust develop")


def develop_build_only(optimize: str = "Debug", verbose: bool = False) -> None:
    """
    Build the extension modules without installing.

    Args:
        optimize: Optimization level
        verbose: Enable verbose output
    """
    project_root = Path.cwd()
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print("❌ Error: pyproject.toml not found in current directory!")
        print("   Make sure you're in a Pydust project directory.")
        sys.exit(1)

    print(f"Building Zig extension modules (optimize={optimize})...")

    try:
        from pydust import buildzig, config

        conf = config.load()

        import os

        env = os.environ.copy()
        env["PYDUST_OPTIMIZE"] = optimize

        buildzig.zig_build(
            argv=["install", f"-Dpython-exe={sys.executable}", f"-Doptimize={optimize}"],
            conf=conf,
            env=env,
        )
        print("✅ Extension modules built successfully!")
    except Exception as e:
        print(f"❌ Failed to build extension modules: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)
