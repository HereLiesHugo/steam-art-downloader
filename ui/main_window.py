
from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QMenuBar
from PySide6.QtGui import QAction
import logging

from ui.downloader_tab import DownloaderTab
from ui.settings_tab import SettingsTab
from ui.manager_tab import ManagerTab
from ui.log_window import LogWindow, QtLogHandler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Art Downloader v0.9")
        self.resize(1000, 750) # Increased size for Manager Tab
        
        # Setup Logging
        self.setup_logging()

        self.init_ui()

    def setup_logging(self):
        self.log_window = LogWindow(self)
        
        # Create handler
        handler = QtLogHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handler.log_signal.connect(self.log_window.append_log)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        
        # File Handler
        try:
            file_handler = logging.FileHandler("downloader.log")
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            root_logger.addHandler(file_handler)
        except OSError as e:
            # Fallback if we can't write to file (e.g. permissions)
            print(f"Failed to setup file logging: {e}")

    def show_log_window(self):
        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()

    def init_ui(self):
        # Central Widget & Tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.downloader_tab = DownloaderTab()
        self.manager_tab = ManagerTab()
        self.settings_tab = SettingsTab()
        
        # Connect settings "Show logs" button
        self.settings_tab.show_logs_requested.connect(self.show_log_window)

        self.tabs.addTab(self.manager_tab, "Manager")
        self.tabs.addTab(self.downloader_tab, "Downloader")
        self.tabs.addTab(self.settings_tab, "Settings")

        layout.addWidget(self.tabs)

