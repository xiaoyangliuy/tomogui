Batch Processing Guide
======================

End-to-end guide to processing many datasets in one go. For an in-depth
reference of every Batch tab control, see :doc:`../features/batch_tab`.
For AI-based COR discovery in batch mode, see :doc:`ai_reco`.

Overview
--------

The Batch tab lets you:

- process dozens to thousands of datasets with one click
- run reconstruction on local or remote GPUs
- run **Batch AI Reco** with a 3-phase multi-GPU pipeline
- detect and correct bad CORs via **Fix COR Outliers** with filename-based
  series grouping
- auto-skip undersized files within a series
- monitor progress and per-file status in real time

.. figure:: /_static/screenshots/batch_tab_overview.png
   :alt: Batch tab
   :align: center

Quick start
-----------

1. Open the **Batch** tab.
2. Click *Refresh File List* (or use *Sync Acquisition* during a live
   scan).
3. Tick the files you want to process. **Shift-click** to select a range;
   Ctrl-click to toggle individual rows.
4. For each row, enter a COR (or use *Batch AI Reco* later to fill them in
   automatically).
5. Click **Batch Try**, **Batch Full**, or **Batch AI Reco**.

.. figure:: /_static/screenshots/batch_tab_range_select.png
   :alt: Shift-click range select
   :align: center

Per-file and top-bar COR
------------------------

Each row has its own COR. The top-bar *Try COR* field is used as a
fallback for any row that does not have one. Concretely, Batch Full /
Batch Try use:

.. code-block:: text

   effective_COR(row) =
       row.cor_input  if row.cor_input is valid
       else top_bar_cor  if top_bar_cor is valid
       else FAIL (blocked with a clear error)

This means you can leave the top-bar field blank as long as every
selected row has its own COR, or vice-versa.

Series-aware operations
-----------------------

Series grouping
~~~~~~~~~~~~~~~

Filenames are grouped into series by stripping a trailing numeric index
(``^(.*?)[._-]*(\d+)$``). For example, ``sample_001.h5``, ``sample_002.h5``
and ``sample_010.h5`` all belong to the ``sample`` series regardless of
the length of the index or how many files are in the group.

Series tinting
~~~~~~~~~~~~~~

Rows in the same series share a subtle background tint so you can see the
grouping at a glance.

.. figure:: /_static/screenshots/batch_tab_series_tint.png
   :alt: Batch table with series tint
   :align: center

Auto-skip undersized files
~~~~~~~~~~~~~~~~~~~~~~~~~~

Within each series, any file whose HDF5 ``/exchange/data`` array is
noticeably smaller than its peers is flagged *skipped* automatically.
This catches aborted acquisitions and avoids failing the whole batch on a
single bad file.

Fix COR Outliers
~~~~~~~~~~~~~~~~

See :doc:`ai_reco` for the full algorithm. Summary: within each series,
compute the median and MAD, flag any COR that differs by more than
``min(max_delta, max(10, 5·MAD))``, and replace it with the series
median. The ``max_delta`` is exposed as a *Max COR delta* spinbox on the
Batch tab (default 50 px).

.. figure:: /_static/screenshots/batch_tab_fix_cor_outliers.png
   :alt: Fix COR Outliers confirmation
   :align: center

Deleting files from the list
----------------------------

Select one or more rows and click **Delete Selected**. A confirmation
dialog lists the files first. Deletion removes them from the internal
list (``batch_file_main_list``) and from the table; it does **not**
delete anything on disk.

.. figure:: /_static/screenshots/batch_tab_delete_confirm.png
   :alt: Delete Selected confirmation
   :align: center

Remote / multi-GPU
------------------

The Advanced Config tab sets the remote host and the **Number of GPUs**.
*Batch Try* and *Batch Full* split the job queue across GPUs (one
TomoCuPy process per GPU), and *Batch AI Reco* uses the same GPU count
for Phase B inference.

See :doc:`../advanced/gpu_management` and :doc:`../advanced/ssh_setup`
for configuration details.
