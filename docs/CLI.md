# Pydust CLI Reference

Pydust includes a command-line interface (CLI) similar to [Maturin](https://github.com/PyO3/maturin) for easy project management and development.

## Installation

```bash
pip install ziggy-pydust
```

After installation, the `pydust` command will be available in your terminal.

## Commands Overview

| Command | Description |
|---------|-------------|
| `pydust new` | Create a new project with boilerplate |
| `pydust init` | Initialize pydust in an existing directory |
| `pydust develop` | Build and install in development mode |
| `pydust build-wheel` | Build distribution wheels |
| `pydust build` | Build extension modules directly |
| `pydust watch` | Watch for changes and rebuild automatically |
| `pydust debug` | Compile Zig file with debug symbols |

---

## `pydust new`

Create a new Pydust project in a new directory with all necessary boilerplate.

### Usage

```bash
pydust new <project-name> [OPTIONS]
```

### Arguments

- `<project-name>` - Name of the project (required)

### Options

- `-p, --path <PATH>` - Parent directory (defaults to current directory)

### Example

```bash
# Create a new project called "my_extension"
pydust new my_extension

# Create in a specific directory
pydust new my_extension --path ~/projects
```

### What Gets Created

```
my_extension/
├── .git/                    # Git repository
├── .gitignore               # Python/Zig gitignore
├── build.zig                # Zig build file
├── pyproject.toml           # Python project config
├── README.md                # Project documentation
├── my_extension/            # Python package
│   └── __init__.py
├── src/                     # Zig source files
│   └── my_extension.zig
└── tests/                   # Python tests
    └── test_my_extension.py
```

---

## `pydust init`

Initialize Pydust in an existing directory. Useful when you want to add Pydust to an existing Python project.

### Usage

```bash
pydust init [OPTIONS]
```

### Options

- `-n, --name <NAME>` - Package name (defaults to directory name)
- `-a, --author <AUTHOR>` - Author name (defaults to git config)
- `-f, --force` - Overwrite existing files

### Example

```bash
# Initialize in current directory
cd my_project
pydust init

# Initialize with custom name
pydust init --name my_custom_name

# Force overwrite existing files
pydust init --force
```

---

## `pydust develop`

Build Zig extension modules and install the package in development mode (editable install). This is similar to `pip install -e .` but also builds the Zig extensions first.

### Usage

```bash
pydust develop [OPTIONS]
```

### Options

- `-o, --optimize <LEVEL>` - Optimization level: `Debug`, `ReleaseSafe`, `ReleaseFast`, `ReleaseSmall` (default: `Debug`)
- `-v, --verbose` - Enable verbose output
- `-e, --extras <EXTRAS>` - Install optional extras (e.g., `dev`, `test`)
- `--build-only` - Only build extensions without installing

### Examples

```bash
# Basic development install
pydust develop

# Release build for performance testing
pydust develop --optimize ReleaseFast

# Install with dev extras
pydust develop --extras dev test

# Just build, don't install
pydust develop --build-only

# Verbose output for debugging
pydust develop --verbose
```

### What It Does

1. Builds Zig extension modules with specified optimization level
2. Installs the package in editable mode (`pip install -e .`)
3. Verifies the installation

This is the recommended command for day-to-day development!

---

## `pydust build-wheel`

Build distribution wheels for one or more platforms. This is an alias for `python -m pydust.wheel` with a more convenient interface.

### Usage

```bash
pydust build-wheel [OPTIONS]
```

### Options

- `--platform <PLATFORM>` - Target platform (see table below)
- `--all-platforms` - Build for all supported platforms
- `--optimize <LEVEL>` - Optimization level (default: `ReleaseFast`)
- `--output-dir <DIR>` - Output directory (default: `dist`)
- `--no-clean` - Don't clean build artifacts before building
- `-v, --verbose` - Enable verbose output

### Supported Platforms

| Platform | Flag |
|----------|------|
| Linux x86_64 | `linux-x86_64` |
| Linux ARM64 | `linux-aarch64` |
| macOS x86_64 | `macos-x86_64` |
| macOS ARM64 | `macos-arm64` |
| Windows x64 | `windows-x64` |

### Examples

```bash
# Build for current platform
pydust build-wheel

# Build for specific platform
pydust build-wheel --platform linux-x86_64

# Build for all platforms
pydust build-wheel --all-platforms

# Optimized for size (good for AWS Lambda)
pydust build-wheel --optimize ReleaseSmall

# Custom output directory
pydust build-wheel --output-dir wheelhouse
```

### Cross-Compilation

Pydust uses Zig's built-in cross-compilation to build wheels for any platform from any platform:

```bash
# Build Linux wheels from macOS
pydust build-wheel --platform linux-x86_64

# Build macOS ARM64 wheels from Windows
pydust build-wheel --platform macos-arm64
```

---

## `pydust build`

Lower-level command to build specific Zig extension modules. Most users should use `pydust develop` instead.

### Usage

```bash
pydust build [OPTIONS] <EXTENSIONS>
```

### Arguments

- `<EXTENSIONS>` - Space-separated list of extensions in format `<name>=<path>` or `<path>`

### Options

- `-z, --zig-exe <PATH>` - Custom Zig executable path
- `-b, --build-zig <FILE>` - Custom build.zig file (default: `build.zig`)
- `-m, --self-managed` - Use self-managed build mode
- `-a, --limited-api` - Use Python limited API (default: true)
- `-p, --prefix <PREFIX>` - Module name prefix

### Examples

```bash
# Build a single module
pydust build src/my_module.zig

# Build with custom name
pydust build mypackage.core=src/core.zig

# Build multiple modules
pydust build src/module1.zig src/module2.zig
```

---

## `pydust watch`

Watch Zig source files for changes and automatically rebuild. Great for iterative development.

### Usage

```bash
pydust watch [OPTIONS] [PYTEST_ARGS]
```

### Options

- `-o, --optimize <LEVEL>` - Optimization level (default: `Debug`)
- `-t, --test` - Run Zig tests after rebuild
- `--pytest` - Run pytest instead of Zig tests
- `<PYTEST_ARGS>` - Additional arguments for pytest (when using `--pytest`)

### Examples

```bash
# Watch and rebuild on changes
pydust watch

# Watch and run Zig tests
pydust watch --test

# Watch and run pytest
pydust watch --pytest

# Watch with specific pytest args
pydust watch --pytest -v tests/test_core.py

# Watch with release optimization
pydust watch --optimize ReleaseFast
```

---

## `pydust debug`

Compile a Zig file with debug symbols. Useful for IDE debugging.

### Usage

```bash
pydust debug <entrypoint>
```

### Arguments

- `<entrypoint>` - Zig file to compile with debug symbols

### Example

```bash
pydust debug src/my_module.zig
```

---

## Comparison with Maturin

If you're familiar with Maturin (for PyO3/Rust), here's how Pydust commands map:

| Maturin | Pydust | Notes |
|---------|--------|-------|
| `maturin new` | `pydust new` | Creates new project |
| `maturin init` | `pydust init` | Initializes existing directory |
| `maturin develop` | `pydust develop` | Development install |
| `maturin build` | `pydust build-wheel` | Builds wheels |
| `maturin publish` | *(use twine)* | Publish to PyPI |

---

## Typical Workflows

### Starting a New Project

```bash
# 1. Create project
pydust new my_extension
cd my_extension

# 2. Develop and test
pydust develop
pytest

# 3. Make changes and rebuild
# Edit src/my_extension.zig
pydust develop

# 4. Build release wheels
pydust build-wheel --all-platforms
```

### Adding Pydust to Existing Project

```bash
# 1. Initialize
cd existing_project
pydust init

# 2. Write your Zig code in src/
# Edit src/my_module.zig

# 3. Develop
pydust develop
```

### Development with Auto-Rebuild

```bash
# Terminal 1: Watch mode
pydust watch --pytest

# Terminal 2: Edit code
# Changes trigger automatic rebuild and test
```

### Building for Production

```bash
# Build optimized wheels for all platforms
pydust build-wheel --all-platforms --optimize ReleaseSmall

# Wheels in dist/
ls dist/*.whl
```

---

## Environment Variables

Some Pydust commands respect environment variables:

- `ZIG_TARGET` - Override target platform (e.g., `x86_64-linux-gnu`)
- `PYDUST_OPTIMIZE` - Override optimization level
- `PYTHON` - Python executable to use

---

## Getting Help

For any command, use `--help`:

```bash
pydust --help
pydust new --help
pydust develop --help
pydust build-wheel --help
```

---

## See Also

- [Distribution Guide](./distribution.md) - Detailed guide on building and distributing wheels
- [Quick Start Guide](./DISTRIBUTION_QUICKSTART.md) - Fast-track commands
- [Main Documentation](https://pydust.fulcrum.so) - Full Pydust documentation
