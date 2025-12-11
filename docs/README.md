# TomoGUI Documentation

This directory contains the documentation for TomoGUI built with Sphinx.

## Building the Documentation

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Build HTML Documentation

```bash
make html
```

The built documentation will be in `_build/html/index.html`.

### Build PDF Documentation

```bash
make latexpdf
```

Requires LaTeX installation.

### Clean Build

```bash
make clean
```

## Viewing Documentation Locally

After building, open in browser:

```bash
# Linux/Mac
open _build/html/index.html

# Or use Python's built-in server
cd _build/html
python -m http.server 8000
# Then visit http://localhost:8000
```

## Documentation Structure

```
docs/
├── index.rst                 # Main documentation index
├── conf.py                   # Sphinx configuration
├── user_guide/              # User guides
│   ├── installation.rst
│   ├── getting_started.rst
│   ├── interface_overview.rst
│   ├── reconstruction.rst
│   ├── batch_processing.rst
│   └── themes.rst
├── features/                # Feature documentation
│   ├── main_tab.rst
│   ├── reconstruction_params.rst
│   ├── batch_tab.rst
│   ├── advanced_config.rst
│   └── tomolog_integration.rst
├── advanced/                # Advanced topics
│   ├── ssh_setup.rst
│   ├── gpu_management.rst
│   ├── cor_management.rst
│   └── troubleshooting.rst
└── developer/               # Developer documentation
    ├── architecture.rst
    ├── api_reference.rst
    └── contributing.rst
```

## Contributing to Documentation

1. Edit `.rst` files using reStructuredText syntax
2. Run `make html` to preview changes
3. Check for warnings in build output
4. Submit pull request with documentation changes

## Publishing to Read the Docs

1. Create account on readthedocs.org
2. Import GitHub repository
3. Documentation builds automatically on push
4. Access at https://tomogui.readthedocs.io
