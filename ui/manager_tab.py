from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
                               QTableWidget, QTableWidgetItem, QPushButton, 
                               QLabel, QLineEdit, QHeaderView, QScrollArea, 
                               QGridLayout, QMessageBox, QFrame, QAbstractItemView)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon

import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional

from core.game_scanner import GameScanner, DetectedGame
from core.steam_paths import SteamPathDetector
from core.steamdb import SteamDBFetcher
from core.image_cache import ImageCache
from core.settings import SettingsManager
from ui.search_dialog import SearchDialog

logger = logging.getLogger(__name__)

# --- Workers ---

class ScanWorker(QThread):
    finished = Signal(list) # List[DetectedGame]
    
    def run(self):
        settings = SettingsManager()
        # Ensure we check settings path if provided
        steam_path = None
        if settings.steam_path:
             path = Path(settings.steam_path)
             if path.exists():
                 steam_path = path
        
        scanner = GameScanner(steam_install_path=steam_path)
        games = scanner.get_installed_games()
        games.extend(scanner.get_non_steam_games())
        self.finished.emit(games)

class ArtDownloadWorker(QThread):
    finished = Signal(str, str, bytes) # app_id, key, data
    download_complete = Signal()

    def __init__(self, app_id: str, fetch_all: bool = True):
        super().__init__()
        self.app_id = app_id
        self.fetch_all = fetch_all
    
    def run(self):
        # We only really care about grid images for the manager, but let's fetch standard keys
        # The Manager usually needs: 
        # - Header (capsule) -> header.jpg
        # - Hero -> hero.jpg
        # - Logo -> logo.png
        # - Portrait (Library 600x900) -> p.jpg
        
        # SteamDBFetcher keys: "header", "library_600x900_2x", "library_hero_2x", "logo", "capsule_231x87"
        
        keys = ["header", "library_hero_2x", "logo", "library_600x900_2x"]
        
        for key in keys:
            data = SteamDBFetcher.fetch_image(self.app_id, key)
            if data:
                self.finished.emit(self.app_id, key, data)
        self.download_complete.emit()

# --- Widgets ---

class ArtSlotWidget(QWidget):
    """
    Displays a comparison: Current Steam Art vs New/Cached Art.
    Allows Applying the cached art.
    """
    apply_requested = Signal(str, str) # app_id, art_type

    def __init__(self, title, art_type, app_id, current_path: Optional[Path], cache_path: Optional[Path]):
        super().__init__()
        self.art_type = art_type
        self.app_id = app_id
        self.current_path = current_path
        self.cache_path = cache_path
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl_title)
        
        # Comparison Layout
        comp_layout = QHBoxLayout()
        
        # Current
        self.lbl_current = QLabel("No Current Art")
        self.lbl_current.setFixedSize(140, 80)
        self.lbl_current.setStyleSheet("border: 1px solid #444; background: #222;")
        self.lbl_current.setAlignment(Qt.AlignCenter)
        self.lbl_current.setScaledContents(True)
        if current_path and current_path.exists():
            pix = QPixmap(str(current_path))
            self.lbl_current.setPixmap(pix)
        
        comp_layout.addWidget(self.lbl_current)
        
        # New / Cached
        self.lbl_new = QLabel("Not Downloaded")
        self.lbl_new.setFixedSize(140, 80)
        self.lbl_new.setStyleSheet("border: 1px solid #444; background: #222;")
        self.lbl_new.setAlignment(Qt.AlignCenter)
        self.lbl_new.setScaledContents(True)
        
        has_new = False
        if cache_path and cache_path.exists():
            pix = QPixmap(str(cache_path))
            self.lbl_new.setPixmap(pix)
            has_new = True
            
        comp_layout.addWidget(self.lbl_new)
        
        layout.addLayout(comp_layout)
        
        # Action Button
        self.btn_apply = QPushButton("Apply to Steam")
        self.btn_apply.setEnabled(has_new)
        self.btn_apply.clicked.connect(self.on_apply)
        layout.addWidget(self.btn_apply)
        
    def on_apply(self):
        self.apply_requested.emit(self.app_id, self.art_type)

class ManagerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.cache = ImageCache()
        self.current_games = [] # List[DetectedGame]
        self.selected_game: Optional[DetectedGame] = None
        self.scan_worker = None
        self.dl_worker = None
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Top Bar
        top_bar = QHBoxLayout()
        
        self.btn_scan = QPushButton("Scan Games")
        self.btn_scan.clicked.connect(self.start_scan)
        top_bar.addWidget(self.btn_scan)
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter games...")
        self.filter_input.textChanged.connect(self.filter_games)
        top_bar.addWidget(self.filter_input)
        
        main_layout.addLayout(top_bar)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left: Game Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "AppID"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        splitter.addWidget(self.table)
        
        # Right: Details
        self.details_container = QWidget()
        details_layout = QVBoxLayout(self.details_container)
        
        self.lbl_game_title = QLabel("Select a game to manage artwork")
        self.lbl_game_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        details_layout.addWidget(self.lbl_game_title)
        
        # Controls for the specific game
        game_controls = QHBoxLayout()
        
        self.btn_match = QPushButton("Match Steam ID")
        self.btn_match.clicked.connect(self.match_game)
        self.btn_match.setEnabled(False)
        game_controls.addWidget(self.btn_match)
        
        self.btn_download_all = QPushButton("Download All Assets")
        self.btn_download_all.clicked.connect(self.download_current_game)
        self.btn_download_all.setEnabled(False)
        game_controls.addWidget(self.btn_download_all)
        
        details_layout.addLayout(game_controls)
        
        # Scroll Area for Art Slots
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.art_grid_widget = QWidget()
        self.art_grid_layout = QGridLayout(self.art_grid_widget)
        scroll.setWidget(self.art_grid_widget)
        
        details_layout.addWidget(scroll)
        
        splitter.addWidget(self.details_container)
        
        # Set initial sizes
        splitter.setSizes([300, 500])

    def start_scan(self):
        logger.info("Starting game scan...")
        self.btn_scan.setEnabled(False)
        self.btn_scan.setText("Scanning...")
        self.table.setRowCount(0)
        self.current_games = []
        
        self.scan_worker = ScanWorker()
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.start()
        
    def on_scan_finished(self, games: List[DetectedGame]):
        logger.info(f"Scan finished. Found {len(games)} games.")
        self.current_games = games
        self.populate_table(games)
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText("Scan Games")
        
    def populate_table(self, games):
        self.table.setRowCount(0)
        for game in games:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(game.display_name))
            self.table.setItem(row, 1, QTableWidgetItem("Steam" if game.is_steam else "Non-Steam"))
            self.table.setItem(row, 2, QTableWidgetItem(game.app_id))
            
            # Store the actual object in the first item
            self.table.item(row, 0).setData(Qt.UserRole, game)

    def filter_games(self, text):
        filtered = []
        text = text.lower()
        for game in self.current_games:
            if text in game.display_name.lower() or text in game.app_id:
                filtered.append(game)
        self.populate_table(filtered)

    def on_selection_changed(self):
        items = self.table.selectedItems()
        if not items:
            return
            
        game = items[0].data(Qt.UserRole)
        self.load_game_details(game)

    def load_game_details(self, game: DetectedGame):
        logger.info(f"Loading details for game: {game.name} (AppID: {game.app_id}, RealID: {game.real_id})")
        self.selected_game = game
        
        title = f"{game.display_name} ({game.app_id})"
        if game.real_id and game.real_id != game.app_id:
            title += f" [Matched: {game.real_id}]"
        
        self.lbl_game_title.setText(title)
        
        # Enable matching for all games (you might want to fix broken steam associations too)
        self.btn_match.setEnabled(True)
        
        # Only enable download if we have a real ID
        self.btn_download_all.setEnabled(bool(game.real_id))
        
        # Clear grid
        for i in reversed(range(self.art_grid_layout.count())): 
            self.art_grid_layout.itemAt(i).widget().setParent(None)
            
        # Define slots
        # Use real_id for cache lookups, app_id (target) for file applying.
        lookup_id = game.real_id if game.real_id else game.app_id
        
        slots = [
            ("Portrait (600x900)", "library_600x900_2x", f"{game.app_id}p.jpg"),
            ("Hero Banner", "library_hero_2x", f"{game.app_id}_hero.jpg"),
            ("Logo", "logo", f"{game.app_id}_logo.png"),
            ("Header", "header", f"{game.app_id}_header.jpg"),
        ]
        
        row, col = 0, 0
        
        target_grid_dir = self._get_grid_target_dir(game)
        self.target_grid_dir = target_grid_dir
        
        for title, db_key, filename in slots:
            # Check current
            current_path = target_grid_dir / filename if target_grid_dir else None
            
            # Check cache using LOOKUP ID (Real ID)
            # If no real_id, we can't really cache effectively from SteamDB anyway.
            cache_path = None
            if lookup_id:
                cache_path = self.cache.get_image_path(lookup_id, db_key)
            
            slot = ArtSlotWidget(title, db_key, lookup_id, current_path, cache_path)
            slot.apply_requested.connect(self.apply_art)
            
            self.art_grid_layout.addWidget(slot, row, col)
            
            col += 1
            if col > 1:
                col = 0
                row += 1

    def match_game(self):
        if not self.selected_game:
            return
            
        logger.info(f"Initiating match for {self.selected_game.name}")
        # Pre-fill with game name
        dialog = SearchDialog(self.selected_game.name, self)
        if dialog.exec():
            new_id = dialog.selected_appid
            logger.info(f"Matched {self.selected_game.name} to Steam AppID: {new_id}")
            self.selected_game.real_id = new_id
            self.load_game_details(self.selected_game)

    def download_current_game(self):
        if not self.selected_game or not self.selected_game.real_id:
            return
        
        logger.info(f"Downloading assets for {self.selected_game.name} using RealID: {self.selected_game.real_id}")
        self.btn_download_all.setEnabled(False)
        self.btn_download_all.setText("Downloading...")
        
        # Download using REAL ID
        self.dl_worker = ArtDownloadWorker(self.selected_game.real_id)
        self.dl_worker.finished.connect(self.on_image_downloaded)
        self.dl_worker.download_complete.connect(self.on_download_complete)
        self.dl_worker.start()

    def on_image_downloaded(self, app_id, key, data):
        # Save to cache
        self.cache.save_image(app_id, key, data)

    def on_download_complete(self):
        self.btn_download_all.setEnabled(True)
        self.btn_download_all.setText("Download All Assets")
        # Refresh details
        if self.selected_game:
            self.load_game_details(self.selected_game)

    def apply_art(self, app_id, art_type):
        logger.info(f"Apply requested for AppID: {app_id}, Type: {art_type}")
        
        if not self.target_grid_dir:
            logger.error("Target grid directory is None.")
            QMessageBox.warning(self, "Error", "Could not determine Steam userdata grid folder.")
            return
            
        if not self.target_grid_dir.exists():
            try:
                self.target_grid_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                QMessageBox.warning(self, "Error", f"Failed to create grid folder: {e}")
                return

        # Map art_type to filename
        filename_map = {
            "library_600x900_2x": f"{app_id}p.jpg",
            "library_hero_2x": f"{app_id}_hero.jpg",
            "logo": f"{app_id}_logo.png",
            "header": f"{app_id}_header.jpg"
        }
        
        filename = filename_map.get(art_type)
        if not filename:
            return
            
        cached_path = self.cache.get_image_path(app_id, art_type)
        if not cached_path.exists():
            QMessageBox.warning(self, "Error", "Image not found in cache. Please download it first.")
            return
            
        target_path = self.target_grid_dir / filename
        
        logger.info(f"Copying {cached_path} -> {target_path}")
        try:
            shutil.copy2(cached_path, target_path)
            # Refresh to show it
            self.load_game_details(self.selected_game)
            logger.info("Apply successful.")
        except Exception as e:
            logger.error(f"Failed to apply artwork: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply artwork: {e}")

    def _get_grid_target_dir(self, game: DetectedGame) -> Optional[Path]:
        userdata_path = SteamPathDetector.get_userdata_path()
        if not userdata_path:
            return None
            
        if game.user_id:
             return userdata_path / game.user_id / "config" / "grid"
        
        # Fallback to first found user
        users = SteamPathDetector.get_grid_paths(userdata_path)
        if users:
            return users[0]
            
        return userdata_path / "anonymous" / "config" / "grid"

