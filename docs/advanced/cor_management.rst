.. _cor-management:

COR Management
==============

This page covers how TomoGUI stores, resolves, and corrects center-of-rotation
(COR) values across single-file and batch workflows.

Sources of COR
--------------

A COR can come from four places:

1. **Manual** — typed into the top-bar *COR* field or a per-row cell on
   the Batch tab.
2. **Auto** — TomoCuPy's built-in auto-centre algorithm (selected via
   the COR method dropdown).
3. **Try + View Try** — the user scrubs the try-grid slider and picks
   the best slice; the associated COR is copied back.
4. **AI Reco** — DINOv2 inference writes
   ``center_of_rotation.txt`` inside the try_center folder; TomoGUI
   reads it and populates the per-file COR.

Resolution order (batch)
------------------------

Batch Try / Full use, per row:

.. code-block:: text

   row.cor_input                     if valid
   else top_bar_cor                  if valid
   else FAIL (block run, report row)

This means the top-bar *Try COR* acts as a fallback: you can leave it
blank when every row has its own COR, or leave per-row CORs blank when
the top-bar is set (typical for homogeneous batches).

Storage
-------

Per-file CORs are written to the per-dataset parameter JSON sidecar
(next to the HDF5 file). AI Reco additionally writes
``center_of_rotation.txt`` inside the dataset's ``try_center/`` folder
so the value survives across TomoGUI sessions even if the sidecar is
deleted.

Some beamlines also keep a global COR summary JSON (e.g.
``rot_cen.json``) that TomoGUI can read/write; this is handy for shared
access across users.

Fix COR Outliers
----------------

Given a set of checked rows:

1. Group rows by **filename series** using the regex
   ``^(.*?)[._-]*(\d+)$`` — the part before the trailing numeric index
   is the series key.
2. Within each series, compute ``median`` and ``MAD``.
3. Flag any COR deviating by more than
   ``min(max_delta, max(10, 5·MAD))`` from the series median.
4. Replace each flagged COR with its series median.

``max_delta`` is the *Max COR delta* spinbox on the Batch tab (default
50 px). The lower bound of ``max(10, 5·MAD)`` prevents a very tight
series from flagging everything slightly off the median.

.. figure:: /_static/screenshots/batch_tab_fix_cor_outliers.png
   :alt: Fix COR Outliers confirmation
   :align: center

The confirmation dialog lists each flagged row with its current and
proposed COR; nothing changes until you accept.

Why series grouping?
~~~~~~~~~~~~~~~~~~~~

A sliding-window approach (as used in earlier versions) was confusing
for users: a series of 5 files and a series of 50 files need different
windows. Filename grouping is intrinsic to how datasets are named
(``sample_001.h5``, ``sample_002.h5`` …) and robust to variable series
lengths.

Series can span dozens or hundreds of files. If a series has only a
single flagged row that looks like a true outlier, correction is
high-confidence; if it has many flagged rows, the "median" may not be
the true value and manual review is recommended.

Auto-skip undersized files
--------------------------

Within each series, TomoGUI compares HDF5 ``/exchange/data`` sizes. Any
file noticeably smaller than its peers is marked *skipped* — typically
an acquisition that was aborted partway through and did not finish
writing the expected number of projections.

Skipped files do not participate in Fix COR Outliers and are excluded
from Batch Try / Full runs unless you manually re-enable them.
