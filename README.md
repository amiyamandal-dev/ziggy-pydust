# Ziggy Pydust

<p align="center">
  <a href="https://pydust.fulcrum.so">
    <img src="https://pydust.fulcrum.so/assets/ziggy-pydust.png" style="border-radius: 20px" />
  </a>
</p>
<p align="center">
    <em>A framework for writing and packaging native Python extension modules written in Zig.</em>
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

**API**: <a href="https://pydust.fulcrum.so/latest/zig" target="_blank">https://pydust.fulcrum.so/latest/zig</a>

**Source Code**: <a href="https://github.com/fulcrum-so/ziggy-pydust" target="_blank">https://github.com/fulcrum-so/ziggy-pydust</a>

**Template**: <a href="https://github.com/fulcrum-so/ziggy-pydust-template" target="_blank">https://github.com/fulcrum-so/ziggy-pydust-template</a>

---

Ziggy Pydust is a framework for writing and packaging native Python extension modules written in Zig.

- Package Python extension modules written in Zig.
- Pytest plugin to discover and run Zig tests.
- Comptime argument wrapping / unwrapping for interop with native Zig types.

```zig
const py = @import("pydust");

pub fn fibonacci(args: struct { n: u64 }) u64 {
    if (args.n < 2) return args.n;

    var sum: u64 = 0;
    var last: u64 = 0;
    var curr: u64 = 1;
    for (1..args.n) {
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

## Compatibility

Pydust supports:

- [Zig 0.14.0](https://ziglang.org/download/0.14.0/release-notes.html)
- [CPython >=3.11](https://docs.python.org/3.11/c-api/stable.html)

Please reach out if you're interested in helping us to expand compatibility.

## Getting Started

### Quick Start with CLI (Maturin-style)

Pydust now includes a CLI similar to Maturin for easy project setup and development:

```bash
# Install pydust
pip install ziggy-pydust

# Create a new project
pydust new my_extension
cd my_extension

# Build and install in development mode
pydust develop

# Run tests
pytest

# Build wheels for distribution
pydust build-wheel --all-platforms
```

### CLI Commands

- **`pydust new <name>`** - Create a new project with boilerplate
- **`pydust init`** - Initialize pydust in an existing directory
- **`pydust develop`** - Build and install in development mode (like `pip install -e .`)
- **`pydust build-wheel`** - Build distribution wheels
- **`pydust watch`** - Watch for changes and rebuild automatically

### Using the Template

Pydust docs can be found [here](https://pydust.fulcrum.so).
Zig documentation (beta) can be found [here](https://pydust.fulcrum.so/latest/zig).

There is also a [template repository](https://github.com/fulcrum-so/ziggy-pydust-template) including Poetry build, Pytest and publishing from Github Actions.

## Distribution & Cross-Compilation

Pydust includes built-in support for building and distributing wheels for multiple platforms:

### Build Wheels

```bash
# Build for current platform
python -m pydust.wheel

# Build for all platforms (Linux, macOS, Windows)
python -m pydust.wheel --all-platforms

# Build for specific platform
python -m pydust.wheel --platform linux-x86_64
```

### Supported Platforms

- **Linux**: x86_64, aarch64 (manylinux_2_17 compatible)
- **macOS**: x86_64 (10.9+), arm64 (11.0+)
- **Windows**: x64

### Automated Builds with GitHub Actions

The included GitHub Actions workflow automatically builds wheels for all platforms when you push a tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

This will:
- Build wheels for all platforms and Python versions (3.9-3.13)
- Test each wheel
- Publish to PyPI (if configured)
- Create a GitHub release

### Quick Start

1. **Build a wheel**: `python -m pydust.wheel`
2. **Test it**: `pip install dist/*.whl`
3. **Publish**: `twine upload dist/*`

For detailed instructions, see:
- [Quick Start Guide](docs/DISTRIBUTION_QUICKSTART.md)
- [Full Distribution Guide](docs/distribution.md)

## Contributing

We welcome contributions! Pydust is in its early stages so there is lots of low hanging
fruit when it comes to contributions.

- Assist other Pydust users with GitHub issues or discussions.
- Suggest or implement features, fix bugs, fix performance issues.
- Improve our documentation.
- Write articles or other content demonstrating how you have used Pydust.

## License

Pydust is released under the [Apache-2.0 license](https://opensource.org/licenses/APACHE-2.0).
