import sys, os, glob, json, subprocess
import numpy as np
import matplotlib
from pathlib import Path
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QTextEdit, QLineEdit, QLabel, QProgressBar,
    QComboBox, QSlider, QGroupBox, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QEvent, QProcess, QRectF, QPointF
from PIL import Image
import matplotlib as mpl
from matplotlib.widgets import RectangleSelector
from matplotlib.backend_bases import MouseButton


GUI_path = Path(__file__).resolve().parent
mpl.rcdefaults()
mpl.style.use(f"{GUI_path}/tomoGUI_mpl_format.mplstyle")

class TomoCuPyGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TomoCuPy-Tomolog GUI")
        self.resize(1650, 950)

        # State
        self.default_cmap = "gray"
        self.current_cmap = self.default_cmap
        self.vmin = None
        self.vmax = None
        self.preview_files = []
        self.full_files = []
        self.process = []
        self._current_img = None # currently displayed image
        self._current_img_path = None

        main_layout = QHBoxLayout()

        # ==== LEFT PANEL ====
        left_layout = QVBoxLayout()

        # Data folder
        folder_layout = QHBoxLayout()
        self.data_path = QLineEdit()
        browse_btn = QPushButton("Browse Data Folder")
        browse_btn.clicked.connect(self.browse_data_folder)
        folder_layout.addWidget(QLabel("Data Folder:"))
        folder_layout.addWidget(self.data_path)
        folder_layout.addWidget(browse_btn)
        left_layout.addLayout(folder_layout)

        # Projection file
        proj_layout = QHBoxLayout()
        self.proj_file_box = QComboBox()
        self.proj_file_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        proj_layout.addWidget(QLabel("Projection File:"))
        proj_layout.addWidget(self.proj_file_box)
        refresh_btn2 = QPushButton("Refresh")
        refresh_btn2.clicked.connect(self.refresh_h5_files)
        proj_layout.addWidget(refresh_btn2)
        left_layout.addLayout(proj_layout)

        # Rotation axis + Refresh + Abort
        cor_layout = QHBoxLayout()
        self.cor_input = QLineEdit()
        cor_layout.addWidget(QLabel("Center of Rotation:"))
        cor_layout.addWidget(self.cor_input)

        load_config_btn = QPushButton("Load Config")
        save_config_btn = QPushButton("Save Config")
        load_config_btn.clicked.connect(self.load_config)
        save_config_btn.clicked.connect(self.save_config)
        cor_layout.addWidget(load_config_btn)
        cor_layout.addWidget(save_config_btn)

        help_tomo_btn = QPushButton("help")
        help_tomo_btn.clicked.connect(self.help_tomo)
        cor_layout.addWidget(help_tomo_btn)

        abort_btn = QPushButton("Abort")
        abort_btn.clicked.connect(self.abort_process)
        abort_btn.setStyleSheet("color: red;")
        cor_layout.addWidget(abort_btn)
        left_layout.addLayout(cor_layout)


        # Try and Full config boxes
        config_frame_layout = QHBoxLayout()

        # Try config group
        left_config_group = QGroupBox("Config for Try Reconstruction")
        left_config_layout = QVBoxLayout()
        self.config_editor_try = QTextEdit()
        self.config_editor_try.setFixedHeight(300)
        self.config_editor_try.setStyleSheet("QTextEdit { border: 1px solid gray; font-size: 12.5pt; }")
        self.config_editor_try.focusInEvent = lambda event: self.highlight_editor(self.config_editor_try, event)
        self.config_editor_try.focusOutEvent = lambda event: self.unhighlight_editor(self.config_editor_try, event)
        left_config_layout.addWidget(self.config_editor_try)

        try_btn_layout = QHBoxLayout()
        try_btn = QPushButton("Try")
        try_btn.clicked.connect(self.try_reconstruction)
        view_try_btn = QPushButton("View Try")
        view_try_btn.clicked.connect(self.view_try_reconstruction)
        batch_try_btn = QPushButton("Batch Try")
        batch_try_btn.clicked.connect(self.batch_try_reconstruction)
        try_btn_layout.addWidget(try_btn)
        try_btn_layout.addWidget(view_try_btn)
        try_btn_layout.addWidget(batch_try_btn)
        left_config_layout.addLayout(try_btn_layout)

        # Start/End for Batch Try
        scan_range_layout = QHBoxLayout()
        scan_range_layout.addWidget(QLabel("Start:"))
        self.start_scan_input = QLineEdit()
        scan_range_layout.addWidget(self.start_scan_input)
        scan_range_layout.addWidget(QLabel("End:"))
        self.end_scan_input = QLineEdit()
        scan_range_layout.addWidget(self.end_scan_input)
        left_config_layout.addLayout(scan_range_layout)

        left_config_group.setLayout(left_config_layout)

        # Full config group
        right_config_group = QGroupBox("Config for Full Reconstruction")
        right_config_layout = QVBoxLayout()
        self.config_editor_full = QTextEdit()
        self.config_editor_full.setFixedHeight(300)
        self.config_editor_full.setStyleSheet("QTextEdit { border: 1px solid gray; font-size: 12.5pt; }")
        self.config_editor_full.focusInEvent = lambda event: self.highlight_editor(self.config_editor_full, event)
        self.config_editor_full.focusOutEvent = lambda event: self.unhighlight_editor(self.config_editor_full, event)
        right_config_layout.addWidget(self.config_editor_full)

        self.active_editor = self.config_editor_try #default target

        full_btn_layout = QHBoxLayout()
        full_btn = QPushButton("Full")
        full_btn.clicked.connect(self.full_reconstruction)
        self.view_btn = QPushButton("View Full")
        self.view_btn.setEnabled(True)
        self.view_btn.clicked.connect(self.view_full_reconstruction)
        batch_full_btn = QPushButton("Batch Full")
        batch_full_btn.clicked.connect(self.batch_full_reconstruction)
        full_btn_layout.addWidget(full_btn)
        full_btn_layout.addWidget(self.view_btn)
        full_btn_layout.addWidget(batch_full_btn)
        right_config_layout.addLayout(full_btn_layout)
        
        # COR (Full) inline
        cor_full_layout = QHBoxLayout()
        cor_full_layout.addWidget(QLabel("COR (Full):"))
        self.cor_input_full = QLineEdit()
        cor_full_layout.addWidget(self.cor_input_full)

        rec_cor_btn = QPushButton("Add COR")
        rec_cor_btn.clicked.connect(self.record_cor_to_json)
        cor_full_layout.addWidget(rec_cor_btn)

        right_config_layout.addLayout(cor_full_layout)

        right_config_group.setLayout(right_config_layout)

        config_frame_layout.addWidget(left_config_group)
        config_frame_layout.addWidget(right_config_group)
        left_layout.addLayout(config_frame_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        left_layout.addWidget(self.progress)

        # Log + COR JSON
        log_json_layout = QHBoxLayout()
        log_box_layout = QVBoxLayout()
        log_box_layout.addWidget(QLabel("Log Output:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_box_layout.addWidget(self.log_output)
        log_json_layout.addLayout(log_box_layout, 6)
        json_box_layout = QVBoxLayout()
        json_box_layout.addWidget(QLabel("COR Log File:"))
        self.cor_json_output = QTextEdit()
        self.cor_json_output.setReadOnly(True)
        self.cor_json_output.setStyleSheet("QTextEdit { font-size: 12pt; }")
        json_box_layout.addWidget(self.cor_json_output)
        log_json_layout.addLayout(json_box_layout, 2)
        self.load_cor_json_btn = QPushButton("Load COR file")
        json_box_layout.addWidget(self.load_cor_json_btn)
        self.load_cor_json_btn.clicked.connect(self.load_cor_to_jsonbox)
        left_layout.addLayout(log_json_layout)

        main_layout.addLayout(left_layout, 3.5)

        # Right panel
        right_layout = QVBoxLayout()
        toolbar_row = QHBoxLayout()
        self.fig = Figure(figsize=(5, 6.65))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self._keep_zoom = False
        self._last_xlim = None
        self._last_ylim = None
        self._last_image_shape = None
        self.rect_selector = None  # Placeholder for rectangle selector
        self.roi_extent = None  # Placeholder for ROI extent
        self._drawing_roi = False  # Flag to track if ROI is being drawn
        self.canvas.mpl_connect("button_press_event", self._on_canvas_click)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        toolbar_row.addWidget(self.toolbar)
        self._cid_release = self.canvas.mpl_connect("button_release_event", self._nav_oneshot_release)

        

        # Colormap dropdown
        toolbar_row.addWidget(QLabel("Colormap:"))
        self.cmap_box = QComboBox()
        self.cmap_box.addItems(["gray", "viridis", "plasma", "inferno", "magma", "cividis"])
        self.cmap_box.setCurrentText(self.default_cmap)
        self.cmap_box.currentIndexChanged.connect(self.update_cmap)
        toolbar_row.addWidget(self.cmap_box)

        #auto/reset scale image button
        draw_box_btn = QPushButton("Draw")
        draw_box_btn.clicked.connect(self.draw_box)
        draw_box_btn.setFixedWidth(48)
        auto_scale_btn = QPushButton("Auto")
        auto_scale_btn.setFixedWidth(48)
        auto_scale_btn.clicked.connect(self.auto_img_contrast)
        reset_scale_btn = QPushButton("Reset")
        reset_scale_btn.setFixedWidth(48)
        reset_scale_btn.clicked.connect(self.reset_img_contrast)
        toolbar_row.addWidget(draw_box_btn)
        toolbar_row.addWidget(auto_scale_btn)
        toolbar_row.addWidget(reset_scale_btn)

        # Min/Max inputs
        toolbar_row.addWidget(QLabel("Min:"))
        self.min_input = QLineEdit()
        self.min_input.setFixedWidth(60)
        self.min_input.editingFinished.connect(self.update_vmin_vmax)
        toolbar_row.addWidget(self.min_input)

        toolbar_row.addWidget(QLabel("Max:"))
        self.max_input = QLineEdit()
        self.max_input.setFixedWidth(60)
        self.max_input.editingFinished.connect(self.update_vmin_vmax)
        toolbar_row.addWidget(self.max_input)

        right_layout.addLayout(toolbar_row)
        self.canvas.installEventFilter(self)

        canvas_slider_frame = QVBoxLayout()
        canvas_slider_frame.addWidget(self.canvas)
        slider_layout = QHBoxLayout()
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 20px; background: #ccc; border-radius: 5px; }
            QSlider::handle:horizontal { background: #4CAF50; border: 1px solid #5c5c5c; width: 20px; height: 20px;
                                         margin: -5px 0; border-radius: 10px; }
        """)
        slider_layout.addWidget(QLabel("Image Index:"))
        slider_layout.addWidget(self.slice_slider)
        canvas_slider_frame.addLayout(slider_layout)
        right_layout.addLayout(canvas_slider_frame, 8)

        # Tomolog placeholder
        tomolog_group = QGroupBox("Tomolog")
        tomolog_layout = QVBoxLayout()

        # Row 1: Beamline + Scan
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Beamline"))
        self.beamline_box = QComboBox()
        self.beamline_box.addItems(["2-bm", "7-bm", "32-id"])
        row1.addWidget(self.beamline_box)

        row1.addWidget(QLabel("Scan"))
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("e.g. 1 or 2-5 or 6,8-15,18")
        row1.addWidget(self.scan_input)

        # Row 2: Cloud + URL
        row1.addWidget(QLabel("Cloud"))
        self.cloud_box = QComboBox()
        self.cloud_box.addItems(["imgur", "globus", "aps"])
        self.cloud_box.setCurrentText("imgur")
        row1.addWidget(self.cloud_box)
        tomolog_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("URL"))
        self.url_input = QLineEdit()
        row2.addWidget(self.url_input)
        tomolog_layout.addLayout(row2)

        # Row 3: X, Y, Z
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("X"))
        self.x_input = QLineEdit("-1")
        row3.addWidget(self.x_input)
        row3.addWidget(QLabel("Y"))
        self.y_input = QLineEdit("-1")
        row3.addWidget(self.y_input)
        row3.addWidget(QLabel("Z"))
        self.z_input = QLineEdit("-1")
        row3.addWidget(self.z_input)
        tomolog_layout.addLayout(row3)

        # Row 4: Extra parameters
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Note"))
        self.note_input = QLineEdit()
        row4.addWidget(self.note_input)

        row4.addWidget(QLabel("Extra Params"))
        self.extra_params_input = QLineEdit()
        self.extra_params_input.setPlaceholderText("--public True")  # Example shown when empty
        row4.addWidget(self.extra_params_input)
        tomolog_layout.addLayout(row4)

        # Row 5: Apply button
        row5 = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.run_tomolog)
        help_tomolog_btn = QPushButton("help-log")
        help_tomolog_btn.clicked.connect(self.help_tomolog)
        row5.addWidget(apply_btn)
        row5.addWidget(help_tomolog_btn)
        row5.setStretch(0,3)
        row5.setStretch(1,1)
        tomolog_layout.addLayout(row5)


        tomolog_group.setLayout(tomolog_layout)
        right_layout.addWidget(tomolog_group, 2)

        main_layout.addLayout(right_layout, 4)
        self.setLayout(main_layout)

    def help_tomo(self):
        """Run the CLI `tomocupy recon -h` and show output in the GUI log."""
        name = "tomocupy-help"
        self.log_output.append(f"📖[{name}] tomocupy recon -h")

        p = QProcess(self)
        # Keep stdout/stderr separate so we see errors too
        p.setProcessChannelMode(QProcess.SeparateChannels)

        # Stream output to the log pane
        p.readyReadStandardOutput.connect(
            lambda: self.log_output.append(
                bytes(p.readAllStandardOutput()).decode(errors="ignore")
            )
        )
        p.readyReadStandardError.connect(
            lambda: self.log_output.append(
                bytes(p.readAllStandardError()).decode(errors="ignore")
            )
        )

        # Start/finish/error handling
        def _done(code, _status):
            try:
                self.process[:] = [(pp, nn) for (pp, nn) in self.process if pp is not p]
            except Exception:
                pass
            self.log_output.append(f"✅[{name}] done." if code == 0
                                else f"❌[{name}] failed with code {code}.")

        p.finished.connect(_done)
        p.errorOccurred.connect(
            lambda _err: self.log_output.append(f"❌[{name}] {p.errorString()}")
        )

        # Track so your existing Abort button can terminate it
        if not isinstance(self.process, list):
            self.process = []
        self.process.append((p, name))

        # --- CLI only (no python -m) ---
        p.start("tomocupy", ["recon", "-h"])


    def update_cmap(self):
        self.current_cmap = self.cmap_box.currentText()
        self.refresh_current_image()

    #change vmin vmax in plot
    def update_vmin_vmax(self):
        try:
            vmin = float(self.min_input.text()) if self.min_input.text() else None
        except ValueError:
            vmin = None
        try:
            vmax = float(self.max_input.text()) if self.max_input.text() else None
        except ValueError:
            vmax = None
        self.vmin = vmin
        self.vmax = vmax
        im = self.ax.images[0] if self.ax.images else None
        if im is not None and self.vmin is not None and self.vmax is not None:
            im.set_clim(self.vmin, self.vmax)
            self.canvas.draw_idle()
        else:
            self.refresh_current_image()

    #add refresh helper
    def refresh_current_image(self):
        if self.full_files and 0 <= self.slice_slider.value() < len(self.full_files):
            self.show_image(self.full_files[self.slice_slider.value()])
        elif self.preview_files and 0 <= self.slice_slider.value() < len(self.preview_files):
            self.show_image(self.preview_files[self.slice_slider.value()])

    # Highlight border on focus
    def highlight_editor(self, editor, event):
        editor.setStyleSheet("QTextEdit { border: 2px solid green; font-size: 12.5pt; }")
        self.active_editor = editor
        QTextEdit.focusInEvent(editor, event)

    def unhighlight_editor(self, editor, event):
        editor.setStyleSheet("QTextEdit { border: 1px solid gray; font-size: 12.5pt; }")
        QTextEdit.focusOutEvent(editor, event)

    # Event filter for scroll
    def eventFilter(self, obj, event):
        if obj == self.canvas and event.type() == QEvent.Wheel:
            step = 1 if event.angleDelta().y() > 0 else -1
            new_val = self.slice_slider.value() + step
            new_val = max(0, min(self.slice_slider.maximum(), new_val))
            self._keep_zoom = True
            self.slice_slider.setValue(new_val)
            return True
        return super().eventFilter(obj, event)

    # Utility methods
    def browse_data_folder(self):
        start_dir = self.data_path.text().strip() or os.path.expanduser("/")
        dialog = QFileDialog(self, "Select data folder")
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setDirectory(start_dir)    # <-- seed with last folder
        if dialog.exec():
            self.data_path.setText(dialog.selectedFiles()[0])
            self.refresh_h5_files()

    def refresh_h5_files(self):
        self.proj_file_box.clear()
        folder = self.data_path.text()
        if folder and os.path.isdir(folder):
            for f in sorted(glob.glob(os.path.join(folder, "*.h5"))):
                self.proj_file_box.addItem(os.path.basename(f), f)

    def load_config(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        if dialog.exec():
            fn = dialog.selectedFiles()[0]
            with open(fn, "r") as f:
                target = self.active_editor or self.config_editor_try
                target.setPlainText(f.read())

    def save_config(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        if dialog.exec():
            fn = dialog.selectedFiles()[0]
            text = (self.active_editor or self.config_editor_try).toPlainText()
            with open(fn, "w") as f:
                f.write(text)

    def abort_process(self):
        if not self.process:
            self.log_output.append("ℹ️[INFO] No running process.")
            return

        # Graceful terminate first
        for p, name in list(self.process):
            if p.state() != QProcess.NotRunning:
                p.terminate()

        # Force kill stragglers
        for p, name in list(self.process):
            if p.state() != QProcess.NotRunning:
                if not p.waitForFinished(2000):
                    p.kill()
                    p.waitForFinished(2000)
            self.log_output.append(f"⛔ [{name}] aborted.")

        self.process.clear()

    def _delete_when_done(self, path):
        """Remove a file when the *most recently started* process finishes."""
        if not path:
            return
        if not self.process:
            return
        p = self.process[-1][0]  # the QProcess you just started
        def _rm(*_):
            try:
                if os.path.exists(path):
                    os.remove(path)
                    self.log_output.append(f"🧹 Removed {path}")
            except Exception as e:
                self.log_output.append(f"⚠️ Could not remove {path}: {e}")
        p.finished.connect(_rm)


    def run_command_live(self, cmd, proj_file=None, job_label=None):
        """
        Start an external command without blocking the GUI.
        proj_file: full path to the .h5 (for log naming, optional)
        job_label: e.g., 'recon-try', 'recon-full', 'tomolog' (optional)
        """
        # Build a readable job name for logs
        scan_id = None
        if proj_file:
            try:
                base = os.path.splitext(os.path.basename(proj_file))[0]
                scan_id = base[-4:]  # your convention
            except Exception:
                scan_id = None

        if job_label is None:
            job_label = "job"
        name = f"{job_label}-{scan_id}" if scan_id else job_label

        cli_str = " ".join(map(str, cmd))
        self.log_output.append(f"🚀 [{name}] start: {cli_str}")
        QApplication.processEvents()

        p = QProcess(self)
        p.setProcessChannelMode(QProcess.ForwardedChannels)

        # Cleanup on finish
        def on_finished(code, status):
            try:
                self.process[:] = [(pp, nn) for (pp, nn) in self.process if pp is not p]
            except Exception:
                pass
            if code == 0:
                self.log_output.append(f"✅ [{name}] finished.")
            else:
                self.log_output.append(f"❌ [{name}] failed with code {code}.")

        p.finished.connect(on_finished)

        # Track it so Abort can find it
        self.process.append((p, name))
        p.start(str(cmd[0]), [str(a) for a in cmd[1:]])


    def try_reconstruction(self):
        proj_file = self.proj_file_box.currentData()
        if not proj_file:
            self.log_output.append(f"❌ No file")
            return
        cor_val = self.cor_input.text().strip() #get user input rotation axis guess
        try:
            cor = float(cor_val)
        except ValueError:
            self.log_output.append(f"❌ wrong rotation axis input")
        config_text = self.config_editor_try.toPlainText()
        temp_try = os.path.join(self.data_path.text(), "temp_try.conf")
        with open(temp_try, "w") as f:
            f.write(config_text)
        cmd = ["tomocupy", "recon", 
               "--reconstruction-type", "try", 
               "--config", temp_try, 
               "--file-name", proj_file,
               "--rotation-axis", str(cor)]
        self.run_command_live(cmd, proj_file=proj_file, job_label="Try recon")
        self._delete_when_done(temp_try)

    def full_reconstruction(self):
        proj_file = self.proj_file_box.currentData()
        try:
            cor_value = float(self.cor_input_full.text())
        except ValueError:
            self.log_output.append("❌[ERROR] Invalid Full COR value.")
            return
        config_text = self.config_editor_full.toPlainText()
        temp_full = os.path.join(self.data_path.text(), "temp_full.conf")
        with open(temp_full, "w") as f:
            f.write(config_text)
        cmd = ["tomocupy", "recon",
               "--reconstruction-type", "full",
               "--config", temp_full, 
               "--file-name", proj_file, 
               "--rotation-axis", str(cor_value)]
        self.run_command_live(cmd, proj_file=proj_file, job_label="Full recon")
        self._delete_when_done(temp_full)
        self.view_btn.setEnabled(True)

    def batch_try_reconstruction(self):
            try:
                start_num = int(self.start_scan_input.text())
                end_num = int(self.end_scan_input.text())
            except ValueError:
                self.log_output.append("❌[ERROR] Invalid start or end scan number.")
                return

            folder = self.data_path.text()
            if not os.path.isdir(folder):
                self.log_output.append("❌[ERROR] Invalid data folder.")
                return

            config_text = self.config_editor_try.toPlainText()
            temp_try = os.path.join(folder, "temp_batch_try.conf")
            with open(temp_try, "w") as f:
                f.write(config_text)

            for scan_num in range(start_num, end_num + 1):
                scan_str = f"{scan_num:04d}"
                match_files = glob.glob(os.path.join(folder, f"*{scan_str}.h5"))
                if not match_files:
                    self.log_output.append(f"⚠️[WARN] No file found for scan {scan_str}, skipping.")
                    continue
                proj_file = match_files[0]

                cmd = ["tomocupy", "recon", 
                       "--reconstruction-type", "try", 
                       "--config", temp_try, 
                       "--file-name", proj_file]
                self.run_command_live(cmd, proj_file=proj_file, job_label='batch try')
                #do not need to delete conf file because we use the same one
                self.log_output.append(f"✅Finish try recon {proj_file}")
            self.log_output.append("✅Done all try")

    def batch_full_reconstruction(self):
        log_file = os.path.join(self.data_path.text(), "cor_log.json")
        if not os.path.exists(log_file):
            return
        with open(log_file) as f:
            data = json.load(f)
        temp_conf = os.path.join(self.data_path.text(), "temp_batch_full.conf")
        with open(temp_conf, "w") as f:
            f.write(self.config_editor_full.toPlainText())
        for entry in data:
            proj_file, cor_value = entry["filename"], entry["center"]
            cmd = ["tomocupy", "recon", 
                   "--reconstruction-type", "full", 
                   "--config", temp_conf, 
                   "--file-name", proj_file, 
                   "--rotation-axis", str(cor_value)]
            self.run_command_live(cmd, proj_file=proj_file, job_label="batch full")
            #do not need to delete conf file because we use the same one
            self.log_output.append(f"✅Finish full recon {proj_file}")
        self.log_output.append("✅Done all full")

    def record_cor_to_json(self):
        # Get data folder and current COR value
        data_folder = self.data_path.text().strip()
        cor_value = self.cor_input_full.text().strip()
        proj_file = self.proj_file_box.currentData()

        if not (data_folder and cor_value and proj_file):
            self.log_output.append("⚠️[WARNING] Missing data folder, COR, or projection file.")
            return

        try:
            cor_value = float(cor_value)
        except ValueError:
            self.log_output.append("❌[ERROR] COR value is not a valid number.")
            return

        # JSON file path
        json_path = os.path.join(data_folder, "rot_cen.json")

        # Load or create JSON data
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                try:
                    cor_data = json.load(f)
                    fns = list(cor_data.keys())
                except json.JSONDecodeError:
                    cor_data = {}
        else:
            cor_data = {}
        if proj_file in fns:
            overfn_msg_box = QMessageBox(self)
            overfn_msg_box.setIcon(QMessageBox.Warning)
            overfn_msg_box.setWindowTitle("Overwrite Existing files in log?")
            overfn_msg_box.setText(f"The scan:\n{os.path.basename(proj_file)}\nalready exists in rot_cen.json.\n\nDo you want to overwrite it?")
            overfn_msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            overfn_msg_box.setDefaultButton(QMessageBox.No)
            result = overfn_msg_box.exec()
            if result != QMessageBox.Yes:
                self.log_output.append("⚠️Not take COR")
                return
                
        # Add/Update entry
        cor_data[proj_file] = cor_value

        # Save JSON
        with open(json_path, "w") as f:
            json.dump(cor_data, f, indent=2)

        self.log_output.append(f"✅[INFO] COR recorded for: {proj_file}")

        # Update COR log box
        self.cor_json_output.clear()
        for k, v in cor_data.items():
            base = os.path.splitext(os.path.basename(k))[0]
            last4 = base[-4:]
            self.cor_json_output.append(f"{last4} : {v}")

    def load_cor_to_jsonbox(self): #load rot_cen.json file to COR box in GUI
        data_folder = self.data_path.text().strip()
        json_path = os.path.join(data_folder, "rot_cen.json")

        if not os.path.exists(json_path):
            self.log_output.append("⚠️[WARNING] rot_cen.json not found in data folder.")
            return

        try:
            with open(json_path, "r") as f:
                cor_data = json.load(f)
            self.cor_json_output.clear()
            for k, v in cor_data.items():
                base = os.path.splitext(os.path.basename(k))[0]
                last4 = base[-4:]
                self.cor_json_output.append(f"{last4} : {v}")
            self.log_output.append("✅[INFO] COR log reloaded.")
        except Exception as e:
            self.log_output.append(f"❌[ERROR] Failed to load COR log: {e}")

    # ==== Viewing ====
    def view_try_reconstruction(self):
        data_folder = self.data_path.text().strip()
        proj_file = self.proj_file_box.currentData()
        proj_name = os.path.splitext(os.path.basename(proj_file))[0]
        try_dir = os.path.join(f"{data_folder}_rec", "try_center", proj_name)
        self.preview_files = sorted(glob.glob(os.path.join(try_dir, "*.tiff")))
        if not self.preview_files:
            self.log_output.append(f"❌No try folder")
            return
        self._keep_zoom = False # reset zoom state
        self._clear_roi()  # clear any existing ROI
        self.set_image_scale(self.preview_files[0])
        try:
            self.slice_slider.valueChanged.disconnect()
        except TypeError:
            pass
        self.slice_slider.setMaximum(len(self.preview_files) - 1)
        self.slice_slider.valueChanged.connect(self.update_try_slice)
        self.update_try_slice()

    def view_full_reconstruction(self):
        data_folder = self.data_path.text().strip()
        proj_file = self.proj_file_box.currentData()
        proj_name = os.path.splitext(os.path.basename(proj_file))[0]
        full_dir = os.path.join(f"{data_folder}_rec", f"{proj_name}_rec")  # ✅ match actual location

        self.full_files = sorted(glob.glob(os.path.join(full_dir, "*.tiff")))
        if not self.full_files:
            self.log_output.append("⚠️ No full reconstruction images found.")
            return
        self._keep_zoom = False # reset zoom state
        self._clear_roi()  # clear any existing ROI
        self.set_image_scale(self.full_files[0])
        try:
            self.slice_slider.valueChanged.disconnect()
        except TypeError:
            pass
        self.slice_slider.setMaximum(len(self.full_files) - 1)
        self.slice_slider.valueChanged.connect(self.update_full_slice)
        self.update_full_slice()

    def set_image_scale(self, img_path):
        img = np.array(Image.open(img_path))
        self.vmin, self.vmax = round(img.min(),5), round(img.max(),5) 
        self.min_input.setText(str(self.vmin))
        self.max_input.setText(str(self.vmax))

    #draw box for auto contrast
    def draw_box(self):
        """Enable interactive ROI drawing. Drag to create; click to finish."""
        if self._current_img is None:
            self.log_output.append("⚠️ No image loaded to draw box.")
            return

        # (Re)create selector if needed
        if self.rect_selector is None:
            style = dict(edgecolor='red', facecolor='none', linewidth=2, alpha=1.0)
            self.rect_selector = RectangleSelector(
                self.ax,
                self._on_rect_complete,     # callback on release
                useblit=True,
                button=[1],                 # left mouse
                minspanx=2, minspany=2,
                spancoords='data',
                interactive=True,
                props=style
            )
        self._drawing_roi = True
        self.roi_extent = None
        self.rect_selector.set_active(True)
        self.log_output.append("Drag to draw ROI, release to set. Any click on image will hide ROI.")

    #This is the ROI-complete & click-to-hide handler
    def _on_rect_complete(self, eclick, erelease):
        """Store ROI extents when user finishes dragging the rectangle."""
        x0, y0 = eclick.xdata, eclick.ydata
        x1, y1 = erelease.xdata, erelease.ydata
        if None in (x0, y0, x1, y1):
            self.roi_extent = None
            self._drawing_roi = False
            return
        # normalize to (min,max)
        self.roi_extent = (min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1))
        self._drawing_roi = False
        self.log_output.append(
            f"ROI set: x[{int(self.roi_extent[0])}:{int(self.roi_extent[1])}], "
            f"y[{int(self.roi_extent[2])}:{int(self.roi_extent[3])}]"
        )

    def _clear_roi(self):
        """Hide/remove any active ROI."""
        try:
            if self.rect_selector is not None:
                # deactivate and hide selector
                try:
                    self.rect_selector.set_active(False)
                    if hasattr(self.rect_selector, "set_visible"):
                        self.rect_selector.set_visible(False)
                except Exception:
                    pass
                self.rect_selector = None
        finally:
            self.roi_extent = None
            # no need to redraw here; show_image will draw


    def _on_canvas_click(self, event):
        """Any click on the image hides/removes the ROI (unless we are mid-draw)."""
        if event.inaxes != self.ax:
            return
        if self._drawing_roi:
            return  # ignore the release/extra clicks during drawing
        if self.roi_extent is None and self.rect_selector is None:
            return

        # hide selector & clear ROI
        try:
            if self.rect_selector is not None:
                self.rect_selector.set_active(False)
                # hide selector artists if present (version-dependent)
                for art in getattr(self.rect_selector, 'artists', []):
                    art.set_visible(False)
                self.rect_selector = None
        except Exception:
            pass
        self.roi_extent = None
        self.canvas.draw_idle()
        self.log_output.append("ROI cleared.")



    #auto contrast function
    def auto_img_contrast(self, saturation=10):
        """Fiji-like Auto: trims tails within current window; uses ROI if present; never edits pixels."""
        if self._current_img is None:
            self.log_output.append("⚠️ No image loaded to auto contrast.")
            return

        img = self._current_img

        # ROI slice if available
        if self.roi_extent is not None:
            x0, x1, y0, y1 = self.roi_extent
            h, w = img.shape[:2]
            # clamp & cast to indices
            x0 = max(0, min(w, int(np.floor(x0))))
            x1 = max(0, min(w, int(np.ceil(x1))))
            y0 = max(0, min(h, int(np.floor(y0))))
            y1 = max(0, min(h, int(np.ceil(y1))))
            if x1 <= x0 or y1 <= y0:
                self.log_output.append("⚠️ ROI too small.")
                return
            data = img[y0:y1, x0:x1]
        else:
            data = img

        a = np.asarray(data, dtype=float).ravel()
        a = a[np.isfinite(a)]
        if a.size == 0:
            self.log_output.append("⚠️ No finite pixels for Auto.")
            return

        #sat = float(saturation)
        #sat_pct = sat * 100.0 if sat < 0.01 else sat
        #per_tail = sat_pct / 2.0

        # current window
        vmin = self.vmin if self.vmin is not None else float(np.nanmin(a))
        vmax = self.vmax if self.vmax is not None else float(np.nanmax(a))
        vis = a[(a >= vmin) & (a <= vmax)]
        if vis.size < 64:
            vis = a

        lo, hi = np.nanpercentile(vis, [3,97]) #hard coded to 3%
        if not np.isfinite(lo) or not np.isfinite(hi) or lo >= hi:
            lo, hi = float(np.nanmin(vis)), float(np.nanmax(vis))
            if lo >= hi:
                hi = lo + 1.0

        new_vmin, new_vmax = float(round(lo, 5)), float(round(hi, 5))
        if (new_vmin, new_vmax) == (self.vmin, self.vmax):
            self.log_output.append("Auto B&C optimal.")
            return

        self.vmin, self.vmax = new_vmin, new_vmax

        # update inputs (avoid signal loops if you later connect them to refresh)
        self.min_input.setText(str(self.vmin))
        self.max_input.setText(str(self.vmax))

        # >>> IMPORTANT: update clim on existing artist instead of reloading image
        im = self.ax.images[0] if self.ax.images else None
        if im is not None:
            im.set_clim(self.vmin, self.vmax)
            self.canvas.draw_idle()
        else:
            # if no image artist (shouldn't happen), fall back
            self.refresh_current_image()

    def reset_img_contrast(self):
        if self._current_img is not None:
            self._current_img = self._safe_open_image(self._current_img_path)
            self.vmin, self.vmax = round(self._current_img.min(), 5), round(self._current_img.max(), 5)
            self.min_input.setText(str(self.vmin))
            self.max_input.setText(str(self.vmax))
            self.refresh_current_image()
        else:
            self.log_output.append("⚠️ No image loaded to reset contrast.")

    def update_try_slice(self):
        self._keep_zoom = True  # keep zoom state
        idx = self.slice_slider.value()
        if 0 <= idx < len(self.preview_files):
            self.show_image(self.preview_files[idx])

    def update_full_slice(self):
        self._keep_zoom = True  # keep zoom state
        idx = self.slice_slider.value()
        if 0 <= idx < len(self.full_files):
            self.show_image(self.full_files[idx])

    def _safe_open_image(self, path, retries=3):
        for _ in range(retries):
            try:
                with Image.open(path) as im:
                    return np.array(im)
            except Exception:
                QApplication.processEvents()
        with Image.open(path) as im:
            return np.array(im)

    def show_image(self, img_path):
        img = self._safe_open_image(img_path)
        if img.ndim == 3:
            img = img[..., 0]
        h, w = img.shape
        self._current_img = img
        self._current_img_path = img_path

        # --- clear ROI whenever a new image is drawn ---
        self._clear_roi()

        # clear axes and draw the image
        self.ax.clear()
        im = self.ax.imshow(
            img,
            cmap=self.current_cmap,
            vmin=self.vmin,
            vmax=self.vmax,
            origin="upper"
        )
        self.ax.set_title(os.path.basename(img_path), pad=5)
        self.ax.set_aspect('equal')

        # --- zoom policy ---
        # keep zoom only if same image shape AND we explicitly asked to keep it
        if (self._keep_zoom and
            self._last_image_shape == (h, w) and
            self._last_xlim is not None and
            self._last_ylim is not None):
            self.ax.set_xlim(self._last_xlim)
            self.ax.set_ylim(self._last_ylim)
        else:
            # reset to full image extents
            left, right, bottom, top = im.get_extent()
            self.ax.set_xlim(left, right)
            self.ax.set_ylim(top, bottom)

        self.fig.tight_layout()
        self.canvas.draw_idle()

        # remember current zoom for next time
        self._last_xlim = self.ax.get_xlim()
        self._last_ylim = self.ax.get_ylim()
        self._last_image_shape = (h, w)

    def _remember_view(self):
        """Record current view so the next image keeps the same zoom/pan."""
        try:
            self._last_xlim = self.ax.get_xlim()
            self._last_ylim = self.ax.get_ylim()
            if self._current_img is not None:
                self._last_image_shape = self._current_img.shape
        except Exception:
            pass

    def _nav_oneshot_release(self, event):
        """After a zoom-rect or pan ends, remember view and auto-disable the tool."""
        if event.inaxes != self.ax:
            return
        # Only left-button releases should toggle tools off
        try:
            if event.button != MouseButton.LEFT:
                return
        except Exception:
            pass

        mode = getattr(self.toolbar, "mode", "")
        if mode in ("zoom rect", "pan/zoom"):
            # 1) remember current view so scrolling slices keeps it
            self._remember_view()
            self._keep_zoom = True

            # 2) turn the tool off (one-shot)
            try:
                if mode == "zoom rect":
                    self.toolbar.zoom()  # toggles off
                else:
                    self.toolbar.pan()   # toggles off
            except Exception:
                pass

            # 3) clear any status text & restore cursor (nice-to-have)
            try:
                self.toolbar.set_message("")
            except Exception:
                pass
            try:
                self.canvas.setCursor(Qt.ArrowCursor)
            except Exception:
                pass



    def get_note_value(self): # for tomolog note
        note = self.note_input.text().strip()
        return f'"{note}"' if note else None

    def help_tomolog(self):
            """Run the CLI `tomolog run -h` and show output in the GUI log."""
            name = "tomolog-help"
            self.log_output.append(f"📖[{name}] tomocupy run -h")

            p = QProcess(self)
            # Keep stdout/stderr separate so we see errors too
            p.setProcessChannelMode(QProcess.SeparateChannels)

            # Stream output to the log pane
            p.readyReadStandardOutput.connect(
                lambda: self.log_output.append(
                    bytes(p.readAllStandardOutput()).decode(errors="ignore")
                )
            )
            p.readyReadStandardError.connect(
                lambda: self.log_output.append(
                    bytes(p.readAllStandardError()).decode(errors="ignore")
                )
            )

            # Start/finish/error handling
            def _done(code, _status):
                try:
                    self.process[:] = [(pp, nn) for (pp, nn) in self.process if pp is not p]
                except Exception:
                    pass
                self.log_output.append(f"✅[{name}] done." if code == 0
                                    else f"❌[{name}] failed with code {code}.")

            p.finished.connect(_done)
            p.errorOccurred.connect(
                lambda _err: self.log_output.append(f"❌[{name}] {p.errorString()}")
            )

            # Track so your existing Abort button can terminate it
            if not isinstance(self.process, list):
                self.process = []
            self.process.append((p, name))

            # --- CLI only (no python -m) ---
            p.start("tomolog", ["run", "-h"])


    def run_tomolog(self):
        beamline = self.beamline_box.currentText()
        cloud = self.cloud_box.currentText()
        url = self.url_input.text().strip()
        x = self.x_input.text().strip()
        y = self.y_input.text().strip()
        z = self.z_input.text().strip()
        scan_number = self.scan_input.text().strip()
        data_folder = self.data_path.text().strip()
        vmin = self.min_input.text().strip()
        vmax = self.max_input.text().strip()
        if not data_folder:
            self.log_output.append("❌[ERROR] Data folder not set.")
            return
        flist = []
        if not scan_number:
            fn = self.proj_file_box.currentText()
            filename = os.path.join(data_folder, f"{fn}")
            flist.append(filename)
            if not filename:
                self.log_output.append("❌[ERROR] Filename not exist.")
                return
        else:
            numbers = set()
            sns = scan_number.split(",")
            for sn in sns:
                if "-" in sn:
                    try:
                        start, end = map(int, sn.split("-"))
                        numbers.update(range(start, end+1))
                    except ValueError:
                        self.log_output.append("❌[ERROR] Invalid range: {sn}")
                else: #single number input
                    try:
                        numbers.add(int(sn))
                    except ValueError:
                        self.log_output.append("❌[ERROR] Invalid scan number: {sn}")
            for n in numbers:
                fn = os.path.join(data_folder,f"*{n}.h5")
                try:
                    filename = glob.glob(fn)[0]
                except IndexError:
                    self.log_output.append(f"Scan {n} not exist, stop")
                    break
                flist.append(filename)
        note_value = self.get_note_value()
        for input_fn in flist:
            cmd = [
                "tomolog", "run",
                "--beamline", beamline,
                "--file-name", input_fn,
                "--cloud", cloud,
                "--presentation-url", url,
                "--idx", x,
                "--idy", y,
                "--idz", z,
                "--note", note_value
            ]
            if vmin != "":
                cmd.extend(["--min", vmin])
            if vmax != "":
                cmd.extend(["--max", vmax])
            extra_params = self.extra_params_input.text().strip()
            if extra_params:
                cmd.extend(extra_params.split())
            # Run the command
            self.log_output.append(f">>> Running Tomolog: {' '.join(cmd)}")
            QApplication.processEvents()  # Force UI to update before running the process
            try:
                self.run_command_live(cmd, proj_file=input_fn, job_label="tomolog")
                self.log_output.append(f"✅ Tomolog finished successfully with scan {input_fn}")
            except subprocess.CalledProcessError as e:
                self.log_output.append(f"❌[ERROR] Tomolog failed with code {e.returncode}")
            except Exception as e:
                self.log_output.append(f"❌[ERROR] Failed to run Tomolog: {e}")





if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = TomoCuPyGUI()
    gui.show()
    sys.exit(app.exec())
