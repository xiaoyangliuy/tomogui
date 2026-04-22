GPU Management
==============

TomoGUI uses one or more GPUs for TomoCuPy reconstruction and for AI Reco
inference. Behaviour differs slightly between single-file and batch modes.

Single-file mode
----------------

On the Main tab, the **GPU** dropdown picks one CUDA device index.
TomoCuPy is invoked with ``CUDA_VISIBLE_DEVICES=<index>``. AI Reco from
the Main tab also runs on this one GPU.

Batch mode
----------

The *Number of GPUs* field on the Advanced Config tab controls
parallelism for all batch operations:

.. figure:: /_static/screenshots/advanced_config_tab.png
   :alt: Advanced Config tab
   :align: center

**Batch Try / Batch Full**
   Spawns *N* TomoCuPy workers (locally, or via SSH to the remote host).
   Each worker has ``CUDA_VISIBLE_DEVICES`` pinned to one GPU and
   consumes jobs from a shared queue.

**Batch AI Reco Phase B**
   Splits the file list into *N* chunks. Spawns

   .. code-block:: bash

      CUDA_VISIBLE_DEVICES=<i> python -m tomogui._infer_worker \
          <data_folder> <model_path> <chunk_of_files>

   once per GPU, so *N* DINOv2 inference processes run simultaneously.
   Stdout from every worker is streamed through a shared queue and
   parsed by the GUI (``[infer-worker] OK|SKIP|FAIL``).

**Batch AI Reco Phases A and C**
   Use the same multi-GPU Batch queue as *Batch Try* and *Batch Full*.

Why N subprocesses?
-------------------

Early prototypes ran AI inference in the GUI thread, which:

- blocked the UI (Qt "not responding")
- never used more than one GPU
- had no per-file status streaming

The subprocess-per-GPU design fixes all three: GIL is bypassed, GPUs
run in parallel, and each worker's stdout is a natural source of
progress events.

Monitoring
----------

During batch runs you will see:

- the progress bar advancing as files complete (not as a fraction of
  Phase B only)
- per-row status updates (``Queued`` → ``Running`` / ``Inferring on GPU
  N`` → ``Done`` / ``Failed``)
- streaming log lines such as
  ``[infer-worker] OK /data/.../sample_0042.h5 => 1024.3``

Use ``nvidia-smi`` on the reconstruction host to confirm all requested
GPUs are busy. If only one GPU shows activity during Phase B, check:

- Advanced Config *Number of GPUs* is > 1
- ``nvidia-smi`` lists every GPU (driver issue otherwise)
- no CUDA_VISIBLE_DEVICES is set in the parent shell before launching
  TomoGUI — this caps what the child processes can see.

Remote GPUs
-----------

When *Remote host* is set in Advanced Config, the batch queue SSHes to
the remote host and runs TomoCuPy / ``_infer_worker`` there. The GPU
count refers to GPUs available on the **remote** host. See
:doc:`ssh_setup` for connection and key setup.
