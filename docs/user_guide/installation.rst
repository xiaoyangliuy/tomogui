Installation
============

Requirements
------------

Python Version
~~~~~~~~~~~~~~

TomoGUI requires Python 3.8 or higher, but must be less than Python 3.13.

Dependencies
~~~~~~~~~~~~

TomoGUI requires the following Python packages:

- **PyQt5** >= 5.15.0 - GUI framework
- **numpy** >= 1.20.0 - Numerical computing
- **matplotlib** >= 3.5.0 - Plotting and visualization
- **Pillow** >= 8.0.0 - Image processing

External Tools
~~~~~~~~~~~~~~

For full functionality, you also need:

- **TomoCuPy** - GPU-accelerated tomographic reconstruction
- **TomoLog** - Machine learning for tomography
- **CUDA** - For GPU acceleration

Installation Methods
--------------------

From Source (Development)
~~~~~~~~~~~~~~~~~~~~~~~~~

Clone the repository and install in editable mode:

.. code-block:: bash

   git clone <repository-url>
   cd tomogui
   pip install -e .

Using Conda Environment
~~~~~~~~~~~~~~~~~~~~~~~

Create and activate the conda environment:

.. code-block:: bash

   conda env create -f environment.yml
   conda activate tomocupy

Then install TomoGUI:

.. code-block:: bash

   pip install -e .

Verifying Installation
----------------------

Test the installation by running:

.. code-block:: bash

   tomogui --version

Or launch the GUI:

.. code-block:: bash

   tomogui

If the GUI window opens successfully, the installation is complete.

Troubleshooting
---------------

Qt Platform Plugin Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you see errors about Qt platform plugins, try:

.. code-block:: bash

   export QT_QPA_PLATFORM_PLUGIN_PATH=""

PyQt5 Import Errors
~~~~~~~~~~~~~~~~~~~

If PyQt5 fails to import, reinstall it:

.. code-block:: bash

   pip uninstall PyQt5
   pip install PyQt5==5.15.9

CUDA Issues
~~~~~~~~~~~

Ensure CUDA is properly installed and accessible:

.. code-block:: bash

   nvidia-smi  # Should show GPU information

If CUDA is not found, install the appropriate version for your system.
