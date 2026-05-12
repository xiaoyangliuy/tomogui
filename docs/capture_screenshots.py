"""Headless-friendly screenshot capture for the TomoGUI docs.

Run on a machine where `tomogui` launches normally (any display works — the
script uses Qt's offscreen buffer via QWidget.grab(), not the X screen).

    python docs/capture_screenshots.py                       # empty GUI shots
    python docs/capture_screenshots.py --data-folder /path   # with data loaded
    python docs/capture_screenshots.py --data-folder /path --themes both

Output goes to docs/_static/screenshots/ with filenames that match the
.. figure:: directives in the .rst pages. Existing files are overwritten.

What you get automatically
--------------------------
- main_window.png, tab_bar.png
- main_tab_overview.png, main_tab_file_picker.png
- <recon>/hardening/phase/rings/geometry/data/performance/advanced_config_tab
- batch_tab_overview.png, batch_tab_series_tint.png (if folder has data)
- batch_tab_fix_cor_settings.png
- sync_acquisition_dialog.png (MachineSettings dialog)
- theme_light.png / theme_dark.png (with --themes both)
- fake confirmation dialogs for Fix COR Outliers and Delete Selected

What you still need to capture manually
---------------------------------------
Anything that requires a running job or real reconstructions:
- main_tab_try_result.png / main_tab_full_result.png
- batch_ai_phase_a/b/c.png, batch_ai_summary.png
- tomolog_output.png, hdf5_viewer_image.png
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OUT = HERE / "_static" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def _save(widget, name: str) -> None:
    """Grab a widget into OUT/<name>.png. Uses QWidget.grab() so no X display is needed."""
    from PyQt5.QtCore import QCoreApplication
    for _ in range(3):
        QCoreApplication.processEvents()
    path = OUT / f"{name}.png"
    pix = widget.grab()
    if pix.isNull():
        print(f"  [warn] empty pixmap for {name}, skipping")
        return
    pix.save(str(path), "PNG")
    print(f"  wrote {path.relative_to(REPO_ROOT)} ({pix.width()}x{pix.height()})")


def _tab_index_by_label(tabs, label: str) -> int:
    for i in range(tabs.count()):
        if tabs.tabText(i).strip().lower() == label.strip().lower():
            return i
    return -1


def _switch_tab(gui, label: str) -> None:
    from PyQt5.QtCore import QCoreApplication
    idx = _tab_index_by_label(gui.tabs, label)
    if idx < 0:
        print(f"  [warn] tab '{label}' not found")
        return
    gui.tabs.setCurrentIndex(idx)
    for _ in range(5):
        QCoreApplication.processEvents()
    time.sleep(0.1)
    QCoreApplication.processEvents()


def _set_theme(gui, theme: str) -> None:
    """Switch TomoGUI to 'bright' or 'dark' theme."""
    from PyQt5.QtCore import QCoreApplication
    current = gui.theme_manager.get_current_theme()
    if current != theme:
        gui.theme_manager.toggle_theme()
        for _ in range(5):
            QCoreApplication.processEvents()
        time.sleep(0.1)


def _capture_all_tabs(gui, suffix: str = "") -> None:
    """Grab the whole GUI with each tab active."""
    tab_to_name = {
        "Main": "main_tab_overview",
        "Reconstruction": "recon_params_tab",
        "Hardening": "hardening_tab",
        "Phase": "phase_tab",
        "Rings": "rings_tab",
        "Geometry": "geometry_tab",
        "Data": "data_tab",
        "Performance": "performance_tab",
        "Advanced Config": "advanced_config_tab",
    }
    for label, base in tab_to_name.items():
        _switch_tab(gui, label)
        _save(gui, f"{base}{suffix}")


def _fake_fix_cor_outliers_dialog(gui):
    """Render a synthetic Fix COR Outliers confirmation box to show the UX."""
    from PyQt5.QtWidgets import QMessageBox
    mb = QMessageBox(gui)
    mb.setWindowTitle("Fix COR Outliers")
    mb.setIcon(QMessageBox.Question)
    mb.setText("3 outlier COR values will be replaced with their series median:")
    mb.setInformativeText(
        "• sample_007.h5 — COR 1238.5 → 1024.0\n"
        "• sample_024.h5 — COR  820.0 → 1024.3\n"
        "• sample_091.h5 — COR 1192.7 → 1023.9"
    )
    mb.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    mb.show()
    _save(mb, "batch_tab_fix_cor_outliers")
    mb.close()


def _fake_delete_confirm_dialog(gui):
    from PyQt5.QtWidgets import QMessageBox
    mb = QMessageBox(gui)
    mb.setWindowTitle("Delete Selected")
    mb.setIcon(QMessageBox.Warning)
    mb.setText("Remove 4 files from the batch list?")
    mb.setInformativeText(
        "• sample_003.h5\n• sample_004.h5\n• other_001.h5\n• other_002.h5\n\n"
        "(Files on disk are not touched.)"
    )
    mb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    mb.show()
    _save(mb, "batch_tab_delete_confirm")
    mb.close()


def _capture_machine_dialog(gui):
    """Show the MachineSettings / Sync Acquisition dialog."""
    try:
        from tomogui.gui import MachineSettingsDialog
    except ImportError:
        print("  [warn] MachineSettingsDialog not importable — skipping")
        return
    try:
        cfg = getattr(gui, "machine_config", {}) or {}
        d = MachineSettingsDialog(gui, cfg)
        d.show()
        _save(d, "sync_acquisition_dialog")
        d.close()
    except Exception as exc:
        print(f"  [warn] MachineSettings dialog failed: {exc}")


def _load_folder(gui, folder: str) -> None:
    """Populate the data folder and refresh the batch table without a file picker."""
    from PyQt5.QtCore import QCoreApplication
    gui.data_path.setText(folder)
    try:
        gui.refresh_main_table()
    except Exception as exc:
        print(f"  [warn] refresh_main_table failed: {exc}")
    for _ in range(10):
        QCoreApplication.processEvents()
    time.sleep(0.3)


def _capture_batch_table(gui):
    """Grab just the batch-file table (useful for 'series tint' crop)."""
    table = getattr(gui, "batch_file_main_table", None)
    if table is None:
        print("  [warn] batch_file_main_table missing — skipping")
        return
    _save(table, "batch_tab_overview")
    _save(table, "batch_tab_series_tint")
    _save(table, "batch_tab_range_select")


def _find_ancestor_groupbox(widget, title: str):
    """Walk up from a child widget until we find a QGroupBox with a given title."""
    from PyQt5.QtWidgets import QGroupBox
    w = widget
    while w is not None:
        if isinstance(w, QGroupBox) and title.lower() in (w.title() or "").lower():
            return w
        w = w.parentWidget()
    return None


def _capture_tomolog_panel(gui):
    """The Tomolog QGroupBox on the right side. Use min_input as anchor."""
    anchor = getattr(gui, "beamline_box", None) or getattr(gui, "scan_input", None)
    if anchor is None:
        print("  [warn] tomolog anchor missing — skipping tomolog_dialog")
        return
    gb = _find_ancestor_groupbox(anchor, "Tomolog")
    if gb is None:
        print("  [warn] Tomolog groupbox not found — skipping")
        return
    _save(gb, "tomolog_dialog")


def _capture_hdf5_viewer(gui, data_folder):
    """Instantiate HDF5ImageDividerDialog on the first .h5 in the folder."""
    import glob
    if not data_folder:
        print("  [info] no --data-folder — skipping hdf5_viewer_overview")
        return
    h5s = sorted(glob.glob(os.path.join(data_folder, "*.h5")))
    if not h5s:
        print(f"  [info] no *.h5 in {data_folder} — skipping hdf5_viewer_overview")
        return
    try:
        from tomogui.hdf5_viewer import HDF5ImageDividerDialog
    except Exception as exc:
        print(f"  [warn] cannot import HDF5ImageDividerDialog: {exc}")
        return
    try:
        d = HDF5ImageDividerDialog(file_path=h5s[0], parent=gui)
        d.resize(1200, 800)
        d.show()
        from PyQt5.QtCore import QCoreApplication
        for _ in range(10):
            QCoreApplication.processEvents()
        time.sleep(0.3)
        _save(d, "hdf5_viewer_overview")
        d.close()
    except Exception as exc:
        print(f"  [warn] HDF5 viewer dialog failed: {exc}")


def _capture_fix_cor_settings(gui):
    """Crop the Max-COR-delta spinbox area. Try known attribute names; fallback."""
    from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox
    candidates = ["cor_outlier_max", "cor_max_delta", "max_delta_spin",
                  "cor_outlier_max_spin"]
    spin = None
    for n in candidates:
        spin = getattr(gui, n, None)
        if spin is not None:
            break
    if spin is None:
        # Heuristic: scan all QDoubleSpinBox children and pick the one whose
        # neighbouring label mentions "COR" and "delta"/"outlier".
        for sb in gui.findChildren((QDoubleSpinBox, QSpinBox)):
            parent = sb.parentWidget()
            if parent is None:
                continue
            text = " ".join(ch.text() for ch in parent.children()
                            if hasattr(ch, "text") and callable(ch.text))
            if "COR" in text and ("outlier" in text.lower() or "delta" in text.lower()):
                spin = sb
                break
    if spin is None:
        print("  [warn] Max COR delta spinbox not found — skipping fix_cor_settings")
        return
    # Grab the parent row so we also see the label + Fix-COR-Outliers button.
    container = spin.parentWidget() or spin
    _save(container, "batch_tab_fix_cor_settings")


def _capture_batch_ai_phase(gui, phase_label: str, out_name: str):
    """Populate fake statuses in the batch table, then grab."""
    from PyQt5.QtCore import QCoreApplication
    from PyQt5.QtWidgets import QTableWidgetItem
    table = getattr(gui, "batch_file_main_table", None)
    if table is None or table.rowCount() == 0:
        print(f"  [info] no rows in batch table — skipping {out_name}")
        return
    # Column index for status — try header names, fall back to last col.
    status_col = table.columnCount() - 1
    for c in range(table.columnCount()):
        h = table.horizontalHeaderItem(c)
        if h and "status" in (h.text() or "").lower():
            status_col = c
            break
    phase_msgs = {
        "A": ["Running try…"] * 3 + ["Done"] * 2,
        "B": ["Inferring on GPU 0…", "Inferring on GPU 1…",
              "Inferring on GPU 2…", "Done", "Done"],
        "C": ["Running full…"] * 2 + ["Done"] * 3,
    }
    msgs = phase_msgs.get(phase_label, ["Queued"] * 5)
    rows = min(table.rowCount(), len(msgs))
    # Backup + overwrite
    backup = []
    for r in range(rows):
        item = table.item(r, status_col)
        backup.append(item.text() if item else "")
        table.setItem(r, status_col, QTableWidgetItem(msgs[r]))
    for _ in range(3):
        QCoreApplication.processEvents()
    _save(table, out_name)
    # Restore
    for r, txt in enumerate(backup):
        table.setItem(r, status_col, QTableWidgetItem(txt))


def _capture_batch_ai_summary(gui):
    from PyQt5.QtWidgets import QMessageBox
    mb = QMessageBox(gui)
    mb.setWindowTitle("Batch AI Reco finished")
    mb.setIcon(QMessageBox.Information)
    mb.setText("Batch AI Reco complete: 48 / 50 files processed.")
    mb.setInformativeText(
        "✓ 48 successful\n"
        "⚠ 1 skipped (no try TIFFs): aborted_003.h5\n"
        "✗ 1 failed: sample_017.h5 (CUDA OOM during inference)"
    )
    mb.setStandardButtons(QMessageBox.Ok)
    mb.show()
    _save(mb, "batch_ai_summary")
    mb.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-folder", help="Populate the data folder so batch table has content")
    ap.add_argument("--themes", choices=["current", "light", "dark", "both"],
                    default="current",
                    help="Which theme(s) to capture (default: current only)")
    ap.add_argument("--geometry", default="1600x1000",
                    help="WxH for the main window (default 1600x1000)")
    args = ap.parse_args()

    # Qt setup — prefer the real display if available so widgets render properly.
    # Offscreen also works (QWidget.grab() doesn't need an X server), but fonts
    # look slightly nicer on a real display.
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication

    app = QApplication.instance() or QApplication(sys.argv)

    from tomogui.gui import TomoGUI
    gui = TomoGUI()
    w, h = (int(x) for x in args.geometry.lower().split("x"))
    gui.resize(w, h)
    gui.show()
    for _ in range(10):
        QCoreApplication.processEvents()
    time.sleep(0.5)

    if args.data_folder:
        print(f"Loading data folder {args.data_folder}...")
        _load_folder(gui, args.data_folder)

    themes = []
    if args.themes == "current":
        themes = [gui.theme_manager.get_current_theme()]
    elif args.themes == "both":
        themes = ["bright", "dark"]
    else:
        themes = ["bright" if args.themes == "light" else "dark"]

    for theme in themes:
        _set_theme(gui, theme)
        theme_suffix = ""
        if args.themes == "both":
            theme_suffix = "_light" if theme == "bright" else "_dark"

        print(f"Capturing theme={theme} (suffix={theme_suffix or '<none>'})...")

        # Full window
        name = f"main_window{theme_suffix}" if theme_suffix else "main_window"
        _save(gui, name)
        if args.themes == "both":
            _save(gui, f"theme_{'light' if theme == 'bright' else 'dark'}")

        # Tab bar only
        _save(gui.tabs.tabBar(), f"tab_bar{theme_suffix}")

        # Each tab as full window
        _switch_tab(gui, "Main")
        _capture_all_tabs(gui, suffix=theme_suffix)

        # Main tab sub-regions — batch table + parameters
        _switch_tab(gui, "Main")
        if hasattr(gui, "data_path"):
            parent = gui.data_path.parentWidget()
            if parent is not None:
                _save(parent, f"main_tab_file_picker{theme_suffix}")

        _capture_batch_table(gui)

        # Dialogs — only captured once (use current theme)
        if theme == themes[0]:
            print("Capturing dialogs...")
            _capture_machine_dialog(gui)
            _fake_fix_cor_outliers_dialog(gui)
            _fake_delete_confirm_dialog(gui)
            _capture_tomolog_panel(gui)
            _capture_hdf5_viewer(gui, args.data_folder)
            _capture_fix_cor_settings(gui)
            print("Capturing Batch AI phase statuses (synthesised)...")
            _switch_tab(gui, "Main")
            _capture_batch_ai_phase(gui, "A", "batch_ai_phase_a")
            _capture_batch_ai_phase(gui, "B", "batch_ai_phase_b")
            _capture_batch_ai_phase(gui, "C", "batch_ai_phase_c")
            _capture_batch_ai_summary(gui)

    print("\nDone.")
    print(f"Screenshots in: {OUT}")
    print("Rebuild the docs with:  make -C docs html")


if __name__ == "__main__":
    main()
