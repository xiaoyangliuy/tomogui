AI Reconstruction
=================

TomoGUI ships a DINOv2-based automatic center-of-rotation (COR) finder,
available both as a single-file action on the Main tab and as a batch
pipeline on the Batch tab. Under the hood, the single-file and batch
variants share the same inference code (``tomogui._tomocor_infer``); the
batch variant additionally parallelises across GPUs.

How it works
------------

1. A Try reconstruction produces a grid of slices at different candidate
   COR values, saved to
   ``<data_folder>_rec/try_center/<dataset>/center*.tiff``.
2. The AI Reco inference pipeline loads those TIFFs, runs the DINOv2-based
   model, and writes the chosen COR to
   ``<data_folder>_rec/try_center/<dataset>/center_of_rotation.txt``.
3. TomoGUI reads ``center_of_rotation.txt`` and updates the per-file COR in
   the GUI / Batch table. You can then run Full reconstruction with the
   chosen COR.

Single-file AI Reco
-------------------

On the Main tab:

1. Load a dataset and run **Try** (or use an already-computed try_center).
2. Click **AI Reco**.
3. Confirm the model path, window size (518 by default), number of
   windows (3), downsample factor (2), and GPU.
4. The chosen COR is written back to the COR input when inference
   completes.

Batch AI Reco (multi-GPU)
-------------------------

The Batch tab's **AI Reco** button runs a 3-phase pipeline across all
checked rows:

**Phase A — Try**
   Runs a try reconstruction for each file, sequentially or with the
   existing Batch queue, producing the try-center TIFFs.

.. figure:: /_static/screenshots/batch_ai_phase_a.png
   :alt: Batch AI Phase A in progress
   :align: center

**Phase B — Inference (parallel across GPUs)**
   The file list is split into N chunks (N = *Number of GPUs* in Advanced
   Config). TomoGUI spawns one ``python -m tomogui._infer_worker``
   subprocess per chunk, pinning each worker to a single GPU via
   ``CUDA_VISIBLE_DEVICES``. Workers stream one line per file
   (``[infer-worker] OK <file> => <cor>`` or ``SKIP``/``FAIL``) and the
   GUI updates each row's status and the progress bar in real time.

.. figure:: /_static/screenshots/batch_ai_phase_b.png
   :alt: Batch AI Phase B with per-file streaming status
   :align: center

**Phase C — Full**
   With per-file CORs now populated, the standard Batch queue runs Full
   reconstruction for all files.

.. figure:: /_static/screenshots/batch_ai_phase_c.png
   :alt: Batch AI Phase C
   :align: center

At the end, TomoGUI displays a summary dialog listing successful rows, any
skipped files (e.g. missing try TIFFs), and any failures.

.. figure:: /_static/screenshots/batch_ai_summary.png
   :alt: Batch AI Reco summary
   :align: center

Fix COR Outliers
----------------

Runs that use AI Reco (or a mix of manual + AI) occasionally produce a
spurious COR for a single file. The Batch tab's **Fix COR Outliers** button
corrects these post-hoc.

.. figure:: /_static/screenshots/batch_tab_fix_cor_settings.png
   :alt: Max COR delta spinbox and Fix COR Outliers button
   :align: center

Algorithm
~~~~~~~~~

1. Group rows by **filename series**. Filenames are normalised by
   stripping trailing separators and a numeric index
   (``^(.*?)[._-]*(\d+)$``), so ``sample_001.h5``, ``sample_002.h5``, …
   all belong to the ``sample`` series, independent of how many files the
   series contains.
2. Within each series, compute the **median** COR and the **median
   absolute deviation (MAD)**.
3. Flag any row whose COR deviates from the series median by more than
   ``min(max_delta, max(10, 5·MAD))`` pixels, where ``max_delta`` is the
   *Max COR delta* spinbox (default **50 px**).
4. Replace flagged CORs with the series median.

This captures both the "hard" physical constraint ("within a series, COR
cannot drift by more than 50 px") and the MAD-based statistical one
("5 σ-equivalent from the series median").

Applying
~~~~~~~~

Click **Fix COR Outliers**. A confirmation dialog lists each flagged row
with its current and proposed COR. Accept to apply.

.. figure:: /_static/screenshots/batch_tab_fix_cor_outliers.png
   :alt: Fix COR Outliers confirmation dialog
   :align: center

Series tinting and auto-skip
----------------------------

Two related features help when operating on series:

**Series tinting** — each filename series gets its own subtle row
background tint in the Batch table, so you can visually confirm which
files are grouped together.

.. figure:: /_static/screenshots/batch_tab_series_tint.png
   :alt: Batch table with series tinting
   :align: center

**Auto-skip undersized files** — within a series, any file whose HDF5
``/exchange/data`` array is noticeably smaller than its peers is marked
*skipped* automatically. This typically catches acquisitions that were
aborted partway through.

TomoLog auto-contrast
---------------------

The TomoLog dialog's Min / Max fields can be left blank: when either is
blank, TomoGUI computes a **5 – 95 % percentile** contrast per file
before handing it to TomoLog. This keeps multi-file PDF reports readable
when datasets have very different absolute intensity ranges.

.. figure:: /_static/screenshots/tomolog_dialog.png
   :alt: Tomolog dialog with blank Min/Max
   :align: center
