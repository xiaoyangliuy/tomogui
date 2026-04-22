Interface Overview
==================

TomoGUI is split into a left-hand control panel (parameters, tabs, log) and
a right-hand visualisation area (image, contrast, slice controls).

.. figure:: /_static/screenshots/main_window.png
   :alt: TomoGUI main window
   :align: center

   TomoGUI main window.

Main Window Layout
------------------

.. code-block:: text

   ┌─────────────────────────────────────────────────────────┐
   │ TomoGUI                                         🌙 / ☀   │
   ├──────────────────┬──────────────────────────────────────┤
   │                  │                                      │
   │  Control Panel   │     Visualisation Area              │
   │  (Left)          │     (Right)                         │
   │                  │                                      │
   │  Data Folder     │  Matplotlib canvas                  │
   │  Projection File │  Navigation toolbar                 │
   │                  │  Colormap, Contrast, Auto-5/95 %    │
   │  Tabs            │  Slice / COR slider                 │
   │   • Main         │  TomoLog panel                      │
   │   • Recon        │                                      │
   │   • Hardening    │                                      │
   │   • Phase        │                                      │
   │   • Rings        │                                      │
   │   • Geometry     │                                      │
   │   • Data         │                                      │
   │   • Performance  │                                      │
   │   • Advanced Cfg │                                      │
   │   • Batch        │                                      │
   │   • HDF5 Viewer  │                                      │
   │                  │                                      │
   │  Log Output      │                                      │
   │                  │                                      │
   └──────────────────┴──────────────────────────────────────┘

Top tab bar
-----------

.. figure:: /_static/screenshots/tab_bar.png
   :alt: Top tab bar
   :align: center

The tab bar switches between:

- **Main** — single-file workflow (Try, Full, AI Reco, TomoLog)
- **Batch** — multi-file workflow (checkboxes, series grouping, Fix COR
  Outliers, Batch AI Reco)
- **HDF5 Viewer** — inspect HDF5 structure / previews
- **Advanced Config** — remote hosts, number of GPUs, AI model path, etc.

Left Panel
----------

Data Selection
~~~~~~~~~~~~~~

At the top of the left panel:

**Data Folder**
   - Current data directory
   - *Browse Data Folder* button
   - Path is persisted between sessions

**Projection File**
   - Dropdown of ``.h5`` files in the folder, newest first
   - Refresh button reloads the list

**Sync Acquisition**
   - Automatically refreshes the dropdown as new files appear in the
     acquisition folder (useful during a live scan)

.. figure:: /_static/screenshots/main_tab_file_picker.png
   :alt: Data folder and file picker
   :align: center

Tab System
~~~~~~~~~~

Main Tab
^^^^^^^^

.. figure:: /_static/screenshots/main_tab_overview.png
   :alt: Main tab
   :align: center

Single-file workflow:

- **Try / Full** — reconstruction controls (see :doc:`reconstruction`)
- **AI Reco** — DINOv2 automatic COR (see :doc:`ai_reco`)
- **TomoLog** — PDF report generator with per-file auto-contrast
- **View Try / View Full** — quick access to the reconstructed output

Reconstruction Parameters Tabs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Per-category tabs below the Main tab expose every TomoCuPy flag:

- **Recon** — algorithm (``FBP``, ``gridrec``, ``LPREC``), binning,
  nsino-per-chunk, start / end slice, etc.
- **Hardening** — beam hardening correction
- **Phase** — phase retrieval (alpha, energy, distance, …)
- **Rings** — ring removal (*sigma*, *level*, algorithm)
- **Geometry** — rotation axis geometry
- **Data** — projection range, flat/dark correction
- **Performance** — nthreads, blocked_views, etc.

Settings are stored **per dataset** in a JSON sidecar so reloading a file
restores its last-used parameters.

Advanced Config Tab
^^^^^^^^^^^^^^^^^^^

.. figure:: /_static/screenshots/advanced_config_tab.png
   :alt: Advanced Config tab
   :align: center

Cross-cutting configuration:

- **Remote host** — SSH user@host for running reconstruction on a remote
  GPU node
- **Number of GPUs** — used by Batch AI Reco to split Phase B inference
- **AI model path** — absolute path to the ``.pth`` checkpoint
- **Extra flags** — free-form extra command-line flags appended to
  ``tomocupy`` invocations

Batch Tab
^^^^^^^^^

See :doc:`batch_processing` for the full batch workflow. Key controls:

.. figure:: /_static/screenshots/batch_tab_overview.png
   :alt: Batch tab
   :align: center

- file table with per-row checkbox, COR, status, and series tint
- **Batch Try**, **Batch Full**, **Batch AI Reco**
- **Fix COR Outliers** with *Max COR delta* (default 50 px)
- **Delete Selected** (with confirmation)
- Shift-click range selection

HDF5 Viewer Tab
^^^^^^^^^^^^^^^

.. figure:: /_static/screenshots/hdf5_viewer_overview.png
   :alt: HDF5 Viewer
   :align: center

Browse the HDF5 tree, view dataset metadata, and preview 2D slices without
leaving TomoGUI.

Right Panel
-----------

Image display
~~~~~~~~~~~~~

- matplotlib canvas with navigation toolbar (pan, zoom, save)
- colormap selector (gray, viridis, magma, …)
- **Contrast** — Min / Max inputs, *Auto* (5 – 95 % percentile), *Reset*
- **Slice / COR slider** — when viewing a try-center grid, the slider
  scrubs through candidate CORs; when viewing a Full reconstruction, the
  slider scrubs through slices.

The auto-contrast behaviour also applies to TomoLog when Min/Max are
blank.

Log Output
~~~~~~~~~~

Structured log with colour-coded statuses:

- ✓ success (green)
- ✗ failure (red)
- ⚠ warning (amber)
- 🚀 job start

During Batch AI Phase B, per-file lines such as
``[infer-worker] OK /data/.../sample_007.h5 => 1024.3`` stream live.
