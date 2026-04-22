Troubleshooting
===============

Common symptoms and fixes. See also :doc:`../user_guide/installation`
(installation), :doc:`../features/batch_tab` (batch operations), and
:doc:`cor_management` (COR issues).

GUI / launch
------------

``ModuleNotFoundError: No module named 'tomogui'``
   The editable install did not register, or a stale site-packages copy is
   shadowing it. From the repo root:

   .. code-block:: bash

      pip uninstall tomogui -y
      rm -rf $(python -c "import site; print(site.getsitepackages()[0])")/tomogui*
      pip install -e . --config-settings editable_mode=compat

``Qt platform plugin could not be initialized``
   Typically a clash between PyQt5 plugin paths. Try:

   .. code-block:: bash

      export QT_QPA_PLATFORM_PLUGIN_PATH=""
      export QT_QPA_PLATFORM=xcb       # or wayland / offscreen

Changes to source do not take effect
   Check that your running ``tomogui`` is from the tree you edited. On
   beamline nodes, multiple clones often exist (e.g.
   ``/home/beams0/AMITTONE/Software/tomogui`` vs
   ``/home/beams19/USERTXM/Software/tomogui``). Verify with:

   .. code-block:: bash

      python -c "import tomogui, inspect; print(inspect.getfile(tomogui))"

   Reinstall from the correct tree if needed.

Reconstruction
--------------

Try succeeds but Full fails with OOM
   Decrease *nsino-per-chunk* on the Recon tab, or increase *binning*.

"Invalid COR" in batch mode
   See :doc:`cor_management` — either the per-row COR is blank and the
   top-bar fallback is also blank, or the value is out of range. The
   error lists the offending rows.

Mass "invalid COR" after AI Reco
   Check:

   - the AI model path is valid on the reconstruction host
   - ``nvidia-smi`` shows GPU activity during Phase B
   - log lines start with ``[infer-worker]``

   If Phase B is writing ``center_of_rotation.txt`` but the GUI is not
   picking it up, verify file ownership / permissions on the
   ``try_center/`` folder.

AI Reco
-------

Only one GPU in use during Batch Phase B
   Verify *Number of GPUs* in Advanced Config is > 1 and every GPU is
   visible to ``nvidia-smi``. If ``CUDA_VISIBLE_DEVICES`` is already
   exported in the parent shell, it caps what the worker subprocesses
   can see — unset it before launching TomoGUI.

``NameError: name 'sys' is not defined``
   An older build of ``gui.py`` had a missing import. Pull the latest
   source and reinstall editable.

Inference worker fails with ``FAIL``
   Look at the log lines just above ``FAIL`` — they contain the
   traceback. Common causes: wrong model path, torch / CUDA version
   mismatch, or try_center TIFFs missing for that file.

TomoLog
-------

TomoLog produces flat or saturated PDFs
   Leave Min / Max blank in the TomoLog dialog to trigger 5 – 95 %
   percentile auto-contrast per file.

Batch table
-----------

``KeyError: 'file'``
   Older bug — per-file dicts use ``path`` as the key. Pull latest
   source; the current code uses
   ``file_info.get('path') or file_info.get('file') or
   file_info.get('filename')``.

Shift-click selects nothing
   Older bug — range select used to iterate an empty list. Pull latest.

Deletion does not refresh list
   Older bug — the list rebuild step was missing. Pull latest.

Performance / parallelism
-------------------------

GUI "not responding" during AI Reco
   Make sure you are on a version that runs inference in a subprocess,
   not in the GUI thread. Confirm by watching the log for
   ``[infer-worker]`` lines.

Progress bar stuck at 100 % during Phase B
   Older bug — progress was computed incorrectly. Pull latest; Phase B
   progress is now ``done/total`` across the whole file list, updated as
   each worker reports completion.
