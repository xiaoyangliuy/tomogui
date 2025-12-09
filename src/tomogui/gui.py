import os, glob, json
import numpy as np
import matplotlib
import importlib.resources
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QTextEdit, QLineEdit, QLabel, QProgressBar,
    QComboBox, QSlider, QGroupBox, QSizePolicy, QMessageBox,
    QTabWidget, QFormLayout, QCheckBox, QSpinBox, QDoubleSpinBox,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QEvent, QProcess, QEventLoop, QSize, QProcessEnvironment
from PyQt5.QtGui import QColor

from PIL import Image
from matplotlib.widgets import RectangleSelector
from matplotlib.backend_bases import MouseButton
from mpl_toolkits.axes_grid1 import make_axes_locatable
import h5py, json
from datetime import datetime

from .theme_manager import ThemeManager
from .hdf5_viewer import HDF5ImageDividerDialog

# Load matplotlib style from package resources
matplotlib.rcdefaults()
try:
    with importlib.resources.path('tomo_gui.styles', 'tomoGUI_mpl_format.mplstyle') as style_path:
        matplotlib.style.use(str(style_path))
except (ImportError, FileNotFoundError):
    # Fallback if style file is not found
    pass


class TomoGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TomoGUI")
        self.resize(1650, 950)

        # Initialize theme manager (will apply theme after UI is built)
        self.theme_manager = ThemeManager()
        self.theme_manager.register_callback(self._on_theme_changed)

        # State
        self.default_cmap = "gray"
        self.current_cmap = self.default_cmap
        self.vmin = None
        self.vmax = None
        self.preview_files = []
        self.full_files = []
        self.process = []
        self._current_img = None
        self._current_img_path = None
        self.cor_data = {}

        # Batch selection state for shift-click
        self.batch_last_clicked_row = None

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

        # recon/recon_step + Rotation axis method + input guess COR + config buttons
        #cor_layout = QHBoxLayout()

        '''
        #======================original method=========================
        self.recon_way_box = QComboBox()
        self.recon_way_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.recon_way_box.addItems(["recon","recon_steps"])
        self.recon_way_box.setCurrentIndex(0) # make recon as default
        cor_layout.addWidget(self.recon_way_box)

        cor_layout.addWidget(QLabel("COR method"))
        self.cor_method_box = QComboBox()
        self.cor_method_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cor_method_box.addItems(["auto","manual"])
        self.cor_method_box.setCurrentIndex(1) # make manual as default
        cor_layout.addWidget(self.cor_method_box)

        self.cor_input = QLineEdit()
        cor_layout.addWidget(QLabel("COR:"))
        cor_layout.addWidget(self.cor_input)
        
        load_config_btn = QPushButton("Load Config")
        save_config_btn = QPushButton("Save Config")
        load_config_btn.clicked.connect(self.load_config)
        save_config_btn.clicked.connect(self.save_config)
        cor_layout.addWidget(load_config_btn)
        cor_layout.addWidget(save_config_btn)
        '''
        #view_prj_btn = QPushButton("View raw")
        #view_prj_btn.clicked.connect(self.view_raw)
        #cor_layout.addWidget(view_prj_btn)

        #help_tomo_btn = QPushButton("help")
        #help_tomo_btn.clicked.connect(self.help_tomo)
        #cor_layout.addWidget(help_tomo_btn)

        #abort_btn = QPushButton("Abort")
        #abort_btn.clicked.connect(self.abort_process)
        #abort_btn.setStyleSheet("color: red;")
        #cor_layout.addWidget(abort_btn)
        #left_layout.addLayout(cor_layout)

        # ==== TABS (Configs + Params) ====
        self.tabs = QTabWidget()
        left_layout.addWidget(self.tabs)

        # Tab 1: Configs (contains two existing config editors)
        first_tab = QWidget()
        #configs_v = QVBoxLayout(configs_tab)
        #self._config_frame_layout = QHBoxLayout()
        #configs_v.addLayout(self._config_frame_layout)
        self.tabs.addTab(first_tab, "Main")

        #==========main tab may===================
        main_tab = QVBoxLayout(first_tab)
        main_rows = QHBoxLayout()
        main_rows.setSpacing(5)
        #left frame for Try
        try_box = QGroupBox("Try Reconstruction")
        try_form = QFormLayout()
        #left - row 1
        try_cuda_layout = QHBoxLayout()
        try_cuda_layout.addWidget(QLabel("Recon method"))
        self.recon_way_box = QComboBox()
        self.recon_way_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.recon_way_box.addItems(["recon","recon_steps"])
        self.recon_way_box.setCurrentIndex(0) # make recon as default
        try_cuda_layout.addWidget(self.recon_way_box)
        try_cuda_layout.addWidget(QLabel("cuda"))
        self.cuda_box_try = QComboBox()
        self.cuda_box_try.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cuda_box_try.addItems(["0","1"])
        self.cuda_box_try.setCurrentIndex(0) # make cuda 0 as default
        try_cuda_layout.addWidget(self.cuda_box_try)
        try_form.addRow(try_cuda_layout)
        #row 2
        self.cor_method_box = QComboBox()
        self.cor_method_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cor_method_box.addItems(["auto","manual"])
        self.cor_method_box.setCurrentIndex(1) # make manual as default
        try_form.addRow("COR method",self.cor_method_box)
        #row 3
        self.cor_input = QLineEdit()
        self.cor_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        try_form.addRow("COR", self.cor_input)
        #row 4: Try, View Try buttons
        try_btn_layout = QHBoxLayout()
        try_btn = QPushButton("Try")
        try_btn.clicked.connect(self.try_reconstruction)
        view_try_btn = QPushButton("View Try")
        view_try_btn.clicked.connect(self.view_try_reconstruction)
        try_btn_layout.addWidget(try_btn)
        try_btn_layout.addWidget(view_try_btn)
        try_form.addRow(try_btn_layout)
        #row 5 - batch try: start, end, batch try btn
        batch_try_layout = QHBoxLayout()
        batch_try_layout.addWidget(QLabel("Start:"))
        self.start_scan_input = QLineEdit()
        batch_try_layout.addWidget(self.start_scan_input)
        batch_try_layout.addWidget(QLabel("End:"))
        self.end_scan_input = QLineEdit()
        batch_try_layout.addWidget(self.end_scan_input)
        batch_try_btn = QPushButton("Batch Try")
        batch_try_btn.clicked.connect(self.batch_try_reconstruction)
        batch_try_layout.addWidget(batch_try_btn)
        try_form.addRow(batch_try_layout)
        #left - row 6: prj, help, abort btn
        others = QGroupBox("Others")
        others_form = QFormLayout()

        others_layout_1 = QHBoxLayout()
        view_prj_btn = QPushButton("View raw")
        view_prj_btn.clicked.connect(self.view_raw)
        help_tomo_btn = QPushButton("help")
        help_tomo_btn.clicked.connect(self.help_tomo)
        help_tomo_btn.setStyleSheet("color: green;")
        abort_btn = QPushButton("Abort")
        abort_btn.clicked.connect(self.abort_process)
        abort_btn.setStyleSheet("color: red;")
        others_layout_1.addWidget(view_prj_btn)
        others_layout_1.addWidget(help_tomo_btn)
        others_layout_1.addWidget(abort_btn)
        others_form.addRow(others_layout_1)
        #left - row 7: preset parameters for recon
        others_layout_2 = QHBoxLayout()
        bhd_btn = QPushButton("BeamHarden") # preset for absorption recon
        bhd_btn.setEnabled(True) #enable
        bhd_btn.clicked.connect(self.preset_beamhardening)
        phase_btn = QPushButton("Phase") # preset for phase recon
        phase_btn.setEnabled(True) #enable
        phase_btn.clicked.connect(self.preset_phase)
        lami_btn = QPushButton("Laminography") # preset for Laminography recon
        lami_btn.setEnabled(True) #enable
        lami_btn.clicked.connect(self.preset_laminography)
        others_layout_2.addWidget(bhd_btn)
        others_layout_2.addWidget(phase_btn)
        others_layout_2.addWidget(lami_btn)
        others_form.addRow(others_layout_2)
        #left - row 8: more functions
        others_layout_3 = QHBoxLayout()
        save_param_btn = QPushButton("Save params")
        save_param_btn.setEnabled(True) #enable
        save_param_btn.clicked.connect(self.save_params_to_file)
        load_param_btn = QPushButton("Load params")
        load_param_btn.setEnabled(True) #enable
        load_param_btn.clicked.connect(self.load_params_from_file)
        reset_param_btn = QPushButton("Reset params")
        reset_param_btn.setEnabled(True) #enable
        reset_param_btn.clicked.connect(self.reset_init_params)
        others_layout_3.addWidget(save_param_btn)
        others_layout_3.addWidget(load_param_btn)
        others_layout_3.addWidget(reset_param_btn)
        others_form.addRow(others_layout_3)
        #left - row 9: more functions
        others_layout_4 = QHBoxLayout()
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.setEnabled(True) #enable
        clear_log_btn.clicked.connect(self.clear_log)    
        save_log_btn = QPushButton("Save Log")
        save_log_btn.setEnabled(True) #enable 
        save_log_btn.clicked.connect(self.save_log)
        others_layout_4.addWidget(clear_log_btn)
        others_layout_4.addWidget(save_log_btn)
        others_form.addRow(others_layout_4)

        others.setLayout(others_form)
        try_form.addRow(others)
        try_box.setLayout(try_form)

        #right frame for Full
        full_box = QGroupBox("Full Reconstruction")
        full_form = QFormLayout()
        #right - row 1 recon/recon_step
        full_cuda_layout = QHBoxLayout()
        full_cuda_layout.addWidget(QLabel("Recon method"))
        self.recon_way_box_full = QComboBox()
        self.recon_way_box_full.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.recon_way_box_full.addItems(["recon","recon_steps"])
        self.recon_way_box_full.setCurrentIndex(0) # make recon as default
        full_cuda_layout.addWidget(self.recon_way_box_full)
        full_cuda_layout.addWidget(QLabel("cuda"))
        self.cuda_box_full = QComboBox()
        self.cuda_box_full.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cuda_box_full.addItems(["0","1"])
        self.cuda_box_full.setCurrentIndex(1) # make cuda 0 as default
        full_cuda_layout.addWidget(self.cuda_box_full)
        full_form.addRow(full_cuda_layout)
        #right - row 2: COR (Full), add COR btn
        cor_full_layout = QHBoxLayout()
        cor_full_layout.addWidget(QLabel("COR (Full)"))
        self.cor_input_full = QLineEdit()
        cor_full_layout.addWidget(self.cor_input_full)
        rec_cor_btn = QPushButton("Add COR")
        rec_cor_btn.clicked.connect(self.record_cor_to_json)
        cor_full_layout.addWidget(rec_cor_btn)
        full_form.addRow(cor_full_layout)
        #right - row 3: Full, View Full buttons
        full_btn_layout = QHBoxLayout()
        full_btn = QPushButton("Full")
        full_btn.clicked.connect(self.full_reconstruction)
        self.view_btn = QPushButton("View Full")
        self.view_btn.setEnabled(True)
        self.view_btn.clicked.connect(self.view_full_reconstruction)
        full_btn_layout.addWidget(full_btn)
        full_btn_layout.addWidget(self.view_btn)
        full_form.addRow(full_btn_layout)
        #right - row 4: Batch Full btn
        batch_full_layout = QHBoxLayout()
        batch_full_btn = QPushButton("Batch Full")
        batch_full_btn.clicked.connect(self.batch_full_reconstruction)
        self.refresh_json_btn = QPushButton("Refresh COR log")
        self.refresh_json_btn.clicked.connect(self.refresh_cor_json)
        batch_full_layout.addWidget(batch_full_btn)
        batch_full_layout.addWidget(self.refresh_json_btn)
        full_form.addRow(batch_full_layout)
        #right - row 5: COR Log file
        json_box_layout = QVBoxLayout()
        json_box_layout.addWidget(QLabel("COR Log File:"))
        self.cor_json_output = QTextEdit()
        self.cor_json_output.setReadOnly(True)
        self.cor_json_output.setStyleSheet("QTextEdit { font-size: 12pt; }")
        json_box_layout.addWidget(self.cor_json_output)
        self.load_cor_json_btn = QPushButton("Load/create COR file")
        json_box_layout.addWidget(self.load_cor_json_btn)
        self.load_cor_json_btn.clicked.connect(self.load_cor_to_jsonbox)
        full_form.addRow(json_box_layout)

        full_box.setLayout(full_form)
        main_rows.addWidget(try_box,1)
        main_rows.addWidget(full_box,1)
        main_tab.addLayout(main_rows)
        '''
        # Try config group
        left_config_group = QGroupBox("Config for Try Reconstruction")
        left_config_layout = QVBoxLayout()
        self.config_editor_try = QTextEdit()
        self.config_editor_try.setFixedHeight(300)
        self.config_editor_try.setStyleSheet("QTextEdit { border: 1px solid gray; font-size: 12.5pt; }")
        self.config_editor_try.focusInEvent = lambda event: self.highlight_editor(self.config_editor_try, event)
        self.config_editor_try.focusOutEvent = lambda event: self.unhighlight_editor(self.config_editor_try, event)
        left_config_layout.addWidget(self.config_editor_try)

        
        #==============original======================= left config group (buttons, no box config txt)
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

        self.active_editor = self.config_editor_try
        #===========original=========right config group (buttons, no box config txt)
        
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

        # Place groups into "Configs" tab
        self._config_frame_layout.addWidget(left_config_group)
        self._config_frame_layout.addWidget(right_config_group)
        '''
        # Tab 2: Params (all CLI flags + extra args)
        self._build_params_tab()
        self._build_rings_tab()
        self._build_bhard_tab()
        self._build_phase_tab()
        self._build_Geometry_tab()
        self._build_Data_tab()        
        self._build_Performance_tab()
        self._build_advanced_config_tab()
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
        self.log_output.setStyleSheet("QTextEdit { font-size: 12.5pt; }")
        self.log_output.append("Start tomoGUI")
        log_box_layout.addWidget(self.log_output)
        log_json_layout.addLayout(log_box_layout)
        #json_box_layout = QVBoxLayout()
        #json_box_layout.addWidget(QLabel("COR Log File:"))
        #self.cor_json_output = QTextEdit()
        #self.cor_json_output.setReadOnly(True)
        #self.cor_json_output.setStyleSheet("QTextEdit { font-size: 12pt; }")
        #json_box_layout.addWidget(self.cor_json_output)
        #log_json_layout.addLayout(json_box_layout, 2)
        #self.load_cor_json_btn = QPushButton("Load/create COR file")
        #json_box_layout.addWidget(self.load_cor_json_btn)
        #self.load_cor_json_btn.clicked.connect(self.load_cor_to_jsonbox)
        left_layout.addLayout(log_json_layout)

        main_layout.addLayout(left_layout, 4)

        # ==== RIGHT PANEL ====
        right_layout = QVBoxLayout()
        toolbar_row = QHBoxLayout()
        self.fig = Figure(figsize=(5, 6.65))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.fig.set_constrained_layout(True)
        self._keep_zoom = False
        self._last_xlim = None
        self._last_ylim = None
        self._last_image_shape = None
        self.rect_selector = None
        self.roi_extent = None
        self._drawing_roi = False
        self.canvas.mpl_connect("button_press_event", self._on_canvas_click)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setIconSize(QSize(23,23))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.toolbar.setStyleSheet("QToolButton { padding: 0.15px; }")
        self.toolbar.coordinates = False #disable default coords
        self.canvas.setMouseTracking(True)
        self.toolbar.setFixedWidth(270)
        toolbar_row.addWidget(self.toolbar)
        toolbar_row.addSpacing(1)
        self.coord_label = QLabel("")
        self.coord_label.setFixedWidth(150)
        self.coord_label.setStyleSheet("font-size: 11pt;")
        toolbar_row.addWidget(self.coord_label)
        try:
            self.toolbar._actions['home'].triggered.connect(self._on_toolbar_home)
        except Exception:
            pass
        self._cid_motion = self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self._cid_release = self.canvas.mpl_connect("button_release_event", self._nav_oneshot_release)

        # Colormap dropdown
        toolbar_row.addWidget(QLabel("Cmap"))
        self.cmap_box = QComboBox()
        self.cmap_box.setFixedWidth(51)
        self.cmap_box.addItems(["gray", "viridis", "plasma", "inferno", "magma", "cividis"])
        self.cmap_box.setCurrentText(self.default_cmap)
        self.cmap_box.currentIndexChanged.connect(self.update_cmap)
        toolbar_row.addWidget(self.cmap_box)

        # Image control buttons
        draw_box_btn = QPushButton("Draw")
        draw_box_btn.clicked.connect(self.draw_box)
        draw_box_btn.setFixedWidth(42)
        auto_scale_btn = QPushButton("Auto")
        auto_scale_btn.setFixedWidth(42)
        auto_scale_btn.clicked.connect(self.auto_img_contrast)
        reset_scale_btn = QPushButton("Reset")
        reset_scale_btn.setFixedWidth(42)
        reset_scale_btn.clicked.connect(self.reset_img_contrast)
        toolbar_row.addWidget(draw_box_btn)
        toolbar_row.addWidget(auto_scale_btn)
        toolbar_row.addWidget(reset_scale_btn)

        # Min/Max inputs
        toolbar_row.addWidget(QLabel("Min"))
        self.min_input = QLineEdit()
        self.min_input.setFixedWidth(50)
        self.min_input.editingFinished.connect(self.update_vmin_vmax)
        toolbar_row.addWidget(self.min_input)

        toolbar_row.addWidget(QLabel("Max"))
        self.max_input = QLineEdit()
        self.max_input.setFixedWidth(50)
        self.max_input.editingFinished.connect(self.update_vmin_vmax)
        toolbar_row.addWidget(self.max_input)

        # Theme toggle button
        toolbar_row.addSpacing(10)
        self.theme_toggle_btn = QPushButton("🌙" if self.theme_manager.get_current_theme() == 'bright' else "☀")
        self.theme_toggle_btn.setFixedWidth(35)
        self.theme_toggle_btn.setToolTip("Toggle bright/dark theme")
        self.theme_toggle_btn.clicked.connect(self._toggle_theme)
        toolbar_row.addWidget(self.theme_toggle_btn)

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

        # Tomolog section
        tomolog_group = QGroupBox("Tomolog")
        tomolog_layout = QVBoxLayout()

        # Row 1: Beamline + Scan + Cloud
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Beamline"))
        self.beamline_box = QComboBox()
        self.beamline_box.addItems(["2-bm", "7-bm", "32-id"])
        row1.addWidget(self.beamline_box)

        row1.addWidget(QLabel("Scan"))
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("e.g. 1 or 2-5 or 6,8-15,18")
        row1.addWidget(self.scan_input)

        row1.addWidget(QLabel("Cloud"))
        self.cloud_box = QComboBox()
        self.cloud_box.addItems(["imgur", "globus", "aps"])
        self.cloud_box.setCurrentText("imgur")
        row1.addWidget(self.cloud_box)
        tomolog_layout.addLayout(row1)

        # Row 2: URL
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

        # Row 4: Note and Extra params
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Note"))
        self.note_input = QLineEdit()
        row4.addWidget(self.note_input)

        row4.addWidget(QLabel("Extra Params"))
        self.extra_params_input = QLineEdit()
        self.extra_params_input.setPlaceholderText("--public True")
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
        row5.setStretch(0, 3)
        row5.setStretch(1, 1)
        tomolog_layout.addLayout(row5)

        tomolog_group.setLayout(tomolog_layout)
        right_layout.addWidget(tomolog_group, 2)

        main_layout.addLayout(right_layout, 4)
        self.setLayout(main_layout)

        # Apply initial theme after UI is fully built
        self.theme_manager.apply_theme(self.theme_manager.get_current_theme())

    # ===== PARAMS TAB =====
    def _build_params_tab(self):
        params_tab = QWidget()
        outer = QVBoxLayout(params_tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_host = QWidget()
        form = QFormLayout(form_host)
        scroll.setWidget(form_host)
        outer.addWidget(scroll)

        self.param_widgets = {}
        #add check box
        def _add_row(flag, kind, w, default=None, label_text=None, include=True):
            #include: show the checkbox, not--> always include in params
            label_text = label_text or flag

            # label cell = [ include_cb | "flag" ]
            label_widget = QWidget()
            h = QHBoxLayout(label_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            lbl = QLabel(label_text)

            include_cb = None

            if include:
                include_cb = QCheckBox()
                include_cb.setChecked(False) #default not enable
                h.addWidget(include_cb)
                lbl.setEnabled(False) #defalut not check
                w.setEnabled(False)

                def on_toggle(checked):
                    lbl.setEnabled(checked)
                    w.setEnabled(checked)
                    if not checked:
                        # reset to a sensible "off" state
                        if kind in ("spin", "dspin") and default is not None:
                            w.blockSignals(True)
                            w.setValue(default)
                            w.blockSignals(False)
                        elif kind == "combo":
                            if default is not None:
                                w.setCurrentText(str(default))
                            else:
                                w.setCurrentIndex(0)
                        elif kind == "line":
                            w.clear()
                        elif kind == "check":
                            w.setChecked(False)

                include_cb.toggled.connect(on_toggle)
            else:
                lbl.setEnabled(True)
                w.setEnabled(True)
            h.addWidget(lbl)
            h.addStretch(1)
            form.addRow(label_widget, w)

            self.param_widgets[flag] = (kind, w, include_cb, default)

        def add_line(flag, placeholder="", tip="", width=240, include=True):
            w = QLineEdit()
            if placeholder:
                w.setPlaceholderText(placeholder)
            if tip:
                w.setToolTip(tip)
            w.setFixedWidth(width)
            if flag == "--nsino":
                w.setText("0.5")
            _add_row(flag, "line", w, default="",include=include)

        def add_combo(flag, items, default=None, tip="", include=True):
            w = QComboBox()
            w.addItems(items)
            if default in items:
                w.setCurrentText(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "combo", w, default=default, include=include)

        def add_check(flag, tip="", include=True):
            w = QCheckBox()
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "check", w, default=False, include=include)

        def add_spin(flag, minv, maxv, step=1, default=None, tip="", include=True):
            w = QSpinBox()
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "spin", w, default=default, include=include)

        def add_dspin(flag, minv, maxv, step=0.1, default=None, tip="", include=True):
            w = QDoubleSpinBox()
            w.setDecimals(6)
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "dspin", w, default=default, include=include)

        add_combo("--binning", ["0","1","2","3"], default="0", include=False) #always include


        add_combo("--file-type", ["standard","double_fov"], default="standard", include=False) #always include


        add_dspin("--bright-ratio", 0.0, 1e9, step=0.1, default=1.0, include=False) #always include
        add_dspin("--center-search-step", 0.0, 1e6, step=0.05, default=0.5, include=False) #always include
        add_dspin("--center-search-width", 0.0, 1e6, step=0.5, default=50.0, include=False) #always include
        add_spin("--dezinger", 0, 10000, step=1, default=5, include=False) #always include
        add_spin("--dezinger-threshold", 0, 1000000, step=100, default=5000) 

        add_combo("--fbp-filter", ["none","ramp","shepp","hann","hamming","parzen","cosine","cosine2"], default="parzen", include=False) #always include
        add_spin("--find-center-end-row", -1, 10_000_000, step=1, default=-1, include=False) #always include
        add_spin("--find-center-start-row", 0, 10_000_000, step=1, default=0, include=False) #always include
        add_combo("--flat-linear", ["False","True"], default="False", include=False) #always include

        add_combo("--minus-log", ["True","False"], default="True", include=False) #always include

        add_line("--nsino", "", include=False) #always include
        #add_line("--nsino", "0.5 or [0,0.9]", include=False) #always include
#        add_dspin("--rotation-axis", -1e9, 1e9, step=0.01, default=-1.0)
#        add_combo("--rotation-axis-auto", ["manual","auto"], default="manual")
        add_combo("--rotation-axis-method", ["sift","vo"], default="sift", include=False) #always include
        add_line("--rotation-axis-pairs", "[0,1499] or [0,1499,749,2249]")
        add_dspin("--rotation-axis-sift-threshold", 0.0, 1.0, step=0.01, default=0.5)


        # Misc / algorithm
        add_combo("--pre-processing", ["True","False"], default="True", include=False) #always include
        add_combo("--reconstruction-algorithm", ["fourierrec","linerec"], default="fourierrec", include=False) #always include

        self.tabs.addTab(params_tab, "Reconstruction")

    def _gather_params_args(self):
        args = []
        for flag, (kind, w, include_cb, _default) in self.param_widgets.items():
            if include_cb is not None and not include_cb.isChecked():
                continue
            if kind == "line":
                val = w.text().strip()
                if val != "":
                    args += [flag, val]
            elif kind == "combo":
                args += [flag, w.currentText().strip()]
            elif kind == "check":
                if w.isChecked():
                    args += [flag]
            elif kind == "spin":
                args += [flag, str(w.value())]
            elif kind == "dspin":
                args += [flag, str(w.value())]
        return args


# ===== Beam Hardening TAB =====
    def _build_bhard_tab(self):
        bhard_tab = QWidget()
        outer = QVBoxLayout(bhard_tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_host = QWidget()
        form = QFormLayout(form_host)
        scroll.setWidget(form_host)
        outer.addWidget(scroll)

        self.bhard_widgets = {}
        #add check box before each line
        def _add_row(flag, kind, w, default=None, label_text=None, include=True):
            #include: show the checkbox, not--> always include in params
            label_text = label_text or flag

            # label cell = [ include_cb | "flag" ]
            label_widget = QWidget()
            h = QHBoxLayout(label_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            lbl = QLabel(label_text)

            include_cb = None

            if include:
                include_cb = QCheckBox()
                include_cb.setChecked(False) #default not enable
                h.addWidget(include_cb)
                lbl.setEnabled(False) #defalut not check
                w.setEnabled(False)

                def on_toggle(checked):
                    lbl.setEnabled(checked)
                    w.setEnabled(checked)
                    if not checked:
                        # reset to a sensible "off" state
                        if kind in ("spin", "dspin") and default is not None:
                            w.blockSignals(True)
                            w.setValue(default)
                            w.blockSignals(False)
                        elif kind == "combo":
                            if default is not None:
                                w.setCurrentText(str(default))
                            else:
                                w.setCurrentIndex(0)
                        elif kind == "line":
                            w.clear()
                        elif kind == "check":
                            w.setChecked(False)

                include_cb.toggled.connect(on_toggle)
            else:
                lbl.setEnabled(True)
                w.setEnabled(True)
            h.addWidget(lbl)
            h.addStretch(1)
            form.addRow(label_widget, w)

            self.bhard_widgets[flag] = (kind, w, include_cb, default)         

        def add_line(flag, placeholder="", tip="", width=240, include=True):
            w = QLineEdit()
            if placeholder:
                w.setPlaceholderText(placeholder)
            if tip:
                w.setToolTip(tip)
            w.setFixedWidth(width)
            _add_row(flag, "line", w, default="",include=include)

        def add_combo(flag, items, default=None, tip="",include=True):
            w = QComboBox()
            w.addItems(items)
            if default in items:
                w.setCurrentText(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "combo", w, default=default, include=include)

        def add_check(flag, tip="", include=True):
            w = QCheckBox()
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "check", w, default=False, include=include)

        def add_spin(flag, minv, maxv, step=1, default=None, tip="", include=True):
            w = QSpinBox()
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "spin", w, default=default, include=include)

        def add_dspin(flag, minv, maxv, step=0.1, default=None, tip="", include=True):
            w = QDoubleSpinBox()
            w.setDecimals(6)
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "dspin", w, default=default, include=include)

        # Beam hardening / source & scintillator
        add_combo("--beam-hardening-method", ["none","standard"], default="none")
        add_combo("--calculate-source", ["none","standard"], default="none")
        add_dspin("--b-storage-ring", 0.0, 10.0, step=0.001, default=0.599)
        add_dspin("--e-storage-ring", 0.0, 50.0, step=0.1, default=7.0)
        add_combo("--filter-1-auto", ["False","True"], default="False")
        add_dspin("--filter-1-density", 0.0, 100.0, step=0.01, default=1.0)
        add_line("--filter-1-material", "none/Al/Cu/...")
        add_dspin("--filter-1-thickness", 0.0, 1e6, step=0.1, default=0.0)
        add_combo("--filter-2-auto", ["False","True"], default="False")
        add_dspin("--filter-2-density", 0.0, 100.0, step=0.01, default=1.0)
        add_line("--filter-2-material", "none/Al/Cu/...")
        add_dspin("--filter-2-thickness", 0.0, 1e6, step=0.1, default=0.0)
        add_combo("--filter-3-auto", ["False","True"], default="False")
        add_dspin("--filter-3-density", 0.0, 100.0, step=0.01, default=1.0)
        add_line("--filter-3-material", "none")
        add_dspin("--filter-3-thickness", 0.0, 1e6, step=0.1, default=0.0)
        add_dspin("--maximum-E", 0.0, 1e9, step=1.0, default=200000.0)
        add_dspin("--maximum-psi-urad", 0.0, 1e9, step=1.0, default=40.0)
        add_dspin("--minimum-E", 0.0, 1e9, step=1.0, default=1000.0)
        add_check("--read-pixel-size")
        add_check("--read-scintillator")
        add_dspin("--sample-density", 0.0, 100.0, step=0.01, default=1.0)
        add_line("--sample-material", "Fe")
        add_dspin("--scintillator-density", 0.0, 100.0, step=0.01, default=6.0)
        add_line("--scintillator-material", "LuAG_Ce")
        add_dspin("--scintillator-thickness", 0.0, 1e6, step=0.1, default=100.0)
        add_dspin("--source-distance", 0.0, 1e9, step=0.1, default=36.0)
        add_dspin("--step-E", 0.0, 1e9, step=1.0, default=500.0)

        self.tabs.addTab(bhard_tab, "Hardening")

    def _gather_bhard_args(self):
        args = []
        for flag, (kind, w, include_cb, _default) in self.bhard_widgets.items():
            if include_cb is not None and not include_cb.isChecked():
                continue #skip grayed lines                
            if kind == "line":
                val = w.text().strip()
                if val != "":
                    args += [flag, val]
            elif kind == "combo":
                args += [flag, w.currentText().strip()]
            elif kind == "check":
                if w.isChecked():
                    args += [flag]
            elif kind == "spin":
                args += [flag, str(w.value())]
            elif kind == "dspin":
                args += [flag, str(w.value())]
        return args
        
        
# ===== Phase TAB =====
    def _build_phase_tab(self):
        phase_tab = QWidget()
        outer = QVBoxLayout(phase_tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_host = QWidget()
        form = QFormLayout(form_host)
        scroll.setWidget(form_host)
        outer.addWidget(scroll)

        self.phase_widgets = {}

        def _add_row(flag, kind, w, default=None, label_text=None, include=True):
            #include: show the checkbox, not--> always include in params
            label_text = label_text or flag

            # label cell = [ include_cb | "flag" ]
            label_widget = QWidget()
            h = QHBoxLayout(label_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            lbl = QLabel(label_text)

            include_cb = None

            if include:
                include_cb = QCheckBox()
                include_cb.setChecked(False) #default not enable
                h.addWidget(include_cb)
                lbl.setEnabled(False) #defalut not check
                w.setEnabled(False)

                def on_toggle(checked):
                    lbl.setEnabled(checked)
                    w.setEnabled(checked)
                    if not checked:
                        # reset to a sensible "off" state
                        if kind in ("spin", "dspin") and default is not None:
                            w.blockSignals(True)
                            w.setValue(default)
                            w.blockSignals(False)
                        elif kind == "combo":
                            if default is not None:
                                w.setCurrentText(str(default))
                            else:
                                w.setCurrentIndex(0)
                        elif kind == "line":
                            w.clear()
                        elif kind == "check":
                            w.setChecked(False)

                include_cb.toggled.connect(on_toggle)
            else:
                lbl.setEnabled(True)
                w.setEnabled(True)
            h.addWidget(lbl)
            h.addStretch(1)
            form.addRow(label_widget, w)

            self.phase_widgets[flag] = (kind, w, include_cb, default)   

        def add_line(flag, placeholder="", tip="", width=240, include=True):
            w = QLineEdit()
            if placeholder:
                w.setPlaceholderText(placeholder)
            if tip:
                w.setToolTip(tip)
            w.setFixedWidth(width)
            _add_row(flag, "line", w, default="",include=include)

        def add_combo(flag, items, default=None, tip="", include=True):
            w = QComboBox()
            w.addItems(items)
            if default in items:
                w.setCurrentText(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "combo", w, default=default, include=include)

        def add_check(flag, tip="", include=True):
            w = QCheckBox()
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "check", w, default=False, include=include)

        def add_spin(flag, minv, maxv, step=1, default=None, tip="", include=True):
            w = QSpinBox()
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "spin", w, default=default, include=include)

        def add_dspin(flag, minv, maxv, step=0.1, default=None, tip="", include=True):
            w = QDoubleSpinBox()
            w.setDecimals(6)
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "dspin", w, default=default, include=include)

        # Phase retrieval   
        add_combo("--retrieve-phase-method", ["none","paganin","Gpaganin"], default="none")
        add_dspin("--pixel-size", 0.0, 1e9, step=0.01, default=0.0)        
        add_dspin("--energy", 0.0, 1e6, step=0.1, default=0.0)
        add_dspin("--propagation-distance", 0.0, 1e6, step=0.1, default=0.0)        
        add_dspin("--retrieve-phase-W", 0.0, 1.0, step=0.0001,default=0.0002)
        add_dspin("--retrieve-phase-alpha", 0.0, 1e6, step=0.0001,default=0.0)
        add_dspin("--retrieve-phase-delta-beta", 0.0, 1e9, step=0.1,default=1500.0)
        add_spin("--retrieve-phase-pad", 0, 1024, step=1,default=1)
  
        self.tabs.addTab(phase_tab, "Phase")

    def _gather_phase_args(self):
        args = []
        for flag, (kind, w, include_cb, _default) in self.phase_widgets.items():
            if include_cb is not None and not include_cb.isChecked():
                continue #skip grayed lines
            if kind == "line":
                val = w.text().strip()
                if val != "":
                    args += [flag, val]
            elif kind == "combo":
                args += [flag, w.currentText().strip()]
            elif kind == "check":
                if w.isChecked():
                    args += [flag]
            elif kind == "spin":
                args += [flag, str(w.value())]
            elif kind == "dspin":
                if bool(w.value()) != "None":
                    args += [flag, str(w.value())]
                else:
                    pass

        return args        

    # ===== RINGS TAB =====
    def _build_rings_tab(self):
        rings_tab = QWidget()
        outer = QVBoxLayout(rings_tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_host = QWidget()
        form = QFormLayout(form_host)
        scroll.setWidget(form_host)
        outer.addWidget(scroll)

        self.rings_widgets = {}

        def _add_row(flag, kind, w, default=None, label_text=None, include=True):
            #include: show the checkbox, not--> always include in params
            label_text = label_text or flag

            # label cell = [ include_cb | "flag" ]
            label_widget = QWidget()
            h = QHBoxLayout(label_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            lbl = QLabel(label_text)

            include_cb = None

            if include:
                include_cb = QCheckBox()
                include_cb.setChecked(False) #default not enable
                h.addWidget(include_cb)
                lbl.setEnabled(False) #defalut not check
                w.setEnabled(False)

                def on_toggle(checked):
                    lbl.setEnabled(checked)
                    w.setEnabled(checked)
                    if not checked:
                        # reset to a sensible "off" state
                        if kind in ("spin", "dspin") and default is not None:
                            w.blockSignals(True)
                            w.setValue(default)
                            w.blockSignals(False)
                        elif kind == "combo":
                            if default is not None:
                                w.setCurrentText(str(default))
                            else:
                                w.setCurrentIndex(0)
                        elif kind == "line":
                            w.clear()
                        elif kind == "check":
                            w.setChecked(False)

                include_cb.toggled.connect(on_toggle)
            else:
                lbl.setEnabled(True)
                w.setEnabled(True)
            h.addWidget(lbl)
            h.addStretch(1)
            form.addRow(label_widget, w)

            self.rings_widgets[flag] = (kind, w, include_cb, default)   

        def add_line(flag, placeholder="", tip="", width=240, include=True):
            w = QLineEdit()
            if placeholder:
                w.setPlaceholderText(placeholder)
            if tip:
                w.setToolTip(tip)
            w.setFixedWidth(width)
            _add_row(flag, "line", w, default="",include=include)

        def add_combo(flag, items, default=None, tip="", include=True):
            w = QComboBox()
            w.addItems(items)
            if default in items:
                w.setCurrentText(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "combo", w, default=default, include=include)

        def add_check(flag, tip="", include=True):
            w = QCheckBox()
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "check", w, default=False, include=include)

        def add_spin(flag, minv, maxv, step=1, default=None, tip="", include=True):
            w = QSpinBox()
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "spin", w, default=default, include=include)

        def add_dspin(flag, minv, maxv, step=0.1, default=None, tip="", include=True):
            w = QDoubleSpinBox()
            w.setDecimals(6)
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "dspin", w, default=default, include=include)


        # Stripe/ring filters
        add_combo("--remove-stripe-method", ["none","fw","ti","vo-all"], default="none", include=False) #always include      
        add_combo("--fw-filter", ["haar","db5","sym5","sym16"], default="sym16")
        add_spin("--fw-level", 0, 64, step=1, default=7)
        add_check("--fw-pad")
        add_dspin("--fw-sigma", 0.0, 100.0, step=0.1, default=1.0)
        add_dspin("--ti-beta", 0.0, 1.0, step=0.001, default=0.022)
        add_dspin("--ti-mask", 0.0, 1.0, step=0.01, default=1.0)
        add_spin("--vo-all-dim", 1, 3, step=1, default=1)
        add_spin("--vo-all-la-size", 1, 4096, step=2, default=61)
        add_spin("--vo-all-sm-size", 1, 4096, step=2, default=21)
        add_dspin("--vo-all-snr", 0.0, 100.0, step=0.1, default=3.0)

        self.tabs.addTab(rings_tab, "Rings")

    def _gather_rings_args(self):
        args = []
        for flag, (kind, w, include_cb, _default) in self.rings_widgets.items():
            if include_cb is not None and not include_cb.isChecked():
                continue #skip grayed lines

            if kind == "line":
                val = w.text().strip()
                if val != "":
                    args += [flag, val]
            elif kind == "combo":
                args += [flag, w.currentText().strip()]
            elif kind == "check":
                if w.isChecked():
                    args += [flag]
            elif kind == "spin":
                args += [flag, str(w.value())]
            elif kind == "dspin":
                args += [flag, str(w.value())]

        return args

# ===== Geometry TAB =====
    def _build_Geometry_tab(self):
        Geometry_tab = QWidget()
        outer = QVBoxLayout(Geometry_tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_host = QWidget()
        form = QFormLayout(form_host)
        scroll.setWidget(form_host)
        outer.addWidget(scroll)

        self.Geometry_widgets = {}

        def _add_row(flag, kind, w, default=None, label_text=None, include=True):
            #include: show the checkbox, not--> always include in params
            label_text = label_text or flag

            # label cell = [ include_cb | "flag" ]
            label_widget = QWidget()
            h = QHBoxLayout(label_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            lbl = QLabel(label_text)

            include_cb = None

            if include:
                include_cb = QCheckBox()
                include_cb.setChecked(False) #default not enable
                h.addWidget(include_cb)
                lbl.setEnabled(False) #defalut not check
                w.setEnabled(False)

                def on_toggle(checked):
                    lbl.setEnabled(checked)
                    w.setEnabled(checked)
                    if not checked:
                        # reset to a sensible "off" state
                        if kind in ("spin", "dspin") and default is not None:
                            w.blockSignals(True)
                            w.setValue(default)
                            w.blockSignals(False)
                        elif kind == "combo":
                            if default is not None:
                                w.setCurrentText(str(default))
                            else:
                                w.setCurrentIndex(0)
                        elif kind == "line":
                            w.clear()
                        elif kind == "check":
                            w.setChecked(False)

                include_cb.toggled.connect(on_toggle)
            else:
                lbl.setEnabled(True)
                w.setEnabled(True)
            h.addWidget(lbl)
            h.addStretch(1)
            form.addRow(label_widget, w)

            self.Geometry_widgets[flag] = (kind, w, include_cb, default) 

        def add_line(flag, placeholder="", tip="", width=240, include=True):
            w = QLineEdit()
            if placeholder:
                w.setPlaceholderText(placeholder)
            if tip:
                w.setToolTip(tip)
            w.setFixedWidth(width)
            _add_row(flag, "line", w, default="",include=include)

        def add_combo(flag, items, default=None, tip="", include=True):
            w = QComboBox()
            w.addItems(items)
            if default in items:
                w.setCurrentText(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "combo", w, default=default, include=include)

        def add_check(flag, tip="", include=True):
            w = QCheckBox()
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "check", w, default=False, include=include)

        def add_spin(flag, minv, maxv, step=1, default=None, tip="", include=True):
            w = QSpinBox()
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "spin", w, default=default, include=include)

        def add_dspin(flag, minv, maxv, step=0.1, default=None, tip="", include=True):
            w = QDoubleSpinBox()
            w.setDecimals(6)
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "dspin", w, default=default, include=include)

        # Geometry & lamino
        add_line("--blocked-views", "[[0,1.2],[3,3.14]]")        
        add_dspin("--rotate-proj-angle", -360.0, 360.0, step=0.1, default=0.0)
        add_spin("--rotate-proj-order", 0, 5, step=1, default=1)        
        add_dspin("--lamino-angle", -90, 90.0, step=0.01, default=0.0)
        add_spin("--lamino-end-row", -1, 10_000_000, step=1, default=-1)
        add_dspin("--lamino-search-step", 0.0, 1e6, step=0.01, default=0.25)
        add_dspin("--lamino-search-width", 0.0, 1e6, step=0.1, default=5.0)
        add_spin("--lamino-start-row", 0, 10_000_000, step=1, default=0)
  
        self.tabs.addTab(Geometry_tab, "Geometry")

    def _gather_Geometry_args(self):
        args = []
        for flag, (kind, w, include_cb, _default) in self.Geometry_widgets.items():
            if include_cb is not None and not include_cb.isChecked():
                continue #skip grayed lines

            if kind == "line":
                val = w.text().strip()
                if val != "":
                    args += [flag, val]
            elif kind == "combo":
                args += [flag, w.currentText().strip()]
            elif kind == "check":
                if w.isChecked():
                    args += [flag]
            elif kind == "spin":
                args += [flag, str(w.value())]
            elif kind == "dspin":
                args += [flag, str(w.value())]

        return args        

# ===== Data TAB =====
    def _build_Data_tab(self):
        Data_tab = QWidget()
        outer = QVBoxLayout(Data_tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_host = QWidget()
        form = QFormLayout(form_host)
        scroll.setWidget(form_host)
        outer.addWidget(scroll)

        self.data_widgets = {}

        def _add_row(flag, kind, w, default=None, label_text=None, include=True):
            #include: show the checkbox, not--> always include in params
            label_text = label_text or flag

            # label cell = [ include_cb | "flag" ]
            label_widget = QWidget()
            h = QHBoxLayout(label_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            lbl = QLabel(label_text)

            include_cb = None

            if include:
                include_cb = QCheckBox()
                include_cb.setChecked(False) #default not enable
                h.addWidget(include_cb)
                lbl.setEnabled(False) #defalut not check
                w.setEnabled(False)

                def on_toggle(checked):
                    lbl.setEnabled(checked)
                    w.setEnabled(checked)
                    if not checked:
                        # reset to a sensible "off" state
                        if kind in ("spin", "dspin") and default is not None:
                            w.blockSignals(True)
                            w.setValue(default)
                            w.blockSignals(False)
                        elif kind == "combo":
                            if default is not None:
                                w.setCurrentText(str(default))
                            else:
                                w.setCurrentIndex(0)
                        elif kind == "line":
                            w.clear()
                        elif kind == "check":
                            w.setChecked(False)

                include_cb.toggled.connect(on_toggle)
            else:
                lbl.setEnabled(True)
                w.setEnabled(True)
            h.addWidget(lbl)
            h.addStretch(1)
            form.addRow(label_widget, w)

            self.data_widgets[flag] = (kind, w, include_cb, default) 

        def add_line(flag, placeholder="", tip="", width=240, include=True):
            w = QLineEdit()
            if placeholder:
                w.setPlaceholderText(placeholder)
            if tip:
                w.setToolTip(tip)
            w.setFixedWidth(width)
            _add_row(flag, "line", w, default="",include=include)

        def add_combo(flag, items, default=None, tip="", include=True):
            w = QComboBox()
            w.addItems(items)
            if default in items:
                w.setCurrentText(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "combo", w, default=default, include=include)

        def add_check(flag, tip="", include=True):
            w = QCheckBox()
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "check", w, default=False, include=include)

        def add_spin(flag, minv, maxv, step=1, default=None, tip="", include=True):
            w = QSpinBox()
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "spin", w, default=default, include=include)

        def add_dspin(flag, minv, maxv, step=0.1, default=None, tip="", include=True):
            w = QDoubleSpinBox()
            w.setDecimals(6)
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "dspin", w, default=default, include=include)

        add_line("--dark-file-name", "/path/dark.h5")
        add_line("--flat-file-name", "/path/flat.h5")
        add_line("--out-path-name", "/path/out")
        add_combo("--save-format", ["tiff","h5","h5sino","h5nolinks"], default="tiff", include=False) #always include
        add_check("--config-update")
        add_line("--logs-home", "/home/user/logs", include=False) #always include
        add_check("--verbose", include=False) #always include
        
        self.tabs.addTab(Data_tab, "Data")

    def _gather_Data_args(self):
        args = []
        for flag, (kind, w, include_cb, _default) in self.data_widgets.items():
            if include_cb is not None and not include_cb.isChecked():
                continue #skip grayed lines

            if kind == "line":
                val = w.text().strip()
                if val != "":
                    args += [flag, val]
            elif kind == "combo":
                args += [flag, w.currentText().strip()]
            elif kind == "check":
                if w.isChecked():
                    args += [flag]
            elif kind == "spin":
                args += [flag, str(w.value())]
            elif kind == "dspin":
                args += [flag, str(w.value())]

        return args        


# ===== Performance TAB =====
    def _build_Performance_tab(self):
        Performance_tab = QWidget()
        outer = QVBoxLayout(Performance_tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_host = QWidget()
        form = QFormLayout(form_host)
        scroll.setWidget(form_host)
        outer.addWidget(scroll)

        self.perf_widgets = {}

        def _add_row(flag, kind, w, default=None, label_text=None, include=True):
            #include: show the checkbox, not--> always include in params
            label_text = label_text or flag

            # label cell = [ include_cb | "flag" ]
            label_widget = QWidget()
            h = QHBoxLayout(label_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            lbl = QLabel(label_text)

            include_cb = None

            if include:
                include_cb = QCheckBox()
                include_cb.setChecked(False) #default not enable
                h.addWidget(include_cb)
                lbl.setEnabled(False) #defalut not check
                w.setEnabled(False)

                def on_toggle(checked):
                    lbl.setEnabled(checked)
                    w.setEnabled(checked)
                    if not checked:
                        # reset to a sensible "off" state
                        if kind in ("spin", "dspin") and default is not None:
                            w.blockSignals(True)
                            w.setValue(default)
                            w.blockSignals(False)
                        elif kind == "combo":
                            if default is not None:
                                w.setCurrentText(str(default))
                            else:
                                w.setCurrentIndex(0)
                        elif kind == "line":
                            w.clear()
                        elif kind == "check":
                            w.setChecked(False)

                include_cb.toggled.connect(on_toggle)
            else:
                lbl.setEnabled(True)
                w.setEnabled(True)
            h.addWidget(lbl)
            h.addStretch(1)
            form.addRow(label_widget, w)

            self.perf_widgets[flag] = (kind, w, include_cb, default) 

        def add_line(flag, placeholder="", tip="", width=240, include=True):
            w = QLineEdit()
            if placeholder:
                w.setPlaceholderText(placeholder)
            if tip:
                w.setToolTip(tip)
            w.setFixedWidth(width)
            _add_row(flag, "line", w, default="",include=include)

        def add_combo(flag, items, default=None, tip="", include=True):
            w = QComboBox()
            w.addItems(items)
            if default in items:
                w.setCurrentText(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "combo", w, default=default, include=include)

        def add_check(flag, tip="", include=True):
            w = QCheckBox()
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "check", w, default=False, include=include)

        def add_spin(flag, minv, maxv, step=1, default=None, tip="", include=True):
            w = QSpinBox()
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "spin", w, default=default, include=include)

        def add_dspin(flag, minv, maxv, step=0.1, default=None, tip="", include=True):
            w = QDoubleSpinBox()
            w.setDecimals(6)
            w.setRange(minv, maxv)
            w.setSingleStep(step)
            if default is not None:
                w.setValue(default)
            if tip:
                w.setToolTip(tip)
            _add_row(flag, "dspin", w, default=default, include=include)

        # Perfomance related settings
        add_combo("--clear-folder", ["False","True"], default="False")
        add_combo("--dtype", ["float32","float16"], default="float32", include=False) #always include
        add_spin("--start-column", 0, 10_000_000, step=1, default=0, include=False) #always include
        add_spin("--end-column", -1, 10_000_000, step=1, default=-1, include=False) #always include
        add_spin("--start-proj", 0, 10_000_000, step=1, default=0, include=False) #always include
        add_spin("--end-proj", -1, 10_000_000, step=1, default=-1, include=False) #always include
        add_spin("--start-row", 0, 10_000_000, step=1, default=0, include=False) #always include
        add_spin("--end-row", -1, 10_000_000, step=1, default=-1, include=False) #always include
        add_spin("--nproj-per-chunk", 1, 65535, step=1, default=8, include=False) #always include      
        add_spin("--nsino-per-chunk", 1, 65535, step=1, default=8, include=False) #always include      
        add_spin("--max-read-threads", 1, 1024, step=1, default=4, include=False) #always include
        add_spin("--max-write-threads", 1, 1024, step=1, default=8, include=False) #always include      

  
        self.tabs.addTab(Performance_tab, "Performance")

    def _gather_Performance_args(self):
        args = []
        for flag, (kind, w, include_cb, _default) in self.perf_widgets.items():
            if include_cb is not None and not include_cb.isChecked():
                continue #skip grayed lines

            if kind == "line":
                val = w.text().strip()
                if val != "":
                    args += [flag, val]
            elif kind == "combo":
                args += [flag, w.currentText().strip()]
            elif kind == "check":
                if w.isChecked():
                    args += [flag]
            elif kind == "spin":
                args += [flag, str(w.value())]
            elif kind == "dspin":
                args += [flag, str(w.value())]

        return args        

        # ===== advanced config tab====
    def _build_advanced_config_tab(self):
        config_tab = QWidget()
        self.tabs.addTab(config_tab, "Advanced Config")
        config_main = QVBoxLayout(config_tab) #main layout for the tab
        config_txt_main = QHBoxLayout() #layout for left/right
        config_rows = QHBoxLayout()
        config_rows.setSpacing(5)
        # some common functions for both try/full
        func_box = QHBoxLayout()
        self.use_conf_box = QCheckBox("Enable config")
        self.use_conf_box.setChecked(False)
        func_box.addWidget(self.use_conf_box)
        load_config_btn = QPushButton("Load Config")
        save_config_btn = QPushButton("Save Config")
        load_config_btn.clicked.connect(self.load_config)
        save_config_btn.clicked.connect(self.save_config)
        func_box.addWidget(load_config_btn)
        func_box.addWidget(save_config_btn)
        config_main.addLayout(func_box)
        #left frame for Try
        left_try_box = QGroupBox("Try Recon Config")
        #left - row 1: config txt box
        left_try_layout = QVBoxLayout()
        self.config_editor_try = QTextEdit()
        self.config_editor_try.setFixedHeight(300)
        self.config_editor_try.setStyleSheet("QTextEdit { border: 1px solid gray; font-size: 12.5pt; }")
        self.config_editor_try.focusInEvent = lambda event: self.highlight_editor(self.config_editor_try, event)
        self.config_editor_try.focusOutEvent = lambda event: self.unhighlight_editor(self.config_editor_try, event)
        left_try_layout.addWidget(self.config_editor_try)
        left_try_box.setLayout(left_try_layout)
        #right - row 1: conf full txt box
        right_full_box = QGroupBox("Full Recon Config")
        right_full_layout = QVBoxLayout()
        self.config_editor_full = QTextEdit()
        self.config_editor_full.setFixedHeight(300)
        self.config_editor_full.setStyleSheet("QTextEdit { border: 1px solid gray; font-size: 12.5pt; }")
        self.config_editor_full.focusInEvent = lambda event: self.highlight_editor(self.config_editor_full, event)
        self.config_editor_full.focusOutEvent = lambda event: self.unhighlight_editor(self.config_editor_full, event)
        right_full_layout.addWidget(self.config_editor_full)
        right_full_box.setLayout(right_full_layout)

        self.active_editor = self.config_editor_try
        config_txt_main.addWidget(left_try_box,1)
        config_txt_main.addWidget(right_full_box,1)
        config_main.addLayout(config_txt_main)

        # ==== BATCH PROCESSING TAB ====
        batch_tab = QWidget()
        self.tabs.addTab(batch_tab, "Batch Processing")
        self._build_batch_tab(batch_tab)

    def _build_batch_tab(self, batch_tab):
        """Build the batch processing tab for managing multiple datasets"""
        main_layout = QVBoxLayout(batch_tab)

        # Top controls
        controls_layout = QHBoxLayout()

        refresh_list_btn = QPushButton("Refresh File List")
        refresh_list_btn.clicked.connect(self._refresh_batch_file_list)
        controls_layout.addWidget(refresh_list_btn)

        save_cor_btn = QPushButton("Save COR to CSV")
        save_cor_btn.clicked.connect(self._batch_save_cor_csv)
        save_cor_btn.setToolTip("Save COR values to batch_cor_values.csv in data folder")
        controls_layout.addWidget(save_cor_btn)

        load_cor_btn = QPushButton("Load COR from CSV")
        load_cor_btn.clicked.connect(self._batch_load_cor_csv)
        load_cor_btn.setToolTip("Load COR values from batch_cor_values.csv in data folder")
        controls_layout.addWidget(load_cor_btn)

        controls_layout.addStretch()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._batch_select_all)
        controls_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._batch_deselect_all)
        controls_layout.addWidget(deselect_all_btn)

        main_layout.addLayout(controls_layout)

        # File list table
        self.batch_file_table = QTableWidget()
        self.batch_file_table.setColumnCount(9)
        self.batch_file_table.setHorizontalHeaderLabels([
            "Select", "Filename", "Size", "COR", "Status", "View Data", "View Try", "View Full", "Actions"
        ])

        # Configure table
        self.batch_file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.batch_file_table.setSortingEnabled(True)  # Enable column sorting
        header = self.batch_file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Select checkbox
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Filename - user can resize
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Size
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # COR
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # View Data
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # View Try
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # View Full
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Actions
        header.setSectionsClickable(True)  # Make headers clickable for sorting

        # Set initial width for filename column to be wider (can be resized by user)
        self.batch_file_table.setColumnWidth(1, 400)

        main_layout.addWidget(self.batch_file_table)

        # Machine and GPU configuration
        machine_layout = QHBoxLayout()
        machine_layout.addWidget(QLabel("Target Machine:"))

        self.batch_machine_box = QComboBox()
        self.batch_machine_box.addItems(["Local", "tomo1", "tomo2", "tomo3", "tomo4", "tomo5"])
        self.batch_machine_box.setCurrentText("Local")
        self.batch_machine_box.setToolTip("Select machine to run batch reconstructions")
        machine_layout.addWidget(self.batch_machine_box)

        machine_layout.addSpacing(20)
        machine_layout.addWidget(QLabel("GPUs per machine:"))

        self.batch_gpus_per_machine = QSpinBox()
        self.batch_gpus_per_machine.setMinimum(1)
        self.batch_gpus_per_machine.setMaximum(8)
        self.batch_gpus_per_machine.setValue(1)
        self.batch_gpus_per_machine.setToolTip("Number of GPUs available on the target machine (1 job per GPU)")
        machine_layout.addWidget(self.batch_gpus_per_machine)

        machine_layout.addSpacing(20)
        self.batch_queue_label = QLabel("Queue: 0 jobs waiting")
        machine_layout.addWidget(self.batch_queue_label)

        machine_layout.addStretch()
        main_layout.addLayout(machine_layout)

        # Batch operations
        batch_ops_layout = QHBoxLayout()

        batch_ops_layout.addWidget(QLabel("Batch Operations (on selected):"))

        batch_try_btn = QPushButton("Run Try on Selected")
        batch_try_btn.clicked.connect(self._batch_run_try_selected)
        batch_ops_layout.addWidget(batch_try_btn)

        batch_full_btn = QPushButton("Run Full on Selected")
        batch_full_btn.clicked.connect(self._batch_run_full_selected)
        batch_ops_layout.addWidget(batch_full_btn)

        self.batch_stop_btn = QPushButton("Stop Queue")
        self.batch_stop_btn.clicked.connect(self._batch_stop_queue)
        self.batch_stop_btn.setEnabled(False)
        batch_ops_layout.addWidget(self.batch_stop_btn)

        batch_ops_layout.addStretch()

        remove_selected_btn = QPushButton("Remove Selected from List")
        remove_selected_btn.clicked.connect(self._batch_remove_selected)
        batch_ops_layout.addWidget(remove_selected_btn)

        main_layout.addLayout(batch_ops_layout)

        # Progress section
        progress_group = QGroupBox("Batch Progress")
        progress_layout = QVBoxLayout()

        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setValue(0)
        progress_layout.addWidget(self.batch_progress_bar)

        self.batch_status_label = QLabel("Ready")
        progress_layout.addWidget(self.batch_status_label)

        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # Initialize batch state
        self.batch_file_list = []
        self.batch_current_index = 0
        self.batch_running = False
        self.batch_job_queue = []  # Queue of pending jobs: [(file_info, recon_type, machine), ...]
        self.batch_running_jobs = {}  # Dict of currently running jobs: {gpu_id: (process, file_info, recon_type)}
        self.batch_available_gpus = []  # List of available GPU IDs
        self.batch_total_jobs = 0  # Total number of jobs in current batch
        self.batch_completed_jobs = 0  # Number of completed jobs
        self.batch_current_machine = "Local"  # Current machine for batch
        self.batch_current_num_gpus = 1  # Current number of GPUs


    # ===== HELPER METHODS =====
    
    def help_tomo(self):
        """Run the CLI `tomocupy recon (or recon_steps) -h` and show output in the GUI log."""
        name = "tomocupy-help"
        recon_way = self.recon_way_box.currentText()
        self.log_output.append(f"\U0001f4d6[{name}] tomocupy {recon_way} -h")

        p = QProcess(self)
        p.setProcessChannelMode(QProcess.SeparateChannels)

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

        def _done(code, _status):
            try:
                self.process[:] = [(pp, nn) for (pp, nn) in self.process if pp is not p]
            except Exception:
                pass
            self.log_output.append(f"\u2705[{name}] done." if code == 0
                                else f"\u274c[{name}] failed with code {code}.")

        p.finished.connect(_done)
        p.errorOccurred.connect(
            lambda _err: self.log_output.append(f"\u274c[{name}] {p.errorString()}")
        )

        if not isinstance(self.process, list):
            self.process = []
        self.process.append((p, name))

        p.start("tomocupy", [str(recon_way), "-h"])

    def update_cmap(self): #link to cmap dropdown
        self.current_cmap = self.cmap_box.currentText()
        self.refresh_current_image()

    def update_vmin_vmax(self): #link to min/max input
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

    def refresh_current_image(self):
        if self.full_files and 0 <= self.slice_slider.value() < len(self.full_files):
            self.show_image(self.full_files[self.slice_slider.value()], flag=None)
        elif self.preview_files and 0 <= self.slice_slider.value() < len(self.preview_files):
            self.show_image(self.preview_files[self.slice_slider.value()], flag=None)
        elif 0<= self.slice_slider.value() < self.raw_files_num:
            self.show_image(img_path=self.slice_slider.value(), flag="raw")

    def highlight_editor(self, editor, event):
        editor.setStyleSheet("QTextEdit { border: 2px solid green; font-size: 12.5pt; }")
        self.active_editor = editor
        QTextEdit.focusInEvent(editor, event)

    def unhighlight_editor(self, editor, event):
        editor.setStyleSheet("QTextEdit { border: 1px solid gray; font-size: 12.5pt; }")
        QTextEdit.focusOutEvent(editor, event)

    def eventFilter(self, obj, event):
        if obj == self.canvas and event.type() == QEvent.Wheel:
            step = 1 if event.angleDelta().y() > 0 else -1
            new_val = self.slice_slider.value() + step
            new_val = max(0, min(self.slice_slider.maximum(), new_val))
            self._keep_zoom = True
            self.slice_slider.setValue(new_val)
            return True
        return super().eventFilter(obj, event)

    def browse_data_folder(self):
        start_dir = self.data_path.text().strip() or os.path.expanduser("/")
        dialog = QFileDialog(self, "Select data folder")
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setDirectory(start_dir)
        if dialog.exec():
            self.data_path.setText(dialog.selectedFiles()[0])
            self.refresh_h5_files()
            # Auto-refresh batch file list when folder is selected
            self._refresh_batch_file_list()

    def refresh_h5_files(self):
        self.proj_file_box.clear()
        folder = self.data_path.text()
        if folder and os.path.isdir(folder):
            for f in sorted(glob.glob(os.path.join(folder, "*.h5")),key=os.path.getmtime, reverse=True): #newest → oldest
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
    
    def save_params_to_file(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fn = f"{self.data_path.text().strip()}/tomocupy_reconparams_{timestamp}.json"
        params = {} #gather all enabled params
        for widgets in [self.param_widgets, self.phase_widgets, self.Geometry_widgets,
                        self.bhard_widgets, self.rings_widgets, self.perf_widgets, self.data_widgets]:    
            for flag, (kind, w, include_cb, _default) in widgets.items():
                if include_cb is not None and not include_cb.isChecked():
                    continue #skip grayed lines
                if kind == "line":
                    val = w.text().strip()
                    if val != "":
                        params[flag] = val
                elif kind == "combo":
                    params[flag] = w.currentText().strip()
                elif kind == "check":
                    if w.isChecked():
                        params[flag] = "checked"
                elif kind == "spin":
                    params[flag] = str(w.value())
                elif kind == "dspin":
                    params[flag] = str(w.value())
        if params:
            try:
                with open(fn, "a") as f:
                    json.dump(params, f, indent=2)
            except Exception as e:
                self.log_output.append(f'\u274c Failed to save params to {fn}: {e}')
        self.log_output.append(f'\u2705 Saved enabled params to {fn}')

    def load_params_from_file(self):
        start_dir = self.data_path.text().strip()
        if not start_dir or not os.path.isdir(start_dir):
            start_dir = os.path.expanduser("/")
        dialog = QFileDialog(self, "Select params folder")
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilters(["JSON files (*.json)", "All files (*)"])
        dialog.selectNameFilter("JSON files (*.json)")
        dialog.setDirectory(start_dir)
        load_fn = None
        if dialog.exec():
            load_fn = dialog.selectedFiles()[0]
        if not load_fn or not os.path.isfile(load_fn):
            self.log_output.append(f'<span style="color:red;">\u274c Invalid file: {load_fn}</span>')
            return
        with open(load_fn, "r") as f:
            try:
                params = json.load(f)
            except Exception as e:
                self.log_output.append(f'<span style="color:red;">\u274c Failed to load params from {load_fn}: {e}</span>')
                return
        for key, v in params.items():
            for widgets in [self.param_widgets, self.phase_widgets, self.Geometry_widgets,
                            self.bhard_widgets, self.rings_widgets, self.perf_widgets, self.data_widgets]:   
                if key in widgets.keys():
                    kind, w, include_cb, _default = widgets[key]
                    if include_cb is not None and not include_cb.isChecked():
                        include_cb.setChecked(True)
                    if kind == "line":
                        w.setText(v)
                    elif kind == "combo":
                        if v in [w.itemText(i) for i in range(w.count())]:
                            w.setCurrentText(v)
                    elif kind == "check":
                        w.setChecked(True)
                    elif kind == "spin":
                        try:
                            iv = int(v)
                            if w.minimum() <= iv <= w.maximum():
                                w.setValue(iv)
                        except Exception:
                            pass
                    elif kind == "dspin":
                        try:
                            fv = float(v)
                            if w.minimum() <= fv <= w.maximum():
                                w.setValue(fv)
                        except Exception:
                            pass
        self.log_output.append(f'\u2705 Loaded params from {load_fn}')
    def reset_init_params(self):
        #parameters always included in recon
        init_flags_values = {"--binning": "0", "--file-type": "standard", "--bright-ratio": "1.0",
                               "--center-search-step": "0.5", "--center-search-width": "50.0",
                               "--dezinger": "5", "--fbp-filter": "parzen",
                               "--find-center-end-row": "-1", "--find-center-start-row": "0",
                               "--flat-linear": "False", "--minus-log": "True",
                               "--nsino": "0.5", "--rotation-axis-method": "sift", "--pre-processing": "True",
                                "--reconstruction-algorithm": "fourierrec", #params in params_widgets
                                "--remove-stripe-method": "none", #params in rings_widgets
                                "--save-format": "tiff", "--logs-home": "/home/user/logs", "--verbose": "", #params in data_widgets
                                "--clear-folder": "False", "--dtype": "float32", 
                                "--start-column": "0", "--end-column": "-1", "--start-proj": "0", "--end-proj": "-1",
                                "--start-row": "0", "--end-row": "-1", "--nproj-per-chunk": "8",
                                "--nsino-per-chunk": "8", "--max-read-threads": "4", "--max-write-threads": "8"} #params in perf_widgets                      
        for widgets in [self.param_widgets, self.phase_widgets, self.Geometry_widgets,
                        self.bhard_widgets, self.rings_widgets, self.perf_widgets, self.data_widgets]:   
            if widgets == self.Geometry_widgets or widgets == self.bhard_widgets or widgets == self.phase_widgets:
                for flag, (kind, w, include_cb, _default) in widgets.items():
                    if include_cb is not None and include_cb.isChecked():
                        include_cb.setChecked(False)
            else:
                for flag, (kind, w, include_cb, _default) in widgets.items():
                    if include_cb is not None and include_cb.isChecked():
                        include_cb.setChecked(False)
                    if flag in init_flags_values.keys():
                        v = init_flags_values[flag]
                        if kind == "line":
                            w.setText(v)
                        elif kind == "combo":
                            if v in [w.itemText(i) for i in range(w.count())]:
                                w.setCurrentText(v)
                        elif kind == "check":
                            w.setChecked(v.lower() in ("true","1","yes","checked"))
                        elif kind == "spin":
                            try:
                                iv = int(v)
                                if w.minimum() <= iv <= w.maximum():
                                    w.setValue(iv)
                            except Exception:
                                pass
                        elif kind == "dspin":
                            try:
                                fv = float(v)
                                if w.minimum() <= fv <= w.maximum():
                                    w.setValue(fv)
                            except Exception:
                                pass
        self.log_output.append(f'\u2705 Reset parameters to initial values')

    def clear_log(self):
        self.log_output.clear()

    def save_log(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_fn = f"Process_log_{timestamp}.txt"
        if not os.path.exists(log_fn):
            with open(log_fn, "a", encoding="utf-8") as f:  
                for line in self.log_output:
                    f.write(f"{line}\n")
            self.log_output.append(f'\u2705 Saved log to {log_fn}')


    def preset_beamhardening(self):
        enable_flags = ["--beam-hardening-method", "--calculate-source",
                        "--b-storage-ring","--e-storage-ring", 
                        "--filter-1-auto", "--filter-1-density",
                        "--filter-1-material", "--filter-1-thickness", 
                        "--filter-2-auto","--filter-2-density",
                        "--filter-2-material","--filter-2-thickness",
                        "--filter-3-auto", "--filter-3-density", 
                        "--filter-3-material","--filter-3-thickness",
                        "--maximum-E","--maximum-psi-urad",
                        "--minimum-E", "--read-pixel-size", 
                        "--read-scintillator","--sample-density", 
                        "--sample-material", "--scintillator-density", 
                        "--scintillator-material", "--scintillator-thickness", 
                        "--source-distance", "--step-E"]
        for flag in enable_flags:
            if flag in self.bhard_widgets:
                kind, w, include_cb, _default = self.bhard_widgets[flag]
                if include_cb is not None and not include_cb.isChecked():
                    include_cb.setChecked(True)
        self.log_output.append("Enable beamhardening params")

    def preset_phase(self):
        enable_flags = ["--retrieve-phase-method", 
                        "--pixel-size", 
                        "--propagation-distance", 
                        "--energy", 
                        "--retrieve-phase-alpha"]
        for flag in enable_flags:
            if flag in self.phase_widgets:
                kind, w, include_cb, _default = self.phase_widgets[flag]
                if include_cb is not None and not include_cb.isChecked():
                    include_cb.setChecked(True)
        self.recon_way_box_full.setCurrentText("recon_steps")
        self.log_output.append("Enable phase params, set recon way to recon_steps for full recon")

    def preset_laminography(self):
        enable_flags = ["--lamino-angle", 
                        "--lamino-end-row", 
                        "--lamino-search-step", 
                        "--lamino-search-width", 
                        "--lamino-start-row"]
        for flag in enable_flags:
            if flag in self.Geometry_widgets:
                kind, w, include_cb, _default = self.Geometry_widgets[flag]
                if include_cb is not None and not include_cb.isChecked():
                    include_cb.setChecked(True)
        #self.recon_way_box.setCurrentText("recon_steps")
        self.recon_way_box_full.setCurrentText("recon_steps")
        self.log_output.append("Enable laminography params, set recon way to recon_steps for full recon")
        #place holder: any params need to disable?

    def abort_process(self):
        if not self.process:
            self.log_output.append('<span style="color:red;">\u2139\ufe0f No running process.</span>')
            return

        for p, name in list(self.process):
            if p.state() != QProcess.NotRunning:
                p.terminate()

        for p, name in list(self.process):
            if p.state() != QProcess.NotRunning:
                if not p.waitForFinished(2000):
                    p.kill()
                    p.waitForFinished(2000)
            self.log_output.append(f'<span style="color:red;">\u26d4 [{name}] aborted.</span>')

        self.process.clear()

    def run_command_live(self, cmd, proj_file=None, job_label=None, *, wait=False, cuda_devices=None):
        """
        cmd: list of command and args
        proj_file: projections path
        job_label: label for the job
        wait: whether to wait for the process to finish, if False, return QProcess object immediately, if True, return exit code when finished
        cuda_devices: str, e.g. "0", "1" for GPU tomocupy use
        """
        scan_id = None
        if proj_file:
            try:
                base = os.path.splitext(os.path.basename(proj_file))[0]
                scan_id = base[-4:]
            except Exception:
                scan_id = None

        if job_label is None:
            job_label = "job"
        name = f"{job_label}-{scan_id}" if scan_id else job_label

        cli_str = " ".join(map(str, cmd))
        self.log_output.append(f'\U0001f680 [{name}] start: {cli_str}')
        QApplication.processEvents()

        p = QProcess(self)
        p.setProcessChannelMode(QProcess.ForwardedChannels)

        #define env with CUDA_VISIBLE_DEVICES
        env = QProcessEnvironment.systemEnvironment()
        if cuda_devices is not None:
            env.insert("CUDA_VISIBLE_DEVICES", str(cuda_devices))
        p.setProcessEnvironment(env)
        
        loop = QEventLoop() if wait else None
        result = {"code": None}

        def on_finished(code, status):
            try:
                self.process[:] = [(pp, nn) for (pp, nn) in self.process if pp is not p]
            except Exception:
                pass
            if code != 0:
                self.log_output.append(f'<span style="color:red;">\u274c [{name}] failed, check terminal</span>')
            result["code"] = code
            if loop is not None:
                loop.quit()

        def on_error(_err):
            if result["code"] is None:
                result["code"] = -1
            if loop is not None:
                loop.quit()
            self.log_output.append(f'<span style="color:red;">\u274c [{name}] {p.errorString()}</span>')

        p.finished.connect(on_finished)
        p.errorOccurred.connect(on_error)

        if not isinstance(self.process, list):
            self.process = []
        self.process.append((p, name))

        p.start(str(cmd[0]), [str(a) for a in cmd[1:]])

        if wait:
            loop.exec()
            return int(result["code"])

        return p

    # ===== RECONSTRUCTION METHODS =====

    def try_reconstruction(self):
        proj_file = self.proj_file_box.currentData()
        if not proj_file:
            self.log_output.append(f"\u274c No file")
            return
        recon_way = self.recon_way_box.currentText()
        cor_method = self.cor_method_box.currentText()
        cor_val = self.cor_input.text().strip()
        if cor_method == "auto":
            if cor_val:
                self.log_output.append(f'<span style="color:red;">\u274c no manual cor for auto method</span>')
                return
        else:
            try:
                cor = float(cor_val)
            except ValueError:
                self.log_output.append(f'<span style="color:red;">\u274c wrong rotation axis input</span>')
                return
        # cuda for tomocupy try
        gpu = self.cuda_box_try.currentText().strip()
        #add check box for config, seperate from selecting parameters from GUI
        if self.use_conf_box.isChecked():
            self.log_output.append("\u26a0\ufe0f You are using config file, only recon type, filename, rot axis from GUI")
            config_text = self.config_editor_try.toPlainText()
            if not config_text.strip():
                self.log_output.append(f'<span style="color:red;">\u26a0\ufe0f no text in conf, stop</span>')
                return
            temp_try = os.path.join(self.data_path.text(), "temp_try.conf")
            with open(temp_try, "w") as f:
                f.write(config_text)
            # Base command
            cmd = ["tomocupy", str(recon_way), 
                "--reconstruction-type", "try", 
                "--config", temp_try, 
                "--file-name", proj_file]
            if cor_method == "auto":
                cmd += ["--rotation-axis-auto", "auto"]
            else:
                cmd += ["--rotation-axis-auto", "manual",
                        "--rotation-axis", str(cor)]
        else:
            self.log_output.append('\u26a0\ufe0f You are using params from GUI')
            # Base command
            cmd = ["tomocupy", str(recon_way), 
                "--reconstruction-type", "try", 
                "--file-name", proj_file]
            if cor_method == "auto":
                cmd += ["--rotation-axis-auto", "auto"]
            else:
                cmd += ["--rotation-axis-auto", "manual",
                        "--rotation-axis", str(cor)]

            # Append tabs selections
            cmd += self._gather_params_args()
            cmd += self._gather_rings_args()
            cmd += self._gather_bhard_args()
            cmd += self._gather_phase_args()
            cmd += self._gather_Geometry_args()
            cmd += self._gather_Data_args()                        
            cmd += self._gather_Performance_args()
                                
        code = self.run_command_live(cmd, proj_file=proj_file, job_label="Try recon", wait=True, cuda_devices=gpu)
        try:
            if code == 0:
                self.log_output.append(f'<span style="color:green;">\u2705 Done try recon {proj_file}</span>')
            else:
                self.log_output.append(f'<span style="color:red;">\u274c Try recon {proj_file} failed</span>')
        finally:
            if self.use_conf_box.isChecked():
                try:
                    if os.path.exists(temp_try):
                        os.remove(temp_try)
                        self.log_output.append(f"\U0001f9f9 Removed {temp_try}")
                except Exception as e:
                    self.log_output.append(f'<span style="color:red;">\u26a0\ufe0f Could not remove {temp_try}: {e}</span>')

    def full_reconstruction(self):
        proj_file = self.proj_file_box.currentData()
        recon_way = self.recon_way_box_full.currentText()  # fixed (was currentData)
        try:
            cor_value = float(self.cor_input_full.text())
        except ValueError:
            self.log_output.append(f'<span style="color:red;">\u274c[ERROR] Invalid Full COR value</span>')
            return
        gpu = self.cuda_box_full.currentText().strip()
        if self.use_conf_box.isChecked():
            self.log_output.append("\u26a0\ufe0f You are using config file, only recon type, filename, rot axis from GUI")
            config_text = self.config_editor_full.toPlainText()
            if not config_text.strip():
                self.log_output.append(f'<span style="color:red;">\u26a0\ufe0f No text in conf, stop</span>')
                return
            temp_full = os.path.join(self.data_path.text(), "temp_full.conf")
            with open(temp_full, "w") as f:
                f.write(config_text)
            # Base command
            cmd = ["tomocupy", str(recon_way),
             "--reconstruction-type", "full",
             "--config", temp_full, 
             "--file-name", proj_file, 
             "--rotation-axis", str(cor_value)]    
        else:
            self.log_output.append('\u26a0\ufe0f You are using params from GUI')
            # Base command
            cmd = ["tomocupy", str(recon_way),
               "--reconstruction-type", "full",
               "--file-name", proj_file, 
               "--rotation-axis", str(cor_value)]
            # Append tabs selections
            cmd += self._gather_params_args()
            cmd += self._gather_rings_args()
            cmd += self._gather_bhard_args()
            cmd += self._gather_phase_args()
            cmd += self._gather_Geometry_args()        
            cmd += self._gather_Data_args()                
            cmd += self._gather_Performance_args()
                                
        code = self.run_command_live(cmd, proj_file=proj_file, job_label="Full recon", wait=True, cuda_devices=gpu)
        try:
            if code == 0:
                self.log_output.append(f'<span style="color:green;">\u2705 Done full recon {proj_file}</span>')
            else:
                self.log_output.append(f'<span style="color:red;">\u274c Full recon {proj_file} failed</span>')
        finally:
            if self.use_conf_box.isChecked():
                try:
                    if os.path.exists(temp_full):
                        os.remove(temp_full)
                        self.log_output.append(f"\U0001f9f9 Removed {temp_full}")
                except Exception as e:
                    self.log_output.append(f'<span style="color:red;">\u26a0\ufe0f Could not remove {temp_full}: {e}</span>')
        self.view_btn.setEnabled(True)

    def batch_try_reconstruction(self):
        try:
            start_num = int(self.start_scan_input.text())
            end_num = int(self.end_scan_input.text())
            total = end_num - start_num + 1
        except ValueError:
            self.log_output.append(f'<span style="color:red;">\u274c[ERROR] Invalid start or end scan number</span>')
            return

        folder = self.data_path.text()
        if not os.path.isdir(folder):
            self.log_output.append(f'<span style="color:red;">\u274c[ERROR] Invalid data folder</span>')
            return
        recon_way = self.recon_way_box.currentText()
        cor_method = self.cor_method_box.currentText()  # fixed (was currenText)
        cor_val = self.cor_input.text().strip()
        cor = None
        if cor_method == 'auto':
            if cor_val:
                self.log_output.append(f'<span style="color:red;">\u274c no manual cor for auto method</span>')
                return
        else:
            try:
                cor = float(cor_val)
            except ValueError:
                self.log_output.append(f'<span style="color:red;">\u274c wrong rotation axis input</span>')
                return
        gpu = self.cuda_box_try.currentText().strip()
        if self.use_conf_box.isChecked():
            self.log_output.append('\ufe0f You are using config file, only recon type, filename, rot axis from GUI')
            config_text = self.config_editor_try.toPlainText()
            if not config_text.strip():
                self.log_output.append(f'<span style="color:red;">\u26a0\ufe0f No text in conf, stop</span>')
                return
            temp_try = os.path.join(folder, "temp_batch_try.conf")
            with open(temp_try, "w") as f:
                f.write(config_text)
            cmd = ["tomocupy", str(recon_way), 
                    "--reconstruction-type", "try", 
                    "--config", temp_try]      
        else:      
            self.log_output.append('\ufe0f You are using params from GUI')
            cmd = ["tomocupy", str(recon_way), 
                    "--reconstruction-type", "try"]        
        summary = {"done": [], "fail": [], 'no_file': []}
        try:
            for i, scan_num in enumerate(range(start_num, end_num + 1), start=1):
                scan_str = f"{scan_num:04d}"
                match_files = glob.glob(os.path.join(folder, f"*{scan_str}.h5"))
                if not match_files:
                    self.log_output.append(f'<span style="color:#fb8c00;">[WARN] No file found for scan {scan_str}, skipping</span>')
                    summary['no_file'].append(scan_str)
                    continue
                proj_file = match_files[0]
                cmd += ["--file-name", proj_file]
                if cor_method == "auto":
                    cmd += ["--rotation-axis-auto", "auto"]
                else:
                    cmd += ["--rotation-axis-auto", "manual",
                            "--rotation-axis", str(cor)]
                if self.use_conf_box.isChecked() is False:
                    # Append Params
                    cmd += self._gather_params_args()
                    cmd += self._gather_rings_args()
                    cmd += self._gather_bhard_args()
                    cmd += self._gather_phase_args()
                    cmd += self._gather_Geometry_args()      
                    cmd += self._gather_Data_args()                                          
                    cmd += self._gather_Performance_args()
                                
                code = self.run_command_live(cmd, proj_file=proj_file, job_label=f'batch try {i}/{total}', wait=True, cuda_devices=gpu)
                if code == 0:
                    self.log_output.append(f'<span style="color:green;">\u2705 Done try recon {proj_file}</span>')
                    summary['done'].append(scan_str)
                else:
                    self.log_output.append(f'<span style="color:red;">\u274c Try recon {proj_file} failed</span>')
                    summary['fail'].append(scan_str)
        finally:
            if self.use_conf_box.isChecked():
                try:
                    if os.path.exists(temp_try):
                        os.remove(temp_try)
                        self.log_output.append(f"\U0001f9f9 Removed {temp_try}")
                except Exception as e:
                    self.log_output.append(f'<span style="color:red;">\u26a0\ufe0f Could not remove {temp_try}: {e}</span>')
            self.log_output.append(f"\u2705Done batch try, check summary: {str(summary)}")

    def batch_full_reconstruction(self):
        """use cor_log.json and the config file in the right config txt box files to do 
            batch recon and delete cor_log.json and temp_full.conf after batch, and only run batch recon full for files 
            not reconstructed yet, or part recon
            two cases: full recon, or part recon defining by tomocupy"""
        log_file = os.path.join(self.data_path.text(), "rot_cen.json")
        if not os.path.exists(log_file):
            self.log_output.append(f'<span style="color:red;">\u274c[ERROR] rot_cen.json not found</span>')
            return
        with open(log_file) as f:
            data = json.load(f)
        gpu = self.cuda_box_full.currentText().strip()
        if self.use_conf_box.isChecked():
            self.log_output.append(f"\u26a0\ufe0f You are using conf file, recon way is from GUI")
            config_text = self.config_editor_full.toPlainText()
            if not config_text.strip():
                self.log_output.append(f'<span style="color:red;">\u26a0\ufe0f no text in conf, stop</span>')
                return
            temp_full = os.path.join(self.data_path.text(), "temp_full.conf")
            with open(temp_full, "w") as f:
                f.write(config_text)
            cmd = ["tomocupy", self.recon_way_box_full.currentText(), 
                "--reconstruction-type", "full", 
                "--config", temp_full]
        else:
            self.log_output.append("\u26a0\ufe0f You are using params from GUI")
            cmd = ["tomocupy", self.recon_way_box_full.currentText(), 
                "--reconstruction-type", "full"]
        summary = {"done": [], "fail": []}
        size = len(data)
        try:
            for i, (proj_file, (cor_value,status)) in enumerate(data.items(), start=1):
                if status == "no_rec" or status == "part_rec":
                    cmd += ["--file-name", proj_file]
                    cmd += ["--rotation-axis", str(cor_value)]
                    # Append Params
                    cmd += self._gather_params_args()
                    cmd += self._gather_rings_args()
                    cmd += self._gather_bhard_args()
                    cmd += self._gather_phase_args()
                    cmd += self._gather_Geometry_args()        
                    cmd += self._gather_Data_args()                                        
                    cmd += self._gather_Performance_args()
                                                                
                    code = self.run_command_live(cmd, proj_file=proj_file, job_label=f"batch full {i}/{size}", wait=True, cuda_devices=gpu)
                    if code == 0:
                        self.log_output.append(f'<span style="color:green;">\u2705 Done full recon {proj_file}</span>')
                        summary['done'].append(f"{os.path.basename(proj_file)}")
                    else:
                        self.log_output.append(f'<span style="color:red;">\u274c full recon {proj_file} failed</span>')
                        summary['fail'].append(f"{os.path.basename(proj_file)}")      
                else:
                    continue          
        finally:
            if self.use_conf_box.isChecked():
                try:
                    if os.path.exists(temp_full):
                        os.remove(temp_full)
                        self.log_output.append(f"\U0001f9f9 Removed {temp_full}")
                except Exception as e:
                    self.log_output.append(f'<span style="color:red;">\u26a0\ufe0f Could not remove {temp_full}: {e}</span>')
            self.log_output.append(f"\u2705Done batch full, check summary: {str(summary)}")

    # ===== COR MANAGEMENT =====
    def record_cor_to_json(self):
        data_folder = self.data_path.text().strip()
        cor_value = self.cor_input_full.text().strip()
        proj_file = self.proj_file_box.currentData()

        if not (data_folder and cor_value and proj_file):
            self.log_output.append(f'<span style="color:red;">\u26a0\ufe0fMissing data folder, COR, or projection file</span>')
            return

        try:
            cor_value = float(cor_value)
        except ValueError:
            self.log_output.append(f'<span style="color:red;">\u274c[ERROR] COR value is not a valid number</span>')
            return

        json_path = os.path.join(data_folder, "rot_cen.json")

        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                try:
                    self.cor_data = json.load(f)
                    fns = list(self.cor_data.keys())
                except json.JSONDecodeError:
                    self.cor_data = {}
        else:
            self.cor_data = {}
            fns = []
        
        if proj_file in fns:
            overfn_msg_box = QMessageBox(self)
            overfn_msg_box.setIcon(QMessageBox.Warning)
            overfn_msg_box.setWindowTitle("Overwrite Existing files in log?")
            overfn_msg_box.setText(f"The scan:\n{os.path.basename(proj_file)}\nalready exists in rot_cen.json.\n\nDo you want to overwrite it?")
            overfn_msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            overfn_msg_box.setDefaultButton(QMessageBox.No)
            result = overfn_msg_box.exec()
            if result != QMessageBox.Yes:
                self.log_output.append("\u26a0\ufe0fNot take COR")
                return
        # check if recon folder exists and add comment to cor_log               
        proj_name = os.path.splitext(os.path.basename(proj_file))[0]
        full_dir = os.path.join(f"{data_folder}_rec", f"{proj_name}_rec")
        num_recon = len(glob.glob(f'{full_dir}/*.tiff'))
        raw_prj = proj_file  # fixed: currentData() already carries the full path
        try:
            self._raw_h5 = h5py.File(raw_prj, "r")
        except Exception as e:
            self.log_output.append(f'<span style="color:red;">\u274c Failed to open H5: {e}</span>')
            return
        self.raw_files_y = self._raw_h5['/exchange/data'].shape[1] # y in prj, z in recon
        self._raw_h5.close()

        if os.path.exists(full_dir) is True and num_recon == self.raw_files_y:
            status = "full_rec"
        elif os.path.exists(full_dir) is True and num_recon < self.raw_files_y:
            status = "part_rec"
        elif os.path.exists(full_dir) is False:
            status = "no_rec"
        
        self.cor_data[proj_file] = (cor_value, status)
        try:
            with open(json_path, "w") as f:
                json.dump(self.cor_data, f, indent=2)
            self.log_output.append(f"\u2705[INFO] COR saved for: {proj_file}")
        except Exception as e:
            self.log_output.append(f'<span style="color:red;">\u274cFailed to save rot_cen.json: {e}</span>')
            return

        self.cor_json_output.clear()
        for k, (v1,v2) in self.cor_data.items():
            base = os.path.splitext(os.path.basename(k))[0]
            last4 = base[-4:] #for 7bm
            self.cor_json_output.append(f"{last4} : {v1} {v2}")

    def load_cor_to_jsonbox(self):
        data_folder = self.data_path.text().strip()
        json_path = os.path.join(data_folder, "rot_cen.json")

        if not os.path.exists(json_path):
            self.log_output.append("\u26a0\ufe0f[WARNING] no rot_cen.json, create one")
            with open(json_path, "w") as f:
                json.dump(self.cor_data, f, indent=2)
            return
        try:
            with open(json_path, "r") as f:
                self.cor_data = json.load(f)
            self.cor_json_output.clear()
            for k, (v1, v2) in self.cor_data.items():
                base = os.path.splitext(os.path.basename(k))[0]
                last4 = base[-4:] #for 7bm
                self.cor_json_output.append(f"{last4} : {v1} {v2}")
            self.log_output.append("\u2705[INFO] COR log reloaded.")
        except Exception as e:
            self.log_output.append(f"\u274c[ERROR] Failed to load COR log: {e}")
            return
        
    def refresh_cor_json(self):
        data_folder = self.data_path.text().strip()
        self.refresh_json_btn.setEnabled(False)
        json_path = os.path.join(data_folder, "rot_cen.json")
        if not os.path.exists(json_path):
            self.log_output.append("\u274c[ERROR] no rot_cen.json")
            self.refresh_json_btn.setEnabled(True)
            return
        try:
            with open(json_path, "r") as f:
                self.cor_data = json.load(f)
            self.cor_json_output.clear()
            for k, (v1, v2) in self.cor_data.items():
                base = os.path.splitext(os.path.basename(k))[0]
                rec_f = f"{data_folder}_rec/{base}_rec"
                if os.path.exists(rec_f) is False:
                    v2 = "no_rec"
                else:
                    num_recon = len(glob.glob(f'{rec_f}/*.tiff'))
                    prj = h5py.File(k, "r")
                    num_prj = prj['/exchange/data'].shape[1] # y in prj, z in recon
                    prj.close()
                    if num_recon == num_prj:
                        v2 = "full_rec"
                    elif num_recon < num_prj:
                        v2 = "part_rec"
                self.cor_data[k] = (v1, v2)
                last4 = base[-4:] #for 7bm
                self.cor_json_output.append(f"{last4} : {v1} {v2}")
            try:
                with open(json_path, "w") as f:
                    json.dump(self.cor_data, f, indent=2)
                self.log_output.append(f"\u2705[INFO] COR refreshed")
                self.refresh_json_btn.setEnabled(True)
            except Exception as e:
                self.refresh_cor_json_btn.setEnabled(True)
                self.log_output.append(f'<span style="color:red;">\u274cFailed to save new rot_cen.json: {e}</span>')
                return
        except Exception as e:
            self.log_output.append(f'<span style="color:red;">\u274cFailed to refresh rot_cen.json: {e}</span>')
            self.refresh_json_btn.setEnabled(True)
            return

    # ===== IMAGE VIEWING =====
    def view_raw(self):
        "use h5py read, assume same structure for aps IMG"
        proj_file = self.proj_file_box.currentData()
        if not proj_file:
            self.log_output.append("\u274c No file selected")
            return
        raw_fn = proj_file  # fixed: currentData() already carries the full path
        try:
            self._raw_h5 = h5py.File(raw_fn, "r")
        except Exception as e:
            self.log_output.append(f'<span style="color:red;">\u274c Failed to open H5: {e}</span>')
            return
        self.raw_files_num = self._raw_h5['/exchange/data'].shape[0] # number of projections
        # safe mean to float to avoid uint overflows
        self.dark = np.array(self._raw_h5['/exchange/data_dark'][:], dtype=np.float32).mean(axis=0)
        self.flat = np.array(self._raw_h5['/exchange/data_white'][:], dtype=np.float32).mean(axis=0)
        self._keep_zoom = False
        self._clear_roi()
        self._reset_view_state()
        first_img = self._raw_h5['/exchange/data'][0, :, :]
        self.set_image_scale(first_img, flag="raw")
        try:
            self.slice_slider.valueChanged.disconnect()
        except TypeError:
            pass
        self.slice_slider.setMaximum(self.raw_files_num - 1)
        self.slice_slider.valueChanged.connect(self.update_raw_slice)
        # Store the source filename for display
        self._current_source_file = os.path.basename(raw_fn)
        self._current_view_mode = "raw"
        self.update_raw_slice()

    def view_try_reconstruction(self):
        data_folder = self.data_path.text().strip()
        proj_file = self.proj_file_box.currentData()
        proj_name = os.path.splitext(os.path.basename(proj_file))[0]
        try_dir = os.path.join(f"{data_folder}_rec", "try_center", proj_name)
        self.preview_files = sorted(glob.glob(os.path.join(try_dir, "*.tiff")))
        if not self.preview_files:
            self.log_output.append(f'<span style="color:red;">\u274cNo try folder</span>')
            return
        self._keep_zoom = False
        self._clear_roi()
        self._reset_view_state()
        self.set_image_scale(self.preview_files[0])
        try:
            self.slice_slider.valueChanged.disconnect()
        except TypeError:
            pass
        self.slice_slider.setMaximum(len(self.preview_files) - 1)
        self.slice_slider.valueChanged.connect(self.update_try_slice)
        # Store the source filename for display
        self._current_source_file = os.path.basename(proj_file)
        self._current_view_mode = "try"
        self.update_try_slice()

    def view_full_reconstruction(self):
        data_folder = self.data_path.text().strip()
        proj_file = self.proj_file_box.currentData()
        proj_name = os.path.splitext(os.path.basename(proj_file))[0]
        full_dir = os.path.join(f"{data_folder}_rec", f"{proj_name}_rec")

        self.full_files = sorted(glob.glob(os.path.join(full_dir, "*.tiff")))
        if not self.full_files:
            self.log_output.append(f'<span style="color:red;">\u26a0\ufe0f No full reconstruction images found</span>')
            return
        self._keep_zoom = False
        self._clear_roi()
        self._reset_view_state()
        self.set_image_scale(self.full_files[0])
        try:
            self.slice_slider.valueChanged.disconnect()
        except TypeError:
            pass
        self.slice_slider.setMaximum(len(self.full_files) - 1)
        self.slice_slider.valueChanged.connect(self.update_full_slice)
        # Store the source filename for display
        self._current_source_file = os.path.basename(proj_file)
        self._current_view_mode = "full"
        self.update_full_slice()

    def set_image_scale(self, img_path, flag=None):
        if flag == "raw":
            img = img_path
        else:
            img = np.array(Image.open(img_path))
        self.vmin, self.vmax = round(np.nanmin(img), 5), round(np.nanmax(img), 5)
        self.min_input.setText(str(self.vmin))
        self.max_input.setText(str(self.vmax))

    # ===== ROI AND CONTRAST =====
    def draw_box(self):
        """Enable interactive ROI drawing. Drag to create; click to finish."""
        if self._current_img is None:
            self.log_output.append("\u26a0\ufe0f No image loaded to draw box.")
            return

        if self.rect_selector is None:
            style = dict(edgecolor='red', facecolor='none', linewidth=2, alpha=1.0)
            self.rect_selector = RectangleSelector(
                self.ax,
                self._on_rect_complete,
                useblit=True,
                button=[1],
                minspanx=2, minspany=2,
                spancoords='data',
                interactive=True,
                props=style
            )
        self._drawing_roi = True
        self.roi_extent = None
        self.rect_selector.set_active(True)
        self.log_output.append("Drag to draw ROI, release to set. Any click on image will hide ROI.")

    def _on_rect_complete(self, eclick, erelease):
        """Store ROI extents when user finishes dragging the rectangle."""
        x0, y0 = eclick.xdata, eclick.ydata
        x1, y1 = erelease.xdata, erelease.ydata
        if None in (x0, y0, x1, y1):
            self.roi_extent = None
            self._drawing_roi = False
            return
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
                try:
                    self.rect_selector.set_active(False)
                    if hasattr(self.rect_selector, "set_visible"):
                        self.rect_selector.set_visible(False)
                except Exception:
                    pass
                self.rect_selector = None
        finally:
            self.roi_extent = None

    def _on_canvas_click(self, event):
        """Any click on the image hides/removes the ROI (unless we are mid-draw)."""
        if event.inaxes != self.ax:
            return
        if self._drawing_roi:
            return
        if self.roi_extent is None and self.rect_selector is None:
            return

        try:
            if self.rect_selector is not None:
                self.rect_selector.set_active(False)
                for art in getattr(self.rect_selector, 'artists', []):
                    art.set_visible(False)
                self.rect_selector = None
        except Exception:
            pass
        self.roi_extent = None
        self.canvas.draw_idle()
        self.log_output.append(f'<span style="color:green;">ROI cleared</span>')

    def _on_mouse_move(self, event):
        # show x,y and pixel value when mouse on image
        if event.inaxes != self.ax or self._current_img is None:
            if hasattr(self, "coord_label"):
                self.coord_label.setText("")
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            if hasattr(self, "coord_label"):
                self.coord_label.setText("")
            return
        h, w = self._current_img.shape[:2]
        ix, iy = int(round(x)), int(round(y))
        if 0 <= ix < w and 0 <= iy < h:
            val = self._current_img[iy, ix]
            msg = f"({ix},{iy}): {float(val):.5f}"
        else:
            msg = ""
        if hasattr(self, "coord_label"):
            self.coord_label.setText(msg)

    def auto_img_contrast(self, saturation=10):
        """Fiji-like Auto: trims tails within current window; uses ROI if present; never edits pixels."""
        if self._current_img is None:
            self.log_output.append("\u26a0\ufe0f No image loaded to auto contrast.")
            return

        img = self._current_img

        if self.roi_extent is not None:
            x0, x1, y0, y1 = self.roi_extent
            h, w = img.shape[:2]
            x0 = max(0, min(w, int(np.floor(x0))))
            x1 = max(0, min(w, int(np.ceil(x1))))
            y0 = max(0, min(h, int(np.floor(y0))))
            y1 = max(0, min(h, int(np.ceil(y1))))
            if x1 <= x0 or y1 <= y0:
                self.log_output.append("\u26a0\ufe0f ROI too small.")
                return
            data = img[y0:y1, x0:x1]
        else:
            data = img

        a = np.asarray(data, dtype=float).ravel()
        a = a[np.isfinite(a)]
        if a.size == 0:
            self.log_output.append("\u26a0\ufe0f No finite pixels for Auto.")
            return

        vmin = self.vmin if self.vmin is not None else float(np.nanmin(a))
        vmax = self.vmax if self.vmax is not None else float(np.nanmax(a))
        vis = a[(a >= vmin) & (a <= vmax)]
        if vis.size < 64:
            vis = a

        lo, hi = np.nanpercentile(vis, [1.5, 99.5])
        if not np.isfinite(lo) or not np.isfinite(hi) or lo >= hi:
            lo, hi = float(np.nanmin(vis)), float(np.nanmax(vis))
            if lo >= hi:
                hi = lo + 1.0

        new_vmin, new_vmax = float(round(lo, 5)), float(round(hi, 5))
        if (new_vmin, new_vmax) == (self.vmin, self.vmax):
            self.log_output.append("Auto B&C optimal")
            return

        self.vmin, self.vmax = new_vmin, new_vmax

        self.min_input.setText(str(self.vmin))
        self.max_input.setText(str(self.vmax))

        im = self.ax.images[0] if self.ax.images else None
        if im is not None:
            im.set_clim(self.vmin, self.vmax)
            self.canvas.draw_idle()
        else:
            self.refresh_current_image()

    def reset_img_contrast(self): #link to Reset button
        if self._current_img is None:
            self.log_output.append("\u26a0\ufe0f No image loaded to reset contrast.")
            return
        else:
            self.vmin, self.vmax = round(self._current_img.min(), 5), round(self._current_img.max(), 5)
            self.min_input.setText(str(self.vmin))
            self.max_input.setText(str(self.vmax))            
            im = self.ax.images[0] if self.ax.images else None
            if im is not None:
                im.set_clim(self.vmin, self.vmax)
                self.canvas.draw_idle()
            else:
                self.refresh_current_image()

    def update_raw_slice(self):
        self._keep_zoom = True
        idx = self.slice_slider.value()
        if 0 <= idx < self.raw_files_num:
            self.show_image(img_path=idx, flag="raw")

    def update_try_slice(self):
        self._keep_zoom = True
        idx = self.slice_slider.value()
        if 0 <= idx < len(self.preview_files):
            self.show_image(self.preview_files[idx], flag=None)

    def update_full_slice(self):
        self._keep_zoom = True
        idx = self.slice_slider.value()
        if 0 <= idx < len(self.full_files):
            self.show_image(self.full_files[idx], flag=None)

    def _safe_open_image(self, path, flag=None, retries=3): 
        #add flag to seperate raw, recon
        for _ in range(retries):
            try:
                if flag == "raw":
                    return self._raw_h5['/exchange/data'][path,:,:]
                else:
                    with Image.open(path) as im:
                        return np.array(im)
            except Exception:
                QApplication.processEvents()
        if flag == "raw":
            return self._raw_h5['/exchange/data'][path,:,:]
        else:
            with Image.open(path) as im:
                return np.array(im)

    def show_image(self, img_path, flag=None):
        #Flag arg to seperate prj and recon 
        if flag == "raw":
            img = self._raw_h5['/exchange/data'][img_path,:,:] #for raw projections, it takes img_path as idx
            img = (img - self.dark)/(self.flat - self.dark)
        else:
            img = self._safe_open_image(img_path)
            if img.ndim == 3:
                img = img[..., 0]
        h, w = img.shape
        self._current_img = img
        self._current_img_path = img_path
        self._clear_roi()
        self.ax.clear()
        im = self.ax.imshow(
            img,
            cmap=self.current_cmap,
            vmin=self.vmin,
            vmax=self.vmax,
            origin="upper",
            extent=[0, w, h, 0]
        )

        # Build title with source filename - LARGE and VISIBLE
        if hasattr(self, '_current_source_file') and hasattr(self, '_current_view_mode'):
            title = f"{self._current_source_file} [{self._current_view_mode}] - {os.path.basename(str(img_path))}"
        else:
            title = os.path.basename(str(img_path))

        # Adapt title color and background to current theme
        current_theme = self.theme_manager.get_current_theme()
        if current_theme == 'dark':
            title_color = 'white'
            bg_color = 'black'
        else:
            title_color = 'black'
            bg_color = 'white'

        self.ax.set_title(title, pad=15, fontsize=16, fontweight='bold', color=title_color)
        self.ax.set_facecolor(bg_color)
        self.fig.patch.set_facecolor(bg_color)

        self.ax.set_aspect('equal', adjustable='box')  # square pixels; obey zoom limits without warnings
        if (self._keep_zoom and
            self._last_image_shape == (h, w) and
            self._last_xlim is not None and
            self._last_ylim is not None):
            self.ax.set_xlim(self._last_xlim)
            self.ax.set_ylim(self._last_ylim)
        else:
            left, right, bottom, top = im.get_extent()
            self.ax.set_xlim(left, right)
            self.ax.set_ylim(bottom, top)

        self.canvas.draw_idle()

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
        try:
            if event.button != MouseButton.LEFT:
                return
        except Exception:
            pass

        mode = getattr(self.toolbar, "mode", "")
        if mode in ("zoom rect", "pan/zoom"):
            self._remember_view()
            self._keep_zoom = True

            try:
                if mode == "zoom rect":
                    self.toolbar.zoom()
                else:
                    self.toolbar.pan()
            except Exception:
                pass

            try:
                self.toolbar.set_message("")
            except Exception:
                pass
            try:
                self.canvas.setCursor(Qt.ArrowCursor)
            except Exception:
                pass

    def _reset_view_state(self):
        """Forget any prior zoom/pan so the next image shows full frame."""
        try:
            mode = getattr(self.toolbar, "mode", "")
            if mode == "zoom rect":
                self.toolbar.zoom()
            elif mode == "pan/zoom":
                self.toolbar.pan()
            try:
                self.toolbar.set_message("")
            except Exception:
                pass
        except Exception:
            pass

        self._keep_zoom = False
        self._last_xlim = None
        self._last_ylim = None
        self._last_image_shape = None


    def _on_toolbar_home(self):
        # forget any persisted zoom so the next slice uses full extents
        self._keep_zoom = False
        self._last_xlim = None
        self._last_ylim = None
        self._last_image_shape = None

    # ===== TOMOLOG METHODS =====

    def get_note_value(self):
        note = self.note_input.text().strip()
        return f'"{note}"' if note else None

    def help_tomolog(self):
        """Run the CLI `tomolog run -h` and show output in the GUI log."""
        name = "tomolog-help"
        self.log_output.append(f"\U0001f4d6[{name}] tomolog run -h")

        p = QProcess(self)
        p.setProcessChannelMode(QProcess.SeparateChannels)

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

        def _done(code, _status):
            try:
                self.process[:] = [(pp, nn) for (pp, nn) in self.process if pp is not p]
            except Exception:
                pass
            self.log_output.append(f"\u2705[{name}] done." if code == 0
                                else f"\u274c[{name}] failed with code {code}.")

        p.finished.connect(_done)
        p.errorOccurred.connect(
            lambda _err: self.log_output.append(f"\u274c[{name}] {p.errorString()}")
        )

        if not isinstance(self.process, list):
            self.process = []
        self.process.append((p, name))

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
            self.log_output.append(f'<span style="color:red;">\u274c[ERROR] Data folder not set</span>')
            return
        
        flist = []
        if not scan_number:
            fn = self.proj_file_box.currentText()
            filename = os.path.join(data_folder, f"{fn}")
            flist.append(filename)
            if not filename:
                self.log_output.append(f'<span style="color:red;">\u274c[ERROR] Filename not exist</span>')
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
                        self.log_output.append(f'<span style="color:red;">\u274c[ERROR] Invalid range: {sn}</span>')
                else:
                    try:
                        numbers.add(int(sn))
                    except ValueError:
                        self.log_output.append(f'<span style="color:red;">\u274c[ERROR] Invalid scan number: {sn}</span>')
            for n in numbers:
                fn = os.path.join(data_folder, f"*{n:04d}.h5")
                try:
                    filename = glob.glob(fn)[0]
                except IndexError:
                    self.log_output.append(f'<span style="color:red;">Scan {n:04d} not exist, stop</span>')
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
            
            QApplication.processEvents()
            code = self.run_command_live(cmd, proj_file=input_fn, job_label="tomolog", wait=True, cuda_devices=None)
            if code == 0:
                self.log_output.append(f'<span style="color:green;">\u2705 Done tomolog {input_fn}</span>')
            else:
                self.log_output.append(f'<span style="color:red;">\u274c Tomolog {input_fn} failed</span>')

    # ===== BATCH PROCESSING METHODS =====

    def _get_batch_machine_command(self, cmd, machine):
        """
        Wrap command for remote execution via SSH if needed

        Args:
            cmd: List of command arguments (e.g., ["tomocupy", "recon", ...])
            machine: Machine name ("Local", "tomo1", etc.)

        Returns:
            List of command arguments, potentially wrapped in SSH
        """
        if machine == "Local":
            return cmd

        # Build SSH command to execute on remote machine
        # Assumes SSH keys are set up for passwordless login
        # Properly quote arguments for shell execution
        remote_cmd = " ".join([f'"{str(arg)}"' if " " in str(arg) else str(arg) for arg in cmd])

        # Use SSH to execute the command on the remote machine
        ssh_cmd = ["ssh", machine, remote_cmd]

        return ssh_cmd

    def _run_reconstruction_on_machine(self, file_path, recon_type='try'):
        """
        Run reconstruction on selected machine (local or remote)

        Args:
            file_path: Path to the .h5 file
            recon_type: 'try' or 'full'

        Returns:
            Exit code (0 for success)
        """
        machine = self.batch_machine_box.currentText()

        # Get reconstruction parameters from Main tab
        recon_way = self.recon_way_box.currentText()

        # Get COR value EXCLUSIVELY from the batch table for this file
        filename = os.path.basename(file_path)
        cor_val = None
        for file_info in self.batch_file_list:
            if file_info['filename'] == filename:
                cor_val = file_info['cor_input'].text().strip()
                break

        # Batch tab ALWAYS uses manual COR with the value from the batch table
        # Validate COR input - batch tab requires COR to be set in table
        if not cor_val:
            self.log_output.append(f'<span style="color:red;">❌ No COR value in batch table for {filename}</span>')
            return -1

        try:
            cor = float(cor_val)
            self.log_output.append(f'📍 Using COR value from batch table: {cor_val} for {filename}')
        except ValueError:
            self.log_output.append(f'<span style="color:red;">❌ Invalid COR value "{cor_val}" for {filename}</span>')
            return -1

        gpu = self.cuda_box_try.currentText().strip() if recon_type == 'try' else self.cuda_box_full.currentText().strip()

        # Build command
        # Batch tab ALWAYS uses manual COR with the value from the batch table
        if self.use_conf_box.isChecked():
            config_editor = self.config_editor_try if recon_type == 'try' else self.config_editor_full
            config_text = config_editor.toPlainText()
            if not config_text.strip():
                self.log_output.append(f'<span style="color:red;">⚠️ No config text</span>')
                return -1

            temp_conf = os.path.join(self.data_path.text(), f"temp_{recon_type}.conf")
            with open(temp_conf, "w") as f:
                f.write(config_text)

            cmd = ["tomocupy", str(recon_way),
                   "--reconstruction-type", recon_type,
                   "--config", temp_conf,
                   "--file-name", file_path,
                   "--rotation-axis-auto", "manual",
                   "--rotation-axis", str(cor)]
        else:
            cmd = ["tomocupy", str(recon_way),
                   "--reconstruction-type", recon_type,
                   "--file-name", file_path,
                   "--rotation-axis-auto", "manual",
                   "--rotation-axis", str(cor)]

        # Wrap command for remote execution if needed
        cmd = self._get_batch_machine_command(cmd, machine)

        # Log the machine being used
        if machine != "Local":
            self.log_output.append(f'🖥️ Running on {machine}: {os.path.basename(file_path)}')

        # Execute command
        code = self.run_command_live(cmd, proj_file=file_path,
                                     job_label=f"{recon_type}-{machine}",
                                     wait=True, cuda_devices=gpu if machine == "Local" else None)

        return code

    def _format_file_size(self, size_bytes):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def _batch_checkbox_clicked(self, row, checked):
        """
        Handle checkbox clicks with shift-click support for range selection
        If shift is held, select all rows between last click and current click
        """
        from PyQt5.QtWidgets import QApplication

        modifiers = QApplication.keyboardModifiers()
        from PyQt5.QtCore import Qt

        if modifiers == Qt.ShiftModifier and self.batch_last_clicked_row is not None:
            # Shift-click: select range
            start_row = min(self.batch_last_clicked_row, row)
            end_row = max(self.batch_last_clicked_row, row)

            # Get the first selected row's COR value for propagation
            first_cor = None
            first_filename = None
            for file_info in self.batch_file_list:
                if file_info['row'] == start_row:
                    first_cor = file_info['cor_input'].text().strip()
                    first_filename = file_info['filename']
                    break

            # Validate that first row has COR value
            if not first_cor:
                QMessageBox.warning(
                    self, "Missing COR",
                    f"The first selected file ({first_filename}) must have a COR value.\n"
                    f"Please enter a COR value for this file before shift-selecting."
                )
                # Uncheck the current checkbox since shift-select failed
                for file_info in self.batch_file_list:
                    if file_info['row'] == row:
                        file_info['checkbox'].setChecked(False)
                        break
                return

            # Select all rows in range and propagate COR if not set
            for r in range(start_row, end_row + 1):
                for file_info in self.batch_file_list:
                    if file_info['row'] == r:
                        # Check the checkbox
                        file_info['checkbox'].setChecked(True)

                        # Propagate COR from first if this row doesn't have one
                        current_cor = file_info['cor_input'].text().strip()
                        if not current_cor and first_cor:
                            file_info['cor_input'].setText(first_cor)
                        break

            self.log_output.append(f'<span style="color:green;">✅ Selected rows {start_row} to {end_row} ({end_row - start_row + 1} files)</span>')
            if first_cor:
                propagated_count = sum(1 for r in range(start_row, end_row + 1)
                                     for f in self.batch_file_list
                                     if f['row'] == r and f['cor_input'].text().strip() == first_cor)
                if propagated_count > 1:  # More than just the first one
                    self.log_output.append(f'<span style="color:blue;">📍 Propagated COR value {first_cor} to {propagated_count - 1} file(s)</span>')

        # Update last clicked row
        self.batch_last_clicked_row = row

    def _update_row_color(self, file_info):
        """Update the row color based on current reconstruction status"""
        try:
            # Check reconstruction status
            data_folder = self.data_path.text().strip()
            filename = file_info['filename']
            proj_name = os.path.splitext(filename)[0]
            try_dir = os.path.join(f"{data_folder}_rec", "try_center", proj_name)
            full_dir = os.path.join(f"{data_folder}_rec", f"{proj_name}_rec")

            has_try = os.path.isdir(try_dir) and len(glob.glob(os.path.join(try_dir, "*.tiff"))) > 0
            has_full = os.path.isdir(full_dir) and len(glob.glob(os.path.join(full_dir, "*.tiff"))) > 0

            # Determine new color
            if has_full:
                row_color = "green"
            elif has_try:
                row_color = "orange"
            else:
                row_color = "red"

            # Update the checkbox widget border color
            if 'checkbox' in file_info:
                checkbox = file_info['checkbox']
                checkbox_widget = checkbox.parentWidget()
                if checkbox_widget:
                    checkbox_widget.setStyleSheet(f"QWidget {{ border-left: 6px solid {row_color}; }}")

            # Update stored status
            file_info['recon_status'] = row_color

        except Exception as e:
            # Silently ignore errors (widget might be deleted)
            pass

    def _refresh_batch_file_list(self):
        """Refresh the file list in the batch processing tab"""
        folder = self.data_path.text()
        if not folder or not os.path.isdir(folder):
            QMessageBox.warning(self, "Warning", "Please select a valid data folder first.")
            return

        # Warn if queue is running
        if self.batch_running:
            reply = QMessageBox.question(
                self, 'Queue Running',
                f'A batch queue is currently running ({len(self.batch_running_jobs)} jobs active, {len(self.batch_job_queue)} queued).\n\n'
                f'Refreshing will delete the table widgets but jobs will continue running in the background.\n\n'
                f'Continue with refresh?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            self.log_output.append(f'<span style="color:orange;">⚠️  Refreshed file list while queue was running - status updates may be lost</span>')

        # Get all .h5 files
        h5_files = sorted(glob.glob(os.path.join(folder, "*.h5")), key=os.path.getmtime, reverse=True)

        # Save current COR values before clearing (to preserve user input)
        cor_values = {}
        for file_info in self.batch_file_list:
            try:
                filename = file_info['filename']
                cor_val = file_info['cor_input'].text().strip()
                if cor_val:
                    cor_values[filename] = cor_val
            except (KeyError, RuntimeError):
                # Widget may have been deleted
                pass

        # Clear existing table - disable sorting first to avoid issues
        self.batch_file_table.setSortingEnabled(False)
        self.batch_file_table.setRowCount(0)
        self.batch_file_list = []
        # Reset last clicked row to avoid stale row references
        self.batch_last_clicked_row = None

        # Populate table
        data_folder = self.data_path.text().strip()
        for file_path in h5_files:
            filename = os.path.basename(file_path)
            row = self.batch_file_table.rowCount()
            self.batch_file_table.insertRow(row)

            # Check reconstruction status
            proj_name = os.path.splitext(filename)[0]
            try_dir = os.path.join(f"{data_folder}_rec", "try_center", proj_name)
            full_dir = os.path.join(f"{data_folder}_rec", f"{proj_name}_rec")

            has_try = os.path.isdir(try_dir) and len(glob.glob(os.path.join(try_dir, "*.tiff"))) > 0
            has_full = os.path.isdir(full_dir) and len(glob.glob(os.path.join(full_dir, "*.tiff"))) > 0

            # Determine row color based on reconstruction status
            if has_full:
                row_color = "green"  # Full reconstruction exists
            elif has_try:
                row_color = "orange"  # Only try reconstruction exists
            else:
                row_color = "red"  # No reconstruction

            # Store file info
            file_info = {
                'path': file_path,
                'filename': filename,
                'status': 'Ready',
                'row': row,
                'recon_status': row_color
            }
            self.batch_file_list.append(file_info)

            # Checkbox for selection with shift-click support
            checkbox = QCheckBox()
            checkbox.clicked.connect(lambda checked, r=row: self._batch_checkbox_clicked(r, checked))
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.batch_file_table.setCellWidget(row, 0, checkbox_widget)
            file_info['checkbox'] = checkbox

            # Filename - show full name and set tooltip with full path
            filename_item = QTableWidgetItem(filename)
            filename_item.setToolTip(f"{filename}\n\nFull path:\n{file_path}")
            self.batch_file_table.setItem(row, 1, filename_item)

            # File size
            try:
                file_size = os.path.getsize(file_path)
                size_str = self._format_file_size(file_size)
                size_item = QTableWidgetItem(size_str)
                size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                # Store numeric value for proper sorting
                size_item.setData(Qt.UserRole, file_size)
                self.batch_file_table.setItem(row, 2, size_item)
            except Exception as e:
                self.batch_file_table.setItem(row, 2, QTableWidgetItem("N/A"))

            # COR value (editable)
            cor_input = QLineEdit()
            cor_input.setPlaceholderText("COR value")
            cor_input.setAlignment(Qt.AlignCenter)
            cor_input.setFixedWidth(80)
            # Restore previous COR value if it exists
            if filename in cor_values:
                cor_input.setText(cor_values[filename])
            self.batch_file_table.setCellWidget(row, 3, cor_input)
            file_info['cor_input'] = cor_input

            # Status
            status_item = QTableWidgetItem('Ready')
            self.batch_file_table.setItem(row, 4, status_item)
            file_info['status_item'] = status_item

            # View Data button (original HDF5 data)
            view_data_btn = QPushButton("View Data")
            view_data_btn.clicked.connect(lambda checked, fp=file_path: self._batch_view_data(fp))
            self.batch_file_table.setCellWidget(row, 5, view_data_btn)

            # View Try button
            view_try_btn = QPushButton("View Try")
            view_try_btn.clicked.connect(lambda checked, fp=file_path: self._batch_view_try(fp))
            self.batch_file_table.setCellWidget(row, 6, view_try_btn)

            # View Full button
            view_full_btn = QPushButton("View Full")
            view_full_btn.clicked.connect(lambda checked, fp=file_path: self._batch_view_full(fp))
            self.batch_file_table.setCellWidget(row, 7, view_full_btn)

            # Actions button
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)

            try_btn = QPushButton("Try")
            try_btn.setFixedWidth(50)
            try_btn.clicked.connect(lambda checked, fp=file_path: self._batch_run_try_single(fp))
            actions_layout.addWidget(try_btn)

            full_btn = QPushButton("Full")
            full_btn.setFixedWidth(50)
            full_btn.clicked.connect(lambda checked, fp=file_path: self._batch_run_full_single(fp))
            actions_layout.addWidget(full_btn)

            self.batch_file_table.setCellWidget(row, 8, actions_widget)

            # Apply colored left border indicator based on reconstruction status
            # Create a colored indicator in the checkbox column
            checkbox_widget.setStyleSheet(f"QWidget {{ border-left: 6px solid {row_color}; }}")

        # Re-enable sorting after populating the table
        self.batch_file_table.setSortingEnabled(True)

        self.batch_status_label.setText(f"Loaded {len(h5_files)} files")

        # Try to auto-load COR values from CSV if no values were preserved from previous refresh
        # Only auto-load if we don't already have COR values
        if not cor_values:
            self._batch_load_cor_csv(silent=True)
        else:
            # Count how many COR values were restored
            restored_count = len(cor_values)
            self.batch_status_label.setText(f"Loaded {len(h5_files)} files ({restored_count} with COR values)")

    def _batch_save_cor_csv(self):
        """Save COR values to CSV file in the data directory"""
        folder = self.data_path.text()
        if not folder or not os.path.isdir(folder):
            QMessageBox.warning(self, "Warning", "Please select a valid data folder first.")
            return

        if not self.batch_file_list:
            QMessageBox.warning(self, "Warning", "No files in the batch list.")
            return

        csv_path = os.path.join(folder, "batch_cor_values.csv")

        try:
            import csv
            saved_count = 0
            skipped_count = 0

            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Filename', 'COR'])

                for file_info in self.batch_file_list:
                    try:
                        filename = file_info['filename']
                        cor_value = file_info['cor_input'].text().strip()
                        writer.writerow([filename, cor_value])
                        saved_count += 1
                    except (RuntimeError, KeyError):
                        # Widget was deleted (e.g., file was removed)
                        skipped_count += 1
                        continue

            if skipped_count > 0:
                self.log_output.append(f'<span style="color:orange;">⚠️  Saved {saved_count} COR values to {csv_path} ({skipped_count} skipped - widgets deleted)</span>')
                self.batch_status_label.setText(f"COR values saved ({skipped_count} files skipped)")
                QMessageBox.information(self, "Success", f"COR values saved to:\n{csv_path}\n\n{saved_count} saved, {skipped_count} skipped (deleted files)")
            else:
                self.log_output.append(f'<span style="color:green;">✅ Saved {saved_count} COR values to {csv_path}</span>')
                self.batch_status_label.setText(f"COR values saved to batch_cor_values.csv")
                QMessageBox.information(self, "Success", f"COR values saved to:\n{csv_path}")

        except Exception as e:
            self.log_output.append(f'<span style="color:red;">❌ Failed to save COR CSV: {e}</span>')
            QMessageBox.critical(self, "Error", f"Failed to save COR values:\n{e}")

    def _batch_load_cor_csv(self, silent=False):
        """Load COR values from CSV file in the data directory"""
        folder = self.data_path.text()
        if not folder or not os.path.isdir(folder):
            if not silent:
                QMessageBox.warning(self, "Warning", "Please select a valid data folder first.")
            return

        if not self.batch_file_list:
            if not silent:
                QMessageBox.warning(self, "Warning", "No files in the batch list. Refresh the file list first.")
            return

        csv_path = os.path.join(folder, "batch_cor_values.csv")

        if not os.path.exists(csv_path):
            if not silent:
                QMessageBox.warning(self, "Warning", f"COR CSV file not found:\n{csv_path}")
            return

        try:
            import csv
            cor_dict = {}
            with open(csv_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    filename = row.get('Filename', '').strip()
                    cor_value = row.get('COR', '').strip()
                    if filename:
                        cor_dict[filename] = cor_value

            # Apply COR values to the table
            loaded_count = 0
            skipped_count = 0
            for file_info in self.batch_file_list:
                try:
                    filename = file_info['filename']
                    if filename in cor_dict:
                        file_info['cor_input'].setText(cor_dict[filename])
                        loaded_count += 1
                except (RuntimeError, KeyError):
                    # Widget was deleted (e.g., file was removed)
                    skipped_count += 1
                    continue

            if not silent:
                if skipped_count > 0:
                    self.log_output.append(f'<span style="color:orange;">⚠️  Loaded {loaded_count} COR values from {csv_path} ({skipped_count} skipped - widgets deleted)</span>')
                    self.batch_status_label.setText(f"Loaded {loaded_count} COR values ({skipped_count} skipped)")
                    QMessageBox.information(self, "Success", f"Loaded {loaded_count} COR values from:\n{csv_path}\n\n{skipped_count} files skipped (deleted widgets)")
                else:
                    self.log_output.append(f'<span style="color:green;">✅ Loaded COR values from {csv_path}</span>')
                    self.batch_status_label.setText(f"Loaded {loaded_count} COR values from CSV")
                    QMessageBox.information(self, "Success", f"Loaded {loaded_count} COR values from:\n{csv_path}")
            else:
                self.batch_status_label.setText(f"Loaded {len(self.batch_file_list)} files ({loaded_count} with COR values)")

        except Exception as e:
            if not silent:
                self.log_output.append(f'<span style="color:red;">❌ Failed to load COR CSV: {e}</span>')
                QMessageBox.critical(self, "Error", f"Failed to load COR values:\n{e}")

    def _batch_select_all(self):
        """Select all files in the batch list"""
        for file_info in self.batch_file_list:
            file_info['checkbox'].setChecked(True)

    def _batch_deselect_all(self):
        """Deselect all files in the batch list"""
        for file_info in self.batch_file_list:
            file_info['checkbox'].setChecked(False)

    def _batch_remove_selected(self):
        """Physically delete selected files from the filesystem"""
        files_to_remove = [f for f in self.batch_file_list if f['checkbox'].isChecked()]

        if not files_to_remove:
            QMessageBox.warning(self, "Warning", "No files selected.")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self, 'Confirm File Deletion',
            f'Are you sure you want to PERMANENTLY DELETE {len(files_to_remove)} file(s) from disk?\n\nThis action cannot be undone!',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # Delete files from disk
        deleted_count = 0
        failed_files = []
        rows_to_remove = []

        for file_info in files_to_remove:
            try:
                os.remove(file_info['path'])
                rows_to_remove.append(file_info['row'])
                deleted_count += 1
                self.log_output.append(f'<span style="color:green;">✅ Deleted: {file_info["filename"]}</span>')
            except Exception as e:
                failed_files.append(file_info['filename'])
                self.log_output.append(f'<span style="color:red;">❌ Failed to delete {file_info["filename"]}: {e}</span>')

        # Remove rows from table
        for row in sorted(rows_to_remove, reverse=True):
            self.batch_file_table.removeRow(row)

        # Update file list and row indices
        self.batch_file_list = [f for f in self.batch_file_list if f['row'] not in rows_to_remove]
        for i, file_info in enumerate(self.batch_file_list):
            file_info['row'] = i

        # Update status
        if failed_files:
            self.batch_status_label.setText(f"Deleted {deleted_count} files, {len(failed_files)} failed")
        else:
            self.batch_status_label.setText(f"Successfully deleted {deleted_count} files")

        # Refresh the main file dropdown
        self.refresh_h5_files()

    def _batch_view_data(self, file_path):
        """Open HDF5 viewer to view original data"""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"File does not exist:\n{file_path}")
            return

        try:
            # Create and show the HDF5 viewer dialog
            viewer = HDF5ImageDividerDialog(file_path=file_path, parent=self)
            viewer.show()
            self.log_output.append(f'<span style="color:green;">✅ Opened HDF5 viewer for: {os.path.basename(file_path)}</span>')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open HDF5 viewer:\n{str(e)}")
            self.log_output.append(f'<span style="color:red;">❌ Failed to open HDF5 viewer: {str(e)}</span>')

    def _batch_view_try(self, file_path):
        """View try reconstruction for a specific file"""
        # Set the file in the main dropdown
        index = self.proj_file_box.findData(file_path)
        if index >= 0:
            self.proj_file_box.setCurrentIndex(index)
        else:
            # File not in dropdown, refresh and try again
            self.refresh_h5_files()
            index = self.proj_file_box.findData(file_path)
            if index >= 0:
                self.proj_file_box.setCurrentIndex(index)

        # Call the existing view try method
        self.view_try_reconstruction()

    def _batch_view_full(self, file_path):
        """View full reconstruction for a specific file"""
        # Set the file in the main dropdown
        index = self.proj_file_box.findData(file_path)
        if index >= 0:
            self.proj_file_box.setCurrentIndex(index)
        else:
            # File not in dropdown, refresh and try again
            self.refresh_h5_files()
            index = self.proj_file_box.findData(file_path)
            if index >= 0:
                self.proj_file_box.setCurrentIndex(index)

        # Call the existing view full method
        self.view_full_reconstruction()

    def _batch_run_try_single(self, file_path):
        """Run try reconstruction on a single file using the queue system"""
        # Find the file info in batch list
        file_info = None
        for f in self.batch_file_list:
            if f['path'] == file_path:
                file_info = f
                break

        if not file_info:
            self.log_output.append(f'<span style="color:red;">❌ File not found in batch list</span>')
            return

        # Get COR value from batch table
        batch_cor = file_info['cor_input'].text().strip()
        if not batch_cor:
            self.log_output.append(f'<span style="color:red;">❌ No COR value in batch table for {os.path.basename(file_path)}</span>')
            QMessageBox.warning(self, "Missing COR", f"Please enter a COR value in the batch table for:\n{os.path.basename(file_path)}")
            return

        # Use the queue system with 1 GPU (respects the GPU settings)
        machine = self.batch_machine_box.currentText()
        num_gpus = self.batch_gpus_per_machine.value()

        # Run through the queue system to prevent memory overflow
        self._run_batch_with_queue([file_info], recon_type='try', num_gpus=num_gpus, machine=machine)

    def _batch_run_full_single(self, file_path):
        """Run full reconstruction on a single file using the queue system"""
        # Find the file info in batch list
        file_info = None
        for f in self.batch_file_list:
            if f['path'] == file_path:
                file_info = f
                break

        if not file_info:
            self.log_output.append(f'<span style="color:red;">❌ File not found in batch list</span>')
            return

        # Get COR value from batch table
        batch_cor = file_info['cor_input'].text().strip()
        if not batch_cor:
            self.log_output.append(f'<span style="color:red;">❌ No COR value in batch table for {os.path.basename(file_path)}</span>')
            QMessageBox.warning(self, "Missing COR", f"Please enter a COR value in the batch table for:\n{os.path.basename(file_path)}")
            return

        # Use the queue system with configured GPUs (respects the GPU settings)
        machine = self.batch_machine_box.currentText()
        num_gpus = self.batch_gpus_per_machine.value()

        # Run through the queue system to prevent memory overflow
        self._run_batch_with_queue([file_info], recon_type='full', num_gpus=num_gpus, machine=machine)

    def _batch_run_try_selected(self):
        """Run try reconstruction on all selected files with GPU queue management"""
        selected_files = [f for f in self.batch_file_list if f['checkbox'].isChecked()]
        machine = self.batch_machine_box.currentText()

        if not selected_files:
            QMessageBox.warning(self, "Warning", "No files selected.")
            return

        num_gpus = self.batch_gpus_per_machine.value()
        machine_text = f" on {machine}" if machine != "Local" else ""

        reply = QMessageBox.question(
            self, 'Confirm Batch Try',
            f'Run try reconstruction on {len(selected_files)} selected files{machine_text}?\n'
            f'Using {num_gpus} GPU(s) in parallel.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        self._run_batch_with_queue(selected_files, recon_type='try', num_gpus=num_gpus, machine=machine)

    def _batch_run_full_selected(self):
        """Run full reconstruction on all selected files with GPU queue management"""
        selected_files = [f for f in self.batch_file_list if f['checkbox'].isChecked()]
        machine = self.batch_machine_box.currentText()

        if not selected_files:
            QMessageBox.warning(self, "Warning", "No files selected.")
            return

        num_gpus = self.batch_gpus_per_machine.value()
        machine_text = f" on {machine}" if machine != "Local" else ""

        reply = QMessageBox.question(
            self, 'Confirm Batch Full Reconstruction',
            f'Run full reconstruction on {len(selected_files)} selected files{machine_text}?\n'
            f'Using {num_gpus} GPU(s) in parallel.\nThis may take a long time.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        self._run_batch_with_queue(selected_files, recon_type='full', num_gpus=num_gpus, machine=machine)

    def _run_batch_with_queue(self, selected_files, recon_type, num_gpus, machine):
        """
        Run batch reconstructions with GPU queue management

        Args:
            selected_files: List of file info dictionaries
            recon_type: 'try' or 'full'
            num_gpus: Number of GPUs to use in parallel
            machine: Target machine name
        """
        # Add jobs to queue with their type and machine info
        jobs_to_add = [(f, recon_type, machine) for f in selected_files]

        # Mark all jobs as queued (safely handle deleted widgets)
        for f, _, _ in jobs_to_add:
            try:
                f['status_item'].setText('Queued')
            except RuntimeError:
                # Widget was deleted, skip status update
                pass

        # If queue is already running, just add to it
        if self.batch_running:
            self.batch_job_queue.extend(jobs_to_add)
            self.batch_total_jobs += len(selected_files)
            self.log_output.append(f'<span style="color:blue;">➕ Added {len(selected_files)} job(s) to running queue</span>')
            self.batch_queue_label.setText(f"Queue: {len(self.batch_job_queue)} jobs waiting")
            return

        # Start new queue
        self.batch_running = True
        self.batch_stop_btn.setEnabled(True)
        self.batch_job_queue = jobs_to_add
        self.batch_running_jobs = {}
        self.batch_available_gpus = list(range(num_gpus))  # GPUs 0, 1, 2, etc.
        self.batch_current_machine = machine
        self.batch_current_num_gpus = num_gpus

        self.batch_total_jobs = len(selected_files)
        self.batch_completed_jobs = 0

        self.batch_status_label.setText(f"Starting batch queue on {machine} with {num_gpus} GPU(s)")
        self.batch_progress_bar.setValue(0)
        self.log_output.append(f'<span style="color:green;">🔧 Queue started with {num_gpus} GPU(s): {self.batch_available_gpus}</span>')
        QApplication.processEvents()

        # Keep processing until queue is empty and all jobs are done
        while self.batch_job_queue or self.batch_running_jobs:
            # Start new jobs if GPUs are available and jobs are queued
            while self.batch_available_gpus and self.batch_job_queue:
                gpu_id = self.batch_available_gpus.pop(0)
                job_tuple = self.batch_job_queue.pop(0)
                file_info, job_recon_type, job_machine = job_tuple

                # Update status (safely handle deleted widgets)
                try:
                    file_info['status_item'].setText(f'Running on GPU {gpu_id}')
                except RuntimeError:
                    # Widget was deleted, skip status update
                    pass
                queue_len = len(self.batch_job_queue)
                self.batch_queue_label.setText(f"Queue: {len(self.batch_job_queue)} jobs waiting")
                QApplication.processEvents()

                # Start job asynchronously
                process = self._start_batch_job_async(file_info, job_recon_type, gpu_id, job_machine)
                self.batch_running_jobs[gpu_id] = (process, file_info, job_recon_type)

                self.log_output.append(f'<span style="color:blue;">🚀 GPU {gpu_id}: Started {job_recon_type} - {file_info["filename"]} (Running: {len(self.batch_running_jobs)}, Queued: {len(self.batch_job_queue)})</span>')

            # Check for completed jobs
            completed_gpus = []
            for gpu_id, (process, file_info, job_recon_type) in list(self.batch_running_jobs.items()):
                if process.state() == QProcess.NotRunning:
                    # Job finished
                    exit_code = process.exitCode()
                    self.batch_completed_jobs += 1

                    # Safely update status (widget may have been deleted if list was refreshed)
                    try:
                        if exit_code == 0:
                            file_info['status_item'].setText(f'{job_recon_type.capitalize()} Complete')
                            self.log_output.append(f'<span style="color:green;">✅ GPU {gpu_id} finished: {file_info["filename"]}</span>')
                            # Update row color based on new reconstruction status
                            self._update_row_color(file_info)
                        else:
                            file_info['status_item'].setText(f'{job_recon_type.capitalize()} Failed')
                            self.log_output.append(f'<span style="color:red;">❌ GPU {gpu_id} failed: {file_info["filename"]}</span>')
                    except RuntimeError:
                        # Widget was deleted (e.g., user refreshed the list)
                        self.log_output.append(f'<span style="color:gray;">✅ GPU {gpu_id} finished: {file_info["filename"]} (widget deleted)</span>')

                    completed_gpus.append(gpu_id)

            # Free up completed GPUs
            for gpu_id in completed_gpus:
                del self.batch_running_jobs[gpu_id]
                self.batch_available_gpus.append(gpu_id)
                self.batch_available_gpus.sort()

            # Update progress
            if self.batch_total_jobs > 0:
                progress = int((self.batch_completed_jobs / self.batch_total_jobs) * 100)
            else:
                progress = 0
            self.batch_progress_bar.setValue(progress)

            # Show which GPUs are active
            active_gpus = sorted(self.batch_running_jobs.keys())
            gpu_status = f"GPUs: {active_gpus}" if active_gpus else "GPUs: idle"

            self.batch_status_label.setText(
                f"Completed {self.batch_completed_jobs}/{self.batch_total_jobs} | {gpu_status} ({len(self.batch_running_jobs)} running) | Queue: {len(self.batch_job_queue)}"
            )

            QApplication.processEvents()

            # Small delay to prevent CPU spinning
            if self.batch_running_jobs:
                import time
                time.sleep(0.1)

        self.batch_progress_bar.setValue(100)
        self.batch_status_label.setText(f"Batch queue complete: {self.batch_completed_jobs} files processed on {self.batch_current_machine}")
        self.batch_queue_label.setText("Queue: 0 jobs waiting")
        self.batch_running = False
        self.batch_stop_btn.setEnabled(False)
        self.log_output.append(f'<span style="color:green;">🏁 Batch queue finished: {self.batch_completed_jobs} files completed</span>')

    def _batch_stop_queue(self):
        """Stop the batch queue and kill all running processes"""
        if not self.batch_running:
            return

        reply = QMessageBox.question(
            self, 'Stop Batch Queue',
            f'Stop the batch queue?\n\n'
            f'This will kill {len(self.batch_running_jobs)} running job(s) and clear {len(self.batch_job_queue)} queued job(s).',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # Kill all running processes
        for gpu_id, (process, file_info, job_recon_type) in list(self.batch_running_jobs.items()):
            try:
                process.kill()
                try:
                    file_info['status_item'].setText('Cancelled')
                except RuntimeError:
                    pass  # Widget was deleted
                self.log_output.append(f'<span style="color:orange;">⚠️  Killed job on GPU {gpu_id}: {file_info["filename"]}</span>')
            except:
                pass

        # Clear queued jobs
        for file_info, job_recon_type, job_machine in self.batch_job_queue:
            try:
                file_info['status_item'].setText('Cancelled')
            except RuntimeError:
                pass  # Widget was deleted

        # Reset queue state
        self.batch_job_queue = []
        self.batch_running_jobs = {}
        self.batch_running = False
        self.batch_stop_btn.setEnabled(False)
        self.batch_progress_bar.setValue(0)
        self.batch_status_label.setText("Batch queue stopped by user")
        self.batch_queue_label.setText("Queue: 0 jobs waiting")
        self.log_output.append(f'<span style="color:orange;">🛑 Batch queue stopped by user</span>')

    def _start_batch_job_async(self, file_info, recon_type, gpu_id, machine):
        """
        Start a reconstruction job asynchronously

        Args:
            file_info: File information dictionary
            recon_type: 'try' or 'full'
            gpu_id: GPU ID to use
            machine: Target machine

        Returns:
            QProcess object
        """
        file_path = file_info['path']
        filename = os.path.basename(file_path)

        # Get reconstruction parameters from Main tab
        recon_way = self.recon_way_box.currentText()

        # Get COR value EXCLUSIVELY from batch table (not from Main tab)
        cor_val = file_info['cor_input'].text().strip()

        # Batch tab always uses manual COR with the value from the batch table
        # Validate COR - batch tab requires COR value to be set
        if not cor_val:
            self.log_output.append(f'<span style="color:orange;">⚠️  No COR value in batch table for {filename}, skipping</span>')
            # Return a dummy finished process
            p = QProcess(self)
            p.start("echo", ["skipped"])
            p.waitForFinished()
            return p

        try:
            cor = float(cor_val)
        except ValueError:
            self.log_output.append(f'<span style="color:red;">❌ Invalid COR value "{cor_val}" for {filename}, skipping</span>')
            p = QProcess(self)
            p.start("echo", ["skipped"])
            p.waitForFinished()
            return p

        # Build command
        # Batch tab ALWAYS uses manual COR with the value from the batch table
        if self.use_conf_box.isChecked():
            config_editor = self.config_editor_try if recon_type == 'try' else self.config_editor_full
            config_text = config_editor.toPlainText()

            temp_conf = os.path.join(self.data_path.text(), f"temp_{recon_type}_gpu{gpu_id}.conf")
            with open(temp_conf, "w") as f:
                f.write(config_text)

            cmd = ["tomocupy", str(recon_way),
                   "--reconstruction-type", recon_type,
                   "--config", temp_conf,
                   "--file-name", file_path,
                   "--rotation-axis-auto", "manual",
                   "--rotation-axis", str(cor)]
        else:
            cmd = ["tomocupy", str(recon_way),
                   "--reconstruction-type", recon_type,
                   "--file-name", file_path,
                   "--rotation-axis-auto", "manual",
                   "--rotation-axis", str(cor)]

        # Wrap for remote execution if needed
        cmd = self._get_batch_machine_command(cmd, machine)

        # Create and configure process
        p = QProcess(self)
        p.setProcessChannelMode(QProcess.ForwardedChannels)

        # Set CUDA_VISIBLE_DEVICES for GPU assignment (only for local execution)
        if machine == "Local":
            env = QProcessEnvironment.systemEnvironment()
            env.insert("CUDA_VISIBLE_DEVICES", str(gpu_id))
            p.setProcessEnvironment(env)

        # Start process
        p.start(str(cmd[0]), [str(a) for a in cmd[1:]])

        return p

    # ===== THEME METHODS =====

    def _toggle_theme(self):
        """Toggle between bright and dark themes"""
        self.theme_manager.toggle_theme()

    def _on_theme_changed(self, theme_name):
        """Callback when theme changes - update UI elements"""
        # Update theme toggle button icon
        if theme_name == 'bright':
            self.theme_toggle_btn.setText("🌙")
        else:
            self.theme_toggle_btn.setText("☀")

        # Redraw the matplotlib canvas with new theme
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.draw_idle()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = TomoGUI()
    w.show()
    sys.exit(app.exec_())

