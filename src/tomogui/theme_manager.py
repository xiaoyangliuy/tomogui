"""
Theme Manager for TomoGUI
Handles theme switching between bright and dark modes with persistence
"""

import os
import json
import matplotlib
import importlib.resources
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from .styles.themes import get_theme_stylesheet


class ThemeManager:
    """Manages application themes including PyQt and matplotlib styling"""

    THEMES = ['bright', 'dark']
    DEFAULT_THEME = 'bright'
    SETTINGS_FILE = os.path.expanduser('~/.tomogui_settings.json')

    def __init__(self, app=None):
        """
        Initialize the theme manager

        Args:
            app: QApplication instance (optional, will use QApplication.instance() if not provided)
        """
        self.app = app or QApplication.instance()
        self.current_theme = self.DEFAULT_THEME
        self.callbacks = []

        # Load saved theme preference
        self.load_theme_preference()

    def load_theme_preference(self):
        """Load the saved theme preference from settings file"""
        try:
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    theme = settings.get('theme', self.DEFAULT_THEME)
                    if theme in self.THEMES:
                        self.current_theme = theme
        except Exception as e:
            print(f"Warning: Could not load theme preference: {e}")

    def save_theme_preference(self):
        """Save the current theme preference to settings file"""
        try:
            settings = {}
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)

            settings['theme'] = self.current_theme

            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save theme preference: {e}")

    def apply_theme(self, theme_name):
        """
        Apply a theme to the application

        Args:
            theme_name (str): 'bright' or 'dark'
        """
        if theme_name not in self.THEMES:
            print(f"Warning: Unknown theme '{theme_name}', using '{self.DEFAULT_THEME}'")
            theme_name = self.DEFAULT_THEME

        self.current_theme = theme_name

        # Apply Qt stylesheet
        if self.app:
            stylesheet = get_theme_stylesheet(theme_name)
            self.app.setStyleSheet(stylesheet)

        # Apply matplotlib style
        self._apply_matplotlib_theme(theme_name)

        # Save preference
        self.save_theme_preference()

        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(theme_name)
            except Exception as e:
                print(f"Warning: Theme callback failed: {e}")

    def _apply_matplotlib_theme(self, theme_name):
        """Apply matplotlib style for the given theme"""
        try:
            matplotlib.rcdefaults()

            if theme_name == 'dark':
                style_file = 'tomoGUI_mpl_dark.mplstyle'
            else:
                style_file = 'tomoGUI_mpl_bright.mplstyle'

            try:
                with importlib.resources.path('tomogui.styles', style_file) as style_path:
                    matplotlib.style.use(str(style_path))
            except (ImportError, FileNotFoundError):
                print(f"Warning: Could not load matplotlib style file: {style_file}")
        except Exception as e:
            print(f"Warning: Could not apply matplotlib theme: {e}")

    def toggle_theme(self):
        """Toggle between bright and dark themes"""
        new_theme = 'dark' if self.current_theme == 'bright' else 'bright'
        self.apply_theme(new_theme)

    def get_current_theme(self):
        """Get the current theme name"""
        return self.current_theme

    def register_callback(self, callback):
        """
        Register a callback to be called when theme changes

        Args:
            callback: Function that takes theme_name as argument
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unregister_callback(self, callback):
        """
        Unregister a theme change callback

        Args:
            callback: Previously registered callback function
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
