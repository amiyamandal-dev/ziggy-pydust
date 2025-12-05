# Pydust CLI Usage Examples

Quick reference guide for the new Maturin-like CLI commands.

## Installation

```bash
pip install ziggy-pydust
```

## Command Comparison: Before and After

### Creating a New Project

**Before:**
```bash
# Manual setup
mkdir my_extension
cd my_extension
touch pyproject.toml build.zig README.md
mkdir src tests my_extension
# ... manually create all files ...
git init
```

**After (New CLI):**
```bash
pydust new my_extension
# Done! Everything created automatically
```

### Setting Up for Development

**Before:**
```bash
pip install -e .
# Build manually or use pytest
```

**After (New CLI):**
```bash
pydust develop
# Builds Zig extensions + installs in editable mode
```

### Building Wheels

**Before:**
```bash
python -m pydust.wheel --all-platforms
```

**After (New CLI):**
```bash
pydust build-wheel --all-platforms
# Shorter and more intuitive!
```

## Complete Workflow Examples

### Example 1: Brand New Project

```bash
# Step 1: Create project
pydust new awesome_extension
cd awesome_extension

# Step 2: Develop
pydust develop

# Step 3: Test
pytest

# Step 4: Make changes to src/awesome_extension.zig
# ... edit your code ...

# Step 5: Rebuild
pydust develop

# Step 6: Build wheels for distribution
pydust build-wheel --all-platforms

# Step 7: Publish to PyPI
pip install twine
twine upload dist/*
```

### Example 2: Add Pydust to Existing Project

```bash
# Step 1: Navigate to your project
cd my_existing_project

# Step 2: Initialize Pydust
pydust init

# Step 3: Create your Zig extension in src/
# ... write your Zig code ...

# Step 4: Configure in pyproject.toml
# Add [[tool.pydust.ext_module]] entries

# Step 5: Develop
pydust develop

# Step 6: Test
pytest
```

### Example 3: Fast Iteration with Watch Mode

```bash
# Terminal 1: Start watch mode
pydust watch --pytest

# Terminal 2: Edit your code
vim src/my_module.zig

# Watch mode automatically rebuilds and runs tests!
```

### Example 4: Cross-Platform Distribution

```bash
# Build for multiple platforms from a single machine
pydust build-wheel --platform linux-x86_64
pydust build-wheel --platform macos-arm64
pydust build-wheel --platform windows-x64

# Or build all at once
pydust build-wheel --all-platforms

# Result: dist/ contains wheels for all platforms
ls dist/
# my_extension-0.1.0-cp311-cp311-linux_x86_64.whl
# my_extension-0.1.0-cp311-cp311-macosx_11_0_arm64.whl
# my_extension-0.1.0-cp311-cp311-win_amd64.whl
```

### Example 5: Optimized Builds

```bash
# Development (fast compile, includes debug info)
pydust develop --optimize Debug

# Release testing (optimized, with safety checks)
pydust develop --optimize ReleaseSafe

# Production (maximum performance)
pydust build-wheel --optimize ReleaseFast

# Size-optimized (for AWS Lambda, edge functions)
pydust build-wheel --optimize ReleaseSmall
```

## Command Quick Reference

### Project Creation

```bash
# Create new project
pydust new <name>              # Creates directory with name
pydust new <name> --path ~/dev # Create in specific location

# Initialize existing directory
pydust init                    # Use directory name
pydust init --name mylib       # Override package name
pydust init --force            # Overwrite existing files
```

### Development

```bash
# Build and install
pydust develop                      # Debug build
pydust develop -o ReleaseFast       # Release build
pydust develop --verbose            # Show detailed output
pydust develop --extras dev test    # Install with extras
pydust develop --build-only         # Just build, don't install
```

### Distribution

```bash
# Build wheels
pydust build-wheel                          # Current platform
pydust build-wheel --platform linux-x86_64  # Specific platform
pydust build-wheel --all-platforms          # All platforms
pydust build-wheel --optimize ReleaseSmall  # Optimize for size
pydust build-wheel --output-dir wheelhouse  # Custom output
pydust build-wheel --verbose                # Detailed output
```

### Other Commands

```bash
# Watch mode
pydust watch                   # Watch and rebuild
pydust watch --test           # Watch and run Zig tests
pydust watch --pytest         # Watch and run pytest
pydust watch -o ReleaseFast   # Watch with optimization

# Low-level build
pydust build src/module.zig   # Build specific module
pydust debug src/module.zig   # Compile with debug symbols
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: Build and Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install ziggy-pydust pytest

      - name: Build and test
        run: |
          pydust develop
          pytest

  build-wheels:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Build wheels
        run: |
          pip install ziggy-pydust
          pydust build-wheel --all-platforms

      - uses: actions/upload-artifact@v3
        with:
          name: wheels
          path: dist/*.whl
```

### GitLab CI

```yaml
stages:
  - test
  - build

test:
  stage: test
  script:
    - pip install ziggy-pydust pytest
    - pydust develop
    - pytest

build:
  stage: build
  script:
    - pip install ziggy-pydust
    - pydust build-wheel --all-platforms
  artifacts:
    paths:
      - dist/
```

## Tips and Tricks

### 1. Use Aliases

```bash
# Add to your ~/.bashrc or ~/.zshrc
alias pd='pydust'
alias pdd='pydust develop'
alias pdw='pydust build-wheel'

# Then use:
pd new my_ext
pdd
pdw --all-platforms
```

### 2. Development Workflow

```bash
# Keep two terminals open:
# Terminal 1: Watch mode
pydust watch --pytest

# Terminal 2: Edit and commit
vim src/module.zig
git commit -am "Add new feature"
```

### 3. Quick Testing

```bash
# Build and test in one line
pydust develop && pytest -v
```

### 4. Check What Gets Created

```bash
# Before creating a project, see what would be created
pydust new test_project
ls -la test_project/
cat test_project/pyproject.toml
rm -rf test_project  # Clean up after exploring
```

### 5. Build for Specific Python Versions

Currently builds for the Python version you're using:

```bash
# Use different Python versions
python3.11 -m pydust develop
python3.12 -m pydust develop
```

## Troubleshooting

### "Command not found: pydust"

```bash
# Make sure pydust is installed
pip install ziggy-pydust

# Or use as module
python -m pydust --help
```

### "pyproject.toml not found"

```bash
# Make sure you're in a pydust project directory
pydust init  # Initialize current directory
```

### Build Fails

```bash
# Try verbose mode to see what's happening
pydust develop --verbose

# Check Zig installation
zig version

# Make sure dependencies are installed
pip install -e .
```

### Import Errors After Installation

```bash
# Verify installation
pip show your-package-name

# Reinstall
pip uninstall your-package-name
pydust develop
```

## See Also

- [CLI Reference](docs/CLI.md) - Detailed command documentation
- [Distribution Guide](docs/distribution.md) - Full distribution guide
- [Quick Start](docs/DISTRIBUTION_QUICKSTART.md) - Fast-track commands
- [Main Documentation](https://pydust.fulcrum.so) - Complete Pydust docs

## Comparison with Other Tools

| Tool | Language | Create Project | Dev Install | Build Wheels |
|------|----------|----------------|-------------|--------------|
| **Pydust** | Zig | `pydust new` | `pydust develop` | `pydust build-wheel` |
| Maturin | Rust | `maturin new` | `maturin develop` | `maturin build` |
| Cython | Python/C | Manual | `pip install -e .` | `python setup.py bdist_wheel` |
| pybind11 | C++ | Manual | `pip install -e .` | `python setup.py bdist_wheel` |

Pydust brings Zig's simplicity with Maturin's developer experience!
