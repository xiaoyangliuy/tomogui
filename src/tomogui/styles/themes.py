"""
Theme definitions for TomoGUI
Provides bright and dark theme stylesheets for PyQt5 widgets
"""

BRIGHT_THEME = """
QWidget {
    background-color: #f5f5f5;
    color: #212121;
    font-family: Arial, sans-serif;
}

QMainWindow {
    background-color: #ffffff;
}

QPushButton {
    background-color: #e0e0e0;
    border: 1px solid #bdbdbd;
    border-radius: 3px;
    padding: 5px 10px;
    color: #212121;
}

QPushButton:hover {
    background-color: #d0d0d0;
    border: 1px solid #9e9e9e;
}

QPushButton:pressed {
    background-color: #bdbdbd;
}

QPushButton:disabled {
    background-color: #eeeeee;
    color: #9e9e9e;
}

QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 3px;
    padding: 3px;
    color: #212121;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #4CAF50;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 3px;
    padding: 3px;
    color: #212121;
}

QComboBox:hover {
    border: 1px solid #9e9e9e;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    selection-background-color: #e0e0e0;
    selection-color: #212121;
}

QLabel {
    color: #212121;
    background-color: transparent;
}

QGroupBox {
    border: 1px solid #bdbdbd;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    color: #212121;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #212121;
}

QTabWidget::pane {
    border: 1px solid #bdbdbd;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #e0e0e0;
    border: 1px solid #bdbdbd;
    padding: 5px 10px;
    color: #212121;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    border-bottom-color: #ffffff;
}

QTabBar::tab:hover {
    background-color: #d0d0d0;
}

QProgressBar {
    border: 1px solid #bdbdbd;
    border-radius: 3px;
    text-align: center;
    background-color: #ffffff;
}

QProgressBar::chunk {
    background-color: #4CAF50;
}

QSlider::groove:horizontal {
    height: 20px;
    background: #e0e0e0;
    border-radius: 5px;
}

QSlider::handle:horizontal {
    background: #4CAF50;
    border: 1px solid #388E3C;
    width: 20px;
    height: 20px;
    margin: -5px 0;
    border-radius: 10px;
}

QSlider::handle:horizontal:hover {
    background: #66BB6A;
}

QCheckBox {
    color: #212121;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #bdbdbd;
    border-radius: 3px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #4CAF50;
    border: 1px solid #388E3C;
}

QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #bdbdbd;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #9e9e9e;
}

QScrollBar:horizontal {
    background-color: #f5f5f5;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #bdbdbd;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #9e9e9e;
}

QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}

QToolButton {
    background-color: transparent;
    border: none;
    padding: 2px;
}

QToolButton:hover {
    background-color: #e0e0e0;
    border-radius: 2px;
}
"""

DARK_THEME = """
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: Arial, sans-serif;
}

QMainWindow {
    background-color: #1e1e1e;
}

QPushButton {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 5px 10px;
    color: #e0e0e0;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border: 1px solid #6a6a6a;
}

QPushButton:pressed {
    background-color: #555555;
}

QPushButton:disabled {
    background-color: #333333;
    color: #666666;
}

QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #1e1e1e;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 3px;
    color: #e0e0e0;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #4CAF50;
}

QComboBox {
    background-color: #1e1e1e;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 3px;
    color: #e0e0e0;
}

QComboBox:hover {
    border: 1px solid #6a6a6a;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    selection-background-color: #4a4a4a;
    selection-color: #e0e0e0;
}

QLabel {
    color: #e0e0e0;
    background-color: transparent;
}

QGroupBox {
    border: 1px solid #555555;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    color: #e0e0e0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #e0e0e0;
}

QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #1e1e1e;
}

QTabBar::tab {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    padding: 5px 10px;
    color: #e0e0e0;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    border-bottom-color: #1e1e1e;
}

QTabBar::tab:hover {
    background-color: #4a4a4a;
}

QProgressBar {
    border: 1px solid #555555;
    border-radius: 3px;
    text-align: center;
    background-color: #1e1e1e;
    color: #e0e0e0;
}

QProgressBar::chunk {
    background-color: #4CAF50;
}

QSlider::groove:horizontal {
    height: 20px;
    background: #3c3c3c;
    border-radius: 5px;
}

QSlider::handle:horizontal {
    background: #4CAF50;
    border: 1px solid #388E3C;
    width: 20px;
    height: 20px;
    margin: -5px 0;
    border-radius: 10px;
}

QSlider::handle:horizontal:hover {
    background: #66BB6A;
}

QCheckBox {
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    border-radius: 3px;
    background-color: #1e1e1e;
}

QCheckBox::indicator:checked {
    background-color: #4CAF50;
    border: 1px solid #388E3C;
}

QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6a6a6a;
}

QScrollBar:horizontal {
    background-color: #2b2b2b;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #555555;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #6a6a6a;
}

QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}

QToolButton {
    background-color: transparent;
    border: none;
    padding: 2px;
}

QToolButton:hover {
    background-color: #3c3c3c;
    border-radius: 2px;
}
"""

def get_theme_stylesheet(theme_name):
    """
    Get the stylesheet for a given theme

    Args:
        theme_name (str): 'bright' or 'dark'

    Returns:
        str: QSS stylesheet string
    """
    if theme_name == 'dark':
        return DARK_THEME
    else:
        return BRIGHT_THEME
