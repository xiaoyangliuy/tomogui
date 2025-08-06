import sys, os, glob, json, subprocess
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QTextEdit, QLineEdit, QLabel, QProgressBar,
    QComboBox, QSlider, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, QEvent
from PIL import Image


class TomoCuPyGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TomoCuPy Reconstruction GUI")
        self.resize(1650, 950)

        # State
        self.default_cmap = "gray"
        self.current_cmap = self.default_cmap
        self.vmin = None
        self.vmax = None
        self.preview_files = []
        self.full_files = []
        self.process = None

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
        left_layout.addLayout(proj_layout)

        # Rotation axis + Refresh + Abort
        cor_layout = QHBoxLayout()
        self.cor_input = QLineEdit()
        cor_layout.addWidget(QLabel("Center of Rotation:"))
        cor_layout.addWidget(self.cor_input)
        refresh_btn2 = QPushButton("Refresh")
        refresh_btn2.clicked.connect(self.refresh_h5_files)
        abort_btn = QPushButton("Abort")
        abort_btn.clicked.connect(self.abort_process)
        cor_layout.addWidget(refresh_btn2)
        cor_layout.addWidget(abort_btn)
        left_layout.addLayout(cor_layout)

        # Load/Save Config buttons
        config_btn_layout = QHBoxLayout()
        load_config_btn = QPushButton("Load Config")
        save_config_btn = QPushButton("Save Config")
        load_config_btn.clicked.connect(self.load_config)
        save_config_btn.clicked.connect(self.save_config)
        config_btn_layout.addWidget(load_config_btn)
        config_btn_layout.addWidget(save_config_btn)
        left_layout.addLayout(config_btn_layout)

        # Try and Full config boxes
        config_frame_layout = QHBoxLayout()

        # Try config group
        left_config_group = QGroupBox("Config for Try Reconstruction")
        left_config_layout = QVBoxLayout()
        self.config_editor_try = QTextEdit()
        self.config_editor_try.setFixedHeight(300)
        self.config_editor_try.setStyleSheet("QTextEdit { border: 1px solid gray; }")
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
        self.config_editor_full.setStyleSheet("QTextEdit { border: 1px solid gray; }")
        self.config_editor_full.focusInEvent = lambda event: self.highlight_editor(self.config_editor_full, event)
        self.config_editor_full.focusOutEvent = lambda event: self.unhighlight_editor(self.config_editor_full, event)
        right_config_layout.addWidget(self.config_editor_full)

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
        log_json_layout.addLayout(log_box_layout, 5)
        json_box_layout = QVBoxLayout()
        json_box_layout.addWidget(QLabel("COR Log File:"))
        self.cor_json_output = QTextEdit()
        self.cor_json_output.setReadOnly(True)
        json_box_layout.addWidget(self.cor_json_output)
        log_json_layout.addLayout(json_box_layout, 3)
        left_layout.addLayout(log_json_layout)

        main_layout.addLayout(left_layout, 3.5)

        # Right panel
        right_layout = QVBoxLayout()
        toolbar_row = QHBoxLayout()
        self.fig = Figure(figsize=(5, 5))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)
        toolbar_row.addWidget(self.toolbar)
        

        # Colormap dropdown
        toolbar_row.addWidget(QLabel("Colormap:"))
        self.cmap_box = QComboBox()
        self.cmap_box.addItems(["gray", "viridis", "plasma", "inferno", "magma", "cividis"])
        self.cmap_box.setCurrentText(self.default_cmap)
        self.cmap_box.currentIndexChanged.connect(self.update_cmap)
        toolbar_row.addWidget(self.cmap_box)

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
        tomolog_group.setLayout(tomolog_layout)
        right_layout.addWidget(tomolog_group, 2)

        main_layout.addLayout(right_layout, 4)
        self.setLayout(main_layout)


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
        self.refresh_current_image()

    #add refresh helper
    def refresh_current_image(self):
        if self.full_files and 0 <= self.slice_slider.value() < len(self.full_files):
            self.show_image(self.full_files[self.slice_slider.value()])
        elif self.preview_files and 0 <= self.slice_slider.value() < len(self.preview_files):
            self.show_image(self.preview_files[self.slice_slider.value()])


    # Highlight border on focus
    def highlight_editor(self, editor, event):
        editor.setStyleSheet("QTextEdit { border: 2px solid green; }")
        QTextEdit.focusInEvent(editor, event)

    def unhighlight_editor(self, editor, event):
        editor.setStyleSheet("QTextEdit { border: 1px solid gray; }")
        QTextEdit.focusOutEvent(editor, event)

    # Event filter for scroll
    def eventFilter(self, obj, event):
        if obj == self.canvas and event.type() == QEvent.Wheel:
            step = 1 if event.angleDelta().y() > 0 else -1
            new_val = self.slice_slider.value() + step
            new_val = max(0, min(self.slice_slider.maximum(), new_val))
            self.slice_slider.setValue(new_val)
            return True
        return super().eventFilter(obj, event)

    # Utility methods
    def browse_data_folder(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
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
            with open(fn) as f:
                if self.config_editor_full.hasFocus():
                    self.config_editor_full.setPlainText(f.read())
                else:
                    self.config_editor_try.setPlainText(f.read())

    def save_config(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        if dialog.exec():
            fn = dialog.selectedFiles()[0]
            if self.config_editor_full.hasFocus():
                text = self.config_editor_full.toPlainText()
            else:
                text = self.config_editor_try.toPlainText()
            with open(fn, "w") as f:
                f.write(text)

    def abort_process(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.kill()
            except:
                pass
            self.log_output.append("✅[INFO] Process aborted.")
            self.process = None

    def run_command_live(self, cmd, mode=""):
        cli_str = " ".join(map(str, cmd))
        proj_file = self.proj_file_box.currentData()
        if proj_file:
            scan_id = os.path.splitext(os.path.basename(proj_file))[0][-4:]
        self.log_output.append(f">>> Running command: {cli_str}")
        QApplication.processEvents()  # ✅ Force UI to update before running the process
        try:
            self.process = subprocess.run(cmd)
            self.process.wait()
            if self.process.returncode == 0:
                self.log_output.append(f"✅[INFO] try center scan {scan_id} successfully")
            else:
                self.log_output.append(f"❌[ERROR] try center scan {scan_id} failed (code {self.process.returncode})")
        except Exception as e:
            self.log_output.append(f"❌[ERROR] Failed to run try scan {scan_id}: {e}")
        finally:
            self.process = None

    def try_reconstruction(self):
        proj_file = self.proj_file_box.currentData()
        if not proj_file:
            return
        config_text = self.config_editor_try.toPlainText()
        temp_conf = os.path.join(self.data_path.text(), "temp_try.conf")
        with open(temp_conf, "w") as f:
            f.write(config_text)
        self.run_command_live(
            ["tomocupy", "recon", "--recon-type", "try", "--config", temp_conf, "--file-name", proj_file]
        )

    def full_reconstruction(self):
        proj_file = self.proj_file_box.currentData()
        try:
            cor_value = float(self.cor_input_full.text())
        except ValueError:
            self.log_output.append("❌[ERROR] Invalid Full COR value.")
            return
        config_text = self.config_editor_full.toPlainText()
        temp_conf = os.path.join(self.data_path.text(), "temp_full.conf")
        with open(temp_conf, "w") as f:
            f.write(config_text)
        self.run_command_live(
            ["tomocupy", "recon","--recon-type", "full","--config", temp_conf, "--file-name", proj_file, "--rotation-axis", str(cor_value)]
        )
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
        temp_conf = os.path.join(folder, "temp_batch_try.conf")
        with open(temp_conf, "w") as f:
            f.write(config_text)
        for scan_num in range(start_num, end_num + 1):
            scan_str = f"{scan_num:04d}"
            match_files = glob.glob(os.path.join(folder, f"*{scan_str}.h5"))
            if not match_files:
                self.log_output.append(f"⚠️[WARN] No file found for scan {scan_str}, skipping.")
                continue
            proj_file = match_files[0]
            self.run_command_live(
                ["tomocupy", "recon", "--recon-type", "try", "--config", temp_conf, "--file-name", proj_file]
            )

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
            temp_conf = os.path.join(folder, "temp_batch_try.conf")
            with open(temp_conf, "w") as f:
                f.write(config_text)

            for scan_num in range(start_num, end_num + 1):
                scan_str = f"{scan_num:04d}"
                match_files = glob.glob(os.path.join(folder, f"*{scan_str}.h5"))
                if not match_files:
                    self.log_output.append(f"⚠️[WARN] No file found for scan {scan_str}, skipping.")
                    continue
                proj_file = match_files[0]
                self.run_command_live(
                    ["tomocupy", "recon", "--recon-type", "try", "--config", temp_conf, "--file-name", proj_file],
                    mode=f"Batch Try {scan_str}"
                )

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
            self.run_command_live(
                ["tomocupy", "recon", "--recon-type", "full", "--config", temp_conf, "--file-name", proj_file, "--rotation-axis", str(cor_value)],
            )

    # ==== Viewing ====
    def view_try_reconstruction(self):
        data_folder = self.data_path.text().strip()
        proj_file = self.proj_file_box.currentData()
        proj_name = os.path.splitext(os.path.basename(proj_file))[0]
        try_dir = os.path.join(f"{data_folder}_rec", "try_center", proj_name)
        self.preview_files = sorted(glob.glob(os.path.join(try_dir, "*.tiff")))
        if not self.preview_files:
            return
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
        if self.vmin is None or self.vmax is None:
            self.vmin, self.vmax = float(img.min()), float(img.max())
            self.min_input.setText(str(self.vmin))
            self.max_input.setText(str(self.vmax))


    def update_try_slice(self):
        idx = self.slice_slider.value()
        if 0 <= idx < len(self.preview_files):
            self.show_image(self.preview_files[idx])

    def update_full_slice(self):
        idx = self.slice_slider.value()
        if 0 <= idx < len(self.full_files):
            self.show_image(self.full_files[idx])

    
    def show_image(self, img_path):
        img = np.array(Image.open(img_path))
        if img.ndim == 3:
            img = img[..., 0]
        height, width = img.shape

        # Save current zoom state
        try:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
        except AttributeError:
            xlim, ylim = (0, width), (height, 0)

        self.ax.clear()

        self.ax.imshow(
            img,
            cmap=self.current_cmap,
            vmin=self.vmin,
            vmax=self.vmax,
            origin="upper"
        )
        self.ax.set_title(os.path.basename(img_path), pad=5)

        # Keep pixels square like ImageJ
        self.ax.set_aspect('equal')

        # Restore zoom if it’s not the very first image
        if (0 <= xlim[0] < xlim[1] <= width and
            0 <= ylim[1] < ylim[0] <= height and
            (xlim, ylim) != ((0, width), (height, 0))):
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)

        self.canvas.draw()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = TomoCuPyGUI()
    gui.show()
    sys.exit(app.exec())
