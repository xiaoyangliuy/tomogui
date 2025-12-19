from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QProgressBar, QLabel, QPushButton
from PyQt5.QtCore import QTimer

class ProgressWindow(QDialog):
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
        self.batch_stop_btn.clicked.connect(self.stop_batch)

        # Timer to simulate progress updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)

        # Keep track of progress
        self.current_value = 0
        self.is_running = False

    def start_progress(self):
        """ Start the timer to simulate the progress bar's progress """
        self.is_running = True
        self.timer.start(100)  # Update progress every 100ms
        self.batch_stop_btn.setEnabled(True)  # Enable stop button

    def stop_batch(self):
        """ Stop the batch process when stop button is clicked """
        self.is_running = False
        self.timer.stop()  # Stop progress updates
        self.batch_stop_btn.setEnabled(False)  # Disable stop button
        self.batch_status_label.setText("Batch stopped.")

    def update_progress(self):
        """ Update progress bar and labels based on batch status """
        if self.is_running:
            # Update progress value
            self.current_value += 1
            if self.current_value > 100:
                self.current_value = 100
                self.timer.stop()  # Stop the timer once 100% is reached
                self.batch_status_label.setText("Batch completed")

            # Update the progress bar and status label
            self.batch_progress_bar.setValue(self.current_value)
            self.batch_status_label.setText(f"Progress: {self.current_value}%")

    def update_queue_label(self, queue_size):
        """ Update the queue label to show remaining jobs """
        self.batch_queue_label.setText(f"Queue: {queue_size} jobs waiting")
