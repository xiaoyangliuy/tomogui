Troubleshooting
===============

Common symptoms and fixes. See also :doc:`../user_guide/installation`,
:doc:`../features/batch_tab`, and :doc:`cor_management`.

GUI / launch
------------

``ModuleNotFoundError: No module named 'tomogui'``
   The editable install did not register, or a stale site-packages
   copy is shadowing it. From the repo root:

   .. code-block:: bash

      pip uninstall tomogui -y
      rm -rf $(python -c "import site; print(site.getsitepackages()[0])")/tomogui*
      pip install -e . --config-settings editable_mode=compat

``Qt platform plugin could not be initialized``
   .. code-block:: bash

      export QT_QPA_PLATFORM_PLUGIN_PATH=""
      export QT_QPA_PLATFORM=xcb       # or wayland / offscreen

Changes to source do not take effect
   Check that the running ``tomogui`` is from the tree you edited. On
   shared beamline accounts, multiple clones often exist:

   .. code-block:: bash

      python -c "import tomogui, inspect; print(inspect.getfile(tomogui))"

Reconstruction
--------------

Try works, Full OOMs
   Decrease *nsino-per-chunk* on the Recon tab, or increase *binning*.

"Invalid COR" in batch mode
   The row's COR is empty and the top-bar fallback is also empty /
   invalid. Fix the row, set the top-bar, or use Fix COR Outliers to
   fill missing CORs from the series mean.

Mass invalid CORs after AI Reco
   Check:

   - AI model path is valid on the reconstruction host
   - ``nvidia-smi`` shows GPU activity during Phase B
   - log lines start with ``[infer-worker]``

   If ``center_of_rotation.txt`` exists but the GUI isn't picking it
   up, verify read permissions on the ``try_center/`` folder.

AI Reco
-------

Only one GPU in use during Phase B
   - *Number of GPUs* in Advanced Config must be > 1
   - all GPUs must be visible to ``nvidia-smi``
   - ``CUDA_VISIBLE_DEVICES`` must not be pre-set in the parent shell

Inference worker stuck (0 % GPU, no progress)
   The worker is hung before inference starts — usually on an NFS
   read or a CUDA init. Kill it with ``kill <pid>``; the queue
   continues on the other GPUs. If it happens repeatedly, grab a
   ``py-spy dump --pid <pid>`` stack trace before killing.

Worker prints ``FAIL <file>``
   Look at the traceback immediately above the FAIL line. Common
   causes: wrong model path, torch / CUDA version mismatch, missing
   try_center TIFFs for that file.

TomoLog
-------

Flat or saturated PDFs
   Leave Min / Max blank on the TomoLog panel → 5 – 95 % percentile
   auto-contrast per file.

Phase D upload skipped
   Tick the **→ TomoLog** checkbox next to *Batch AI Reco* before
   starting. Files whose Full failed are skipped automatically.
