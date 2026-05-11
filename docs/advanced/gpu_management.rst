GPU Management
==============

TomoGUI uses one or more GPUs for TomoCuPy reconstruction and for AI
Reco inference.

Single-file mode
----------------

On the Main tab, the **GPU** dropdown picks one CUDA device index.
TomoCuPy and AI Reco are invoked with ``CUDA_VISIBLE_DEVICES=<index>``.

Batch mode (unified queue)
--------------------------

The *Number of GPUs* field on the Advanced Config tab controls
parallelism for every batch operation — *Batch Try*, *Batch Full*, and
each phase of *Batch AI Reco*. All three share the same dispatcher
(``_run_batch_with_queue``):

- *N* GPU slots are available.
- When a slot is free and the queue is non-empty, a subprocess is
  spawned for one file, with ``CUDA_VISIBLE_DEVICES`` pinned to that
  slot's GPU.
- When the subprocess exits, the slot is returned to the pool and the
  next file dispatches immediately.

This means a single stuck file only blocks one GPU slot, not a whole
chunk of files; the other GPUs keep draining the queue.

.. figure:: /_static/screenshots/advanced_config_tab.png
   :alt: Advanced Config tab
   :align: center

Per-phase subprocesses
~~~~~~~~~~~~~~~~~~~~~~

- **Try / Full** — ``tomocupy <recon|recon_steps> --file-name <file>
  --rotation-axis <cor> …``
- **Inference** — ``python -m tomogui._infer_worker <folder>
  <model_path> <one_file>``

Both are launched as ``QProcess`` objects, with stdout streamed to the
log and parsed (for inference, ``[infer-worker] OK <path> => <cor>``
updates the row's COR cell live).

Monitoring
----------

During a run you will see:

- the progress bar advancing as files complete
- per-row status updates (``Queued`` → ``Running on GPU N`` →
  ``Inferred`` / ``Done`` / ``Failed`` / ``Uploaded``)
- streaming log lines such as
  ``[infer-worker] OK /data/.../sample_0042.h5 => 1024.3``

Use ``nvidia-smi`` on the reconstruction host to confirm all requested
GPUs are busy. If only one GPU shows activity, check:

- Advanced Config *Number of GPUs* is > 1
- ``nvidia-smi`` lists every GPU (driver issue otherwise)
- no ``CUDA_VISIBLE_DEVICES`` is set in the parent shell before
  launching TomoGUI — it caps what child processes can see.

Remote GPUs
-----------

When *Remote host* is set in Advanced Config, the batch queue SSHes to
the remote host and runs subprocesses there. The GPU count refers to
GPUs on the **remote** host. See :doc:`ssh_setup`.
