"""
Project initialization utilities for Pydust.

Similar to Maturin's init functionality, this module provides templates
and utilities for bootstrapping new Pydust projects.

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

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from pydust.security import SecurityValidator, SecurityError
from pydust.logging_config import get_logger

logger = get_logger(__name__)


# Template files content
TEMPLATE_PYPROJECT = """[tool.poetry]
name = "{package_name}"
version = "0.1.0"
description = "A Python extension module written in Zig using Pydust"
authors = ["{author}"]
readme = "README.md"
packages = [{{ include = "{package_name}" }}]

[tool.poetry.dependencies]
python = "^3.11"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
ziggy-pydust = "^0.1.0"

[build-system]
requires = ["poetry-core", "ziggy-pydust==0.1.0"]
build-backend = "poetry.core.masonry.api"

[tool.pydust]
[[tool.pydust.ext_module]]
name = "{package_name}.{module_name}"
root = "src/{module_name}.zig"
"""

TEMPLATE_BUILD_ZIG = """const std = @import("std");

pub fn build(b: *std.Build) void {{
    const target = b.standardTargetOptions(.{{}});
    const optimize = b.standardOptimizeOption(.{{}});

    // Get pydust dependency
    const pydust = b.dependency("pydust", .{{
        .target = target,
        .optimize = optimize,
    }});

    // Create the Python extension module
    const py_module = pydust.artifact("{module_name}");
    py_module.root_module.addImport("pydust", pydust.module("pydust"));

    b.installArtifact(py_module);
}}
"""

TEMPLATE_ZIG_MODULE = """const py = @import("pydust");

/// Add two numbers together.
pub fn add(args: struct {{ a: i32, b: i32 }}) i32 {{
    return args.a + args.b;
}}

/// Multiply two numbers.
pub fn multiply(args: struct {{ a: i32, b: i32 }}) i32 {{
    return args.a * args.b;
}}

/// Say hello to someone.
pub fn hello(args: struct {{ name: []const u8 }}) !py.PyString {{
    const greeting = try std.fmt.allocPrint(
        py.allocator(),
        "Hello, {{s}}!",
        .{{args.name}},
    );
    defer py.allocator().free(greeting);
    return py.PyString.create(greeting);
}}

// Tests
test "add" {{
    try py.testing.expect(add(.{{ .a = 2, .b = 3 }}) == 5);
    try py.testing.expect(add(.{{ .a = -1, .b = 1 }}) == 0);
}}

test "multiply" {{
    try py.testing.expect(multiply(.{{ .a = 2, .b = 3 }}) == 6);
    try py.testing.expect(multiply(.{{ .a = -2, .b = 3 }}) == -6);
}}

// Register this module with Python
comptime {{
    py.rootmodule(@This());
}}
"""

TEMPLATE_TEST_PY = """\"\"\"Tests for {package_name}.\"\"\"

import {package_name}.{module_name} as m


def test_add():
    assert m.add(2, 3) == 5
    assert m.add(-1, 1) == 0
    assert m.add(0, 0) == 0


def test_multiply():
    assert m.multiply(2, 3) == 6
    assert m.multiply(-2, 3) == -6
    assert m.multiply(0, 5) == 0


def test_hello():
    assert m.hello("World") == "Hello, World!"
    assert m.hello("Pydust") == "Hello, Pydust!"
"""

TEMPLATE_README = """# {package_name}

A Python extension module written in Zig using [Pydust](https://github.com/fulcrum-so/ziggy-pydust).

## Installation

```bash
pip install {package_name}
```

## Development

### Prerequisites

- Python 3.11+
- Zig 0.14.0+
- Poetry (for development)

### Setup

```bash
# Install dependencies
pip install -e .[dev]

# Build the extension
pydust develop

# Run tests
pytest
```

### Building

```bash
# Build for current platform
pydust build-wheel

# Build for all platforms
pydust build-wheel --all-platforms
```

## Usage

```python
import {package_name}.{module_name} as m

# Call functions from the Zig extension
result = m.add(2, 3)
print(result)  # 5

greeting = m.hello("World")
print(greeting)  # Hello, World!
```

## License

This project is licensed under the Apache 2.0 License.
"""

TEMPLATE_GITIGNORE = """# Zig
zig-cache/
zig-out/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg-info/
dist/
build/
.eggs/
*.egg

# Virtual environments
.venv/
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Poetry
poetry.lock
"""

TEMPLATE_BUILD_ZIG_DEPS = """const std = @import("std");

pub fn build(b: *std.Build) void {{
    const target = b.standardTargetOptions(.{{}});
    const optimize = b.standardOptimizeOption(.{{}});

    const python_exe = b.option([]const u8, "python-exe", "Python executable") orelse "python3";

    // Import pydust build utilities
    const pydust_dep = b.dependency("ziggy_pydust", .{{
        .target = target,
        .optimize = optimize,
    }});

    const pydust_mod = pydust_dep.module("pydust");

    // Build the extension module
    const lib = b.addSharedLibrary(.{{
        .name = "{module_name}",
        .root_source_file = b.path("src/{module_name}.zig"),
        .target = target,
        .optimize = optimize,
    }});

    lib.root_module.addImport("pydust", pydust_mod);
    lib.linkLibC();

    // Python configuration
    const python_config = b.addSystemCommand(&.{{python_exe}});
    python_config.addArgs(&.{{"-c", "import sysconfig; print(sysconfig.get_path('include'))"}});

    lib.addIncludePath(.{{ .cwd_relative = b.pathFromRoot(".") }});

    const install = b.addInstallArtifact(lib, .{{}});
    b.getInstallStep().dependOn(&install.step);
}}
"""


def get_git_user_info() -> tuple[str, str]:
    """Get git user name and email if available."""
    name = "Your Name <your.email@example.com>"
    try:
        # SECURITY: Add timeout to prevent hanging
        git_name = subprocess.check_output(
            ["git", "config", "user.name"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,  # 5 second timeout
        ).strip()
        git_email = subprocess.check_output(
            ["git", "config", "user.email"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,  # 5 second timeout
        ).strip()
        if git_name and git_email:
            name = f"{git_name} <{git_email}>"
            logger.debug(f"Detected git user: {name}")
    except subprocess.TimeoutExpired:
        logger.warning("Git config command timed out")
    except subprocess.CalledProcessError as e:
        logger.debug(f"Git config not available: {e}")
    except FileNotFoundError:
        logger.debug("Git not found in PATH")
    except Exception as e:
        logger.warning(f"Unexpected error getting git info: {e}")
    return name, name


def init_project(
    path: Path,
    package_name: Optional[str] = None,
    author: Optional[str] = None,
    force: bool = False,
) -> None:
    """
    Initialize a new Pydust project in the given directory.

    Args:
        path: Directory to initialize the project in
        package_name: Name of the package (defaults to directory name)
        author: Author name (defaults to git config)
        force: Overwrite existing files
    """
    logger.info(f"Initializing Pydust project in {path}")

    # SECURITY: Validate path before using
    try:
        path = path.resolve()
        # Ensure path is absolute and normalized
        if not path.is_absolute():
            raise SecurityError("Path must be absolute")

        # Create directory with validation
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created project directory: {path}")
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to create directory: {e}")
        print(f"❌ Error: Cannot create directory at {path}: {e}")
        sys.exit(1)
    except SecurityError as e:
        logger.error(f"Security validation failed: {e}")
        print(f"❌ Security Error: {e}")
        sys.exit(1)

    if package_name is None:
        package_name = path.name.replace("-", "_")

    # SECURITY: Validate and sanitize package name
    is_valid, error, package_name = SecurityValidator.sanitize_package_name(package_name)
    if not is_valid:
        logger.error(f"Invalid package name: {error}")
        print(f"❌ Error: {error}")
        sys.exit(1)

    logger.debug(f"Validated package name: {package_name}")
    module_name = package_name

    if author is None:
        author, _ = get_git_user_info()

    # SECURITY: Escape author string for TOML to prevent injection
    author_safe = SecurityValidator.escape_toml_string(author)
    logger.debug(f"Sanitized author string")

    print(f"Initializing Pydust project: {package_name}")
    print(f"  Location: {path}")
    print(f"  Author: {author}")

    # Check if directory is not empty
    if list(path.iterdir()) and not force:
        print("\n⚠️  Directory is not empty!")
        response = input("Do you want to continue? This may overwrite existing files. (y/N): ")
        if response.lower() != "y":
            print("Aborted.")
            return

    # Create directory structure
    try:
        (path / "src").mkdir(exist_ok=True)
        (path / "tests").mkdir(exist_ok=True)
        (path / package_name).mkdir(exist_ok=True)
        logger.debug("Created directory structure")
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to create directories: {e}")
        print(f"❌ Error: Cannot create project directories: {e}")
        sys.exit(1)

    # Create __init__.py for the package
    init_py = path / package_name / "__init__.py"
    if not init_py.exists() or force:
        content = f'"""The {package_name} package."""\n\n__version__ = "0.1.0"\n'
        try:
            # SECURITY: Safe file write (prevents symlink attacks)
            SecurityValidator.safe_write_text(init_py, content, force=force)
            print(f"  ✓ Created {init_py.relative_to(path)}")
            logger.debug(f"Created {init_py.name}")
        except (SecurityError, OSError, IOError) as e:
            logger.error(f"Failed to create {init_py.name}: {e}")
            print(f"  ❌ Failed to create {init_py.name}: {e}")
            sys.exit(1)

    # Create pyproject.toml
    pyproject_path = path / "pyproject.toml"
    if not pyproject_path.exists() or force:
        # Use sanitized author string to prevent TOML injection
        content = TEMPLATE_PYPROJECT.format(
            package_name=package_name,
            module_name=module_name,
            author=author_safe,
        )
        try:
            # SECURITY: Safe file write (prevents symlink attacks)
            SecurityValidator.safe_write_text(pyproject_path, content, force=force)
            print(f"  ✓ Created {pyproject_path.relative_to(path)}")
            logger.debug(f"Created {pyproject_path.name}")
        except (SecurityError, OSError, IOError) as e:
            logger.error(f"Failed to create {pyproject_path.name}: {e}")
            print(f"  ❌ Failed to create {pyproject_path.name}: {e}")
            sys.exit(1)

    # Create build.zig (simple version that works with pydust CLI)
    build_zig_path = path / "build.zig"
    if not build_zig_path.exists() or force:
        content = "// This project uses Pydust's managed build system.\n"
        try:
            # SECURITY: Safe file write
            SecurityValidator.safe_write_text(build_zig_path, content, force=force)
            print(f"  ✓ Created {build_zig_path.relative_to(path)}")
            logger.debug(f"Created {build_zig_path.name}")
        except (SecurityError, OSError, IOError) as e:
            logger.error(f"Failed to create {build_zig_path.name}: {e}")
            print(f"  ❌ Failed to create {build_zig_path.name}: {e}")
            sys.exit(1)

    # Create Zig source file
    zig_src_path = path / "src" / f"{module_name}.zig"
    if not zig_src_path.exists() or force:
        try:
            # SECURITY: Safe file write
            SecurityValidator.safe_write_text(zig_src_path, TEMPLATE_ZIG_MODULE, force=force)
            print(f"  ✓ Created {zig_src_path.relative_to(path)}")
            logger.debug(f"Created {zig_src_path.name}")
        except (SecurityError, OSError, IOError) as e:
            logger.error(f"Failed to create {zig_src_path.name}: {e}")
            print(f"  ❌ Failed to create {zig_src_path.name}: {e}")
            sys.exit(1)

    # Create Python test file
    test_path = path / "tests" / f"test_{module_name}.py"
    if not test_path.exists() or force:
        content = TEMPLATE_TEST_PY.format(package_name=package_name, module_name=module_name)
        try:
            # SECURITY: Safe file write
            SecurityValidator.safe_write_text(test_path, content, force=force)
            print(f"  ✓ Created {test_path.relative_to(path)}")
            logger.debug(f"Created {test_path.name}")
        except (SecurityError, OSError, IOError) as e:
            logger.error(f"Failed to create {test_path.name}: {e}")
            print(f"  ❌ Failed to create {test_path.name}: {e}")
            sys.exit(1)

    # Create README
    readme_path = path / "README.md"
    if not readme_path.exists() or force:
        content = TEMPLATE_README.format(package_name=package_name, module_name=module_name)
        try:
            # SECURITY: Safe file write
            SecurityValidator.safe_write_text(readme_path, content, force=force)
            print(f"  ✓ Created {readme_path.relative_to(path)}")
            logger.debug(f"Created {readme_path.name}")
        except (SecurityError, OSError, IOError) as e:
            logger.error(f"Failed to create {readme_path.name}: {e}")
            print(f"  ❌ Failed to create {readme_path.name}: {e}")
            sys.exit(1)

    # Create .gitignore
    gitignore_path = path / ".gitignore"
    if not gitignore_path.exists() or force:
        try:
            # SECURITY: Safe file write
            SecurityValidator.safe_write_text(gitignore_path, TEMPLATE_GITIGNORE, force=force)
            print(f"  ✓ Created {gitignore_path.relative_to(path)}")
            logger.debug(f"Created {gitignore_path.name}")
        except (SecurityError, OSError, IOError) as e:
            logger.error(f"Failed to create {gitignore_path.name}: {e}")
            print(f"  ❌ Failed to create {gitignore_path.name}: {e}")
            sys.exit(1)

    # Initialize git repo if not already initialized
    if not (path / ".git").exists():
        try:
            # SECURITY: Add timeout to git init
            subprocess.run(
                ["git", "init"],
                cwd=path,
                check=True,
                capture_output=True,
                timeout=10,  # 10 second timeout
            )
            print("  ✓ Initialized git repository")
            logger.debug("Initialized git repository")
        except subprocess.TimeoutExpired:
            logger.warning("Git init timed out")
            print("  ⚠️  Git init timed out, skipping")
        except subprocess.CalledProcessError as e:
            logger.debug(f"Git init failed: {e}")
            # Don't fail project creation if git init fails
        except FileNotFoundError:
            logger.debug("Git not found in PATH")
            # Git not installed, skip
        except Exception as e:
            logger.warning(f"Unexpected error during git init: {e}")

    logger.info(f"Project {package_name} initialized successfully")
    print("\n✅ Project initialized successfully!\n")
    print("Next steps:")
    print(f"  cd {path.name if path != Path.cwd() else '.'}")
    print("  pip install -e .")
    print("  pydust develop")
    print("  pytest")


def new_project(name: str, path: Optional[Path] = None) -> None:
    """
    Create a new Pydust project in a new directory.

    Args:
        name: Name of the project
        path: Parent directory (defaults to current directory)
    """
    logger.info(f"Creating new project: {name}")

    if path is None:
        path = Path.cwd()

    # SECURITY: Validate project name before using as directory
    is_valid, error, sanitized_name = SecurityValidator.sanitize_package_name(name)
    if not is_valid:
        logger.error(f"Invalid project name: {error}")
        print(f"❌ Error: {error}")
        sys.exit(1)

    # Use sanitized name for directory
    project_path = path / sanitized_name

    if project_path.exists():
        logger.error(f"Directory already exists: {sanitized_name}")
        print(f"❌ Error: Directory '{sanitized_name}' already exists!")
        sys.exit(1)

    logger.debug(f"Creating project at {project_path}")
    init_project(project_path, package_name=sanitized_name)
