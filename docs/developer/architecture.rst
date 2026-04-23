Architecture
============

High-level view of TomoGUI internals for developers and contributors.

Packages
--------

``tomogui`` (``src/tomogui/``)
   Main GUI package. The ``TomoGUI`` class in ``gui.py`` is the PyQt5
   ``QWidget`` that assembles every tab.

``tomogui._infer_worker``
   Standalone CLI worker. Takes a data folder, model path, and **one
   file** per invocation (it also accepts a list of files, unused by
   the current GUI); runs DINOv2 inference on that file's try_center
   TIFFs and writes ``center_of_rotation.txt``.

``tomogui._tomocor_infer``
   Bundled copy of the tomocor inference code (``inference.py``,
   ``model_archs.py``, ``_utils.py``) so TomoGUI can run AI Reco
   without requiring ``tomocor`` separately.

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

Unified batch queue
~~~~~~~~~~~~~~~~~~~

``_run_batch_with_queue(files, recon_type, num_gpus, machine)`` is the
single entry point for all parallel batch dispatch. ``recon_type`` is
``'try'``, ``'full'``, or ``'infer'``; the only per-type variation is
inside ``_start_batch_job_async``, which builds the appropriate
subprocess command (``tomocupy …`` vs
``python -m tomogui._infer_worker …``). Polling uses
``QApplication.processEvents()`` rather than blocking ``QThread``
waits so the GUI stays responsive.

AI Reco pipeline
~~~~~~~~~~~~~~~~

``_batch_run_ai_selected`` orchestrates four phases, each a call to
``_run_batch_with_queue`` (Phase D is a sequential loop instead):

- **A** — ``try`` reconstructions.
- **B** — ``infer`` (one file per GPU slot). ``_on_infer_output`` parses
  ``[infer-worker] OK <path> => <cor>`` lines and updates the row's
  COR input live. On clean exit the completion handler in
  ``_run_batch_with_queue`` also reads ``center_of_rotation.txt`` as a
  fallback.
- **C** — ``full`` reconstructions on files whose Phase B produced a
  COR.
- **D** *(optional, gated by the ``batch_ai_upload_tomolog`` checkbox)*
  — sequential ``_run_tomolog_for_file`` calls for every file whose
  Full completed successfully.

Fix COR Outliers
~~~~~~~~~~~~~~~~

Pure-Python routine in ``gui.py`` (``_fix_cor_outliers``). Two passes
on one click:

1. Group selected rows by filename series
   (``^(.*?)[._-]*(\d+)$``). Within each series, compute median and
   MAD; flag deviations greater than
   ``min(max_delta, max(10, 5·MAD))``; replace flagged values with the
   average of the two nearest non-flagged neighbours by index.
2. Fill any still-empty selected rows with the mean of CORs in their
   series across the **whole table** (donor rows can be unchecked).

Per-dataset parameter persistence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every reconstruction parameter tab writes its state to a JSON sidecar
next to the projection HDF5 file. Selecting the file reloads that
sidecar; ``Apply parameters to selected`` copies the sidecar to other
rows.

See :doc:`api_reference` for a curated API overview.
