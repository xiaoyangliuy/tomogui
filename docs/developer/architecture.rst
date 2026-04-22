Architecture
============

High-level view of TomoGUI internals for developers and contributors.

Packages
--------

``tomogui`` (``src/tomogui/``)
   Main GUI package. The ``TomoGUI`` class in ``gui.py`` is the PyQt5
   ``QWidget`` that assembles every tab.

``tomogui._infer_worker``
   Standalone CLI worker used by Batch AI Reco Phase B. Takes a
   data folder, model path, and list of files; runs DINOv2 inference on
   the try_center TIFFs of each file and writes
   ``center_of_rotation.txt``.

``tomogui._tomocor_infer``
   Bundled copy of the tomocor inference code (``inference.py``,
   ``model_archs.py``, ``_utils.py``) so TomoGUI can run AI Reco without
   requiring ``tomocor`` to be installed separately.

Layering
--------

::

   ┌──────────────────────────────────────────┐
   │          PyQt5 GUI (gui.py)              │
   │  Main / Batch / HDF5 Viewer / Advanced   │
   └──────────────────────────────────────────┘
                   │
                   ▼
   ┌──────────────────────────────────────────┐
   │    Subprocess dispatch (local / SSH)     │
   │   TomoCuPy • _infer_worker • tomolog     │
   └──────────────────────────────────────────┘
                   │
                   ▼
   ┌──────────────────────────────────────────┐
   │  Torch / DINOv2 • CUDA • HDF5 / TIFF IO  │
   └──────────────────────────────────────────┘

Key subsystems
--------------

Batch queue
~~~~~~~~~~~

A multi-GPU job queue dispatches TomoCuPy subprocesses with
``CUDA_VISIBLE_DEVICES`` set per worker. Each queued job carries the per-row
COR (fallback to top-bar), parameters, and output paths. Polling uses
``processEvents`` rather than ``QThread`` blocking waits to keep the GUI
responsive.

AI Reco 3-phase pipeline
~~~~~~~~~~~~~~~~~~~~~~~~

``_batch_run_ai_selected`` orchestrates:

- **Phase A** — reuse the Batch queue for ``try``.
- **Phase B** — split files into *N* chunks; spawn one
  ``_infer_worker`` subprocess per GPU via ``subprocess.Popen``; drain
  each worker's stdout in a Python thread into a shared ``queue.Queue``;
  the main Qt loop consumes events from that queue, parses
  ``[infer-worker] OK|SKIP|FAIL`` lines, and updates per-row status and
  the progress bar.
- **Phase C** — reuse the Batch queue for ``full``.

Fix COR Outliers
~~~~~~~~~~~~~~~~

Pure-Python routine in ``gui.py`` (``_fix_cor_outliers``):

- Group rows by filename series (``^(.*?)[._-]*(\d+)$``).
- Compute series median and MAD.
- Flag deviations greater than ``min(max_delta, max(10, 5·MAD))``.
- Prompt for confirmation and replace in-place.

Per-dataset parameter persistence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every reconstruction parameter tab writes its state to a JSON sidecar
next to the projection HDF5 file. Selecting the file reloads that
sidecar; ``Apply parameters to selected`` copies the sidecar to other
rows.

See :doc:`api_reference` for a generated API overview (or use
``pydoc tomogui`` from a shell).
