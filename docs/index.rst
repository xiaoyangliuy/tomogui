TomoGUI Documentation
=====================

**TomoGUI** is a comprehensive graphical user interface for tomographic reconstruction using TomoCuPy and TomoLog.

.. image:: https://img.shields.io/badge/python-3.8%2B-blue
   :alt: Python Version

.. image:: https://img.shields.io/badge/license-MIT-green
   :alt: License

Overview
--------

TomoGUI provides an intuitive interface for:

- **Interactive reconstruction** with try and full modes
- **Batch processing** with parallel GPU execution
- **Machine learning integration** with TomoLog
- **Multi-machine support** via SSH
- **Real-time visualization** of reconstruction results
- **Bright/Dark theme** support

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install -e .

Usage
~~~~~

Launch TomoGUI:

.. code-block:: bash

   tomogui

Or use as a Python module:

.. code-block:: python

   from tomogui import TomoGUI
   from PyQt5.QtWidgets import QApplication
   import sys

   app = QApplication(sys.argv)
   gui = TomoGUI()
   gui.show()
   sys.exit(app.exec_())

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/installation
   user_guide/getting_started
   user_guide/interface_overview
   user_guide/reconstruction
   user_guide/batch_processing
   user_guide/themes

.. toctree::
   :maxdepth: 2
   :caption: Features

   features/main_tab
   features/reconstruction_params
   features/batch_tab
   features/advanced_config
   features/tomolog_integration

.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics

   advanced/ssh_setup
   advanced/gpu_management
   advanced/cor_management
   advanced/troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   developer/architecture
   developer/api_reference
   developer/contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
