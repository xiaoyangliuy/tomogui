API Reference
=============

Selected classes and entry points for developers. This is a hand-curated
summary; for the full API, use ``pydoc tomogui`` or
``python -c "help('tomogui')"``.

Main classes
------------

``tomogui.TomoGUI``
   The main PyQt5 window. Assembles tabs, manages the batch queue,
   dispatches subprocesses, and owns all per-dataset state.

``tomogui.ThemeManager``
   Bright / Dark theme engine; applies QSS stylesheets and persists the
   active theme between sessions.

Entry points
------------

``tomogui`` (console script)
   Launches the GUI. Equivalent to
   ``python -m tomogui``.

``python -m tomogui._infer_worker``
   Standalone AI Reco inference worker used by Batch AI Reco Phase B::

      python -m tomogui._infer_worker <data_folder> <model_path> <file1> [file2 ...]

   Honours ``CUDA_VISIBLE_DEVICES``. Prints one of:

   - ``[infer-worker] OK <file> => <cor>``
   - ``[infer-worker] SKIP <name>: <reason>``
   - ``[infer-worker] FAIL <name>: <err>``

   plus a final ``[infer-worker] done GPU=<i>  OK=<k>/<n>`` line.

Inference pipeline
------------------

``tomogui._tomocor_infer.inference.inference_pipeline(args, images, cors, try_dir)``
   Bundled DINOv2-based COR prediction. Takes a Namespace of args
   (``infer_use_8bits``, ``infer_downsample_factor``,
   ``infer_num_windows``, ``infer_seed_number``, ``infer_model_path``,
   ``infer_window_size``), a stack of try-slice images, their COR values,
   and the output directory. Writes ``center_of_rotation.txt``.

Internal helpers
----------------

``TomoGUI._fix_cor_outliers()``
   Entry point for the *Fix COR Outliers* button. Groups by filename
   series, computes median + MAD, flags, and applies corrections after
   confirmation.

``TomoGUI._find_row_by_filename(name, filename_col=None)``
   Robust row lookup by filename. Consults
   ``self.batch_file_main_list`` first, then falls back to scanning the
   table (column 1 = filename, column 0 = checkbox widget).

``TomoGUI._find_row_by_filepath(path)``
   Same as above but keyed on the full path.

``TomoGUI._run_ai_inference_for_file(file_info)``
   Single-file AI Reco entry point called by Main tab *AI Reco*.

``TomoGUI._batch_run_ai_selected()``
   Batch tab *AI Reco* entry point. Orchestrates the 3-phase pipeline.
