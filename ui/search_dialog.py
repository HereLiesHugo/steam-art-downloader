from PySide6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QListWidgetItem, 
                               QPushButton, QLabel, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from core.steamdb import SteamDBFetcher

class SearchWorker(QThread):
    finished = Signal(list)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        results = SteamDBFetcher.search_games(self.query)
        self.finished.emit(results)

class SearchDialog(QDialog):
    def __init__(self, query, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Game")
        self.resize(500, 400)
        self.selected_appid = None
        self.selected_name = None
        
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel(f"Searching for '{query}'...")
        layout.addWidget(self.status_label)
        
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.select_game)
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self.select_game)
        btn_layout.addWidget(select_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Start search
        self.worker = SearchWorker(query)
        self.worker.finished.connect(self.on_search_finished)
        self.worker.start()

    def on_search_finished(self, results):
        self.list_widget.clear()
        if not results:
            self.status_label.setText("No games found.")
            return
            
        self.status_label.setText(f"Found {len(results)} games. Please select one:")
        
        for item in results:
            text = f"{item['name']} (ID: {item['id']})"
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.UserRole, item['id'])
            list_item.setData(Qt.UserRole + 1, item['name'])
            # We could load the icon async here too if we wanted fanciness
            self.list_widget.addItem(list_item)

    def select_game(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_appid = str(current_item.data(Qt.UserRole))
            self.selected_name = current_item.data(Qt.UserRole + 1)
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a game from the list.")
