import os, glob, json
import numpy as np

# Configure OpenGL for remote display BEFORE importing VisPy
# This helps with SSH X11 forwarding and remote displays
if 'LIBGL_ALWAYS_SOFTWARE' not in os.environ:
    os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
if 'MESA_GL_VERSION_OVERRIDE' not in os.environ:
    os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
# Disable vsync for better remote performance
if 'vblank_mode' not in os.environ:
    os.environ['vblank_mode'] = '0'

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QTextEdit, QLineEdit, QLabel, QProgressBar,
    QComboBox, QSlider, QGroupBox, QSizePolicy, QMessageBox,
    QTabWidget, QFormLayout, QCheckBox, QSpinBox, QDoubleSpinBox,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,QFrame
)
from PyQt5.QtCore import Qt, QEvent, QProcess, QEventLoop, QSize, QProcessEnvironment
from PyQt5.QtGui import QColor
from pathlib import Path

from PIL import Image
import h5py, json
from datetime import datetime

# VisPy for fast GPU-accelerated rendering
try:
    from vispy import scene, app
    from vispy.scene import visuals
    from vispy.color import get_colormaps
    # Use Qt5 backend which is most stable
    try:
        app.use_app('pyqt5')
    except:
        pass
    VISPY_AVAILABLE = True
except ImportError:
    print("Warning: VisPy not available. Install with: pip install vispy")
    print("Falling back to slower rendering...")
    VISPY_AVAILABLE = False

from .theme_manager import ThemeManager
from .hdf5_viewer import HDF5ImageDividerDialog
from .batch_progress_window import ProgressWindow


class TomoGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TomoGUI")
        self.resize(2048,1080)

        # Initialize theme manager (will apply theme after UI is built)
        self.theme_manager = ThemeManager()
        self.theme_manager.register_callback(self._on_theme_changed)

        #initialize progress bar for batch process
        self.progress_window = ProgressWindow(self)
        #stop button in progress window stops the same batch queue
        self.progress_window.stop_requested.connect(self._batch_stop_queue)

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
        self.batch_running = False
        self.batch_file_list = []
        self.highlight_scan = None
        self.highlight_row = None
        self._current_source_file = None
        self.cor_path = None
        self.batch_file_main_list = []

        # Batch selection state for shift-click
        self.batch_last_clicked_row = None

        main_layout = QHBoxLayout()

        # ==== LEFT PANEL ====
        left_layout = QVBoxLayout()

        # Data folder
        folder_layout = QHBoxLayout()
        df_label = QLabel("Data Folder:")
        df_label.setStyleSheet("QLabel { font-size: 10.5pt; }")
        folder_layout.addWidget(df_label)
        self.data_path = QLineEdit()
        self.data_path.setFixedWidth(580)
        self.data_path.setStyleSheet("QLineEdit { font-size: 10.5pt; }")
        folder_layout.addWidget(self.data_path)
        browse_btn = QPushButton(" Browse Data Folder ")
        browse_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        browse_btn.setToolTip(f"Find folder, update from files status and rot_cen.json")
        browse_btn.clicked.connect(self.browse_data_folder)
        folder_layout.addWidget(browse_btn)
        refresh_btn2 = QPushButton("     Refresh     ")
        refresh_btn2.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        refresh_btn2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        refresh_btn2.clicked.connect(self.refresh_main_table)      
        refresh_btn2.setToolTip(f"Update from files status and rot_cen.json")
        folder_layout.addWidget(refresh_btn2)  
        left_layout.addLayout(folder_layout)

        # ==== TABS (Configs + Params) ====
        self.tabs = QTabWidget()
        left_layout.addWidget(self.tabs)        
        
        first_tab = QWidget()
        self.tabs.addTab(first_tab, "Main")

        #==========main tab may===================
        main_tab = QVBoxLayout(first_tab)
        main_tab.setSpacing(6)
        #Row 1 - Try part single file operation
        single_ops = QHBoxLayout()
        single_ops.setSpacing(10)
        label_try = QLabel("Try method")
        label_try.setStyleSheet("QLabel { font-size: 10.5pt; }")
        label_try.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        single_ops.addWidget(label_try)
        self.recon_way_box = QComboBox()
        self.recon_way_box.setFixedWidth(100)
        self.recon_way_box.setStyleSheet("QComboBox { font-size: 10.5pt; }")
        self.recon_way_box.addItems(["recon","recon_steps"])
        self.recon_way_box.setCurrentIndex(0) # make recon as default
        single_ops.addWidget(self.recon_way_box)
        cor_method_label = QLabel("COR method")
        cor_method_label.setStyleSheet("QLabel { font-size: 10.5pt; }")
        single_ops.addWidget(cor_method_label)
        self.cor_method_box = QComboBox()
        self.cor_method_box.setFixedWidth(85)
        self.cor_method_box.setStyleSheet("QComboBox { font-size: 10.5pt; }")
        self.cor_method_box.addItems(["auto","manual"])
        self.cor_method_box.setCurrentIndex(1) # make manual as default
        single_ops.addWidget(self.cor_method_box)
        cor_label = QLabel("COR")
        cor_label.setStyleSheet("QLabel { font-size: 10.5pt; }")
        single_ops.addWidget(cor_label)
        self.cor_input = QLineEdit()
        self.cor_input.setFixedWidth(55)
        self.cor_input.setStyleSheet("QLineEdit { font-size: 10.5pt; }")
        single_ops.addWidget(self.cor_input)
        cuda_label = QLabel("cuda")
        cuda_label.setStyleSheet("QLabel { font-size: 10.5pt; }")
        single_ops.addWidget(cuda_label)
        self.cuda_box_try = QSpinBox()
        self.cuda_box_try.setMinimum(0)
        self.cuda_box_try.setMaximum(1)
        self.cuda_box_try.setValue(0)
        self.cuda_box_try.setFixedWidth(52)
        self.cuda_box_try.setStyleSheet("QSpinBox { font-size: 10.5pt; }")
        single_ops.addWidget(self.cuda_box_try)
        try_btn = QPushButton("  Try  ")
        try_btn.setStyleSheet("QPushButton { font-size: 11pt; font-weight:bold; }")
        try_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        try_btn.clicked.connect(self.try_reconstruction)
        single_ops.addWidget(try_btn)
        view_try_btn = QPushButton("  View Try  ")
        view_try_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        view_try_btn.clicked.connect(self.view_try_reconstruction) 
        single_ops.addWidget(view_try_btn)
        single_ops.setStretch(0,0)
        separator = QLabel(" | ")
        separator.setStyleSheet("QLabel { font-size: 11pt; }")
        single_ops.addWidget(separator)
        clear_log_btn = QPushButton(" clear Log ")
        clear_log_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        clear_log_btn.setEnabled(True) #enable
        clear_log_btn.clicked.connect(self.clear_log)
        single_ops.addWidget(clear_log_btn)
        main_tab.addLayout(single_ops)

        h_line = QFrame()
        h_line.setFrameShape(QFrame.HLine)  # Vertical line
        h_line.setFrameShadow(QFrame.Sunken)
        main_tab.addWidget(h_line)
        
        # Row 2 - Full part single file operation
        single_full_ops = QHBoxLayout()
        single_full_ops.setSpacing(10)
        label_full = QLabel("Full method")
        label_full.setStyleSheet("QLabel { font-size: 10.5pt; }")
        label_full.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        single_full_ops.addWidget(label_full)
        self.recon_way_box_full = QComboBox()
        self.recon_way_box_full.setFixedWidth(99)
        self.recon_way_box_full.setStyleSheet("QComboBox { font-size: 10.5pt; }")
        self.recon_way_box_full.addItems(["recon","recon_steps"])
        self.recon_way_box_full.setCurrentIndex(0) # make recon as default
        single_full_ops.addWidget(self.recon_way_box_full)
        cor_method_full_label = QLabel("COR method")
        cor_method_full_label.setStyleSheet("QLabel { font-size: 10.5pt; }")
        single_full_ops.addWidget(cor_method_full_label)
        self.cor_full_method = QComboBox()
        self.cor_full_method.setFixedWidth(85)
        self.cor_full_method.setStyleSheet("QComboBox { font-size: 10.5pt; }")
        self.cor_full_method.addItems(["auto","manual"])
        self.cor_full_method.setCurrentIndex(1) # make manual as default
        single_full_ops.addWidget(self.cor_full_method)
        rec_cor_btn = QPushButton("  Add COR  ")
        rec_cor_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        rec_cor_btn.clicked.connect(self.record_cor_main_tb)
        single_full_ops.addWidget(rec_cor_btn)
        cuda_full_label = QLabel("cuda")
        cuda_full_label.setStyleSheet("QLabel { font-size: 10.5pt; }")
        single_full_ops.addWidget(cuda_full_label)
        self.cuda_full_box = QSpinBox()
        self.cuda_full_box.setMinimum(0)
        self.cuda_full_box.setMaximum(1)
        self.cuda_full_box.setValue(0)
        self.cuda_full_box.setFixedWidth(52)
        self.cuda_full_box.setStyleSheet("QSpinBox { font-size: 10.5pt; }")
        single_full_ops.addWidget(self.cuda_full_box) 
        full_btn = QPushButton("    Full    ")
        full_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        full_btn.setStyleSheet("QPushButton { font-size: 11pt; font-weight:bold; }")
        full_btn.clicked.connect(self.full_reconstruction)
        single_full_ops.addWidget(full_btn)
        self.view_btn = QPushButton("  View Full  ")
        self.view_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        self.view_btn.setEnabled(True)
        self.view_btn.clicked.connect(self.view_full_reconstruction)
        single_full_ops.addWidget(self.view_btn)
        separator_full = QLabel(" | ")
        separator_full.setStyleSheet("QLabel { font-size: 11pt; }")
        single_full_ops.addWidget(separator_full)
        save_log_btn = QPushButton(" save Log ")
        save_log_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        save_log_btn.setEnabled(True) #enable
        save_log_btn.clicked.connect(self.save_log)
        single_full_ops.addWidget(save_log_btn)
        main_tab.addLayout(single_full_ops)


        h_line2 = QFrame()
        h_line2.setFrameShape(QFrame.HLine)  # Vertical line
        h_line2.setFrameShadow(QFrame.Sunken)
        main_tab.addWidget(h_line2)

        # Row 3: some helpful functions
        others_ops = QHBoxLayout()
        others_ops.setSpacing(5)
        view_meta_btn = QPushButton("raw/meta")
        view_meta_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        view_meta_btn.clicked.connect(lambda checked=False: self._batch_view_data(self.highlight_scan)) #TODO: needs to modify with alrady have functions in Batch Processing tab
        others_ops.addWidget(view_meta_btn)
        save_param_btn = QPushButton("Save params")
        save_param_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        save_param_btn.setEnabled(True) #enable
        save_param_btn.clicked.connect(self.save_params_to_file)
        others_ops.addWidget(save_param_btn)
        load_param_btn = QPushButton("Load params")
        load_param_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        load_param_btn.setEnabled(True) #enable
        load_param_btn.clicked.connect(self.load_params_from_file)    
        others_ops.addWidget(load_param_btn)
        abort_btn =QPushButton("Abort")
        abort_btn.setStyleSheet("QPushButton { font-size: 10.5pt; color: red; }")
        abort_btn.clicked.connect(self.abort_process)
        others_ops.addWidget(abort_btn)
        help_tomo_btn = QPushButton("help")
        help_tomo_btn.setStyleSheet("QPushButton { font-size: 10.5pt; color: green; }")
        help_tomo_btn.clicked.connect(self.help_tomo)
        others_ops.addWidget(help_tomo_btn)
        main_tab.addLayout(others_ops)

        # Row 4 - batch process table
        self.batch_file_main_table = QTableWidget()
        self.batch_file_main_table.cellClicked.connect(self.on_table_row_clicked)
        self.batch_file_main_table.setStyleSheet("""
                                            QTableWidget {
                                             font-size: 10.5pt; /* Set font size for the table cells */
                                            }
                                            QHeaderView::section {
                                                font-size: 10.5pt; /* Set font size for the header */
                                                font-weight: bold; /* Make header text bold */
                                                }
                                                """)
        self.batch_file_main_table.setColumnCount(7)
        self.batch_file_main_table.setHorizontalHeaderLabels(["Select","File Name", "COR",
                                                         "Status", "Size", "Pixel", "View Data"])
        self.batch_file_main_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        header = self.batch_file_main_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # Allow user to resize columns
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Select checkbox
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Filename - user can resize
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # COR
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Size
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Actions
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # View Data
        self.batch_file_main_table.setColumnWidth(0,50)
        self.batch_file_main_table.setColumnWidth(1, 350) # Set initial width for filename column to be wider (can be resized by user)    
        main_tab.addWidget(self.batch_file_main_table)
        #Row 5: batch process operations
        batch_ops = QHBoxLayout()
        batch_ops.setSpacing(5)
        batch_label = QLabel("Batch process ")
        batch_label.setStyleSheet("QLabel { font-size: 10.5pt; font-weight:bold; }")
        batch_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        batch_label.setFixedWidth(97)
        batch_ops.addWidget(batch_label)
        batch_mach_label = QLabel(" Machine ")
        batch_mach_label.setStyleSheet("QLabel { font-size: 10.5pt; }")
        batch_mach_label.setFixedWidth(59)
        batch_ops.addWidget(batch_mach_label)
        self.batch_machine_box = QComboBox()
        self.batch_machine_box.addItems(["Local", "tomo1", "tomo2", "tomo3", "tomo4", "tomo5"])
        self.batch_machine_box.setStyleSheet("QComboBox { font-size: 10.5pt; }")
        self.batch_machine_box.setCurrentText("Local") # make Local as default TODO: set initial json file beamline dependent
        self.batch_machine_box.setToolTip("Select machine to run batch reconstructions")
        self.batch_machine_box.setFixedWidth(62)
        batch_ops.addWidget(self.batch_machine_box)
        batch_gpus = QLabel("GPUs")
        batch_gpus.setStyleSheet("QLabel { font-size: 10.5pt; }")
        batch_gpus.setFixedWidth(39)
        batch_ops.addWidget(batch_gpus)
        self.batch_gpus_per_machine = QSpinBox()
        self.batch_gpus_per_machine.setMinimum(1)
        self.batch_gpus_per_machine.setMaximum(8)
        self.batch_gpus_per_machine.setValue(1)
        self.batch_gpus_per_machine.setToolTip("Number of GPUs to use on the target machine (1 job per GPU)")
        self.batch_gpus_per_machine.setFixedWidth(38)
        self.batch_gpus_per_machine.setStyleSheet("QSpinBox { font-size: 10.5pt; }")
        batch_ops.addWidget(self.batch_gpus_per_machine)
        #TODO: monitor folder and auto recon
        #monitor_btn = QPushButton("Monitor")
        #monitor_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        #monitor_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        #monitor_btn.setToolTip(f"Auto try or full recon")
        #monitor_btn.setVisible(False)  # Unavailable
        #monitor_btn.clicked.connect(self.monitor)#TODO: to implement
        #batch_ops.addWidget(monitor_btn)
        select_all_btn = QPushButton("Select all")
        select_all_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        select_all_btn.clicked.connect(self._batch_select_all)
        select_all_btn.setFixedWidth(120)
        batch_ops.addWidget(select_all_btn)
        deselect_all_btn = QPushButton("Unselect all")
        deselect_all_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        deselect_all_btn.clicked.connect(self._batch_deselect_all)
        deselect_all_btn.setFixedWidth(120)
        batch_ops.addWidget(deselect_all_btn)
        view_selected_btn = QPushButton("View Selected Data")
        view_selected_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        view_selected_btn.setToolTip("Open HDF5 viewer for first selected file")
        view_selected_btn.clicked.connect(self._batch_view_selected_data)
        view_selected_btn.setFixedWidth(135)
        batch_ops.addWidget(view_selected_btn)
        separator_batch = QLabel("  |  ")
        separator_batch.setStyleSheet("QLabel { font-size: 11pt; }")
        separator_batch.setFixedWidth(23)
        batch_ops.addWidget(separator_batch)
        batch_recon_btn =QPushButton("Batch Try")
        batch_recon_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        batch_recon_btn.setToolTip("Run batch try reconstruction on selected files,the params are from GUI and COR guess from value put on single operation above")
        batch_recon_btn.clicked.connect(self._batch_run_try_selected)
        #batch_recon_btn.setFixedWidth(100)
        batch_ops.addWidget(batch_recon_btn)
        batch_full_btn =QPushButton("Batch Full")
        batch_full_btn.setStyleSheet("QPushButton { font-size: 10.5pt; }")
        batch_full_btn.setToolTip("Run batch full reconstruction on selected files,the params are from GUI and COR from Table above")
        batch_full_btn.clicked.connect(self._batch_run_full_selected) #TODO: needs to modify to work with table
        #batch_full_btn.setFixedWidth(100)
        batch_ops.addWidget(batch_full_btn)
        main_tab.addLayout(batch_ops)
        #Row 6: log
        log_box = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("QTextEdit { font-size: 11pt; }")
        self.log_output.append("Start tomoGUI")     
        self.log_output.setFixedHeight(200)  # Set a fixed height
        log_box.addWidget(self.log_output)
        main_tab.addLayout(log_box)   

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
        # self.progress = QProgressBar()
        # self.progress.setRange(0, 0)
        # self.progress.setVisible(False)
        # left_layout.addWidget(self.progress)

        # Log + COR JSON
        #log_json_layout = QHBoxLayout()
        #log_box_layout = QVBoxLayout()
        #log_box_layout.addWidget(QLabel("Log Output:"))
        #self.log_output = QTextEdit()
        #self.log_output.setReadOnly(True)
        #self.log_output.setStyleSheet("QTextEdit { font-size: 12.5pt; }")
        #self.log_output.append("Start tomoGUI")
        #log_box_layout.addWidget(self.log_output)
        #og_json_layout.addLayout(log_box_layout)
        #left_layout.addLayout(log_json_layout)
        
        main_layout.addLayout(left_layout, 4)
        
        # ==== RIGHT PANEL ====
        right_layout = QVBoxLayout()
        toolbar_row = QHBoxLayout()

        # Check if VisPy is available
        if not VISPY_AVAILABLE:
            error_label = QLabel("ERROR: VisPy not installed!\n\nPlease install with:\n  pip install vispy PyOpenGL")
            error_label.setStyleSheet("color: red; font-size: 14pt; font-weight: bold; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            toolbar_row.addWidget(error_label)
            right_layout.addLayout(toolbar_row)
            main_layout.addLayout(right_layout, 8)
            self.setLayout(main_layout)
            return

        # VisPy canvas setup
        try:
            self.canvas = scene.SceneCanvas(keys='interactive', show=False)
        except Exception as e:
            # If canvas creation fails, show error and provide workaround
            error_label = QLabel(
                f"ERROR: VisPy canvas creation failed!\n\n"
                f"Error: {str(e)}\n\n"
                f"If using SSH/remote display, try:\n"
                f"  export LIBGL_ALWAYS_SOFTWARE=1\n"
                f"  export MESA_GL_VERSION_OVERRIDE=3.3\n"
                f"Then restart tomogui"
            )
            error_label.setStyleSheet("color: red; font-size: 11pt; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setWordWrap(True)
            toolbar_row.addWidget(error_label)
            right_layout.addLayout(toolbar_row)
            main_layout.addLayout(right_layout, 8)
            self.setLayout(main_layout)
            return
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera()
        self.view.camera.flip = (False, True, False)  # Flip Y for image coords
        self.image_visual = visuals.Image(cmap='grays', parent=self.view.scene)
        self.canvas_widget = self.canvas.native

        # State for vispy
        self._keep_zoom = False
        self._last_camera_rect = None
        self._last_image_shape = None
        self.roi_extent = None
        self._drawing_roi = False
        self._roi_visual = None
        self._roi_start = None

        # Connect vispy mouse events
        self.canvas.events.mouse_move.connect(self._on_vispy_mouse_move)
        self.canvas.events.mouse_press.connect(self._on_vispy_mouse_click)
        self.canvas.events.mouse_release.connect(self._on_vispy_mouse_release)

        # Coordinate label
        self.coord_label = QLabel("")
        self.coord_label.setFixedWidth(350)
        self.coord_label.setStyleSheet("font-size: 11pt;")
        toolbar_row.addWidget(self.coord_label)
        toolbar_row.addSpacing(10)

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
        self.canvas_widget.installEventFilter(self)

        canvas_slider_frame = QVBoxLayout()
        canvas_slider_frame.addWidget(self.canvas_widget)
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

        main_layout.addLayout(right_layout, 5)
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

    #     # ==== BATCH PROCESSING TAB ====
    #     batch_tab = QWidget()
    #     self.tabs.addTab(batch_tab, "Batch Processing")
    #     self._build_batch_tab(batch_tab)

    # def _build_batch_tab(self, batch_tab):
    #     """Build the batch processing tab for managing multiple datasets"""
    #     main_layout = QVBoxLayout(batch_tab)

    #     # Top controls
    #     controls_layout = QHBoxLayout()

    #     refresh_list_btn = QPushButton("Refresh File List")
    #     refresh_list_btn.clicked.connect(self._refresh_batch_file_list)
    #     controls_layout.addWidget(refresh_list_btn)

    #     save_cor_btn = QPushButton("Save COR to CSV")
    #     save_cor_btn.clicked.connect(self._batch_save_cor_csv)
    #     save_cor_btn.setToolTip("Save COR values to batch_cor_values.csv in data folder")
    #     controls_layout.addWidget(save_cor_btn)

    #     load_cor_btn = QPushButton("Load COR from CSV")
    #     load_cor_btn.clicked.connect(self._batch_load_cor_csv)
    #     load_cor_btn.setToolTip("Load COR values from batch_cor_values.csv in data folder")
    #     controls_layout.addWidget(load_cor_btn)

    #     controls_layout.addStretch()

    #     select_all_btn = QPushButton("Select All")
    #     select_all_btn.clicked.connect(self._batch_select_all)
    #     controls_layout.addWidget(select_all_btn)

    #     deselect_all_btn = QPushButton("Deselect All")
    #     deselect_all_btn.clicked.connect(self._batch_deselect_all)
    #     controls_layout.addWidget(deselect_all_btn)

    #     main_layout.addLayout(controls_layout)

    #     # File list table
    #     self.batch_file_table = QTableWidget()
    #     self.batch_file_table.setColumnCount(9)
    #     self.batch_file_table.setHorizontalHeaderLabels([
    #         "Select", "Filename", "Size", "COR", "Status", "View Data", "View Try", "View Full", "Actions"
    #     ])

    #     # Configure table
    #     self.batch_file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
    #     self.batch_file_table.setSortingEnabled(True)  # Enable column sorting
    #     header = self.batch_file_table.horizontalHeader()
    #     header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Select checkbox
    #     header.setSectionResizeMode(1, QHeaderView.Interactive)  # Filename - user can resize
    #     header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Size
    #     header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # COR
    #     header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
    #     header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # View Data
    #     header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # View Try
    #     header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # View Full
    #     header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Actions
    #     header.setSectionsClickable(True)  # Make headers clickable for sorting

    #     # Set initial width for filename column to be wider (can be resized by user)
    #     self.batch_file_table.setColumnWidth(1, 400)

    #     main_layout.addWidget(self.batch_file_table)

    #     # Machine and GPU configuration
    #     machine_layout = QHBoxLayout()
    #     machine_layout.addWidget(QLabel("Target Machine:"))

    #     self.batch_machine_box = QComboBox()
    #     self.batch_machine_box.addItems(["Local", "tomo1", "tomo2", "tomo3", "tomo4", "tomo5"])
    #     self.batch_machine_box.setCurrentText("Local")
    #     self.batch_machine_box.setToolTip("Select machine to run batch reconstructions")
    #     machine_layout.addWidget(self.batch_machine_box)

    #     machine_layout.addSpacing(20)
    #     machine_layout.addWidget(QLabel("GPUs per machine:"))

    #     self.batch_gpus_per_machine_batch = QSpinBox()
    #     self.batch_gpus_per_machine_batch.setMinimum(1)
    #     self.batch_gpus_per_machine_batch.setMaximum(8)
    #     self.batch_gpus_per_machine_batch.setValue(1)
    #     self.batch_gpus_per_machine_batch.setToolTip("Number of GPUs available on the target machine (1 job per GPU)")
    #     machine_layout.addWidget(self.batch_gpus_per_machine_batch)

    #     machine_layout.addSpacing(20)
    #     self.batch_queue_label = QLabel("Queue: 0 jobs waiting")
    #     machine_layout.addWidget(self.batch_queue_label)

    #     machine_layout.addStretch()
    #     main_layout.addLayout(machine_layout)

    #     # Batch operations
    #     batch_ops_layout = QHBoxLayout()

    #     batch_ops_layout.addWidget(QLabel("Batch Operations (on selected):"))

    #     batch_try_btn = QPushButton("Run Try on Selected")
    #     batch_try_btn.clicked.connect(self._batch_run_try_selected)
    #     batch_ops_layout.addWidget(batch_try_btn)

    #     batch_full_btn = QPushButton("Run Full on Selected")
    #     batch_full_btn.clicked.connect(self._batch_run_full_selected)
    #     batch_ops_layout.addWidget(batch_full_btn)

    #     self.batch_stop_btn = QPushButton("Stop Queue")
    #     self.batch_stop_btn.clicked.connect(self._batch_stop_queue)
    #     self.batch_stop_btn.setEnabled(False)
    #     batch_ops_layout.addWidget(self.batch_stop_btn)

    #     batch_ops_layout.addStretch()

    #     remove_selected_btn = QPushButton("Remove Selected from List")
    #     remove_selected_btn.clicked.connect(self._batch_remove_selected)
    #     batch_ops_layout.addWidget(remove_selected_btn)

    #     main_layout.addLayout(batch_ops_layout)

    #     # Progress section
    #     progress_group = QGroupBox("Batch Progress")
    #     progress_layout = QVBoxLayout()

    #     self.batch_progress_bar = QProgressBar()
    #     self.batch_progress_bar.setValue(0)
    #     progress_layout.addWidget(self.batch_progress_bar)

    #     self.batch_status_label = QLabel("Ready")
    #     progress_layout.addWidget(self.batch_status_label)

    #     progress_group.setLayout(progress_layout)
    #     main_layout.addWidget(progress_group)

    #     # Initialize batch state
    #     self.batch_file_list = []
    #     self.batch_current_index = 0
    #     self.batch_running = False
    #     self.batch_job_queue = []  # Queue of pending jobs: [(file_info, recon_type, machine), ...]
    #     self.batch_running_jobs = {}  # Dict of currently running jobs: {gpu_id: (process, file_info, recon_type)}
    #     self.batch_available_gpus = []  # List of available GPU IDs
    #     self.batch_total_jobs = 0  # Total number of jobs in current batch
    #     self.batch_completed_jobs = 0  # Number of completed jobs
    #     self.batch_current_machine = "Local"  # Current machine for batch
    #     self.batch_current_num_gpus = 1  # Current number of GPUs


    # ===== HELP METHODS =====
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
        if VISPY_AVAILABLE and self._current_img is not None:
            self.image_visual.cmap = self.current_cmap
            self.canvas.update()
        else:
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

        if VISPY_AVAILABLE and self._current_img is not None and self.vmin is not None and self.vmax is not None:
            self.image_visual.clim = (self.vmin, self.vmax)
            self.canvas.update()
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
        if obj == self.canvas_widget and event.type() == QEvent.Wheel:
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
            self.refresh_main_table()
            # Auto-refresh batch file list when folder is selected
            #self._refresh_batch_file_list() #TODO:Need decide if remove the batch process tab

    def _load_cor_data(self, data_folder, h5_files):
        """
        Load COR data from CSV or JSON file.
        CSV format (batch_cor_values.csv): Filename,COR
        JSON format (rot_cen.json): {full_path: cor_value}

        CSV takes priority if both exist.

        Returns:
            tuple: (cor_data_dict, list_of_keys)
                   cor_data_dict uses full file paths as keys
        """
        import csv

        csv_path = os.path.join(data_folder, "batch_cor_values.csv")
        json_path = os.path.join(data_folder, "rot_cen.json")

        cor_data = {}

        # Try CSV first (legacy format, takes priority)
        if os.path.exists(csv_path):
            try:
                with open(csv_path, 'r') as csvfile:
                    reader = csv.DictReader(csvfile)
                    # Build a mapping from filename to full path
                    filename_to_path = {os.path.basename(f): f for f in h5_files}

                    for row in reader:
                        filename = row.get('Filename', '').strip()
                        cor_value = row.get('COR', '').strip()

                        if filename and cor_value:
                            # Convert filename to full path for consistency
                            full_path = filename_to_path.get(filename)
                            if full_path:
                                cor_data[full_path] = cor_value

                self.log_output.append(f'<span style="color:green;">✅ Loaded {len(cor_data)} COR values from batch_cor_values.csv</span>')
                return cor_data, list(cor_data.keys())

            except Exception as e:
                self.log_output.append(f'<span style="color:red;">❌ Error loading CSV: {e}</span>')

        # Try JSON if CSV doesn't exist or failed
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    cor_data = json.load(f)
                    self.log_output.append(f'<span style="color:green;">✅ Loaded {len(cor_data)} COR values from rot_cen.json</span>')
                    return cor_data, list(cor_data.keys())
            except json.JSONDecodeError as e:
                self.log_output.append(f'<span style="color:red;">❌ Error loading rot_cen.json: {e}</span>')
                return {}, []

        # No COR file found
        self.log_output.append('<span style="color:orange;">⚠️  No COR file found (checked batch_cor_values.csv and rot_cen.json)</span>')
        return {}, []

    def refresh_main_table(self):
        table_folder = self.data_path.text()
        if not table_folder or not os.path.isdir(table_folder):
            QMessageBox.warning(self, "Warning", "Please select a valid data folder first.")
            return
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
        h5_files = sorted(glob.glob(os.path.join(table_folder, "*.h5")), key=os.path.getmtime, reverse=True)
        self.batch_file_main_table.setSortingEnabled(False)
        self.batch_file_main_table.setRowCount(0)
        self.batch_file_main_list = []
        self.batch_last_clicked_row = None

        # Load COR data from JSON or CSV (CSV takes priority if both exist)
        self.cor_data, fns = self._load_cor_data(table_folder, h5_files)
        #populate table
        for f in h5_files:
            filename = os.path.basename(f)
            row = self.batch_file_main_table.rowCount()
            self.batch_file_main_table.insertRow(row)
            #check recon status
            proj_name = os.path.splitext(filename)[0]
            try_dir = os.path.join(f"{table_folder}_rec", "try_center", proj_name)
            full_dir = os.path.join(f"{table_folder}_rec", f"{proj_name}_rec")
            has_try = os.path.isdir(try_dir) and len(glob.glob(os.path.join(try_dir, "*.tiff"))) > 0
            has_full = os.path.isdir(full_dir) and len(glob.glob(os.path.join(full_dir, "*.tiff"))) > 0
            # Determine row color based on reconstruction status
            if has_full:
                row_color = "green"  # Full reconstruction exists
                fp = glob.glob(os.path.join(full_dir, "*.tiff"))
                num_1 = int(Path(fp[0]).stem.split("_")[-1])
                num_2 = int(Path(fp[-1]).stem.split("_")[-1])
                status_item = QTableWidgetItem(f"Full {num_1}-{num_2}")
            elif has_try:
                row_color = "orange"  # Only try reconstruction exists
                status_item = QTableWidgetItem("Done try")
            else:
                row_color = "red"  # No reconstruction
                status_item = QTableWidgetItem("Ready")
            # Store file info
            file_info = {
                'path': f,
                'filename': filename,
                'status': status_item,
                'row': row,
                'recon_status': row_color
            }
            self.batch_file_main_list.append(file_info)   
            # Checkbox for selection with shift-click support
            checkbox = QCheckBox()
            checkbox.clicked.connect(lambda checked, r=row: self._batch_checkbox_clicked(r, checked))
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.batch_file_main_table.setCellWidget(row, 0, checkbox_widget)
            file_info['checkbox'] = checkbox

            # Filename - show full name and set tooltip with full path
            filename_item = QTableWidgetItem(filename)
            filename_item.setToolTip(f"{filename}\n\nFull path:\n{f}")
            self.batch_file_main_table.setItem(row, 1, filename_item)       

            # COR value (editable)
            if f in fns:
                cor_input = QLineEdit(self.cor_data[f])
            else:
                cor_input = QLineEdit()
            cor_input.setPlaceholderText("COR value")
            cor_input.setAlignment(Qt.AlignCenter)
            cor_input.setFixedWidth(80)

            self.batch_file_main_table.setCellWidget(row, 2, cor_input)
            file_info['cor_input'] = cor_input
            #allow modify table directly but also update rot_cen.json
            try:
                cor_input.editingFinished.connect(
                    lambda fp=f, r=row: self._on_main_cor_edited(fp,r)
                )
            except Exception:
                pass

            # Status
            self.batch_file_main_table.setItem(row, 3, status_item)
            file_info['status'] = status_item

            # File size
            try:
                file_size = os.path.getsize(f)
                size_str = self._format_file_size(file_size)
                size_item = QTableWidgetItem(size_str)
                size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                # Store numeric value for proper sorting
                size_item.setData(Qt.UserRole, file_size)
                self.batch_file_main_table.setItem(row, 4, size_item)
            except Exception as e:
                self.batch_file_main_table.setItem(row, 4, QTableWidgetItem("N/A"))
            # Actions button (placeholder for future actions)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)
            self.batch_file_main_table.setCellWidget(row, 5, actions_widget)

            # View Data button
            view_data_btn = QPushButton("View Data")
            view_data_btn.setFixedWidth(80)
            view_data_btn.clicked.connect(lambda checked, fp=f: self._batch_view_data(fp))
            self.batch_file_main_table.setCellWidget(row, 6, view_data_btn)

            # Apply colored left border indicator based on reconstruction status
            # Create a colored indicator in the checkbox column
            checkbox_widget.setStyleSheet(f"QWidget {{ border-left: 6px solid {row_color}; }}")
        # Re-enable sorting after populating the table
        #self.batch_file_main_table.setSortingEnabled(True)
        # Highlight the first row
        if self.batch_file_main_table.rowCount() > 0:
            self.batch_file_main_table.setCurrentCell(0, 0)  # Select the first cell in the first row
            self.highlight_scan = h5_files[0] #always the latest coming in scan
            self.highlight_row = 0
            self.log_output.append(f'Clicked on {self.highlight_scan}')

    def _save_cor_data(self, data_folder, cor_data_dict):
        """
        Save COR data to both CSV and JSON formats.
        Saves to the format that already exists, or JSON if neither exists.

        Args:
            data_folder: Path to data folder
            cor_data_dict: Dictionary with full file paths as keys and COR values
        """
        import csv

        csv_path = os.path.join(data_folder, "batch_cor_values.csv")
        json_path = os.path.join(data_folder, "rot_cen.json")

        csv_exists = os.path.exists(csv_path)
        json_exists = os.path.exists(json_path)

        # Save to CSV if it exists or if both don't exist (backward compatibility)
        if csv_exists:
            try:
                with open(csv_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Filename', 'COR'])
                    for full_path, cor_value in sorted(cor_data_dict.items()):
                        filename = os.path.basename(full_path)
                        writer.writerow([filename, cor_value])
                self.log_output.append(f'<span style="color:green;">✔ COR values saved to CSV</span>')
            except Exception as e:
                self.log_output.append(f'<span style="color:red;">❌ Failed to write CSV: {e}</span>')

        # Always save to JSON (current format)
        try:
            with open(json_path, "w") as f:
                json.dump(cor_data_dict, f, indent=2)
            if not csv_exists:
                self.log_output.append(f'<span style="color:green;">✔ COR values saved to JSON</span>')
        except Exception as e:
            self.log_output.append(f'<span style="color:red;">❌ Failed to write JSON: {e}</span>')

    def _on_main_cor_edited(self, file_path:str, row:int):
        """
        Called when the COR QLineEdit in the MAIN table is edited.
        Writes/updates COR data to both CSV and JSON if they exist.
        """
        data_folder = self.data_path.text().strip()
        if not data_folder:
            return

        # Get the widget (QLineEdit) from the table
        w = self.batch_file_main_table.cellWidget(row, 2)
        if w is None:
            return
        txt = w.text().strip()
        if txt == "":
            return  # user cleared it

        # Validate numeric
        try:
            float(txt)
        except ValueError:
            self.log_output.append(f'<span style="color:red;">❌ Invalid COR "{txt}" for {os.path.basename(file_path)}</span>')
            return

        # Update in-memory data
        self.cor_data[file_path] = txt

        # Save to file(s)
        self._save_cor_data(data_folder, self.cor_data)

        # Keep your list consistent: store the widget, not a string
        try:
            self.batch_file_main_list[row]["cor_input"] = w
        except Exception:
            pass    

    def refresh_h5_files(self):
        self.proj_file_box.clear()
        folder = self.data_path.text()
        if folder and os.path.isdir(folder):
            for f in sorted(glob.glob(os.path.join(folder, "*.h5")),key=os.path.getmtime, reverse=True): #newest → oldest
                self.proj_file_box.addItem(os.path.basename(f), f)

    def on_table_row_clicked(self, row, column):
        # Get the filename from the clicked row
        filename_item = self.batch_file_main_table.item(row, 1)  # Column 1 contains the filename
        filename = filename_item.text()
        # Update self.highlight_scan with the full path of the selected file
        for file_info in self.batch_file_main_list:
            if file_info['filename'] == filename:
                self.highlight_scan = file_info['path']
                self.highlight_row = row #gives index of the self.batch_file_table_list
        # Log or print the selected file for debugging
        self.log_output.append(f'Click on {self.highlight_scan} now for other operations')

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
        self.batch_running = False

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
    def _update_row(self,row,color,status):
        row = self.highlight_row
        if row is None:
            self.log_output.append(f'<span style="color:red;">\u274c No row highlighted</span>')
            return
        self.batch_file_main_list[row]['recon_status'] = color
        checkbox_widget = self.batch_file_main_table.cellWidget(row, 0)
        if checkbox_widget:
            checkbox_widget.setStyleSheet(f"QWidget {{ border-left: 6px solid {color}; }}")
        status_item = QTableWidgetItem(status)
        self.batch_file_main_table.setItem(row, 3, status_item)
        self.batch_file_main_list[row]['status'] = status


    def try_reconstruction(self):
        proj_file = self.highlight_scan #the scan highlighted in main table full path
        if not proj_file:
            self.log_output.append(f"\u274c No file")
            return
        recon_way = self.recon_way_box.currentText()
        cor_method = self.cor_method_box.currentText()
        cor_val = self.cor_input.text().strip()
        if cor_method == "auto":
            if cor_val:
                self.log_output.append(f'<span style="color:orange;">\u274c use auto method, ignore input cor</span>')
                pass
        else:
            try:
                cor = float(cor_val)
            except ValueError:
                self.log_output.append(f'<span style="color:red;">\u274c wrong rotation axis input</span>')
                return
        # cuda for tomocupy try
        gpu = str(self.cuda_box_try.value())
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
                self._update_row(row=self.highlight_row,color='orange',status='done try') #change table content and self.batch_file_list
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
        proj_file = self.highlight_scan
        pn = os.path.splitext(os.path.basename(proj_file))[0]
        recon_way = self.recon_way_box_full.currentText()  
        highlight_row = self.highlight_row
        cor_method = self.cor_full_method.currentText()
        gpu = str(self.cuda_full_box.value())
        if cor_method == "manual":
            try:
                cor_value = float(self.batch_file_main_list[highlight_row]['cor_input'].text().strip())
            except ValueError:
                self.log_output.append(f'<span style="color:red;">\u274c[ERROR] Invalid Full COR value</span>')
                return
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
            if cor_method == "auto":
                # Base command
                cmd = ["tomocupy", str(recon_way),
                "--reconstruction-type", "full",
                "--file-name", proj_file, 
                "--rotation-axis-auto", cor_method]
            elif cor_method == "manual":
                # Base command
                cmd = ["tomocupy", str(recon_way),
                "--reconstruction-type", "full",
                "--file-name", proj_file, 
                "--rotation-axis-auto", cor_method,
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
                fullpath = os.path.join(f"{self.data_path.text()}_rec", f"{pn}_rec")
                full_files = glob.glob(os.path.join(fullpath, "*.tiff"))
                num_1 = int(Path(full_files[0]).stem.split("_")[-1])
                num_2 = int(Path(full_files[-1]).stem.split("_")[-1])
                self._update_row(row=highlight_row,color='green',status=f'Full {num_1}-{num_2}') #change table content and self.batch_file_list
                self.log_output.append(f'<span style="color:green;">\u2705 Done full recon {proj_file}</span>')
                del fullpath, full_files, num_1, num_2, pn
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

    #=============Batch OPERATIONS==================
    def _batch_select_all(self):
        """Select all files in the batch list"""
        for file_info in self.batch_file_main_list:
            file_info['checkbox'].setChecked(True)
        self.log_output(f'<span style="color:green;">Select all files in table</span>')

    def _batch_deselect_all(self):
        """Deselect all files in the batch list"""
        for file_info in self.batch_file_main_list:
            file_info['checkbox'].setChecked(False)
        self.log_output(f'<span style="color:green;">Unselect all files in table</span>')

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

    # ===== COR MANAGEMENT =====
    def record_cor_main_tb(self):
        '''
        link to Add COR function: get cor from current viewing image, save to json file and update main table
        '''
        data_folder = self.data_path.text().strip()
        proj_file = self.highlight_scan
        row = self.highlight_row
        idx = self.slice_slider.value()
        cor_file = self.preview_files[idx]
        if not os.path.exists(proj_file) or not os.path.exists(cor_file):
            self.log_output.append(f'<span style="color:red;">\u26a0\ufe0fMissing try data folder or projection file</span>')
            return
        cor_nm = os.path.basename(cor_file)
        try:
            cor_value = cor_nm.split("center")[1].split(".tiff")[0]
        except IndexError:
            self.log_output('<span style="color:red;">\u274c[ERROR] Value not found in expected format, cannot add COR</span>')
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
        self.cor_data[proj_file] = cor_value

        # Save to file(s) using the helper method
        self._save_cor_data(data_folder, self.cor_data)

        # Update the table widget
        w = self.batch_file_main_table.cellWidget(row, 2)
        if w is None:
            w = QLineEdit()
            w.setAlignment(Qt.AlignCenter)
            w.setFixedWidth(80)
            self.batch_file_main_table.setCellWidget(row, 2, w)
        w.setText(str(cor_value))
        # keep list storing the widget
        self.batch_file_main_list[row]['cor_input'] = w
        self.log_output.append(f"\u2705[INFO] COR saved for: {os.path.basename(proj_file)}")

    # ===== IMAGE VIEWING =====
    def view_try_reconstruction(self):
        data_folder = self.data_path.text().strip()
        proj_file = self.highlight_scan #the scan highlighted in main table full path
        proj_name = os.path.splitext(os.path.basename(proj_file))[0]
        try_dir = os.path.join(f"{data_folder}_rec", "try_center", proj_name)
        self.preview_files = [] #clean it before use
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
        proj_file = self.highlight_scan
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
        """Enable interactive ROI drawing with VisPy."""
        if self._current_img is None:
            self.log_output.append("\u26a0\ufe0f No image loaded to draw box.")
            return

        self._drawing_roi = True
        self.roi_extent = None
        self._roi_start = None
        self.log_output.append("Click and drag to draw ROI. Release to set. Click again to clear.")

    def _on_vispy_mouse_click(self, event):
        """Handle mouse press for ROI drawing"""
        if not self._drawing_roi:
            if self.roi_extent is not None:
                # Click clears existing ROI
                self._clear_roi()
                self.log_output.append('<span style="color:green;">ROI cleared</span>')
            return

        tr = self.view.scene.transform
        pos = tr.map(event.pos)[:2]
        self._roi_start = pos

    def _on_vispy_mouse_release(self, event):
        """Handle mouse release for ROI drawing"""
        if not self._drawing_roi or self._roi_start is None:
            return

        tr = self.view.scene.transform
        pos = tr.map(event.pos)[:2]

        x0, y0 = self._roi_start
        x1, y1 = pos
        self.roi_extent = (min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1))
        self._drawing_roi = False

        # Draw ROI rectangle with vispy
        self._draw_roi_visual()

        self.log_output.append(
            f"ROI set: x[{int(self.roi_extent[0])}:{int(self.roi_extent[1])}], "
            f"y[{int(self.roi_extent[2])}:{int(self.roi_extent[3])}]"
        )

    def _draw_roi_visual(self):
        """Draw ROI rectangle using vispy Line visual"""
        if self.roi_extent is None:
            return

        x0, x1, y0, y1 = self.roi_extent
        # Create rectangle vertices
        vertices = np.array([
            [x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]
        ], dtype=np.float32)

        if self._roi_visual is not None:
            self._roi_visual.parent = None

        self._roi_visual = visuals.Line(pos=vertices, color='red', width=2, parent=self.view.scene)
        self.canvas.update()

    def _clear_roi(self):
        """Hide/remove any active ROI."""
        if self._roi_visual is not None:
            self._roi_visual.parent = None
            self._roi_visual = None
        self.roi_extent = None
        self._drawing_roi = False
        self.canvas.update()

    def _on_vispy_mouse_move(self, event):
        """Show coordinates under the mouse in the coord label."""
        if self._current_img is None:
            if hasattr(self, "coord_label"):
                self.coord_label.setText("")
            return

        tr = self.view.scene.transform
        pos = tr.map(event.pos)[:2]
        x, y = int(pos[0]), int(pos[1])

        h, w = self._current_img.shape[:2]
        if 0 <= x < w and 0 <= y < h:
            val = self._current_img[y, x]
            msg = f"({x},{y}): {float(val):.5f}"
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

        if VISPY_AVAILABLE and self._current_img is not None:
            self.image_visual.clim = (self.vmin, self.vmax)
            self.canvas.update()
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
            if VISPY_AVAILABLE and self._current_img is not None:
                self.image_visual.clim = (self.vmin, self.vmax)
                self.canvas.update()
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

        # Update vispy image visual
        self.image_visual.set_data(img)

        # Set color limits
        vmin = self.vmin if self.vmin is not None else np.percentile(img, 1)
        vmax = self.vmax if self.vmax is not None else np.percentile(img, 99)
        self.image_visual.clim = (vmin, vmax)
        self.image_visual.cmap = self.current_cmap

        # Adapt canvas background to current theme
        current_theme = self.theme_manager.get_current_theme()
        bg_color = 'black' if current_theme == 'dark' else 'white'
        self.canvas.bgcolor = bg_color

        # Handle zoom with camera rect
        if (self._keep_zoom and
            self._last_image_shape == (h, w) and
            self._last_camera_rect is not None):
            self.view.camera.rect = self._last_camera_rect
        else:
            self.view.camera.rect = (0, 0, w, h)

        self._last_camera_rect = self.view.camera.rect
        self._last_image_shape = (h, w)

        self.canvas.update()



    def _remember_view(self):
        """Record current view so the next image keeps the same zoom/pan."""
        try:
            if hasattr(self, 'view'):
                self._last_camera_rect = self.view.camera.rect
                if self._current_img is not None:
                    self._last_image_shape = self._current_img.shape
        except Exception:
            pass

    def _reset_view_state(self):
        """Forget any prior zoom/pan so the next image shows full frame."""
        self._keep_zoom = False
        self._last_camera_rect = None
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
    # def _run_reconstruction_on_machine(self, file_path, recon_type='try'):
    #     """
    #     Run reconstruction on selected machine (local or remote)

    #     Args:
    #         file_path: Path to the .h5 file
    #         recon_type: 'try' or 'full'

    #     Returns:
    #         Exit code (0 for success)
    #     """
    #     machine = self.batch_machine_box.currentText()

    #     # Get reconstruction parameters from Main tab
    #     recon_way = self.recon_way_box.currentText()

    #     # Get COR value EXCLUSIVELY from the batch table for this file
    #     filename = os.path.basename(file_path)
    #     cor_val = None
    #     for file_info in self.batch_file_list:
    #         if file_info['filename'] == filename:
    #             cor_val = file_info['cor_input'].text().strip()
    #             break

    #     # Batch tab ALWAYS uses manual COR with the value from the batch table
    #     # Validate COR input - batch tab requires COR to be set in table
    #     if not cor_val:
    #         self.log_output.append(f'<span style="color:red;">❌ No COR value in batch table for {filename}</span>')
    #         return -1

    #     try:
    #         cor = float(cor_val)
    #         self.log_output.append(f'📍 Using COR value from batch table: {cor_val} for {filename}')
    #     except ValueError:
    #         self.log_output.append(f'<span style="color:red;">❌ Invalid COR value "{cor_val}" for {filename}</span>')
    #         return -1

    #     gpu = self.cuda_box_try.currentText().strip() if recon_type == 'try' else self.cuda_box_full.currentText().strip()

    #     # Build command
    #     # Batch tab ALWAYS uses manual COR with the value from the batch table
    #     if self.use_conf_box.isChecked():
    #         config_editor = self.config_editor_try if recon_type == 'try' else self.config_editor_full
    #         config_text = config_editor.toPlainText()
    #         if not config_text.strip():
    #             self.log_output.append(f'<span style="color:red;">⚠️ No config text</span>')
    #             return -1

    #         temp_conf = os.path.join(self.data_path.text(), f"temp_{recon_type}.conf")
    #         with open(temp_conf, "w") as f:
    #             f.write(config_text)

    #         cmd = ["tomocupy", str(recon_way),
    #                "--reconstruction-type", recon_type,
    #                "--config", temp_conf,
    #                "--file-name", file_path,
    #                "--rotation-axis-auto", "manual",
    #                "--rotation-axis", str(cor)]
    #     else:
    #         cmd = ["tomocupy", str(recon_way),
    #                "--reconstruction-type", recon_type,
    #                "--file-name", file_path,
    #                "--rotation-axis-auto", "manual",
    #                "--rotation-axis", str(cor)]

    #     # Wrap command for remote execution if needed
    #     cmd = self._get_batch_machine_command(cmd, machine)

    #     # Log the machine being used
    #     if machine != "Local":
    #         self.log_output.append(f'🖥️ Running on {machine}: {os.path.basename(file_path)}')

    #     # Execute command
    #     code = self.run_command_live(cmd, proj_file=file_path,
    #                                  job_label=f"{recon_type}-{machine}",
    #                                  wait=True, cuda_devices=gpu if machine == "Local" else None)

    #     return code

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

    # def _refresh_batch_file_list(self):
    #     """Refresh the file list in the batch processing tab"""
    #     folder = self.data_path.text()
    #     if not folder or not os.path.isdir(folder):
    #         QMessageBox.warning(self, "Warning", "Please select a valid data folder first.")
    #         return

    #     # Warn if queue is running
    #     if self.batch_running:
    #         reply = QMessageBox.question(
    #             self, 'Queue Running',
    #             f'A batch queue is currently running ({len(self.batch_running_jobs)} jobs active, {len(self.batch_job_queue)} queued).\n\n'
    #             f'Refreshing will delete the table widgets but jobs will continue running in the background.\n\n'
    #             f'Continue with refresh?',
    #             QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    #         )
    #         if reply == QMessageBox.No:
    #             return
    #         self.log_output.append(f'<span style="color:orange;">⚠️  Refreshed file list while queue was running - status updates may be lost</span>')

    #     # Get all .h5 files
    #     h5_files = sorted(glob.glob(os.path.join(folder, "*.h5")), key=os.path.getmtime, reverse=True)

    #     # Save current COR values before clearing (to preserve user input)
    #     cor_values = {}
    #     for file_info in self.batch_file_list:
    #         try:
    #             filename = file_info['filename']
    #             cor_val = file_info['cor_input'].text().strip()
    #             if cor_val:
    #                 cor_values[filename] = cor_val
    #         except (KeyError, RuntimeError):
    #             # Widget may have been deleted
    #             pass

    #     # Clear existing table - disable sorting first to avoid issues
    #     self.batch_file_table.setSortingEnabled(False)
    #     self.batch_file_table.setRowCount(0)
    #     self.batch_file_list = []
    #     # Reset last clicked row to avoid stale row references
    #     self.batch_last_clicked_row = None

    #     # Populate table
    #     data_folder = self.data_path.text().strip()
    #     for file_path in h5_files:
    #         filename = os.path.basename(file_path)
    #         row = self.batch_file_table.rowCount()
    #         self.batch_file_table.insertRow(row)

    #         # Check reconstruction status
    #         proj_name = os.path.splitext(filename)[0]
    #         try_dir = os.path.join(f"{data_folder}_rec", "try_center", proj_name)
    #         full_dir = os.path.join(f"{data_folder}_rec", f"{proj_name}_rec")

    #         has_try = os.path.isdir(try_dir) and len(glob.glob(os.path.join(try_dir, "*.tiff"))) > 0
    #         has_full = os.path.isdir(full_dir) and len(glob.glob(os.path.join(full_dir, "*.tiff"))) > 0

    #         # Determine row color based on reconstruction status
    #         if has_full:
    #             row_color = "green"  # Full reconstruction exists
    #         elif has_try:
    #             row_color = "orange"  # Only try reconstruction exists
    #         else:
    #             row_color = "red"  # No reconstruction

    #         # Store file info
    #         file_info = {
    #             'path': file_path,
    #             'filename': filename,
    #             'status': 'Ready',
    #             'row': row,
    #             'recon_status': row_color
    #         }
    #         self.batch_file_list.append(file_info)

    #         # Checkbox for selection with shift-click support
    #         checkbox = QCheckBox()
    #         checkbox.clicked.connect(lambda checked, r=row: self._batch_checkbox_clicked(r, checked))
    #         checkbox_widget = QWidget()
    #         checkbox_layout = QHBoxLayout(checkbox_widget)
    #         checkbox_layout.addWidget(checkbox)
    #         checkbox_layout.setAlignment(Qt.AlignCenter)
    #         checkbox_layout.setContentsMargins(0, 0, 0, 0)
    #         self.batch_file_table.setCellWidget(row, 0, checkbox_widget)
    #         file_info['checkbox'] = checkbox

    #         # Filename - show full name and set tooltip with full path
    #         filename_item = QTableWidgetItem(filename)
    #         filename_item.setToolTip(f"{filename}\n\nFull path:\n{file_path}")
    #         self.batch_file_table.setItem(row, 1, filename_item)

    #         # File size
    #         try:
    #             file_size = os.path.getsize(file_path)
    #             size_str = self._format_file_size(file_size)
    #             size_item = QTableWidgetItem(size_str)
    #             size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    #             # Store numeric value for proper sorting
    #             size_item.setData(Qt.UserRole, file_size)
    #             self.batch_file_table.setItem(row, 2, size_item)
    #         except Exception as e:
    #             self.batch_file_table.setItem(row, 2, QTableWidgetItem("N/A"))

    #         # COR value (editable)
    #         cor_input = QLineEdit()
    #         cor_input.setPlaceholderText("COR value")
    #         cor_input.setAlignment(Qt.AlignCenter)
    #         cor_input.setFixedWidth(80)
    #         # Restore previous COR value if it exists
    #         if filename in cor_values:
    #             cor_input.setText(cor_values[filename])
    #         self.batch_file_table.setCellWidget(row, 3, cor_input)
    #         file_info['cor_input'] = cor_input

    #         # Status
    #         status_item = QTableWidgetItem('Ready')
    #         self.batch_file_table.setItem(row, 4, status_item)
    #         file_info['status_item'] = status_item

    #         # View Data button (original HDF5 data)
    #         view_data_btn = QPushButton("View Data")
    #         view_data_btn.clicked.connect(lambda checked, fp=file_path: self._batch_view_data(fp))
    #         self.batch_file_table.setCellWidget(row, 5, view_data_btn)

    #         # View Try button
    #         view_try_btn = QPushButton("View Try")
    #         view_try_btn.clicked.connect(lambda checked, fp=file_path: self._batch_view_try(fp))
    #         self.batch_file_table.setCellWidget(row, 6, view_try_btn)

    #         # View Full button
    #         view_full_btn = QPushButton("View Full")
    #         view_full_btn.clicked.connect(lambda checked, fp=file_path: self._batch_view_full(fp))
    #         self.batch_file_table.setCellWidget(row, 7, view_full_btn)

    #         # Actions button
    #         actions_widget = QWidget()
    #         actions_layout = QHBoxLayout(actions_widget)
    #         actions_layout.setContentsMargins(2, 2, 2, 2)
    #         actions_layout.setSpacing(2)

    #         try_btn = QPushButton("Try")
    #         try_btn.setFixedWidth(50)
    #         try_btn.clicked.connect(lambda checked, fp=file_path: self._batch_run_try_single(fp))
    #         actions_layout.addWidget(try_btn)

    #         full_btn = QPushButton("Full")
    #         full_btn.setFixedWidth(50)
    #         full_btn.clicked.connect(lambda checked, fp=file_path: self._batch_run_full_single(fp))
    #         actions_layout.addWidget(full_btn)

    #         self.batch_file_table.setCellWidget(row, 8, actions_widget)

    #         # Apply colored left border indicator based on reconstruction status
    #         # Create a colored indicator in the checkbox column
    #         checkbox_widget.setStyleSheet(f"QWidget {{ border-left: 6px solid {row_color}; }}")

    #     # Re-enable sorting after populating the table
    #     self.batch_file_table.setSortingEnabled(True)

    #     self.batch_status_label.setText(f"Loaded {len(h5_files)} files")

    #     # Try to auto-load COR values from CSV if no values were preserved from previous refresh
    #     # Only auto-load if we don't already have COR values
    #     if not cor_values:
    #         self._batch_load_cor_csv(silent=True)
    #     else:
    #         # Count how many COR values were restored
    #         restored_count = len(cor_values)
    #         self.batch_status_label.setText(f"Loaded {len(h5_files)} files ({restored_count} with COR values)")

    # def _batch_save_cor_csv(self):
    #     """Save COR values to CSV file in the data directory"""
    #     folder = self.data_path.text()
    #     if not folder or not os.path.isdir(folder):
    #         QMessageBox.warning(self, "Warning", "Please select a valid data folder first.")
    #         return

    #     if not self.batch_file_list:
    #         QMessageBox.warning(self, "Warning", "No files in the batch list.")
    #         return

    #     csv_path = os.path.join(folder, "batch_cor_values.csv")

    #     try:
    #         import csv
    #         saved_count = 0
    #         skipped_count = 0

    #         with open(csv_path, 'w', newline='') as csvfile:
    #             writer = csv.writer(csvfile)
    #             writer.writerow(['Filename', 'COR'])

    #             for file_info in self.batch_file_list:
    #                 try:
    #                     filename = file_info['filename']
    #                     cor_value = file_info['cor_input'].text().strip()
    #                     writer.writerow([filename, cor_value])
    #                     saved_count += 1
    #                 except (RuntimeError, KeyError):
    #                     # Widget was deleted (e.g., file was removed)
    #                     skipped_count += 1
    #                     continue

    #         if skipped_count > 0:
    #             self.log_output.append(f'<span style="color:orange;">⚠️  Saved {saved_count} COR values to {csv_path} ({skipped_count} skipped - widgets deleted)</span>')
    #             self.batch_status_label.setText(f"COR values saved ({skipped_count} files skipped)")
    #             QMessageBox.information(self, "Success", f"COR values saved to:\n{csv_path}\n\n{saved_count} saved, {skipped_count} skipped (deleted files)")
    #         else:
    #             self.log_output.append(f'<span style="color:green;">✅ Saved {saved_count} COR values to {csv_path}</span>')
    #             self.batch_status_label.setText(f"COR values saved to batch_cor_values.csv")
    #             QMessageBox.information(self, "Success", f"COR values saved to:\n{csv_path}")

    #     except Exception as e:
    #         self.log_output.append(f'<span style="color:red;">❌ Failed to save COR CSV: {e}</span>')
    #         QMessageBox.critical(self, "Error", f"Failed to save COR values:\n{e}")

    # def _batch_load_cor_csv(self, silent=False):
    #     """Load COR values from CSV file in the data directory"""
    #     folder = self.data_path.text()
    #     if not folder or not os.path.isdir(folder):
    #         if not silent:
    #             QMessageBox.warning(self, "Warning", "Please select a valid data folder first.")
    #         return

    #     if not self.batch_file_list:
    #         if not silent:
    #             QMessageBox.warning(self, "Warning", "No files in the batch list. Refresh the file list first.")
    #         return

    #     csv_path = os.path.join(folder, "batch_cor_values.csv")

    #     if not os.path.exists(csv_path):
    #         if not silent:
    #             QMessageBox.warning(self, "Warning", f"COR CSV file not found:\n{csv_path}")
    #         return

    #     try:
    #         import csv
    #         cor_dict = {}
    #         with open(csv_path, 'r') as csvfile:
    #             reader = csv.DictReader(csvfile)
    #             for row in reader:
    #                 filename = row.get('Filename', '').strip()
    #                 cor_value = row.get('COR', '').strip()
    #                 if filename:
    #                     cor_dict[filename] = cor_value

    #         # Apply COR values to the table
    #         loaded_count = 0
    #         skipped_count = 0
    #         for file_info in self.batch_file_list:
    #             try:
    #                 filename = file_info['filename']
    #                 if filename in cor_dict:
    #                     file_info['cor_input'].setText(cor_dict[filename])
    #                     loaded_count += 1
    #             except (RuntimeError, KeyError):
    #                 # Widget was deleted (e.g., file was removed)
    #                 skipped_count += 1
    #                 continue

    #         if not silent:
    #             if skipped_count > 0:
    #                 self.log_output.append(f'<span style="color:orange;">⚠️  Loaded {loaded_count} COR values from {csv_path} ({skipped_count} skipped - widgets deleted)</span>')
    #                 self.batch_status_label.setText(f"Loaded {loaded_count} COR values ({skipped_count} skipped)")
    #                 QMessageBox.information(self, "Success", f"Loaded {loaded_count} COR values from:\n{csv_path}\n\n{skipped_count} files skipped (deleted widgets)")
    #             else:
    #                 self.log_output.append(f'<span style="color:green;">✅ Loaded COR values from {csv_path}</span>')
    #                 self.batch_status_label.setText(f"Loaded {loaded_count} COR values from CSV")
    #                 QMessageBox.information(self, "Success", f"Loaded {loaded_count} COR values from:\n{csv_path}")
    #         else:
    #             self.batch_status_label.setText(f"Loaded {len(self.batch_file_list)} files ({loaded_count} with COR values)")

    #     except Exception as e:
    #         if not silent:
    #             self.log_output.append(f'<span style="color:red;">❌ Failed to load COR CSV: {e}</span>')
    #             QMessageBox.critical(self, "Error", f"Failed to load COR values:\n{e}")


    # def _batch_remove_selected(self):
    #     """Physically delete selected files from the filesystem"""
    #     files_to_remove = [f for f in self.batch_file_list if f['checkbox'].isChecked()]

    #     if not files_to_remove:
    #         QMessageBox.warning(self, "Warning", "No files selected.")
    #         return

    #     # Confirm deletion
    #     reply = QMessageBox.question(
    #         self, 'Confirm File Deletion',
    #         f'Are you sure you want to PERMANENTLY DELETE {len(files_to_remove)} file(s) from disk?\n\nThis action cannot be undone!',
    #         QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    #     )

    #     if reply == QMessageBox.No:
    #         return

    #     # Delete files from disk
    #     deleted_count = 0
    #     failed_files = []
    #     rows_to_remove = []

    #     for file_info in files_to_remove:
    #         try:
    #             os.remove(file_info['path'])
    #             rows_to_remove.append(file_info['row'])
    #             deleted_count += 1
    #             self.log_output.append(f'<span style="color:green;">✅ Deleted: {file_info["filename"]}</span>')
    #         except Exception as e:
    #             failed_files.append(file_info['filename'])
    #             self.log_output.append(f'<span style="color:red;">❌ Failed to delete {file_info["filename"]}: {e}</span>')

    #     # Remove rows from table
    #     for row in sorted(rows_to_remove, reverse=True):
    #         self.batch_file_table.removeRow(row)

    #     # Update file list and row indices
    #     self.batch_file_list = [f for f in self.batch_file_list if f['row'] not in rows_to_remove]
    #     for i, file_info in enumerate(self.batch_file_list):
    #         file_info['row'] = i

    #     # Update status
    #     if failed_files:
    #         self.batch_status_label.setText(f"Deleted {deleted_count} files, {len(failed_files)} failed")
    #     else:
    #         self.batch_status_label.setText(f"Successfully deleted {deleted_count} files")

    #     # Refresh the main file dropdown
    #     self.refresh_h5_files()

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

    def _batch_view_selected_data(self):
        """Open HDF5 viewer for the first selected file"""
        selected_files = []
        for file_info in self.batch_file_main_list:
            if file_info['checkbox'].isChecked():
                selected_files.append(file_info['path'])

        if not selected_files:
            QMessageBox.warning(self, "No Selection", "Please select at least one file to view.")
            self.log_output.append('<span style="color:orange;">⚠️  No files selected for viewing</span>')
            return

        # Open viewer for the first selected file
        first_file = selected_files[0]
        self._batch_view_data(first_file)

        if len(selected_files) > 1:
            self.log_output.append(f'<span style="color:blue;">ℹ️  {len(selected_files)} files selected, opened first: {os.path.basename(first_file)}</span>')

    # def _batch_view_try(self, file_path):
    #     """View try reconstruction for a specific file"""
    #     # Set the file in the main dropdown
    #     index = self.proj_file_box.findData(file_path)
    #     if index >= 0:
    #         self.proj_file_box.setCurrentIndex(index)
    #     else:
    #         # File not in dropdown, refresh and try again
    #         self.refresh_h5_files()
    #         index = self.proj_file_box.findData(file_path)
    #         if index >= 0:
    #             self.proj_file_box.setCurrentIndex(index)

    #     # Call the existing view try method
    #     self.view_try_reconstruction()

    # def _batch_view_full(self, file_path):
    #     """View full reconstruction for a specific file"""
    #     # Set the file in the main dropdown
    #     index = self.proj_file_box.findData(file_path)
    #     if index >= 0:
    #         self.proj_file_box.setCurrentIndex(index)
    #     else:
    #         # File not in dropdown, refresh and try again
    #         self.refresh_h5_files()
    #         index = self.proj_file_box.findData(file_path)
    #         if index >= 0:
    #             self.proj_file_box.setCurrentIndex(index)

    #     # Call the existing view full method
    #     self.view_full_reconstruction()

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
        selected_files = [f for f in self.batch_file_main_list if f['checkbox'].isChecked()]
        machine = self.batch_machine_box.currentText()

        if not selected_files:
            QMessageBox.warning(self, "Warning", "No files selected.")
            return

        num_gpus = self.batch_gpus_per_machine.value()
        print(f'this is num gpus {num_gpus} before start')
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
        selected_files = [f for f in self.batch_file_main_list if f['checkbox'].isChecked()]
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

  #=========helper to update table based on filename========================
    def _get_full_recon_status(self, file_path):
        """
        Check the full reconstruction output directory and return status with slice range.
        Returns: (status_text, status_color)
        """
        try:
            table_folder = self.data_path.text()
            if not table_folder:
                return "Done full", "green"

            filename = os.path.basename(file_path)
            proj_name = os.path.splitext(filename)[0]
            full_dir = os.path.join(f"{table_folder}_rec", f"{proj_name}_rec")

            # Check if output directory exists and has TIFF files
            if os.path.isdir(full_dir):
                tiff_files = sorted(glob.glob(os.path.join(full_dir, "*.tiff")))
                if len(tiff_files) > 0:
                    # Get slice numbers from first and last file
                    num_1 = int(Path(tiff_files[0]).stem.split("_")[-1])
                    num_2 = int(Path(tiff_files[-1]).stem.split("_")[-1])
                    return f"Full {num_1}-{num_2}", "green"

            # Fallback if directory doesn't exist or no files found
            return "Done full", "green"
        except Exception as e:
            # If anything goes wrong, just return basic status
            return "Done full", "green"

    def _find_row_by_filename(self, filename, filename_col=1):
        table = self.batch_file_main_table
        for row in range(table.rowCount()):
            it = table.item(row, filename_col)
            if it and it.text() == filename:
                return row
        return None

    def _set_status_by_filename(self, filename, text, status_col=3, filename_col=1, color=None):
        table = self.batch_file_main_table
        row = self._find_row_by_filename(filename, filename_col=filename_col)
        if row is None:
            return False  # not found (maybe list refreshed)

        item = table.item(row, status_col)
        if item is None:
            item = QTableWidgetItem()
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # optional
            table.setItem(row, status_col, item)
        if color is not None:
            self.batch_file_main_list[row]['recon_status'] = color
            checkbox_widget = self.batch_file_main_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox_widget.setStyleSheet(f"QWidget {{ border-left: 6px solid {color}; }}")
            status_item = QTableWidgetItem(text)
            self.batch_file_main_table.setItem(row, 3, status_item)
            self.batch_file_main_list[row]['status'] = text
        return True

    def _run_batch_with_queue(self, selected_files, recon_type, num_gpus, machine):
        """
        Run batch reconstructions with GPU queue management
        """
        self.log_output.append(f'<span style="color:magenta;">🔍 DEBUG: Starting {recon_type} batch, batch_running={self.batch_running}</span>')

        jobs_to_add = [(f, recon_type, machine) for f in selected_files]

        # Mark all jobs as queued
        for f, _, _ in jobs_to_add:
            try:
                self._set_status_by_filename(
                    os.path.basename(f["filename"]), "Queued", status_col=3, filename_col=1, color="blue"
                )
            except RuntimeError:
                pass

        # If queue is already running, just add to it
        if self.batch_running:
            self.batch_job_queue.extend(jobs_to_add)
            self.batch_total_jobs += len(selected_files)
            self.log_output.append(
                f'<span style="color:blue;">➕ Added {len(selected_files)} job(s) to running queue</span>'
            )
            return

        # Start new queue
        self.batch_running = True
        self.batch_job_queue = jobs_to_add
        self.batch_running_jobs = {}
        self.batch_available_gpus = list(range(num_gpus))
        self.batch_current_machine = machine
        self.batch_current_num_gpus = num_gpus

        self.batch_total_jobs = len(selected_files)
        self.batch_completed_jobs = 0

        self.log_output.append(
            f'<span style="color:blue;">🚀 Starting batch queue: {len(self.batch_job_queue)} jobs, {num_gpus} GPU(s)</span>'
        )

        QApplication.processEvents()

        progress_window_opened = False  #gate progress window

        # Keep processing until queue is empty and all jobs are done
        while self.batch_job_queue or self.batch_running_jobs:
            self.log_output.append(
                f'<span style="color:gray;">🔄 Queue loop: {len(self.batch_job_queue)} queued, {len(self.batch_running_jobs)} running, {len(self.batch_available_gpus)} GPUs available</span>'
            )
            QApplication.processEvents()

            # Start new jobs if GPUs are available and jobs are queued
            while self.batch_available_gpus and self.batch_job_queue:
                gpu_id = self.batch_available_gpus.pop(0)
                file_info, job_recon_type, job_machine = self.batch_job_queue.pop(0)

                try:
                    self._set_status_by_filename(
                        os.path.basename(file_info["filename"]),
                        f"Running on GPU {gpu_id}",
                        status_col=3,
                        filename_col=1,
                        color="yellow"
                    )
                except RuntimeError:
                    pass

                QApplication.processEvents()

                # capture return value (process) and validate it
                try:
                    process = self._start_batch_job_async(file_info, job_recon_type, gpu_id, job_machine)  
                except Exception as e:
                    self.log_output.append(
                        f'<span style="color:red;">❌ Failed to start job for {file_info.get("filename","?")}: {e}</span>'
                    )
                    # Put GPU back and mark failed
                    self.batch_available_gpus.append(gpu_id)
                    self.batch_available_gpus.sort()
                    try:
                        self._set_status_by_filename(
                            os.path.basename(file_info["filename"]), "Ready", 3, 1, color="red"
                        )
                    except RuntimeError:
                        pass
                    continue  # <<< CHANGED: continue queue

                if process is None or not isinstance(process, QProcess):
                    # Process is None when job is skipped (e.g., missing COR)
                    # The specific reason was already logged in _start_batch_job_async
                    self.batch_available_gpus.append(gpu_id)
                    self.batch_available_gpus.sort()
                    try:
                        self._set_status_by_filename(os.path.basename(file_info["filename"]), "Skipped", 3, 1, color="gray")
                    except RuntimeError:
                        pass
                    # Count as completed to keep progress accurate
                    self.batch_completed_jobs += 1
                    continue

                # open progress window ONLY after first process starts successfully
                if not progress_window_opened:
                    self.progress_window.batch_progress_bar.setValue(0)
                    self.progress_window.batch_queue_label.setText(f"Queue: {len(self.batch_job_queue)} jobs waiting")
                    self.progress_window.batch_status_label.setText("Running batch jobs…")
                    self.progress_window.show()
                    progress_window_opened = True
                    #enable Stop button in the progress window
                    try:
                        self.progress_window.set_running(True)
                    except Exception:
                        pass

                self.batch_running_jobs[gpu_id] = (process, file_info, job_recon_type)

                self.log_output.append(
                    f'<span style="color:blue;">🚀 GPU {gpu_id}: Started {job_recon_type} - {file_info["filename"]} '
                    f'(Running: {len(self.batch_running_jobs)}, Queued: {len(self.batch_job_queue)})</span>'
                )

            # Check for completed jobs
            completed_gpus = []
            for gpu_id, (process, file_info, job_recon_type) in list(self.batch_running_jobs.items()):
                if process.state() == QProcess.NotRunning:
                    exit_code = process.exitCode()
                    self.batch_completed_jobs += 1

                    try:
                        if exit_code == 0:
                            # Set status based on reconstruction type
                            if job_recon_type == 'try':
                                status_text = "Done try"
                                status_color = "orange"
                            else:  # full
                                # Check output directory for actual slice numbers
                                status_text, status_color = self._get_full_recon_status(file_info["filename"])

                            self._set_status_by_filename(
                                os.path.basename(file_info["filename"]),
                                status_text,
                                status_col=3,
                                filename_col=1,
                                color=status_color
                            )
                            self.log_output.append(f'<span style="color:green;">✅ GPU {gpu_id} finished {job_recon_type}: {file_info["filename"]}</span>')
                        else:
                            self._set_status_by_filename(
                                os.path.basename(file_info["filename"]),
                                f"{job_recon_type.capitalize()} Failed",
                                status_col=3,
                                filename_col=1,
                                color="red"
                            )
                            self.log_output.append(f'<span style="color:red;">❌ GPU {gpu_id} failed {job_recon_type}: {file_info["filename"]}</span>')
                    except RuntimeError:
                        self.log_output.append(
                            f'<span style="color:gray;">✅ GPU {gpu_id} finished: {file_info["filename"]} (widget deleted)</span>'
                        )

                    completed_gpus.append(gpu_id)

            # Free up completed GPUs
            for gpu_id in completed_gpus:
                del self.batch_running_jobs[gpu_id]
                self.batch_available_gpus.append(gpu_id)
                self.batch_available_gpus.sort()

            # Update progress
            progress = int((self.batch_completed_jobs / self.batch_total_jobs) * 100) if self.batch_total_jobs else 0

            if progress_window_opened:
                self.progress_window.batch_progress_bar.setValue(progress)
                active_gpus = sorted(self.batch_running_jobs.keys())
                gpu_status = f"GPUs: {active_gpus}" if active_gpus else "GPUs: idle"
                self.progress_window.batch_status_label.setText(
                    f"Completed {self.batch_completed_jobs}/{self.batch_total_jobs} | {gpu_status} | Queue: {len(self.batch_job_queue)}"
                )
                self.progress_window.batch_queue_label.setText(f"Queue: {len(self.batch_job_queue)} jobs waiting")

            QApplication.processEvents()

            if self.batch_running_jobs:
                import time
                time.sleep(0.2)

        # Finalize
        if progress_window_opened:
            self.progress_window.batch_progress_bar.setValue(100)
            self.progress_window.batch_status_label.setText("Batch completed.")
            self.progress_window.batch_queue_label.setText("Queue: 0 jobs waiting")

        self.log_output.append(f'<span style="color:green;">🏁 Batch queue finished: {self.batch_completed_jobs} files completed</span>')

        # Reset batch running flag so new batches can start
        self.batch_running = False
        self.log_output.append('<span style="color:blue;">✅ batch_running set to False, ready for new batch</span>')


    def _batch_stop_queue(self):
        """Immediately stop the batch queue and kill all running jobs."""

        # Nothing to stop
        if not getattr(self, "batch_running", False):
            return

        # ===== CRITICAL: stop scheduling FIRST =====
        self.batch_running = False

        # ===== Kill all running processes =====
        for gpu_id, (process, file_info, job_recon_type) in list(self.batch_running_jobs.items()):
            try:
                # Best-effort terminate → kill
                try:
                    process.terminate()
                    if not process.waitForFinished(1500):
                        process.kill()
                except Exception:
                    process.kill()
            except Exception:
                pass

            # Update table status
            try:
                self._set_status_by_filename(file_info['filename'],text="Cancelled batch",color='red')
            except Exception:
                pass

            self.log_output.append(
                f'<span style="color:orange;">🛑 Cancelled job on GPU {gpu_id}: '
                f'{file_info.get("filename", "")}</span>'
            )

        # ===== Cancel queued (not yet started) jobs =====
        for file_info, job_recon_type, job_machine in self.batch_job_queue:
            try:
                self._set_status_by_filename(file_info['filename'],text="Cancelled batch",color='red')
            except Exception:
                pass

        # ===== Clear internal state =====
        self.batch_job_queue.clear()
        self.batch_running_jobs.clear()

        # ===== Reset MAIN GUI =====
        #self.batch_stop_btn.setEnabled(False)
        #self.batch_progress_bar.setValue(0)
        #self.batch_status_label.setText("Batch stopped")
        #self.batch_queue_label.setText("Queue: 0 jobs waiting")

        # ===== Mirror state to PROGRESS WINDOW =====
        try:
            if hasattr(self, "progress_window") and self.progress_window is not None:
                self.progress_window.set_running(False)
                self.progress_window.set_progress(0)
                self.progress_window.set_status("Batch stopped")
                self.progress_window.set_queue(0)
        except Exception:
            pass

        self.log_output.append(
            '<span style="color:orange;">🛑 Batch queue stopped by user</span>'
        )
            
    def _start_batch_job_async(self, file_info, recon_type, gpu_id, machine):
        """
        Start a reconstruction job asynchronously
        Returns: QProcess object
        """
        file_path = file_info['path']
        filename = os.path.basename(file_path)

        # properly read method text from combo box
        if recon_type == 'try':
            recon_way = self.recon_way_box.currentText()  # <<< CHANGED
            cor_val = self.cor_input.text().strip()
            rec_method = self.cor_method_box.currentText()  # <<< FIX (was widget object)
            if rec_method == 'manual':
                try:
                    cor = float(cor_val)
                except ValueError:
                    self.log_output.append(
                        f'<span style="color:red;">❌ Invalid COR value "{cor_val}" for {filename}, skipping</span>'
                    )
                    return None  #return None to indicate failure

        elif recon_type == 'full':
            recon_way = self.recon_way_box_full.currentText()  
            cor_val = file_info['cor_input'].text().strip()
            rec_method = self.cor_full_method.currentText()  

            if not cor_val:
                self.log_output.append(
                    f'<span style="color:orange;">⚠️ No COR value in batch table for {filename}, skipping</span>'
                )
                # Return None to skip this job - queue will handle it
                return None

            try:
                cor = float(cor_val)
            except ValueError:
                self.log_output.append(
                    f'<span style="color:red;">❌ Invalid COR value "{cor_val}" for {filename}, skipping</span>'
                )
                # Return None to skip this job - queue will handle it
                return None
        else:
            self.log_output.append(
                f'<span style="color:red;">❌ Unknown recon_type "{recon_type}"</span>'
            )
            return None  

        # Build command
        if self.use_conf_box.isChecked():
            config_editor = self.config_editor_try if recon_type == 'try' else self.config_editor_full
            config_text = config_editor.toPlainText()

            temp_conf = os.path.join(self.data_path.text(), f"temp_{recon_type}_gpu{gpu_id}.conf")
            with open(temp_conf, "w") as f:
                f.write(config_text)

            #always build cmd deterministically
            if rec_method == "manual":
                cmd = [
                    "tomocupy", str(recon_way),
                    "--reconstruction-type", recon_type,
                    "--config", temp_conf,
                    "--file-name", file_path,
                    "--rotation-axis-auto", "manual",
                    "--rotation-axis", str(cor)
                ]
            else:
                cmd = [
                    "tomocupy", str(recon_way),
                    "--reconstruction-type", recon_type,
                    "--config", temp_conf,
                    "--file-name", file_path,
                    "--rotation-axis-auto", "auto"
                ]
        else:
            if rec_method == "manual":
                cmd = [
                    "tomocupy", str(recon_way),
                    "--reconstruction-type", recon_type,
                    "--file-name", file_path,
                    "--rotation-axis-auto", rec_method,
                    "--rotation-axis", str(cor)
                ]
            else:
                cmd = [
                    "tomocupy", str(recon_way),
                    "--reconstruction-type", recon_type,
                    "--file-name", file_path,
                    "--rotation-axis-auto", "auto"
                ]
            # Append tabs selections
            cmd += self._gather_params_args()
            cmd += self._gather_rings_args()
            cmd += self._gather_bhard_args()
            cmd += self._gather_phase_args()
            cmd += self._gather_Geometry_args()        
            cmd += self._gather_Data_args()                
            cmd += self._gather_Performance_args()           
        self.log_output.append(f'{cmd}')    

        # <<< FIX: assign wrapped cmd (previously return value was ignored)
        cmd = self._get_batch_machine_command(cmd, machine)  # <<< FIX

        # Create and configure process
        p = QProcess(self)
        p.setProcessChannelMode(QProcess.ForwardedChannels)

        # Set CUDA_VISIBLE_DEVICES for GPU assignment (local only)
        if machine == "Local":
            env = QProcessEnvironment.systemEnvironment()
            env.insert("CUDA_VISIBLE_DEVICES", str(gpu_id))
            p.setProcessEnvironment(env)

        # Start process
        p.start(str(cmd[0]), [str(a) for a in cmd[1:]])

        # Wait a moment for process to actually start
        if not p.waitForStarted(5000):  # Wait up to 5 seconds
            self.log_output.append(
                f'<span style="color:red;">❌ Process failed to start for {filename}</span>'
            )
            return None

        self.log_output.append(
            f'<span style="color:blue;">✓ Process started successfully for {filename} (PID: {p.processId()})</span>'
        )
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

        # Update vispy canvas background
        if hasattr(self, 'canvas'):
            bg_color = 'black' if theme_name == 'dark' else 'white'
            self.canvas.bgcolor = bg_color
            self.canvas.update()

        # Refresh current image if available
        if self._current_img is not None:
            self.refresh_current_image()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = TomoGUI()
    w.show()
    sys.exit(app.exec_())

