# Screenshots for TomoGUI documentation

Capture these from the running GUI and drop the PNG files into this folder
using the exact filenames listed below. All Sphinx pages reference them via
`.. figure:: /_static/screenshots/<name>.png`.

Recommended capture resolution: at least 1280 × 800. Crop tightly to the
relevant area (e.g. a single dialog) rather than screenshotting the full
desktop.

## Top-level / overview

- `main_window.png` — full TomoGUI window, Main tab selected, with a dataset
  loaded and a reconstructed image on the right.
- `tab_bar.png` — close-up of the top tab bar (Main / Batch / HDF5 Viewer /
  Advanced Config / etc.).

## Main tab

- `main_tab_overview.png` — full Main tab, dataset loaded, parameters filled.
- `main_tab_file_picker.png` — the file selector/browser area.
- `main_tab_recon_params.png` — the reconstruction parameters form (COR,
  algorithm, binning, nsino-per-chunk, remove-stripe options, etc.).
- `main_tab_try_result.png` — Main tab after a Try reconstruction, showing
  the try-center grid image.
- `main_tab_full_result.png` — Main tab after a Full reconstruction.

## Batch tab

- `batch_tab_overview.png` — full Batch tab with ~5 files loaded and a mix of
  checked / unchecked rows.
- `batch_tab_series_tint.png` — batch table showing multiple series, with
  alternating background tints per series.
- `batch_tab_context_menu.png` — right-click context menu on a row (Edit,
  Apply to selected, Delete, etc.).
- `batch_tab_range_select.png` — Shift-click range selection highlighted in
  the table.
- `batch_tab_delete_confirm.png` — Delete Selected confirmation dialog.
- `batch_tab_fix_cor_outliers.png` — Fix COR Outliers confirmation dialog
  listing the flagged rows.
- `batch_tab_fix_cor_settings.png` — close-up of the Max COR delta spinbox
  and the Fix COR Outliers button.

## AI Reconstruction

- `ai_reco_dialog.png` — the single-file AI Reco dialog with model path,
  window parameters, number of GPUs, etc.
- `ai_reco_running.png` — Main tab while AI inference is running.
- `batch_ai_phase_a.png` — Batch tab during Phase A (try-center generation),
  with "Running try…" statuses in the table.
- `batch_ai_phase_b.png` — Batch tab during Phase B (GPU inference), with
  "Inferring on GPU N" statuses streaming per file.
- `batch_ai_phase_c.png` — Batch tab during Phase C (full reconstruction).
- `batch_ai_summary.png` — post-run summary dialog showing successes/failures.

## Tomolog

- `tomolog_dialog.png` — Tomolog dialog with Min/Max blank (auto-contrast)
  and output folder chosen.
- `tomolog_output.png` — example tomolog PDF/preview with the auto 5–95 %
  percentile contrast applied.

## HDF5 Viewer

- `hdf5_viewer_overview.png` — HDF5 Viewer tab showing the tree on the left
  and a dataset preview on the right.
- `hdf5_viewer_image.png` — HDF5 Viewer displaying a projection slice.

## Advanced Config / SSH

- `advanced_config_tab.png` — Advanced Config tab with remote host, GPU
  count, model path, etc. filled in.
- `ssh_setup_dialog.png` — dialog or panel where SSH/remote host is
  configured.

## Misc

- `theme_light.png` / `theme_dark.png` — same window in Light and Dark
  themes for the Themes page.
- `sync_acquisition_dialog.png` — Sync Acquisition dialog for picking up
  new files from the acquisition folder.
- `motor_rename_dialog.png` (bl_gui) — right-click → Edit PV / rename motor
  dialog. Used in the cross-link on the advanced page.

## Tips for capturing

- Run `tomogui` against a real dataset folder so the file list and COR
  columns are populated — blank GUIs make unhelpful screenshots.
- For the Phase A/B/C Batch AI screenshots, you can leave the GUI mid-run:
  the status column will show a mix of queued / running / done rows, which
  is exactly what we want.
- For the `batch_tab_series_tint.png` shot, pick a folder with at least two
  filename series (e.g. `sample_001.h5`, `sample_002.h5`, `other_001.h5`) so
  the alternating tint is visible.
- Use your OS screenshot tool (on Linux: `gnome-screenshot -a`) and save as
  PNG.
