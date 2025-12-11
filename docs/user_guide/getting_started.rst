Getting Started
===============

Launching TomoGUI
-----------------

Start TomoGUI from the command line:

.. code-block:: bash

   tomogui

The main window will open with a clean interface ready for use.

Basic Workflow
--------------

1. **Select Data Folder**

   Click "Browse Data Folder" and navigate to your tomography data directory.

2. **Select Projection File**

   From the "Projection File" dropdown, select your HDF5 (.h5) file containing projection data.

3. **Configure Reconstruction**

   - Set the reconstruction method (recon or recon_steps)
   - Choose COR method (auto or manual)
   - If manual, enter the center of rotation value
   - Select GPU device

4. **Try Reconstruction**

   Click "Try" to perform a quick reconstruction test on a subset of data.

5. **View Results**

   Click "View Try" to visualize the reconstruction result.

6. **Full Reconstruction**

   Once satisfied with the try result, click "Full" for complete reconstruction.

Your First Reconstruction
--------------------------

Step-by-Step Example
~~~~~~~~~~~~~~~~~~~~

Let's reconstruct a sample dataset:

.. code-block:: text

   1. Click "Browse Data Folder" → Select: /data/tomo/scan_001/
   2. Projection File dropdown → Select: scan_001.h5
   3. Reconstruction method → Select: recon
   4. COR method → Select: manual
   5. COR value → Enter: 1024.5
   6. GPU → Select: 0
   7. Click "Try" button
   8. Wait for completion (check log output)
   9. Click "View Try" to see result
   10. If good, click "Full" for complete reconstruction

Understanding the Interface
----------------------------

Main Layout
~~~~~~~~~~~

The TomoGUI interface is divided into two main panels:

**Left Panel** - Control panel with tabs:
   - Main: Try and Full reconstruction controls
   - Reconstruction: Parameters for reconstruction algorithms
   - Hardening: Beam hardening correction settings
   - Phase: Phase retrieval parameters
   - Rings: Ring artifact removal
   - Geometry: Geometric corrections
   - Data: Data preprocessing options
   - Performance: Performance tuning
   - Advanced Config: Configuration file editing
   - Batch Processing: Multi-file batch operations

**Right Panel** - Visualization:
   - Image display with matplotlib toolbar
   - Colormap controls
   - Contrast adjustment (Auto, Reset, Min/Max)
   - Slice navigation slider
   - TomoLog integration panel

Log Output
~~~~~~~~~~

The log output area shows:
   - Command execution status
   - Success/failure messages
   - Processing progress
   - Error information

Status indicators:
   - 🚀 Job started
   - ✅ Success (green)
   - ❌ Failure (red)
   - ⚠️  Warning (orange)

Next Steps
----------

- Explore :doc:`interface_overview` for detailed UI components
- Learn about :doc:`reconstruction` parameters
- Try :doc:`batch_processing` for multiple datasets
- Customize with :doc:`themes`
