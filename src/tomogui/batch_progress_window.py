from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QProgressBar, QLabel, QPushButton
from PyQt5.QtCore import QTimer, pyqtSignal

class ProgressWindow(QDialog):
    stop_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Batch Progress")
        self.setGeometry(200, 200, 400, 200)

        # Progress section inside the new window
        progress_group = QGroupBox("Batch Progress")
        progress_layout = QVBoxLayout()

        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setValue(0)  # Initialize to 0
        progress_layout.addWidget(self.batch_progress_bar)

        self.batch_status_label = QLabel("Ready")
        progress_layout.addWidget(self.batch_status_label)

        self.batch_queue_label = QLabel("Queue: 0 jobs waiting")
        progress_layout.addWidget(self.batch_queue_label)

        self.batch_stop_btn = QPushButton("Stop Batch")
        self.batch_stop_btn.setEnabled(False)
        progress_layout.addWidget(self.batch_stop_btn)

        # Set the layout of the progress window
        progress_group.setLayout(progress_layout)
        dialog_layout = QVBoxLayout(self)
        dialog_layout.addWidget(progress_group)
        self.setLayout(dialog_layout)

        # Connect stop button
        self.batch_stop_btn.clicked.connect(self._on_stop_clicked)  # emit stop_requested

        # Timer to simulate progress updates (unused unless you call start_progress)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)

        # Keep track of progress
        self.current_value = 0
        self.is_running = False

    def start_progress(self):
        """Start the timer to simulate the progress bar's progress (optional)."""
        self.is_running = True
        self.timer.start(100)  # Update progress every 100ms
        self.batch_stop_btn.setEnabled(True)  # Enable stop button

    def stop_batch(self):
        """Stop the simulated progress timer (optional)."""
        self.is_running = False
        self.timer.stop()  # Stop progress updates
        self.batch_stop_btn.setEnabled(False)  # Disable stop button
        self.batch_status_label.setText("Batch stopped.")

    def update_progress(self):
        """Simulated progress update (optional)."""
        if self.is_running:
            self.current_value += 1
            if self.current_value > 100:
                self.current_value = 100
                self.timer.stop()
                self.batch_status_label.setText("Batch completed")

            self.batch_progress_bar.setValue(self.current_value)
            self.batch_status_label.setText(f"Progress: {self.current_value}%")

    def update_queue_label(self, queue_size):
        """Update the queue label to show remaining jobs (optional)."""
        self.batch_queue_label.setText(f"Queue: {queue_size} jobs waiting")

    # better stop button UX + emit signal =====
    def _on_stop_clicked(self):
        """UI handler for the Stop button."""
        # Disable immediately to prevent double-clicks; GUI will re-enable if needed
        self.batch_stop_btn.setEnabled(False)
        self.batch_status_label.setText("Stopping…")
        self.stop_requested.emit()

    # external control API used by gui.py =====
    def set_running(self, running: bool):
        """Enable/disable the stop button depending on batch state."""
        self.batch_stop_btn.setEnabled(bool(running))

    def set_progress(self, value: int):
        try:
            self.batch_progress_bar.setValue(int(value))
        except Exception:
            pass

    def set_status(self, text: str):
        self.batch_status_label.setText(str(text))

    def set_queue(self, queue_size: int):
        self.batch_queue_label.setText(f"Queue: {int(queue_size)} jobs waiting")
