from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from ui.downloader_tab import DownloaderTab
from ui.settings_tab import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Art Downloader")
        self.resize(800, 700) # Wider for grid view

        # Central Widget & Tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.downloader_tab = DownloaderTab()
        self.settings_tab = SettingsTab()

        self.tabs.addTab(self.downloader_tab, "Downloader")
        self.tabs.addTab(self.settings_tab, "Settings")

        layout.addWidget(self.tabs)


