# -*- coding: utf-8 -*-
"""
Image Randomizer Utility

A desktop application built with PySide6 that provides a user-friendly interface
for randomizing the filenames of images within a selected directory.

Features:
  - Select a folder containing images.
  - Specify a custom prefix for the new filenames.
  - Randomly renames all supported image files (e.g., jpg, png, etc.).
  - A two-phase renaming process prevents filename conflicts.
  - A non-blocking UI that shows progress via a background worker thread.
  - A complete modern dark theme, including the window's title bar on Windows.
  - A programmatically generated application icon, requiring no external files.
"""

# === IMPORTS ===
import os
import random
import sys
import time
import uuid
from typing import Optional

# Platform-specific import for the dark title bar feature on Windows.
if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QPushButton, QProgressBar, QFileDialog,
                             QMessageBox, QHBoxLayout, QLineEdit)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPen


# === STYLING CONSTANT ===

NIGHT_THEME_STYLESHEET = """
    QWidget {
        background-color: #2b2b2b;
        color: #f0f0f0;
        font-family: 'Segoe UI', 'Arial';
        font-size: 10pt;
    }
    QMainWindow {
        background-color: #2b2b2b;
    }
    QLabel {
        color: #cccccc;
    }
    QLineEdit {
        background-color: #3c3c3c;
        border: 1px solid #555555;
        border-radius: 4px;
        padding: 5px;
        color: #f0f0f0;
    }
    QLineEdit:focus {
        border-color: #007acc;
    }
    QPushButton {
        background-color: #4a4a4a;
        border: 1px solid #555555;
        border-radius: 4px;
        padding: 6px 12px;
        min-height: 20px;
    }
    QPushButton:hover {
        background-color: #5a5a5a;
        border-color: #666666;
    }
    QPushButton:pressed {
        background-color: #007acc;
        color: white;
    }
    QPushButton#RandomizeButton {
        background-color: #007acc;
        font-weight: bold;
        color: white;
    }
    QPushButton#RandomizeButton:hover {
        background-color: #008ae6;
    }
    QPushButton#RandomizeButton:disabled {
        background-color: #333333;
        color: #777777;
        border-color: #444444;
    }
    QProgressBar {
        border: 1px solid #555555;
        border-radius: 4px;
        text-align: center;
        background-color: #3c3c3c;
        color: #f0f0f0;
    }
    QProgressBar::chunk {
        background-color: #007acc;
        border-radius: 4px;
    }
    QMessageBox {
        background-color: #3c3c3c;
    }
    /* FIX: Prevents labels inside QMessageBox from having their own background */
    QMessageBox QLabel {
        background-color: transparent;
        color: #f0f0f0;
    }
"""


# === WORKER THREAD CLASS ===

class RandomizerWorker(QThread):
    """
    Handles the file randomization process in a separate thread.

    This prevents the GUI from freezing during the potentially long-running
    file I/O operations. It communicates its status back to the main thread
    via signals.

    Signals:
        progress_update (Signal): Emits progress (int) and a status message (str).
        finished (Signal): Emits the results (dict) and duration (float) on success.
        error (Signal): Emits an error message (str) on failure.
    """
    progress_update = Signal(int, str)
    finished = Signal(dict, float)
    error = Signal(str)

    def __init__(self, folder_path: str, image_files: list[str], new_prefix: str = "image_"):
        """
        Initializes the worker thread.

        Args:
            folder_path (str): The absolute path to the directory with images.
            image_files (list[str]): A list of image filenames to process.
            new_prefix (str): The user-defined prefix for the new filenames.
        """
        super().__init__()
        self.folder_path = folder_path
        self.image_files = image_files
        self.new_prefix = new_prefix

    def run(self) -> None:
        """
        The main execution method of the thread.

        Performs a two-phase rename to avoid filename conflicts.
        1. Renames all target files to unique temporary names.
        2. Renames the temporary files to their final, randomized names.
        """
        try:
            start_time = time.time()
            random.shuffle(self.image_files)
            total_files = len(self.image_files)

            # --- Phase 1: Rename to temporary names to avoid conflicts ---
            temp_names = {}
            self.progress_update.emit(0, "Phase 1/2: Preparing files...")
            for i, filename in enumerate(self.image_files):
                old_path = os.path.join(self.folder_path, filename)
                temp_name = f"temp_{uuid.uuid4()}{os.path.splitext(filename)[1]}"
                temp_path = os.path.join(self.folder_path, temp_name)
                os.rename(old_path, temp_path)
                temp_names[filename] = temp_name
                progress = int((i + 1) / total_files * 50)
                self.progress_update.emit(progress, f"Phase 1/2: Preparing file {i+1}/{total_files}")

            # --- Phase 2: Rename from temporary names to final names ---
            self.progress_update.emit(50, "Phase 2/2: Finalizing names...")
            final_names = {}
            temp_items = list(temp_names.items())
            for i, (original_name, temp_name) in enumerate(temp_items, 1):
                temp_path = os.path.join(self.folder_path, temp_name)
                extension = os.path.splitext(original_name)[1]
                new_name = f"{self.new_prefix}{i:03d}{extension}"
                new_path = os.path.join(self.folder_path, new_name)
                os.rename(temp_path, new_path)
                final_names[original_name] = new_name
                progress = 50 + int(i / total_files * 50)
                self.progress_update.emit(progress, f"Phase 2/2: Renaming file {i}/{total_files}")

            duration = time.time() - start_time
            self.finished.emit(final_names, duration)

        except Exception as e:
            self.error.emit(str(e))


# === MAIN APPLICATION WINDOW ===

class ImageRandomizer(QMainWindow):
    """
    The main window for the Image Randomizer application.

    This class sets up the user interface, handles user interactions,
    and manages the lifecycle of the RandomizerWorker thread.
    """
    def __init__(self):
        """Initializes the main window and its components."""
        super().__init__()
        
        # --- Initialize Class Attributes ---
        self.path_edit: QLineEdit
        self.prefix_edit: QLineEdit
        self.browse_btn: QPushButton
        self.randomize_btn: QPushButton
        self.status_label: QLabel
        self.progress_bar: QProgressBar
        self.worker: Optional[RandomizerWorker] = None

        # --- Window Configuration ---
        self.setWindowTitle("Image Randomizer")
        self.setMinimumSize(550, 400)
        self.setWindowIcon(self.create_shuffle_icon())

        # --- UI and Style Setup ---
        self.setup_ui()
        self.apply_stylesheet()
        self.setup_dark_title_bar()

    def setup_ui(self) -> None:
        """Creates and arranges all widgets in the main window."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Title ---
        title_label = QLabel("Image File Randomizer")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # --- Folder Path Controls ---
        path_layout = QHBoxLayout()
        path_label = QLabel("Image Folder:")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select a folder containing images...")
        self.path_edit.setReadOnly(True)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.select_folder)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)
        main_layout.addLayout(path_layout)

        # --- Filename Prefix Controls ---
        prefix_layout = QHBoxLayout()
        prefix_label = QLabel("New Filename Prefix:")
        self.prefix_edit = QLineEdit("image_")
        self.prefix_edit.setPlaceholderText("e.g., 'photo_'")
        prefix_layout.addWidget(prefix_label)
        prefix_layout.addWidget(self.prefix_edit)
        main_layout.addLayout(prefix_layout)

        main_layout.addStretch()

        # --- Primary Action Controls ---
        self.randomize_btn = QPushButton("Randomize Files")
        self.randomize_btn.setObjectName("RandomizeButton")
        self.randomize_btn.setMinimumHeight(40)
        self.randomize_btn.setEnabled(False)  # Disabled until a folder is selected
        self.randomize_btn.clicked.connect(self.process_folder)
        main_layout.addWidget(self.randomize_btn)
        
        # --- Status Display ---
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        main_layout.addStretch()

        # --- Exit Button ---
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.close)
        exit_btn.setFixedWidth(100)
        bottom_layout.addWidget(exit_btn)
        main_layout.addLayout(bottom_layout)

    def create_shuffle_icon(self) -> QIcon:
        """
        Generates a QIcon of a shuffle symbol programmatically.

        This avoids the need to distribute a separate icon file with the application.

        Returns:
            QIcon: The generated shuffle icon.
        """
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#f0f0f0"), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)

        # Draw two crossing arrows to represent 'shuffle'
        painter.drawLine(10, 16, 40, 46)
        painter.drawLine(40, 46, 40, 30)
        painter.drawLine(40, 46, 24, 46)
        painter.drawLine(10, 46, 40, 16)
        painter.drawLine(40, 16, 40, 32)
        painter.drawLine(40, 16, 24, 16)
        
        painter.end()
        return QIcon(pixmap)
    
    def apply_stylesheet(self) -> None:
        """Applies the night theme stylesheet to the application."""
        self.setStyleSheet(NIGHT_THEME_STYLESHEET)

    def setup_dark_title_bar(self) -> None:
        """
        Applies a dark theme to the window title bar (Windows 10/11 only).
        This function has no effect on other operating systems.
        """
        if sys.platform == 'win32':
            try:
                hwnd = self.winId()
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                value = wintypes.BOOL(True)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    wintypes.HWND(hwnd),
                    DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(value),
                    ctypes.sizeof(value)
                )
            except (AttributeError, TypeError):
                # Fails gracefully on older versions of Windows or if ctypes fails.
                print("Dark title bar could not be set. Feature requires Windows 10/11.")

    def select_folder(self) -> None:
        """Opens a dialog to select a directory and updates the UI."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder Containing Images",
            os.path.expanduser("~")
        )
        if folder_path:
            self.path_edit.setText(folder_path)
            self.randomize_btn.setEnabled(True)
            self.status_label.setText(f"Folder selected: {os.path.basename(folder_path)}")

    def get_image_files(self, folder_path: str) -> list[str]:
        """
        Scans a directory and returns a list of supported image files.

        Args:
            folder_path (str): The directory to scan.

        Returns:
            list[str]: A list of filenames of the found images.
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        return [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and
            os.path.splitext(f)[1].lower() in image_extensions
        ]

    def process_folder(self) -> None:
        """
        Initiates the randomization process after validation and user confirmation.
        """
        folder_path = self.path_edit.text()
        if not os.path.isdir(folder_path):
            QMessageBox.warning(self, "Invalid Folder", "Please select a valid folder first.")
            return

        image_files = self.get_image_files(folder_path)
        if not image_files:
            QMessageBox.information(self, "No Images", "No compatible image files found in the selected folder.")
            return

        # Confirm the action with the user
        reply = QMessageBox.question(self,
            "Confirm Randomization",
            f"Found {len(image_files)} image files. Are you sure you want to "
            f"randomize their names?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.set_controls_enabled(False)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.progress_bar.setTextVisible(True)
            
            new_prefix = self.prefix_edit.text() or "image_"

            # Create and start the worker thread
            self.worker = RandomizerWorker(folder_path, image_files, new_prefix)
            self.worker.progress_update.connect(self.update_progress)
            self.worker.finished.connect(self.on_randomization_finished)
            self.worker.error.connect(self.on_randomization_error)
            self.worker.start()
        else:
            self.status_label.setText("Operation cancelled.")

    def set_controls_enabled(self, enabled: bool) -> None:
        """
        Enables or disables UI controls to prevent user interference during processing.
        """
        self.browse_btn.setEnabled(enabled)
        self.prefix_edit.setEnabled(enabled)
        self.randomize_btn.setEnabled(enabled)

    # --- Worker Thread Slots ---

    def update_progress(self, value: int, message: str) -> None:
        """Slot to handle progress updates from the worker thread."""
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{message} - %p%")
        self.status_label.setText(message)

    def on_randomization_finished(self, renamed_files: dict, duration: float) -> None:
        """Slot to handle the successful completion of the worker thread."""
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Completed - 100%")
        final_message = f"Successfully renamed {len(renamed_files)} files in {duration:.2f} seconds."
        self.status_label.setText(final_message)
        
        QMessageBox.information(self, "Success", final_message)
        
        self.progress_bar.setVisible(False)
        self.set_controls_enabled(True)

    def on_randomization_error(self, error_message: str) -> None:
        """Slot to handle any errors reported by the worker thread."""
        self.progress_bar.setVisible(False)
        self.status_label.setText("An error occurred during the operation.")
        self.set_controls_enabled(True)
        
        QMessageBox.critical(self, "Error", f"An error occurred:\n\n{error_message}")


# === APPLICATION ENTRY POINT ===

def main() -> None:
    """Initializes and runs the PySide6 application."""
    app = QApplication(sys.argv)
    window = ImageRandomizer()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
