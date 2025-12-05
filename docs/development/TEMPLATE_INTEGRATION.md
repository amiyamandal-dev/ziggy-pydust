# Ziggy-Pydust-Template Integration Architecture

## Overview

The `ziggy-pydust-template` directory is a **cookiecutter template** that lives inside the main ziggy-pydust repository and is used by the `pydust init` command to generate new projects.

## Directory Structure

```
ziggy-pydust/                          # Main repository root
├── pydust/                             # Main pydust package
│   ├── __main__.py                     # CLI entry point
│   ├── init.py                         # Init logic (uses template)
│   ├── deploy.py                       # Deploy logic
│   └── ...
├── ziggy-pydust-template/             # Cookiecutter template directory
│   ├── cookiecutter.json               # Template configuration
│   ├── hooks/                          # Post-generation hooks
│   │   └── post_gen_project.py        # Runs after project creation
│   └── {{cookiecutter.project_slug}}/ # Template files (with variables)
│       ├── .github/workflows/          # CI/CD templates
│       ├── .vscode/                    # VSCode config
│       ├── src/
│       │   └── {{cookiecutter.zig_file_name}}.zig
│       ├── test/
│       ├── {{cookiecutter.package_name}}/
│       ├── pyproject.toml              # Poetry config template
│       ├── build.py
│       └── README.md
└── test/
    └── test_init_deploy.py             # Tests template integration
```

## Integration Flow

```
User runs command:
  $ pydust init -n myproject

       ↓

CLI (__main__.py)
  - Parses arguments
  - Calls init_project()

       ↓

init.py::init_project()
  - Checks if cookiecutter available
  - If yes: calls init_project_cookiecutter()
  - If no: falls back to legacy init_project()

       ↓

init.py::init_project_cookiecutter()
  1. Finds template directory:
     pydust_root = Path(__file__).parent.parent
     template_path = pydust_root / "ziggy-pydust-template"

  2. Prepares context variables:
     extra_context = {
       "project_name": "myproject",
       "author_name": "User Name",
       "author_email": "user@example.com",
       ...
     }

  3. Calls cookiecutter:
     cookiecutter(
       str(template_path),
       no_input=not interactive,
       extra_context=extra_context
     )

       ↓

Cookiecutter processes template:
  1. Reads cookiecutter.json
  2. Prompts user (if interactive)
  3. Applies variable substitutions
  4. Generates project files
  5. Runs post_gen_project.py hook

       ↓

New project created:
  myproject/
  ├── .github/workflows/
  ├── src/myproject.zig
  ├── myproject/
  ├── test/
  ├── pyproject.toml
  └── README.md
```

## Key Integration Points

### 1. Template Location Discovery (init.py:75-82)

```python
# Find the template directory
pydust_root = Path(__file__).parent.parent
template_path = pydust_root / "ziggy-pydust-template"

if not template_path.exists():
    logger.error(f"Template not found at {template_path}")
    print(f"❌ Error: Template directory not found at {template_path}")
    print("\nPlease ensure ziggy-pydust-template is in the repository root.")
    sys.exit(1)
```

**How it works:**
- Gets pydust package directory: `/Volumes/ssd/ziggy-pydust/pydust/`
- Goes up one level: `/Volumes/ssd/ziggy-pydust/`
- Appends template dir: `/Volumes/ssd/ziggy-pydust/ziggy-pydust-template/`

### 2. Variable Substitution (init.py:85-109)

```python
# Prepare cookiecutter context
extra_context = {}

if package_name:
    extra_context["project_name"] = package_name.replace("_", " ").title()
else:
    extra_context["project_name"] = path.name.replace("-", " ").replace("_", " ").title()

if author_name:
    extra_context["author_name"] = author_name

if author_email:
    extra_context["author_email"] = author_email
```

**Variable Flow:**
```
User Input          → Cookiecutter Variable      → Template Output
---------             -------------------          ---------------
"my_project"        → project_name: "My Project" → name = "my-project"
                    → project_slug: "my-project"  → dir: my-project/
                    → package_name: "my_project"  → import my_project
                    → zig_file_name: "my_project" → my_project.zig
```

### 3. Cookiecutter Execution (init.py:111-130)

```python
try:
    # Run cookiecutter
    output_dir = path.parent if path != Path.cwd() else None

    cookiecutter(
        str(template_path),
        output_dir=str(output_dir) if output_dir else None,
        no_input=not use_interactive,
        extra_context=extra_context,
    )

    print("\n✅ Project initialized successfully using cookiecutter template!")
    logger.info("Project initialized successfully with cookiecutter")

except Exception as e:
    logger.error(f"Failed to initialize project with cookiecutter: {e}")
    print(f"❌ Error: Failed to initialize project: {e}")
    print("\nFalling back to legacy init method...")
    # Fall back to legacy method
    init_project(path, package_name, None, force=False)
```

## Template Variables

### Defined in `cookiecutter.json`:

| Variable | Example Value | Usage |
|----------|--------------|-------|
| `project_name` | "My Zig Python Extension" | Human-readable name |
| `project_slug` | "my-zig-python-extension" | Directory name, PyPI name |
| `package_name` | "my_zig_python_extension" | Python import name |
| `zig_file_name` | "my_zig_python_extension" | Zig source file name |
| `module_name` | "_lib" | Compiled module name |
| `description` | "A Python extension..." | Project description |
| `author_name` | "Your Name" | Author name |
| `author_email` | "you@example.com" | Author email |
| `version` | "0.1.0" | Initial version |
| `python_version` | "3.11" | Minimum Python version |

### Variable Substitution in Templates:

**In file names:**
```
{{cookiecutter.project_slug}}/          → my-project/
src/{{cookiecutter.zig_file_name}}.zig  → src/my_project.zig
{{cookiecutter.package_name}}/          → my_project/
```

**In file content:**
```toml
# pyproject.toml template
name = "{{ cookiecutter.project_slug }}"
authors = ["{{ cookiecutter.author_name }} <{{ cookiecutter.author_email }}>"]
packages = [{ include = "{{ cookiecutter.package_name }}" }]
```

## Post-Generation Hook

The `hooks/post_gen_project.py` script runs automatically after project generation:

```python
def main():
    project_dir = Path.cwd()

    # Initialize git repository
    if not (project_dir / ".git").exists():
        run_command("git init", "Initializing git repository")
        run_command("git add .", "Adding files to git")
        run_command(
            'git commit -m "Initial commit from ziggy-pydust-template"',
            "Creating initial commit"
        )

    # Detect available tools (uv, Poetry, pip)
    has_uv = check_uv_installed()
    has_poetry = shutil.which("poetry") is not None

    # Print next steps based on available tools
    print("\nNext steps:")
    if has_uv:
        print("  uv venv")
        print("  source .venv/bin/activate")
        print("  uv pip install -e .")
    # ... etc
```

## Dual Template System

The integration supports **both** cookiecutter and legacy templates:

### Cookiecutter Template (New)
- **Location:** `ziggy-pydust-template/`
- **Trigger:** `pydust init` (default if cookiecutter installed)
- **Features:** Full CI/CD, VSCode config, type stubs, examples
- **Usage:** `pydust init -n myproject`

### Legacy Template (Built-in)
- **Location:** `pydust/init.py` (TEMPLATE_* constants)
- **Trigger:** `pydust init --legacy` OR cookiecutter unavailable
- **Features:** Basic project structure
- **Usage:** `pydust init --legacy -n myproject`

## Benefits of This Integration

1. **Self-Contained:** Template ships with pydust, no external dependencies
2. **Version Locked:** Template version matches pydust version
3. **Offline Support:** Works without internet connection
4. **Backward Compatible:** Legacy templates still available
5. **Easy Testing:** Template tests run with main test suite
6. **Single Package:** Users get template when installing pydust

## Usage Examples

### Using Cookiecutter Template (Interactive)
```bash
pydust init
# Prompts for project name, author, etc.
```

### Using Cookiecutter Template (Non-Interactive)
```bash
pydust init -n myproject \
  --description "My awesome project" \
  --email "me@example.com" \
  --no-interactive
```

### Using Legacy Template
```bash
pydust init --legacy -n myproject -a "Your Name <you@example.com>"
```

### Create New Project in Custom Location
```bash
pydust new myproject -p /path/to/parent
# Creates /path/to/parent/myproject/
```

## Testing the Integration

Tests verify the integration in `test/test_init_deploy.py`:

```python
def test_cookiecutter_template_exists(self):
    """Verify template directory exists"""
    from pydust import init
    pydust_root = Path(init.__file__).parent.parent
    template_path = pydust_root / "ziggy-pydust-template"

    assert template_path.exists()
    assert (template_path / "cookiecutter.json").exists()

def test_init_with_cookiecutter(self):
    """Test project generation"""
    result = subprocess.run([
        sys.executable, "-m", "pydust", "init",
        "-n", "test_package",
        "--no-interactive",
    ], ...)

    assert (project_path / "pyproject.toml").exists()
```

## Package Distribution

When pydust is packaged, the template is included:

```toml
# pyproject.toml
[tool.poetry]
packages = [
    { include = "pydust" },
]
include = [
    "ziggy-pydust-template/**/*",
]
```

This ensures users get the template when they install pydust:
```bash
pip install ziggy-pydust
# Template automatically available at:
# <site-packages>/ziggy-pydust-template/
```

## Summary

The ziggy-pydust-template is integrated as:
- **A subdirectory** of the main repository
- **Discovered dynamically** at runtime by `init.py`
- **Processed by cookiecutter** to generate new projects
- **Distributed with pydust** as package data
- **Tested alongside** main codebase
- **Backward compatible** with legacy templates

This architecture provides a seamless experience where users run `pydust init` and automatically get a fully-featured project with CI/CD, examples, and best practices.
