Reconstruction Workflow
=======================

This page covers the single-file reconstruction workflow. For multi-file
operations, see :doc:`batch_processing`; for automatic COR discovery, see
:doc:`ai_reco`.

Quick reference
---------------

1. Load data folder and select a file
2. Set reconstruction parameters (COR, algorithm, binning, …)
3. Run **Try** (or *AI Reco*) to pick a COR
4. Evaluate the try output
5. Adjust parameters if needed
6. Run **Full**

.. figure:: /_static/screenshots/main_tab_overview.png
   :alt: Main tab with reconstruction parameters
   :align: center

Try vs Full
-----------

Try Reconstruction
~~~~~~~~~~~~~~~~~~

- Runs over a small slice range at multiple candidate CORs
- Fast (seconds to a few minutes)
- Output: ``<folder>_rec/try_center/<dataset>/center*.tiff``
- Used for: picking the COR, checking data quality, tuning filter params

Full Reconstruction
~~~~~~~~~~~~~~~~~~~

- Processes the complete dataset
- Slower (minutes to hours depending on size / binning)
- Output: ``<folder>_rec/<dataset>/recon_*.tiff``

Reconstruction Methods
----------------------

TomoGUI exposes all TomoCuPy methods via the *Recon* tab:

``FBP``
   Direct filtered backprojection. Fast, sufficient for most datasets.

``gridrec``
   Grid-based FBP. Good quality / speed trade-off for 360° scans.

``LPREC``
   Log-polar reconstruction. Faster for very large sinograms.

Additional flags (``recon_steps`` vs ``recon``, binning, nsino-per-chunk,
start / end slice) are available on the same tab.

Centre of Rotation
------------------

COR can be set four ways:

1. **Manual** — type a value in the *COR* field on the Main tab.
2. **Auto** — TomoCuPy's built-in auto-centre. Selected via the COR
   method dropdown.
3. **Try + View Try** — run Try, slide through candidate CORs, pick the
   best one, it is copied into the COR field.
4. **AI Reco** — DINOv2-based automatic selection (see :doc:`ai_reco`).
   Result is written to
   ``<folder>_rec/try_center/<dataset>/center_of_rotation.txt`` and
   pulled back into the GUI.

For multi-file operations, see :ref:`cor-management` for how per-row CORs
interact with the top-bar COR input, and how *Fix COR Outliers* works.

Output folders
--------------

All output lives next to the data folder with a ``_rec`` suffix:

.. code-block:: text

   /data/tomo/scan/                    ← projections
   /data/tomo/scan_rec/                ← reconstructions
       ├── try_center/<dataset>/        ← try TIFFs + center_of_rotation.txt
       └── <dataset>/recon_*.tiff       ← full reconstruction

Per-dataset parameters
----------------------

Every reconstruction parameter tab writes its values to a JSON sidecar
next to the projection file. Re-loading the file restores its last-used
parameters. This sidecar is also what the Batch tab reads when you click
*Apply parameters to selected* on a row.
