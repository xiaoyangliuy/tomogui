import os
os.environ['QT_QPA_PLATFORM'] = 'xcb'
# Force Mesa software renderer for SSH X11 forwarding (no GPU/GLX required)
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE', '1')
os.environ.setdefault('GALLIUM_DRIVER', 'llvmpipe')

import sys
import logging
import traceback
from logging.handlers import RotatingFileHandler
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QSurfaceFormat
from .gui import TomoGUI


def _setup_logging():
    """Route stdout/stderr and uncaught exceptions to ~/.tomogui/logs/tomogui.log."""
    log_dir = os.path.expanduser("~/.tomogui/logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "tomogui.log")

    handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=5)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    # Capture uncaught exceptions
    def _excepthook(exc_type, exc_value, exc_tb):
        logging.critical(
            "Uncaught exception:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        )
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    sys.excepthook = _excepthook

    logging.info("=" * 60)
    logging.info("tomogui started at %s (PID %d)", datetime.now().isoformat(), os.getpid())
    return log_path


def main():
   """Main entry point for the application."""
   log_path = _setup_logging()
   print(f"[tomogui] logging to {log_path}")

   # Request OpenGL 2.1 (no profile) before QApplication — this is the minimum
   # VisPy needs and is reliably supported by Mesa software rendering over
   # SSH X11 forwarding.  Qt5 defaults to 3.x core profile which fails.
   fmt = QSurfaceFormat()
   fmt.setVersion(2, 1)
   fmt.setProfile(QSurfaceFormat.NoProfile)
   QSurfaceFormat.setDefaultFormat(fmt)

   app = QApplication(sys.argv)
   gui = TomoGUI()
   gui.show()
   sys.exit(app.exec_())

if __name__ == "__main__":
   main()