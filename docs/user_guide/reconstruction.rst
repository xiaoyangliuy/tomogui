Reconstruction Workflow
=======================

This guide covers the complete workflow for tomographic reconstruction using TomoGUI.

Quick Reference
---------------

Basic reconstruction steps:

1. Load data folder and select file
2. Set reconstruction parameters
3. Run try reconstruction
4. View and evaluate results
5. Adjust parameters if needed
6. Run full reconstruction

Try vs Full Reconstruction
--------------------------

Try Reconstruction
~~~~~~~~~~~~~~~~~~

- Processes a small subset of data
- Fast execution (seconds to minutes)
- Used for parameter testing
- Preview quality
- Generates try_rec/ output folder

**When to use**:
   - Testing COR values
   - Evaluating filter parameters
   - Checking data quality
   - Parameter optimization

Full Reconstruction
~~~~~~~~~~~~~~~~~~~

- Processes complete dataset
- Slower execution (minutes to hours)
- Production quality
   - Final results
- Generates rec/ output folder

**When to use**:
   - After try reconstruction looks good
   - For final analysis
   - Publication-quality images
   - Complete 3D volumes

Reconstruction Methods
----------------------

recon
~~~~~

Standard reconstruction method:

- Direct filtered backprojection
- Faster execution
- Good for most datasets
- Lower memory usage

**Best for**:
   - Standard CT scans
   - Well-behaved data
   - Quick turnaround

recon_steps
~~~~~~~~~~~

Multi-step reconstruction:

- Iterative reconstruction
- More processing steps
- Advanced correction options
- Higher quality potential

**Best for**:
   - Challenging datasets
   - Advanced corrections needed
   - Maximum quality requirements

Center of Rotation (COR)
-------------------------

Auto Method
~~~~~~~~~~~

Automatically determines COR:

- No manual input needed
- Works for most datasets
- May require good data quality

**Pros**:
   - Convenient
   - No prior knowledge needed
   - Fast

**Cons**:
   - May fail on noisy data
   - Can't override if needed
   - Less control

Manual Method
~~~~~~~~~~~~~

Specify COR value manually:

- Requires COR value input
- Full control
- Consistent results

**Finding COR manually**:

1. Run try reconstruction with estimated value
2. Check for ring artifacts in result
3. Adjust COR value up or down
4. Repeat until minimal artifacts
5. Use final value for full reconstruction

**Typical COR values**:
   - 2048x2048 detector: ~1024
   - 4096x4096 detector: ~2048
   - Depends on detector centering

See :doc:`../advanced/cor_management` for advanced COR techniques.

Parameter Configuration
-----------------------

Main Tab Parameters
~~~~~~~~~~~~~~~~~~~

Essential settings available in Main tab:

- Reconstruction method
- COR method and value
- CUDA device
- Preset configurations

Other Tab Parameters
~~~~~~~~~~~~~~~~~~~~

Additional settings in other tabs:

- **Reconstruction**: Algorithm details
- **Hardening**: Beam hardening correction
- **Phase**: Phase retrieval
- **Rings**: Ring removal
- **Geometry**: Geometric corrections
- **Data**: Data preprocessing

Reconstruction Workflow
-----------------------

Standard Workflow
~~~~~~~~~~~~~~~~~

Complete reconstruction process:

**Step 1: Data Preparation**

.. code-block:: text

   - Click "Browse Data Folder"
   - Navigate to data directory
   - Click "Select Folder"
   - File list auto-populates

**Step 2: File Selection**

.. code-block:: text

   - Click "Projection File" dropdown
   - Select desired .h5 file
   - Note: Files sorted newest first

**Step 3: Basic Configuration**

.. code-block:: text

   - Reconstruction method: recon (for most cases)
   - COR method: manual (for control)
   - COR value: Enter known value or estimate
   - CUDA: Select GPU device (usually 0)

**Step 4: Try Reconstruction**

.. code-block:: text

   - Click "Try" button
   - Monitor log output for progress
   - Wait for completion (🏁 symbol)
   - Check for errors (❌ symbols)

**Step 5: View Try Results**

.. code-block:: text

   - Click "View Try" button
   - Examine reconstruction in right panel
   - Use slice slider to navigate
   - Check for artifacts

**Step 6: Evaluation**

Assess quality:

- Ring artifacts → Adjust COR
- Noise → Check data quality or adjust filters
- Blurriness → Check focus and detector alignment
- Streaks → Check for bad pixels or motion

**Step 7: Parameter Adjustment**

If needed:

.. code-block:: text

   - Adjust COR value (±0.5 typically)
   - Modify filter parameters in other tabs
   - Click "Try" again
   - Repeat until satisfied

**Step 8: Full Reconstruction**

When try looks good:

.. code-block:: text

   - Click "Full" button
   - Wait for completion (longer than try)
   - Monitor progress in log
   - View results with "View Full"

Advanced Workflow
~~~~~~~~~~~~~~~~~

For challenging datasets:

1. Use recon_steps method
2. Enable beam hardening correction
3. Apply ring removal
4. Use phase retrieval (if phase contrast)
5. Iterate try reconstructions
6. Run full with optimized parameters

See individual feature pages for parameter details.

Quality Assessment
------------------

Evaluating Reconstructions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Key quality indicators:

**Ring Artifacts**
   - Concentric circles around COR
   - Indicates wrong COR value
   - Adjust COR to minimize

**Edge Sharpness**
   - Sharp edges = good focus
   - Blurry edges = alignment issues
   - Check detector/sample position

**Noise Level**
   - Random pixel variations
   - Acceptable for try, minimize for full
   - Adjust filters or averaging

**Streaking Artifacts**
   - Radial streaks from center
   - Bad pixels or motion
   - May need data correction

**Contrast**
   - Can features be distinguished?
   - Adjust min/max in visualization
   - May need preprocessing

Interpreting Results
~~~~~~~~~~~~~~~~~~~~~

Good reconstruction:
   - Clear feature boundaries
   - Minimal artifacts
   - Good contrast
   - Sharp edges
   - Uniform background

Poor reconstruction:
   - Heavy ring artifacts
   - Excessive noise
   - Streaks or distortions
   - Blurry features
   - Non-uniform background

Common Issues
-------------

COR Problems
~~~~~~~~~~~~

**Symptoms**: Ring artifacts, distorted features

**Solution**:
   - Adjust COR value incrementally
   - Try auto method
   - Check detector alignment

Data Quality
~~~~~~~~~~~~

**Symptoms**: Noisy, low contrast results

**Solution**:
   - Check flat/dark field quality
   - Verify projection data
   - Increase averaging
   - Use better filters

GPU Issues
~~~~~~~~~~

**Symptoms**: Crashes, CUDA errors

**Solution**:
   - Check nvidia-smi for GPU status
   - Reduce data size
   - Free GPU memory
   - Use different GPU device

See :doc:`../advanced/troubleshooting` for more solutions.

Output Files
------------

Try Reconstruction
~~~~~~~~~~~~~~~~~~

Located in: ``<data_folder>/try_rec/``

Files:
   - Reconstructed slices (TIFF or HDF5)
   - Metadata
   - Processing log

Full Reconstruction
~~~~~~~~~~~~~~~~~~~

Located in: ``<data_folder>/rec/``

Files:
   - Complete reconstructed volume
   - All slices
   - Metadata
   - Processing parameters

Best Practices
--------------

Workflow Tips
~~~~~~~~~~~~~

1. **Always run try first** - Never run full without testing
2. **Save working parameters** - Use Save params button
3. **Document COR values** - Keep notes or use batch CSV
4. **Check logs** - Review for warnings/errors
5. **Keep try results** - Compare before running full

Parameter Selection
~~~~~~~~~~~~~~~~~~~

1. **Start simple** - Use default parameters initially
2. **Change one at a time** - Isolate parameter effects
3. **Use presets** - BeamHarden/Phase buttons
4. **Iterate** - Multiple try runs are cheap
5. **Save configurations** - For reproducibility

Performance
~~~~~~~~~~~

1. **Use appropriate GPU** - Check nvidia-smi
2. **Monitor memory** - Large datasets need more RAM
3. **Optimize binning** - For faster try reconstructions
4. **Batch overnight** - Full reconstructions in batch mode
5. **Use fast storage** - SSD for data folders

Next Steps
----------

- Learn about :doc:`batch_processing` for multiple datasets
- Explore :doc:`../features/reconstruction_params` for advanced parameters
- See :doc:`../features/batch_tab` for parallel processing
- Check :doc:`../advanced/gpu_management` for performance tuning
