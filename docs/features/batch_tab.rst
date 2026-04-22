Batch Processing Tab
====================

The Batch tab runs reconstructions on many datasets in parallel, with
multi-GPU execution, AI Reco integration, COR outlier correction, and
remote-host support.

.. figure:: /_static/screenshots/batch_tab_overview.png
   :alt: Batch tab overview
   :align: center

Overview
--------

Features:

- file list with per-row checkbox, COR input, status, and series tint
- Shift-click range selection
- **Batch Try**, **Batch Full**, **Batch AI Reco** (3-phase pipeline)
- **Fix COR Outliers** with series grouping and configurable max delta
- **Delete Selected** with confirmation dialog
- per-file streaming status during AI Reco Phase B
- progress bar that reflects true completion for all three phases
- remote SSH execution with multi-GPU job queue

File table
----------

The table columns are:

+--------+--------+-----------------------------------------------+
| Col    | Name   | Purpose                                       |
+========+========+===============================================+
| 0      | ☑      | Select / deselect (Shift-click for a range)   |
+--------+--------+-----------------------------------------------+
| 1      | File   | Filename (relative to the data folder)        |
+--------+--------+-----------------------------------------------+
| 2      | COR    | Per-row COR input                             |
+--------+--------+-----------------------------------------------+
| 3      | Size   | HDF5 ``/exchange/data`` size                  |
+--------+--------+-----------------------------------------------+
| 4      | Series | Detected series label                         |
+--------+--------+-----------------------------------------------+
| 5      | Status | Queued / Running / Inferring / Done / Failed  |
+--------+--------+-----------------------------------------------+

.. figure:: /_static/screenshots/batch_tab_series_tint.png
   :alt: Batch table with series tinting
   :align: center

Right-click on a row opens a context menu with actions:

- **Edit parameters** — open the per-file parameter JSON
- **Apply parameters to selected** — copy parameters from this row to all
  checked rows
- **View Try / View Full** — open the try-grid or full reconstruction
- **Delete from list** — shortcut equivalent to *Delete Selected* on the
  single row

Selection
~~~~~~~~~

- Click a checkbox — toggle a single row
- Shift-click a checkbox — toggle every row between the previously
  clicked row and this one
- Header checkbox — select / clear all rows

.. figure:: /_static/screenshots/batch_tab_range_select.png
   :alt: Shift-click range selection
   :align: center

Batch Try / Full
----------------

*Batch Try* and *Batch Full* drop every checked row into a queue. The
queue worker pulls jobs and dispatches one TomoCuPy subprocess per GPU
(local) or per remote session (SSH). The top-bar *Try COR* input is the
fallback COR for any row whose own COR is empty.

If a row has neither a per-row COR nor a valid top-bar fallback,
Batch Try / Full blocks with a clear error listing the offending rows.

Batch AI Reco (3 phases)
------------------------

**Phase A — Try**
   Generates try-center TIFFs for every checked row.

.. figure:: /_static/screenshots/batch_ai_phase_a.png
   :alt: Phase A
   :align: center

**Phase B — Inference (parallel)**
   Splits files into *N* chunks (N = number of GPUs from Advanced
   Config). Spawns one
   ``python -m tomogui._infer_worker <data_folder> <model_path> <files…>``
   per GPU with ``CUDA_VISIBLE_DEVICES`` set. Stdout is streamed through
   a thread-and-queue mechanism; each line such as
   ``[infer-worker] OK /path/to/file.h5 => 1024.3`` triggers:

   - updating the COR column for that row
   - updating the status column (``Inferring…`` → ``Done``)
   - incrementing the progress bar

.. figure:: /_static/screenshots/batch_ai_phase_b.png
   :alt: Phase B
   :align: center

**Phase C — Full**
   Runs Full reconstruction for every row that has a COR (manual or
   AI-assigned) via the standard Batch queue.

.. figure:: /_static/screenshots/batch_ai_phase_c.png
   :alt: Phase C
   :align: center

A summary dialog reports successes, skipped rows (e.g. missing try
TIFFs), and failures.

.. figure:: /_static/screenshots/batch_ai_summary.png
   :alt: Batch AI summary
   :align: center

Fix COR Outliers
----------------

.. figure:: /_static/screenshots/batch_tab_fix_cor_settings.png
   :alt: Max COR delta spinbox
   :align: center

Within each filename series:

1. Compute the **median** and **MAD**.
2. Flag CORs outside ``± min(max_delta, max(10, 5·MAD))``.
3. Replace flagged CORs with the series median.

``max_delta`` is the *Max COR delta* spinbox (default **50 px**).

A confirmation dialog lists each flagged row with its current and
proposed COR before anything is changed.

.. figure:: /_static/screenshots/batch_tab_fix_cor_outliers.png
   :alt: Fix COR Outliers confirmation
   :align: center

Auto-skip undersized files
--------------------------

Within a series, any file with noticeably smaller HDF5 ``/exchange/data``
than its peers is marked *skipped* automatically. This typically catches
acquisitions aborted partway through.

Delete Selected
---------------

Removes checked rows from the file list and table after confirmation.
Does **not** touch anything on disk.

.. figure:: /_static/screenshots/batch_tab_delete_confirm.png
   :alt: Delete Selected confirmation
   :align: center

Remote execution
----------------

Set *Remote host* in :doc:`advanced_config`. The batch queue SSHes to the
remote host, runs TomoCuPy with ``CUDA_VISIBLE_DEVICES`` per worker, and
streams stdout back.

See :doc:`/advanced/ssh_setup` and :doc:`/advanced/gpu_management` for
details.
