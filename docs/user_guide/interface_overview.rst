Interface Overview
==================

TomoGUI features a comprehensive interface divided into control panels and visualization areas.

Main Window Layout
------------------

The application window consists of three main areas:

.. code-block:: text

   ┌─────────────────────────────────────────────────────────┐
   │ TomoGUI                                            🌙/☀  │
   ├──────────────────┬──────────────────────────────────────┤
   │                  │                                      │
   │  Control Panel   │     Visualization Area              │
   │  (Left)          │     (Right)                         │
   │                  │                                      │
   │  - Data Folder   │  - Matplotlib Canvas                │
   │  - File Select   │  - Navigation Toolbar               │
   │  - Tabs          │  - Colormap Controls                │
   │    • Main        │  - Contrast Controls                │
   │    • Recon       │  - Slice Slider                     │
   │    • Hardening   │  - TomoLog Panel                    │
   │    • Phase       │                                      │
   │    • Rings       │                                      │
   │    • Geometry    │                                      │
   │    • Data        │                                      │
   │    • Performance │                                      │
   │    • Config      │                                      │
   │    • Batch       │                                      │
   │                  │                                      │
   │  - Log Output    │                                      │
   │                  │                                      │
   └──────────────────┴──────────────────────────────────────┘

Left Panel
----------

Data Selection
~~~~~~~~~~~~~~

At the top of the left panel:

**Data Folder**
   - Text field showing current data directory
   - Browse button to select new folder
   - Stores path for subsequent file operations

**Projection File**
   - Dropdown list of .h5 files in data folder
   - Sorted by modification time (newest first)
   - Refresh button to reload file list

Tab System
~~~~~~~~~~

The left panel contains a tab widget with multiple configuration sections:

Main Tab
^^^^^^^^

Quick access to basic reconstruction:

- **Try Reconstruction**
   - Recon method (recon/recon_steps)
   - CUDA device selection
   - COR method (auto/manual)
   - COR value input
   - Try button
   - View Try button
   - Batch Try button

- **Full Reconstruction**
   - Same controls as Try
   - Full button
   - View Full button
   - Batch Full button

- **Preset Buttons**
   - BeamHarden: Configure for absorption
   - Phase: Configure for phase contrast
   - Laminography: Configure for laminography

- **Parameter Management**
   - Save params button
   - Load params button
   - Reset params button

Reconstruction Tab
^^^^^^^^^^^^^^^^^^

Fine-tune reconstruction algorithms:

- Algorithm selection
- Iteration parameters
- Regularization settings
- Binning options

See :doc:`../features/reconstruction_params` for details.

Hardening Tab
^^^^^^^^^^^^^

Beam hardening correction:

- Polynomial coefficients
- Correction strength
- Material-specific presets

Phase Tab
^^^^^^^^^

Phase retrieval parameters:

- Phase method selection
- Propagation distance
- Energy settings
- Delta/beta ratios

Rings Tab
^^^^^^^^^

Ring artifact removal:

- Ring removal methods
- Filter parameters
- Strength controls

Geometry Tab
^^^^^^^^^^^^

Geometric corrections:

- Rotation axis offset
- Sample position
- Detector tilt
- Coordinate transformations

Data Tab
^^^^^^^^

Data preprocessing:

- Flat/dark field correction
- Data normalization
- ROI selection
- Projection filtering

Performance Tab
^^^^^^^^^^^^^^^

Performance tuning:

- Memory management
- GPU utilization
- Batch size
- Threading options

Advanced Config Tab
^^^^^^^^^^^^^^^^^^^

Direct configuration file editing:

- Try reconstruction config editor
- Full reconstruction config editor
- Load/Save config buttons
- Enable config checkbox

Batch Processing Tab
^^^^^^^^^^^^^^^^^^^^

Comprehensive batch operations:

- File list with COR values
- Machine selection
- GPU configuration
- Parallel processing
- See :doc:`../features/batch_tab` for full details

Log Output
~~~~~~~~~~

Bottom section of left panel:

- Scrollable text area
- Color-coded messages
- Command history
- Progress indicators
- Clear/Save buttons

Right Panel
-----------

Visualization Area
~~~~~~~~~~~~~~~~~~

Main display for reconstruction results:

**Matplotlib Canvas**
   - Interactive image display
   - Zoom, pan capabilities
   - Crosshair cursor
   - Coordinate display

**Navigation Toolbar**
   - Home: Reset view
   - Back/Forward: View history
   - Pan: Click and drag
   - Zoom: Rectangle selection
   - Configure subplots
   - Save figure

Toolbar Controls
~~~~~~~~~~~~~~~~

Below the matplotlib toolbar:

**Coordinate Label**
   - Shows cursor position
   - Displays pixel value
   - Format: (x, y) = value

**Colormap Selector**
   - Dropdown with standard colormaps
   - gray, viridis, plasma, inferno, magma, cividis
   - Changes apply immediately

**Image Control Buttons**
   - Draw: Enable ROI selection box
   - Auto: Automatic contrast adjustment
   - Reset: Reset contrast to original

**Min/Max Inputs**
   - Manual contrast control
   - Enter numeric values
   - Press Enter to apply

**Theme Toggle**
   - 🌙 Moon: Switch to dark theme
   - ☀ Sun: Switch to bright theme

Slice Slider
~~~~~~~~~~~~

Horizontal slider below canvas:

- Navigate through 3D reconstruction slices
- Shows current slice index
- Click or drag to change slice
- Keyboard arrows supported

TomoLog Panel
~~~~~~~~~~~~~

Integration with TomoLog service:

- Beamline selection
- Cloud configuration
- URL input
- Coordinate inputs (x, y, z)
- Scan number
- Visualization controls
- Apply button
- Help button

Status Indicators
-----------------

Throughout the interface, status is indicated by:

Icons
~~~~~

- 🚀 Process started
- ✅ Success (green)
- ❌ Failure (red)
- ⚠️ Warning (orange)
- 📍 Information (blue)
- 🖥️ Remote execution
- 🏁 Batch complete

Colors
~~~~~~

Text colors in log output:

- **Green**: Success messages
- **Red**: Error messages
- **Orange**: Warnings
- **Blue**: Information
- **Black/White**: Normal text (theme-dependent)

Interactive Elements
--------------------

Mouse Operations
~~~~~~~~~~~~~~~~

**Canvas**:
   - Left click: Select point
   - Click + Drag: Pan (when pan tool active)
   - Click + Drag: Zoom box (when zoom tool active)
   - Scroll wheel: Zoom in/out

**Slider**:
   - Click: Jump to slice
   - Drag: Continuous navigation

**Table (Batch tab)**:
   - Click checkbox: Select/deselect file
   - Click button: Perform action
   - Type in COR field: Edit value

Keyboard Shortcuts
~~~~~~~~~~~~~~~~~~

Currently limited keyboard support. Mouse is primary input method.

**Planned shortcuts**:
   - Ctrl+T: Toggle theme
   - Ctrl+R: Refresh file list
   - Ctrl+S: Save current view
   - Arrow keys: Navigate slices

Workflow Integration
--------------------

Typical workflow through the interface:

1. **Setup** (Top of left panel)
   - Select data folder
   - Choose projection file

2. **Configure** (Left panel tabs)
   - Set reconstruction parameters
   - Choose appropriate tab for settings

3. **Execute** (Main tab buttons)
   - Run try reconstruction
   - View results
   - Adjust parameters
   - Run full reconstruction

4. **Analyze** (Right panel)
   - Visualize results
   - Adjust contrast
   - Navigate slices
   - Save figures

5. **Batch** (Batch tab)
   - Process multiple files
   - Manage COR values
   - Monitor progress

Customization
-------------

Window Size
~~~~~~~~~~~

Default: 1650 x 950 pixels

Resize by dragging window edges. Layout adapts to window size.

Panel Proportions
~~~~~~~~~~~~~~~~~

Left and right panels have 4:4 ratio. Currently fixed, but may become adjustable in future versions.

Themes
~~~~~~

Choose between bright and dark themes. See :doc:`themes` for details.

Accessibility
-------------

The interface is designed with accessibility in mind:

- High contrast ratios
- Readable font sizes
- Clear visual indicators
- Consistent layout
- Tooltips on hover

For users with visual impairments:
   - Use dark theme for reduced glare
   - Adjust screen magnification as needed
   - Status uses both color and symbols

Getting Help
------------

Interface elements provide help through:

- **Tooltips**: Hover over buttons and controls
- **Help buttons**: In-app documentation links
- **Log messages**: Detailed operation feedback
- **This documentation**: Comprehensive guides

For specific features, see:
   - :doc:`getting_started` - Basic operations
   - :doc:`reconstruction` - Reconstruction workflow
   - :doc:`batch_processing` - Batch operations
   - :doc:`../features/batch_tab` - Batch tab details
