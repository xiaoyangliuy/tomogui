import os
os.environ['QT_QPA_PLATFORM'] = 'xcb'

import sys
from PyQt5.QtWidgets import QApplication
from .gui import TomoGUI

def main():
   """Main entry point for the application."""
   app = QApplication(sys.argv)
   gui = TomoGUI()
   gui.show()
   sys.exit(app.exec_())

if __name__ == "__main__":
   main()