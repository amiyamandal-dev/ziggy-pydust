# Ziggy Pydust

<p align="center">
  <a href="https://pydust.fulcrum.so">
    <img src="https://pydust.fulcrum.so/assets/ziggy-pydust.png" style="border-radius: 20px" />
  </a>
</p>
<p align="center">
    <em>A framework for writing native Python extension modules in Zig.</em>
</p>
<p align="center">
<a href="https://github.com/fulcrum-so/ziggy-pydust/actions" target="_blank">
    <img src="https://img.shields.io/github/actions/workflow/status/fulcrum-so/ziggy-pydust/ci.yml?branch=develop&logo=github&style=" alt="Actions">
</a>
<a href="https://pypi.org/project/ziggy-pydust" target="_blank">
    <img src="https://img.shields.io/pypi/v/ziggy-pydust" alt="Package version">
</a>
<a href="https://docs.python.org/3/whatsnew/3.11.html" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/ziggy-pydust" alt="Python version">
</a>
<a href="https://github.com/fulcrum-so/ziggy-pydust/blob/develop/LICENSE" target="_blank">
    <img src="https://img.shields.io/github/license/fulcrum-so/ziggy-pydust" alt="License">
</a>
</p>

---

**Documentation**: <a href="https://pydust.fulcrum.so/latest" target="_blank">https://pydust.fulcrum.so/latest</a>

**API Reference**: <a href="https://pydust.fulcrum.so/latest/zig" target="_blank">https://pydust.fulcrum.so/latest/zig</a>

**Source Code**: <a href="https://github.com/fulcrum-so/ziggy-pydust" target="_blank">https://github.com/fulcrum-so/ziggy-pydust</a>

---

## Overview

Ziggy Pydust is a complete framework for building high-performance Python extension modules in Zig. It provides:

- 🚀 **Seamless Python-Zig Interop** - Automatic argument marshalling and type conversion
- 🔧 **Complete CLI Toolkit** - Maturin-style commands for project lifecycle management
- 📦 **Cross-Platform Builds** - Build wheels for Linux, macOS, and Windows
- 🔗 **C/C++ Integration** - Automatic binding generation for C/C++ libraries
- 🧪 **Testing Integration** - Pytest plugin to discover and run Zig tests
- ⚡ **Hot Reload** - Watch mode with automatic rebuilding
- 🛡️ **Memory Safe** - Leverages Zig's safety features with Python's GC

## Quick Example

```zig
const py = @import("pydust");

pub fn fibonacci(args: struct { n: u64 }) u64 {
    if (args.n < 2) return args.n;

    var sum: u64 = 0;
    var last: u64 = 0;
    var curr: u64 = 1;
    for (1..args.n) |_| {
        sum = last + curr;
        last = curr;
        curr = sum;
    }
    return sum;
}

comptime {
    py.rootmodule(@This());
}
```

```python
import mymodule
print(mymodule.fibonacci(10))  # Output: 55
```

## Compatibility

- **Zig**: 0.15.x (tested with 0.15.2)
- **Python**: 3.11+ (CPython)
- **Platforms**: Linux (x86_64, aarch64), macOS (x86_64, arm64), Windows (x64)

## Installation

```bash
pip install ziggy-pydust
```

Or with distribution extras for building wheels:

```bash
pip install ziggy-pydust[dist]
```

## Quick Start

### 1. Create a New Project

```bash
# Create project using cookiecutter template
pydust init -n myproject --no-interactive
cd myproject

# Or create in a new directory
pydust new myproject
cd myproject
```

This creates a complete project structure with:
- Zig source files in `src/`
- Python package structure
- GitHub Actions CI/CD workflows
- VSCode debug configuration
- Test suite with pytest

### 2. Develop

```bash
# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Or use pydust develop command
pydust develop

# Run tests
pytest
```

### 3. Watch Mode (Hot Reload)

```bash
# Watch for changes and auto-rebuild
pydust watch

# Watch and run tests on each change
pydust watch --test

# Watch and run pytest
pydust watch --pytest
```

### 4. Build Distribution Wheels

```bash
# Build for current platform
pydust build-wheel

# Build for all platforms (requires cross-compilation setup)
pydust build-wheel --all-platforms

# Build for specific platform
pydust build-wheel --platform linux-x86_64
```

### 5. Deploy to PyPI

```bash
# Validate wheels
pydust check --strict

# Upload to PyPI
pydust deploy --username __token__ --password $PYPI_TOKEN
```

## CLI Commands

### Project Management
- `pydust init` - Initialize project in current directory (interactive)
- `pydust new <name>` - Create new project in a new directory
- `pydust develop` - Build and install in development mode

### C/C++ Dependencies
- `pydust add <url>` - Add C/C++ library with auto-generated bindings
- `pydust list` - List all dependencies
- `pydust remove <name>` - Remove a dependency

### Building & Testing
- `pydust watch` - Watch files and auto-rebuild
- `pydust build-wheel` - Build distribution wheels
- `pytest` - Run tests (via pytest plugin)

### Distribution
- `pydust check` - Validate built wheels
- `pydust deploy` - Upload to PyPI

Run `pydust <command> --help` for detailed options.

## C/C++ Library Integration

Easily integrate C/C++ libraries into your extensions:

```bash
# Add a library from GitHub
pydust add https://github.com/nothings/stb

# Pydust automatically:
# - Clones the repository
# - Generates Zig bindings
# - Creates build configuration
```

Then use it in your Zig code:

```zig
const stb = @import("../bindings/stb.zig");

pub fn loadImage(args: struct { path: []const u8 }) !Image {
    // Use stb_image directly
    const data = stb.stbi_load(args.path.ptr, &width, &height, &channels, 4);
    // ...
}
```

See [Dependency Management Guide](docs/DEPENDENCY_MANAGEMENT.md) for details.

## Features

### Type System

Pydust provides comprehensive Python type support:

**Primitives**: int, float, bool, str, bytes, None
**Collections**: list, tuple, dict, set, frozenset, range
**Advanced**: datetime, timedelta, date, time, Decimal, Path, UUID, complex
**Containers**: defaultdict, Counter, deque, Fraction, Enum
**Special**: generator, async generator, bytearray

**Coverage**: 31/43 Python stdlib types (72.1%)

### Automatic Marshalling

Function arguments and return values are automatically converted:

```zig
pub fn processData(args: struct {
    values: []const i64,      // Accepts Python list of ints
    threshold: f64,            // Accepts Python float
    name: []const u8,          // Accepts Python str
    optional: ?bool,           // Accepts None or bool
}) !struct {                   // Returns Python dict
    result: i64,
    success: bool,
} {
    // Your Zig code here
}
```

### Classes and Methods

```zig
pub const MyClass = struct {
    value: i64,

    pub fn __init__(args: struct { initial: i64 }) MyClass {
        return .{ .value = args.initial };
    }

    pub fn increment(self: *MyClass) void {
        self.value += 1;
    }

    pub fn getValue(self: *const MyClass) i64 {
        return self.value;
    }
};
```

### Error Handling

Zig errors are automatically converted to Python exceptions:

```zig
pub fn divide(args: struct { a: f64, b: f64 }) !f64 {
    if (args.b == 0) return error.DivisionByZero;
    return args.a / args.b;
}
```

```python
try:
    result = mymodule.divide(10, 0)
except RuntimeError as e:
    print(e)  # "DivisionByZero"
```

## Cross-Platform Distribution

Pydust includes built-in support for building and distributing wheels:

### Build Wheels for Multiple Platforms

```bash
# Build for all platforms
pydust build-wheel --all-platforms

# Platforms supported:
# - Linux: x86_64, aarch64 (manylinux_2_17)
# - macOS: x86_64 (10.9+), arm64 (11.0+)
# - Windows: x64
```

### Automated GitHub Actions

The generated project includes workflows that automatically:
- Build wheels for all platforms on tag push
- Run tests on each platform
- Publish to PyPI (when configured)
- Create GitHub releases

```bash
git tag v0.1.0
git push origin v0.1.0
# Wheels are automatically built and published!
```

See [Distribution Guide](docs/distribution.md) for details.

## Project Structure

Generated projects follow this structure:

```
myproject/
├── .github/workflows/     # CI/CD automation
│   ├── ci.yml            # Testing workflow
│   └── publish.yml       # Release workflow
├── .vscode/              # VSCode configuration
│   ├── extensions.json   # Recommended extensions
│   └── launch.json       # Debug configuration
├── src/                  # Zig source code
│   └── myproject.zig
├── myproject/            # Python package
│   ├── __init__.py
│   └── _lib.pyi         # Type stubs for IDE
├── test/                 # Test suite
│   ├── __init__.py
│   └── test_myproject.py
├── pyproject.toml        # Project configuration
├── build.py              # Build script
├── README.md
└── LICENSE
```

## Testing

Pydust includes a pytest plugin that discovers and runs Zig tests:

```zig
test "fibonacci correctness" {
    const std = @import("std");
    try std.testing.expectEqual(@as(u64, 55), fibonacci(.{ .n = 10 }));
}
```

```bash
pytest  # Runs both Python and Zig tests
```

## Documentation

- **[Getting Started Guide](https://pydust.fulcrum.so/latest/getting_started)** - Comprehensive tutorial
- **[API Reference](https://pydust.fulcrum.so/latest/zig)** - Complete Zig API documentation
- **[CLI Reference](docs/CLI.md)** - Detailed command documentation
- **[Distribution Guide](docs/distribution.md)** - Building and publishing packages
- **[Dependency Management](docs/DEPENDENCY_MANAGEMENT.md)** - Working with C/C++ libraries
- **[Roadmap](docs/ROADMAP.md)** - Planned features and improvements

## Performance

Zig extensions built with Pydust are typically:
- **10-100x faster** than pure Python for compute-intensive tasks
- **2-5x faster** than NumPy for certain operations
- **Comparable to C extensions** with better safety guarantees

## Contributing

We welcome contributions! Areas where you can help:

- 🐛 **Bug Reports** - File issues with detailed reproduction steps
- 💡 **Feature Requests** - Suggest improvements or new features
- 📝 **Documentation** - Improve guides, fix typos, add examples
- 🔧 **Code Contributions** - Fix bugs, implement features
- 💬 **Community Support** - Help others in discussions and issues
- 📢 **Content Creation** - Write blog posts, tutorials, or demos

See our [contributing guidelines](https://github.com/fulcrum-so/ziggy-pydust/blob/develop/CONTRIBUTING.md) for more details.

## Development Notes

For developers working on Pydust itself, see [docs/development/](docs/development/) for:
- Implementation summaries
- Architecture decisions
- Security improvements
- Test guides

## License

Pydust is released under the [Apache-2.0 License](LICENSE).

## Acknowledgments

- Built on top of the excellent [Zig](https://ziglang.org/) programming language
- Inspired by [PyO3](https://pyo3.rs/) for Rust
- Uses Python's [stable ABI](https://docs.python.org/3/c-api/stable.html) for forward compatibility

---

**Star ⭐ this repo if you find it useful!**
