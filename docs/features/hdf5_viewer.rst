HDF5 Data Viewer
================

The HDF5 Data Viewer provides direct visualization of raw HDF5 data files with advanced features for examining projection data and metadata.

Overview
--------

The HDF5 viewer is integrated into the batch processing tab, allowing you to inspect raw data files before or after reconstruction. It displays the division of two image datasets (data/data_white) with real-time shifting capabilities and comprehensive metadata viewing.

Access
------

From Batch Processing Tab
~~~~~~~~~~~~~~~~~~~~~~~~~~

Each file in the batch processing table has a **View Data** button that opens the HDF5 viewer for that specific file.

.. code-block:: text

   1. Navigate to Batch Processing tab
   2. Click "Refresh" to load file list
   3. Click "View Data" button for any file
   4. HDF5 viewer opens in new window

Features
--------

Image Viewer Tab
~~~~~~~~~~~~~~~~

The image viewer tab displays normalized or raw projection data:

**Normalization**
   - Enable/disable data division (data / data_white)
   - Toggle between normalized and raw data views
   - Real-time switching

**Image Selection**
   - Slider to navigate through all projections
   - Shows current image index
   - Total number of images displayed

**Contrast Control**
   - Multiple auto-level modes:
     - Per Image (default)
     - Min/Max
     - Percentile 1-99%
     - Percentile 2-98%
     - Percentile 5-95%
     - Manual (custom min/max)
   - Auto adjust button
   - Manual min/max spinboxes

**Shift Control**
   - Real-time image shifting for white field alignment
   - Keyboard controls:
     - Arrow keys: Shift by 1 pixel
     - Shift + arrows: Shift by 10 pixels
     - Ctrl + arrows: Shift by 50 pixels
   - X and Y shift display
   - Reset shift button

**Image Statistics**
   - Min value
   - Max value
   - Mean value
   - Standard deviation
   - Updates in real-time

**Dataset Information**
   - Data shape display
   - White field shape display
   - Number of images

Metadata Viewer Tab
~~~~~~~~~~~~~~~~~~~

Comprehensive metadata viewing with two sub-tabs:

**Attributes Tab**
   - Displays all HDF5 attributes and metadata
   - Three-column table:
     - Path/Attribute name
     - Value (with units if available)
     - Data type
   - Search/filter functionality
   - Sortable columns
   - Export to CSV button

**File Structure Tab**
   - Tree view of complete HDF5 structure
   - Shows all groups and datasets
   - Displays shapes and dtypes
   - Expandable hierarchy
   - Easy navigation

Expected HDF5 Structure
-----------------------

The viewer expects HDF5 files with the following structure:

.. code-block:: text

   /exchange/data         - Projection images (3D array)
   /exchange/data_white   - White field images (3D array)

   Optional metadata:
   /process/...           - Processing parameters
   /measurement/...       - Measurement metadata
   /instrument/...        - Instrument configuration

If the file doesn't contain these datasets, a warning will be displayed.

Use Cases
---------

Quality Check
~~~~~~~~~~~~~

Before reconstruction:

.. code-block:: text

   1. Open file in HDF5 viewer
   2. Check data quality (Image Viewer tab)
   3. Verify projections look correct
   4. Check for artifacts or issues
   5. Review metadata (Metadata tab)
   6. Proceed with reconstruction if OK

White Field Alignment
~~~~~~~~~~~~~~~~~~~~~

Check and adjust white field alignment:

.. code-block:: text

   1. Open HDF5 viewer
   2. Enable normalization
   3. Navigate to middle projection
   4. Use arrow keys to shift white field
   5. Observe division result
   6. Note optimal shift values
   7. Apply corrections if needed

Metadata Inspection
~~~~~~~~~~~~~~~~~~~

Review acquisition parameters:

.. code-block:: text

   1. Open HDF5 viewer
   2. Switch to Metadata tab
   3. Review attributes in table
   4. Check File Structure tab
   5. Export metadata to CSV if needed
   6. Verify parameters match expectations

Parameter Verification
~~~~~~~~~~~~~~~~~~~~~~

Confirm experimental settings:

.. code-block:: text

   1. Open HDF5 viewer
   2. Go to Metadata tab
   3. Filter for "energy" or "distance"
   4. Verify beam energy
   5. Check sample-detector distance
   6. Confirm rotation angles
   7. Validate acquisition parameters

Workflow Integration
--------------------

The HDF5 viewer integrates seamlessly with the batch processing workflow:

.. code-block:: text

   1. Load files in Batch Processing tab
   2. Use "View Data" to inspect raw data
   3. Check quality and parameters
   4. Set COR values in batch table
   5. Run "Try" reconstruction
   6. Use "View Try" to see results
   7. Compare with raw data if needed
   8. Run "Full" reconstruction when satisfied

Tips and Best Practices
------------------------

Performance
~~~~~~~~~~~

- Large datasets may take time to load
- Use slider to navigate efficiently
- Metadata loads separately from images
- Close viewer when done to free memory

Visualization
~~~~~~~~~~~~~

- Start with "Per Image" contrast mode
- Use percentile modes for noisy data
- Enable normalization to see flat-field quality
- Shift control helps identify alignment issues

Metadata
~~~~~~~~

- Use filter to find specific parameters
- Export metadata for documentation
- Check file structure for custom datasets
- Verify units are correct

Keyboard Shortcuts
------------------

Image Viewer Tab
~~~~~~~~~~~~~~~~

When normalization is enabled:

- **←** : Shift left 1 pixel
- **→** : Shift right 1 pixel
- **↑** : Shift up 1 pixel
- **↓** : Shift down 1 pixel
- **Shift + ←/→/↑/↓** : Shift 10 pixels
- **Ctrl + ←/→/↑/↓** : Shift 50 pixels

Common Issues
-------------

File Won't Open
~~~~~~~~~~~~~~~

**Symptoms**: Error message when clicking "View Data"

**Solutions**:
   - Verify file exists and is not corrupted
   - Check file has correct HDF5 structure
   - Ensure file is not locked by another process
   - Check file permissions

Missing Datasets
~~~~~~~~~~~~~~~~

**Symptoms**: Warning about missing /exchange/data or /exchange/data_white

**Solutions**:
   - Verify file structure in Metadata tab
   - Check if datasets have different names
   - Confirm this is a valid tomography file
   - Contact data acquisition team if structure is wrong

Slow Performance
~~~~~~~~~~~~~~~~

**Symptoms**: Viewer is slow to respond

**Solutions**:
   - Close other viewer windows
   - Reduce image size if possible
   - Use binned data for preview
   - Check available system memory

Integration with Other Features
--------------------------------

- **Batch Processing**: Direct access from file list
- **Main Tab**: Can inspect files before reconstruction
- **Parameter Management**: Verify settings match metadata
- **Quality Assessment**: Compare raw data with reconstructions

See Also
--------

- :doc:`batch_tab` - Batch processing overview
- :doc:`main_tab` - Main reconstruction controls
- :doc:`../user_guide/reconstruction` - Reconstruction workflow
- :doc:`../advanced/data_quality` - Data quality assessment
