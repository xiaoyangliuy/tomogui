Main Tab
========

The Main tab provides quick access to essential reconstruction operations and parameter management.

Overview
--------

The Main tab is divided into sections:

- Try Reconstruction controls
- Full Reconstruction controls
- Preset configuration buttons
- Parameter management buttons

Try Reconstruction Section
--------------------------

Try reconstruction allows quick testing with a subset of data.

Controls
~~~~~~~~

Recon Method
   Dropdown selector:
      - **recon**: Standard filtered backprojection
      - **recon_steps**: Multi-step iterative reconstruction

CUDA Device
   Select GPU for computation:
      - 0, 1, 2, etc. based on available GPUs
      - Check ``nvidia-smi`` for GPU list

COR Method
   Center of rotation determination:
      - **auto**: Automatic COR finding
      - **manual**: Specify COR value manually

COR Value
   Text input for manual COR:
      - Enter numeric value (e.g., 1024.5)
      - Enabled only when manual method selected

Buttons
~~~~~~~

**Try**
   Execute try reconstruction
      - Processes subset of data
      - Fast execution
      - Outputs to try_rec/ folder

**View Try**
   Load and display try reconstruction results
      - Shows reconstruction in visualization panel
      - Enables slice navigation
      - Allows contrast adjustment

**Batch Try**
   Run try reconstruction on multiple files
      - Opens batch processing confirmation
      - Uses current configuration
      - Processes selected files sequentially

Full Reconstruction Section
---------------------------

Full reconstruction processes the complete dataset.

Controls
~~~~~~~~

Same controls as Try Reconstruction:

- Recon Method
- CUDA Device
- COR Method
- COR Value

Buttons
~~~~~~~

**Full**
   Execute full reconstruction
      - Processes entire dataset
      - Longer execution time
      - Production quality results
      - Outputs to rec/ folder

**View Full**
   Load and display full reconstruction results
      - Shows complete reconstruction
      - Full volume navigation
      - High quality visualization

**Batch Full**
   Run full reconstruction on multiple files
      - Batch processing mode
      - Sequential execution
      - Long-running operation

Preset Configuration Buttons
-----------------------------

Quick parameter presets for common scenarios.

BeamHarden
~~~~~~~~~~

Configure for beam hardening correction:

- Sets absorption reconstruction parameters
- Enables beam hardening correction
- Optimizes for dense materials
- Good for metal samples

**Use when**:
   - Imaging metal objects
   - High Z materials
   - Absorption contrast
   - Cup artifacts present

Phase
~~~~~

Configure for phase contrast imaging:

- Sets phase retrieval parameters
- Optimizes for edge detection
- Good for low Z materials
- Soft tissue imaging

**Use when**:
   - Phase contrast data
   - Soft materials
   - Biological samples
   - Low absorption contrast

Laminography
~~~~~~~~~~~~

Configure for laminography geometry:

- Sets geometric corrections
- Adjusts for tilted axis
- Optimizes for flat samples
- PCB/wafer imaging

**Use when**:
   - Laminography scans
   - Flat sample geometry
   - Tilted rotation axis
   - Non-standard geometry

Parameter Management
--------------------

Save, load, and reset reconstruction parameters.

Save Params
~~~~~~~~~~~

Save current parameter configuration:

- Opens file dialog
- Saves all tab settings
- JSON format
- Reusable configuration

**Saved parameters include**:
   - Reconstruction method
   - COR value
   - All tab settings
   - Filter parameters
   - Correction settings

Load Params
~~~~~~~~~~~

Load previously saved parameters:

- Opens file selection dialog
- Restores all settings
- Updates all tabs
- Overwrites current config

**Use cases**:
   - Reuse successful configurations
   - Share settings between users
   - Document processing pipeline
   - Batch consistency

Reset Params
~~~~~~~~~~~~

Reset all parameters to defaults:

- Clears custom settings
- Restores initial values
- Affects all tabs
- No confirmation required

**Default values**:
   - Recon method: recon
   - COR method: manual
   - Standard filter settings
   - No corrections enabled

Workflow Examples
-----------------

Quick Try-and-Full
~~~~~~~~~~~~~~~~~~

Basic reconstruction workflow:

.. code-block:: text

   1. Select data folder and file
   2. Set COR method: manual
   3. Enter COR value: 1024.5
   4. CUDA: 0
   5. Click "Try"
   6. Wait for completion
   7. Click "View Try"
   8. Check quality
   9. Click "Full"
   10. Click "View Full"

Using Presets
~~~~~~~~~~~~~

Beam hardening correction workflow:

.. code-block:: text

   1. Load data and file
   2. Click "BeamHarden" preset
   3. Adjust COR if needed
   4. Click "Try"
   5. View results
   6. Fine-tune in Hardening tab
   7. Click "Try" again
   8. When satisfied, click "Full"

Parameter Reuse
~~~~~~~~~~~~~~~

Save and reuse configuration:

.. code-block:: text

   1. Configure all parameters
   2. Run successful try
   3. Click "Save Params"
   4. Name: "steel_optimal.json"
   5. Save file

   Later, for similar sample:
   1. Click "Load Params"
   2. Select "steel_optimal.json"
   3. All settings restored
   4. Click "Try" to verify
   5. Click "Full" if good

Tips and Best Practices
------------------------

COR Selection
~~~~~~~~~~~~~

- Always test COR with try reconstruction first
- Adjust in small increments (0.1 to 0.5)
- Look for ring artifacts
- Use batch tab for multiple files with different CORs

GPU Selection
~~~~~~~~~~~~~

- Check GPU memory with ``nvidia-smi``
- Use different GPUs for parallel jobs
- GPU 0 is typically default
- Match GPU to data size

Preset Usage
~~~~~~~~~~~~

- Start with appropriate preset
- Fine-tune in specific tabs
- Save successful configurations
- Document preset modifications

Parameter Management
~~~~~~~~~~~~~~~~~~~~

- Save working configurations
- Name files descriptively
- Keep version history
- Share across team

Common Issues
-------------

Try Reconstruction Fails
~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Error in log, no output

**Solutions**:
   - Check data file is valid
   - Verify COR value is reasonable
   - Ensure GPU is available
   - Check disk space for output

Wrong COR Value
~~~~~~~~~~~~~~~

**Symptoms**: Ring artifacts in reconstruction

**Solutions**:
   - Increase/decrease COR by 0.5
   - Try auto method
   - Run multiple tries
   - Check detector alignment

Preset Not Working
~~~~~~~~~~~~~~~~~~

**Symptoms**: Unexpected results after preset

**Solutions**:
   - Check all tabs for changes
   - Reset and manually configure
   - Verify data type matches preset
   - Review preset documentation

Integration with Other Tabs
----------------------------

Main tab works with other tabs:

- **Reconstruction tab**: Algorithm details
- **Hardening tab**: Beam hardening (BeamHarden preset)
- **Phase tab**: Phase retrieval (Phase preset)
- **Geometry tab**: Laminography (Laminography preset)
- **Batch tab**: Multi-file processing

Keyboard Shortcuts
------------------

Currently no keyboard shortcuts in Main tab.

**Planned**:
   - Ctrl+T: Try reconstruction
   - Ctrl+F: Full reconstruction
   - Ctrl+V: View last reconstruction

See Also
--------

- :doc:`../user_guide/reconstruction` - Complete reconstruction workflow
- :doc:`reconstruction_params` - Detailed parameters
- :doc:`batch_tab` - Batch processing
- :doc:`advanced_config` - Configuration files
