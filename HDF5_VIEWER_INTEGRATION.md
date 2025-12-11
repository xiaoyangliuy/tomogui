# HDF5 Viewer Integration

## Overview

The HDF5 Data Viewer has been integrated into TomoGUI's batch processing tab, providing direct visualization of raw projection data and comprehensive metadata inspection.

## What's New

### Batch Processing Tab

- **New Column**: "View Data" button added between "Status" and "View Try" columns
- **New Column**: "Size" column shows file size for each HDF5 file
- **Updated Table**: Now has 9 columns total (was 7)

### HDF5 Viewer Features

1. **Image Viewer Tab**
   - View raw projection data or normalized (data/data_white)
   - Navigate through all projections with slider
   - Real-time image shifting with keyboard (for white field alignment)
   - Multiple contrast/auto-level modes
   - Image statistics display
   - Dataset information

2. **Metadata Viewer Tab**
   - Display all HDF5 attributes and metadata
   - Search and filter functionality
   - Tree view of complete HDF5 file structure
   - Export metadata to CSV
   - Sortable tables

## Files Added

```
src/tomogui/hdf5_viewer.py              # HDF5 viewer implementation
docs/features/hdf5_viewer.rst           # Complete documentation
HDF5_VIEWER_INTEGRATION.md              # This file
```

## Files Modified

```
src/tomogui/gui.py                      # Added View Data button and integration
pyproject.toml                          # Added h5py and pyqtgraph dependencies
environment.yml                         # Added h5py and pyqtgraph to conda env
```

## New Dependencies

The following packages are now required:

- `h5py>=3.0.0` - HDF5 file reading
- `pyqtgraph>=0.12.0` - Fast image visualization

These are automatically installed when you install/update TomoGUI.

## Usage

### From Batch Processing Tab

1. Navigate to the **Batch Processing** tab
2. Click **Refresh** to load the file list
3. Click the **View Data** button for any file
4. The HDF5 viewer opens in a new window

### Image Viewer

- **Normalization**: Enable/disable to view data/data_white division
- **Slider**: Navigate through projection images
- **Contrast**: Choose auto-level mode or set manual min/max
- **Shift Control**: Use arrow keys to shift white field image
  - Arrow keys: ±1 pixel
  - Shift + arrows: ±10 pixels
  - Ctrl + arrows: ±50 pixels

### Metadata Viewer

- **Attributes Tab**: View all metadata with search/filter
- **File Structure Tab**: Browse HDF5 file hierarchy
- **Export**: Save metadata to CSV for documentation

## Expected HDF5 Structure

The viewer expects files with this structure:

```
/exchange/data          - Projection images (3D array)
/exchange/data_white    - White field images (3D array)
```

Additional metadata groups are optional but will be displayed if present.

## Keyboard Shortcuts

When the HDF5 viewer is active and normalization is enabled:

| Key | Action |
|-----|--------|
| ← | Shift white field left 1 pixel |
| → | Shift white field right 1 pixel |
| ↑ | Shift white field up 1 pixel |
| ↓ | Shift white field down 1 pixel |
| Shift + arrows | Shift by 10 pixels |
| Ctrl + arrows | Shift by 50 pixels |

## Installation/Update

If you're updating an existing TomoGUI installation:

```bash
# Activate your tomogui environment
conda activate tomogui

# Update with new dependencies
conda env update -f environment.yml

# Or install new dependencies manually
conda install -c conda-forge h5py pyqtgraph

# Reinstall TomoGUI
pip install -e .
```

## Common Use Cases

### 1. Quality Check Before Reconstruction

```
Open file → Check data quality → Review metadata → Proceed with reconstruction
```

### 2. White Field Alignment Check

```
Open file → Enable normalization → Use arrow keys to shift → Note optimal alignment
```

### 3. Parameter Verification

```
Open file → Metadata tab → Filter for parameters → Verify values → Export if needed
```

## Technical Details

### Integration Points

The HDF5 viewer is integrated at these locations:

1. **Import**: `from .hdf5_viewer import HDF5ImageDividerDialog` in gui.py
2. **Table Column**: Added "View Data" column at index 5
3. **Button Handler**: `_batch_view_data()` method creates viewer instance
4. **File Size**: `_format_file_size()` helper for human-readable sizes

### Column Layout

The batch table now has this structure:

| Index | Column | Type | Description |
|-------|--------|------|-------------|
| 0 | Select | Checkbox | File selection |
| 1 | Filename | Text | HDF5 filename |
| 2 | Size | Text | Human-readable file size |
| 3 | COR | Input | Center of rotation value |
| 4 | Status | Text | Processing status |
| 5 | View Data | Button | **NEW** - Opens HDF5 viewer |
| 6 | View Try | Button | View try reconstruction |
| 7 | View Full | Button | View full reconstruction |
| 8 | Actions | Buttons | Try/Full buttons |

### Dependencies

The viewer uses:

- **PyQt5**: GUI framework (already required)
- **pyqtgraph**: Fast image display with ImageView widget
- **h5py**: HDF5 file reading (already used in TomoGUI)
- **numpy**: Array operations (already required)

## Troubleshooting

### "Failed to open HDF5 viewer" Error

- Check that h5py and pyqtgraph are installed
- Verify the HDF5 file is not corrupted
- Ensure the file has the expected structure

### "Invalid File Structure" Warning

- The file doesn't contain `/exchange/data` and `/exchange/data_white`
- Check the file structure in another HDF5 viewer
- Verify this is a tomography projection file

### Slow Performance

- Large files (>10GB) may take time to load
- Close viewer windows when done
- Consider using binned data for preview

## Future Enhancements

Potential future improvements:

- [ ] ROI selection for reconstruction preview
- [ ] Save shift parameters for correction
- [ ] Side-by-side comparison of multiple files
- [ ] 3D volume rendering
- [ ] Sinogram view
- [ ] Line profile analysis

## Credits

HDF5 viewer based on:
- meta-cli metadata reading approach
- pyqtgraph ImageView widget
- TomoGUI architecture and theming

## Support

For issues or questions:
- Check documentation in `docs/features/hdf5_viewer.rst`
- Review this integration guide
- Check the main TomoGUI documentation
- Open an issue on GitHub
