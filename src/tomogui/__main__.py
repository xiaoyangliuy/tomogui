import os
os.environ['QT_QPA_PLATFORM'] = 'xcb'
# Force Mesa software renderer for SSH X11 forwarding (no GPU/GLX required)
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE', '1')
os.environ.setdefault('GALLIUM_DRIVER', 'llvmpipe')

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QSurfaceFormat
from .gui import TomoGUI

def main():
   """Main entry point for the application."""
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