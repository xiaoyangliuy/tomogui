API Reference
=============

Hand-curated summary of the most relevant classes and entry points.
For the full surface, use ``pydoc tomogui``.

Main classes
------------

``tomogui.TomoGUI``
   Main PyQt5 window. Assembles tabs, owns the batch queue, dispatches
   subprocesses, and holds all per-dataset state.

``tomogui.ThemeManager``
   Bright / Dark theme engine.

Entry points
------------

``tomogui`` (console script)
   Launches the GUI. Equivalent to ``python -m tomogui``.

``python -m tomogui._infer_worker``
   Standalone AI Reco inference worker. Called once per file by Batch
   AI Reco Phase B (one file per GPU slot)::

      python -m tomogui._infer_worker <data_folder> <model_path> <file1> [file2 ...]

   Honours ``CUDA_VISIBLE_DEVICES``. Emits per file:

   - ``[infer-worker] OK <file> => <cor>``
   - ``[infer-worker] SKIP <name>: <reason>``
   - ``[infer-worker] FAIL <name>: <err>``

   Followed by ``[infer-worker] done GPU=<i>  OK=<k>/<n>``.

Inference pipeline
------------------

``tomogui._tomocor_infer.inference.inference_pipeline(args, images, cors, try_dir)``
   Bundled DINOv2-based COR prediction. ``args`` is a Namespace with
   ``infer_use_8bits``, ``infer_downsample_factor``,
   ``infer_num_windows``, ``infer_seed_number``, ``infer_model_path``,
   ``infer_window_size``. Writes ``center_of_rotation.txt`` in
   ``try_dir``.

Internal helpers (TomoGUI methods)
----------------------------------

``_run_batch_with_queue(files, recon_type, num_gpus, machine)``
   Unified GPU-queue dispatcher. ``recon_type`` ∈
   {``'try'``, ``'full'``, ``'infer'``}.

``_start_batch_job_async(file_info, recon_type, gpu_id, machine)``
   Builds and starts the appropriate subprocess (``QProcess``) for a
   single job. For ``'infer'`` it spawns ``tomogui._infer_worker`` with
   one file and wires ``_on_infer_output`` for stdout streaming.

``_on_infer_output(process, filename, file_info)``
   Parses ``[infer-worker] OK ... => <cor>`` from worker stdout and
   updates the row's COR input live.

``_batch_run_ai_selected()``
   Orchestrates the 4-phase AI Reco pipeline (A try, B inference, C
   full, D optional TomoLog upload gated by
   ``batch_ai_upload_tomolog`` checkbox).

``_run_tomolog_for_file(filepath)``
   Runs ``tomolog`` synchronously for one file using the current
   TomoLog-panel settings. Used by Phase D and by the Main-tab *TomoLog*
   button.

``_fix_cor_outliers(abs_thresh=10.0, mad_k=5.0, max_thresh=None)``
   Fix COR Outliers + missing-value fill. Two passes: (1) series-median
   / MAD outlier replacement using two-nearest-neighbour averages, (2)
   whole-table series-mean fill for any selected row still empty.

``_find_row_by_filename(name, filename_col=None)``
   Row lookup by filename. Consults ``self.batch_file_main_list``
   first, then scans the table (column 1 = filename, column 0 =
   checkbox widget).

``_find_row_by_filepath(path)``
   Same, keyed on full path.

``_run_ai_inference_for_file(file_info)``
   Single-file AI Reco entry point (Main-tab *AI Reco* button).
