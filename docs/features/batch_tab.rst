Batch Processing Tab
====================

The Batch Processing tab enables efficient processing of multiple datasets with advanced features including parallel GPU execution, COR management, and remote machine support.

Overview
--------

The batch processing tab provides:

- **File list management** with checkboxes for selection
- **COR value storage** in CSV format
- **Multi-GPU parallel execution** with job queue
- **Remote machine support** via SSH
- **Progress tracking** for batch operations
- **Individual file operations** (view, try, full)

Interface Components
--------------------

File List Table
~~~~~~~~~~~~~~~

The main table displays all HDF5 files in the data folder:

.. list-table::
   :header-rows: 1
   :widths: 10 30 15 15 15 15 20

   * - Select
     - Filename
     - COR
     - Status
     - View Try
     - View Full
     - Actions
   * - ☑
     - scan_0001.h5
     - 1024.5
     - Ready
     - [View Try]
     - [View Full]
     - [Try] [Full]

Columns:
   - **Select**: Checkbox for batch operations
   - **Filename**: Name of the HDF5 file
   - **COR**: Editable center of rotation value
   - **Status**: Current processing status
   - **View Try/Full**: Buttons to visualize reconstructions
   - **Actions**: Individual Try/Full buttons

Control Buttons
~~~~~~~~~~~~~~~

Top row controls:

- **Refresh File List**: Reload files from data folder
- **Save COR to CSV**: Save all COR values to batch_cor_values.csv
- **Load COR from CSV**: Load COR values from CSV file
- **Select All**: Select all files
- **Deselect All**: Clear all selections

Machine Configuration
~~~~~~~~~~~~~~~~~~~~~

- **Target Machine**: Choose local or remote machine (tomo1-5)
- **GPUs per machine**: Number of available GPUs (1-8)
- **Queue status**: Shows number of waiting jobs

Batch Operations
~~~~~~~~~~~~~~~~

- **Run Try on Selected**: Execute try reconstruction on checked files
- **Run Full on Selected**: Execute full reconstruction on checked files
- **Remove Selected from List**: Permanently delete selected files from disk

Progress Tracking
~~~~~~~~~~~~~~~~~

- **Progress bar**: Visual indicator of batch completion
- **Status label**: Shows completed/running/queued jobs
- **Queue label**: Number of jobs waiting in queue

Using Batch Processing
-----------------------

Basic Batch Workflow
~~~~~~~~~~~~~~~~~~~~

1. **Load Files**

   .. code-block:: text

      Click "Refresh File List" to load all .h5 files from the data folder

2. **Set COR Values**

   .. code-block:: text

      Enter COR values in the table for each file
      Or load from CSV if previously saved

3. **Select Files**

   .. code-block:: text

      Check the files you want to process
      Use "Select All" for all files

4. **Configure Machine**

   .. code-block:: text

      Target Machine: Select "Local" or remote machine
      GPUs per machine: Set number of available GPUs

5. **Run Batch**

   .. code-block:: text

      Click "Run Try on Selected" or "Run Full on Selected"
      Confirm the operation
      Monitor progress in status label and log

COR Management
--------------

Saving COR Values
~~~~~~~~~~~~~~~~~

1. Enter COR values in the table
2. Click "Save COR to CSV"
3. Values are saved to ``<data_folder>/batch_cor_values.csv``

CSV Format:

.. code-block:: csv

   Filename,COR
   scan_0001.h5,1024.5
   scan_0002.h5,1025.2
   scan_0003.h5,1023.8

Loading COR Values
~~~~~~~~~~~~~~~~~~

1. Ensure ``batch_cor_values.csv`` exists in data folder
2. Click "Load COR from CSV"
3. Values are automatically populated in the table

**Auto-load**: COR values are automatically loaded when refreshing the file list if CSV exists.

Parallel GPU Processing
-----------------------

GPU Queue System
~~~~~~~~~~~~~~~~

TomoGUI implements a sophisticated queue system to prevent GPU overload:

- **One job per GPU**: Each GPU processes one reconstruction at a time
- **Automatic scheduling**: Jobs are queued and assigned as GPUs become available
- **Real-time monitoring**: Status shows running/queued/completed jobs

Example: 20 files with 4 GPUs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Initial state:
   - Jobs 1-4 start on GPUs 0-3
   - Jobs 5-20 wait in queue

   After GPU 0 finishes job 1:
   - Job 5 starts on GPU 0
   - Jobs 6-20 remain in queue

   Status: "Completed 4/20 | Running: 4 | Queue: 12"

Configuring GPUs
~~~~~~~~~~~~~~~~

Set the number of available GPUs based on your machine:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Machine
     - GPUs
     - Configuration
   * - Local workstation
     - 1-2
     - Set to actual GPU count
   * - tomo1-5 (servers)
     - 4-8
     - Set based on machine specs
   * - Testing
     - 1
     - Use single GPU for safety

Remote Machine Execution
-------------------------

SSH Setup Required
~~~~~~~~~~~~~~~~~~

Before using remote machines:

1. Configure SSH keys for passwordless login
2. Ensure tomocupy is installed on remote machine
3. Verify network access to data files (shared storage)

See :doc:`../advanced/ssh_setup` for detailed configuration.

Using Remote Machines
~~~~~~~~~~~~~~~~~~~~~

1. **Select Target Machine**

   .. code-block:: text

      Target Machine dropdown → Select "tomo1", "tomo2", etc.

2. **Set GPU Count**

   .. code-block:: text

      GPUs per machine → Enter number of GPUs on that machine

3. **Run Batch**

   .. code-block:: text

      Operations execute via SSH on the remote machine
      Log shows: "🖥️ Running on tomo1: scan_0001.h5"

Job Execution
~~~~~~~~~~~~~

For remote machines, commands are wrapped in SSH:

.. code-block:: bash

   ssh tomo1 "tomocupy recon --file-name /data/scan.h5 ..."

GPU assignment for remote machines:
   - Local: Uses CUDA_VISIBLE_DEVICES environment variable
   - Remote: Relies on remote machine's GPU allocation

Individual File Operations
---------------------------

Each file row provides quick actions:

View Reconstructions
~~~~~~~~~~~~~~~~~~~~

- **View Try**: Load and display try reconstruction
- **View Full**: Load and display full reconstruction

These buttons set the file in the main dropdown and call the visualization functions.

Run Single File
~~~~~~~~~~~~~~~

- **Try button**: Run try reconstruction on this file only
- **Full button**: Run full reconstruction on this file only

Useful for:
   - Testing parameters on one file
   - Re-running failed reconstructions
   - Processing individual files without batch selection

File Management
---------------

Removing Files
~~~~~~~~~~~~~~

The "Remove Selected from List" button **permanently deletes** files from disk:

.. warning::
   This operation cannot be undone! Files are deleted from the filesystem.

Procedure:
   1. Select files to delete
   2. Click "Remove Selected from List"
   3. Confirm the deletion dialog
   4. Files are deleted and removed from table

Safety Features:
   - Confirmation dialog warns about permanent deletion
   - Shows number of files to be deleted
   - Logs each deletion (success or failure)
   - Failed deletions don't stop the process

Status Messages
---------------

File Status Values
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Status
     - Meaning
   * - Ready
     - File loaded, not processed
   * - Running Try on GPU X
     - Try reconstruction in progress on GPU X
   * - Running Full on GPU X
     - Full reconstruction in progress on GPU X
   * - Try Complete
     - Try reconstruction finished successfully
   * - Full Complete
     - Full reconstruction finished successfully
   * - Try Failed
     - Try reconstruction encountered an error
   * - Full Failed
     - Full reconstruction encountered an error

Batch Status Display
~~~~~~~~~~~~~~~~~~~~

The status label format:

.. code-block:: text

   "Completed X/Y | Running: A | Queue: B"

   X = Number of completed jobs
   Y = Total number of jobs
   A = Jobs currently running on GPUs
   B = Jobs waiting in queue

Best Practices
--------------

Organizing COR Values
~~~~~~~~~~~~~~~~~~~~~

1. **Test individual files** first with try reconstruction
2. **Record COR values** in the table as you find them
3. **Save to CSV frequently** to avoid losing work
4. **Version control** CSV files for different datasets

Optimizing GPU Usage
~~~~~~~~~~~~~~~~~~~~

1. **Match GPU count** to actual hardware
2. **Monitor GPU memory** with nvidia-smi during batch runs
3. **Start with small batches** to test configuration
4. **Use try mode** first for large batches

Error Recovery
~~~~~~~~~~~~~~

If batch processing is interrupted:

1. **Check status column** to see which files failed
2. **Review log output** for error messages
3. **Adjust parameters** if needed
4. **Deselect completed files**, rerun failed ones
5. **Use individual actions** for problematic files

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Files not showing in list**
   - Click "Refresh File List"
   - Verify data folder is set correctly
   - Check that .h5 files exist in folder

**COR values not loading**
   - Ensure batch_cor_values.csv exists in data folder
   - Check CSV file format (see example above)
   - Try manual load with "Load COR from CSV"

**Jobs stuck in queue**
   - Check log output for errors
   - Verify GPU availability with nvidia-smi
   - Restart GUI if processes are hung

**SSH errors for remote machines**
   - Test SSH connection: ``ssh tomo1``
   - Verify passwordless login is configured
   - Check network/firewall settings

See :doc:`../advanced/troubleshooting` for more solutions.
