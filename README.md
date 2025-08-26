# TomoGUI

GUI interface for TomoCuPy tomographic reconstruction.

## Installation

### Prerequisites

Install the required backend packages:
- [TomoCuPy](https://tomocupy.readthedocs.io/en/latest/) - Tomographic reconstruction
- [Tomolog](https://tomologcli.readthedocs.io/en/latest/) - Data logging and sharing

### Setup Environment

```bash
conda env create -f environment.yml
conda activate tomogui
```

## Usage

```bash
python -m tomogui
```

## Requirements

- Python 3.8-3.12
- PyQt5
- matplotlib
- numpy
- Pillow
- TomoCuPy (external)
- Tomolog (external)