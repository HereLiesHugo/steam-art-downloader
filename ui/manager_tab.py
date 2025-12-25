from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
                               QTableWidget, QTableWidgetItem, QPushButton, 
                               QLabel, QLineEdit, QHeaderView, QScrollArea, 
                               QGridLayout, QMessageBox, QFrame, QAbstractItemView)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon, QImage

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
            # Bypass QPixmap cache by loading data directly or using QImage
            image = QImage()
            if image.load(str(current_path)):
                self.lbl_current.setPixmap(QPixmap.fromImage(image))
            else:
                self.lbl_current.setText("Failed to Load")
        
        comp_layout.addWidget(self.lbl_current)
        
        # New / Cached
        self.lbl_new = QLabel("Not Downloaded")
        self.lbl_new.setFixedSize(140, 80)
        self.lbl_new.setStyleSheet("border: 1px solid #444; background: #222;")
        self.lbl_new.setAlignment(Qt.AlignCenter)
        self.lbl_new.setScaledContents(True)
        
        has_new = False
        if cache_path and cache_path.exists():
            image = QImage()
            if image.load(str(cache_path)):
                self.lbl_new.setPixmap(QPixmap.fromImage(image))
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
    from PySide6.QtGui import QImage # Ensure import if not at top, but usually fine.
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
            ("Portrait (600x900)", "library_600x900_2x", f"{game.app_id}p.png"),
            ("Hero Banner", "library_hero_2x", f"{game.app_id}_hero.png"),
            ("Logo", "logo", f"{game.app_id}_logo.png"),
            ("Header", "header", f"{game.app_id}.png"),
        ]
        
        row, col = 0, 0
        target_grid_dirs = []
        userdata_path = SteamPathDetector.get_userdata_path()

        if userdata_path:
            target_grid_dirs = SteamPathDetector.get_grid_paths(userdata_path)
            
        for title, db_key, filename in slots:
            # Check current: check ALL users, pick first match
            current_path = None
            for grid_dir in target_grid_dirs:
                check = grid_dir / filename
                if check.exists():
                    current_path = check
                    break
            
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

    def apply_art(self, download_app_id, art_type):
        """
        Applies artwork to Steam Grid.
        CRITICAL: 
        - download_app_id is the Steam Store ID used for downloading/caching.
        - apply_id must be derived differently for Non-Steam games.
        """
        logger.info(f"--- Apply Request Started ---")
        logger.info(f"Game: {self.selected_game.name} (IsSteam: {self.selected_game.is_steam})")
        logger.info(f"Download AppID: {download_app_id}, Type: {art_type}")

        # 1. Verify Cache (Source)
        # We assume download_app_id is valid for the cache (it's what we used to download).
        cached_path = self.cache.get_image_path(download_app_id, art_type)
        if not cached_path.exists():
            msg = f"Image not found in cache for ID {download_app_id}."
            logger.error(msg)
            QMessageBox.warning(self, "Error", "Image not found. Please download it first.")
            return

        # 2. Determine Apply ID (Target)
        apply_id = None
        
        if self.selected_game.is_steam:
            # Steam Game: Use the Store AppID directly.
            apply_id = self.selected_game.app_id
            logger.info(f"Steam Game detected. Using AppID: {apply_id}")
        else:
            # Non-Steam Game: MUST generate ID from shortcuts.vdf (strictly).
            # Even if we matched it to a Steam Store ID, we CANNOT use that for the filename.
            logger.info("Non-Steam Game detected. resolving ID from shortcuts.vdf...")
            apply_id = self._resolve_non_steam_id_live(self.selected_game.name)
            
            if not apply_id:
                # Fallback to the ID we scanned initially (better than nothing)
                logger.warning("Live VDF lookup failed. Falling back to scanned ID.")
                apply_id = self.selected_game.app_id
            
            logger.info(f"Resolved Non-Steam Apply ID: {apply_id}")

        if not apply_id:
            QMessageBox.critical(self, "Error", "Could not determine AppID for application.")
            return

        # 3. Determine Format & Filenames
        # Steam Grid Rules: PNG Only.
        # Suffix Mapping
        suffix_map = {
            "library_600x900_2x": "p.png",          # Vertical
            "library_hero_2x": "_hero.png",         # Hero
            "logo": "_logo.png",            # Logo
            "header": ".png"                # Header/Capsule
        }
        
        suffix = suffix_map.get(art_type)
        if not suffix:
            logger.error(f"Unknown art type: {art_type}")
            return
            
        target_filename = f"{apply_id}{suffix}"
        logger.info(f"Target Filename: {target_filename}")

        # 4. Multi-User Application
        userdata_path = SteamPathDetector.get_userdata_path()
        if not userdata_path:
             QMessageBox.warning(self, "Error", "Could not find Steam userdata folder.")
             return

        grid_paths = SteamPathDetector.get_grid_paths(userdata_path)
        if not grid_paths:
             QMessageBox.warning(self, "Error", "No Steam users found/config/grid directories.")
             return

        # 5. Apply Steps (Convert & Save)
        success_count = 0
        
        # Load Source Image using QImage to handle conversion
        image = QImage()
        if not image.load(str(cached_path)):
            logger.error(f"Failed to load source image: {cached_path}")
            QMessageBox.warning(self, "Error", "Failed to load cached image file.")
            return

        for grid_dir in grid_paths:
            try:
                # Create directory if missing
                grid_dir.mkdir(parents=True, exist_ok=True)
                
                target_path = grid_dir / target_filename
                
                logger.info(f"Writing to: {target_path}")
                
                # Save as PNG
                if image.save(str(target_path), "PNG"):
                    success_count += 1
                else:
                    logger.error(f"Failed to save PNG to {target_path}")

            except Exception as e:
                logger.error(f"Exception writing to {grid_dir}: {e}")

        # 6. Finish
        if success_count > 0:
            logger.info(f"Applied successfully to {success_count} locations.")
            self.load_game_details(self.selected_game) # Refresh UI preview
            QMessageBox.information(self, "Success", 
                                    f"Artwork applied for {self.selected_game.name}!\n\n"
                                    f"Applied to {success_count} user(s).\n"
                                    "IMPORTANT: Restart Steam to see changes.")
        else:
            QMessageBox.warning(self, "Error", "Failed to apply artwork to any Steam user.")


    def _resolve_non_steam_id_live(self, target_name: str) -> Optional[str]:
        """
        Re-scans shortcuts.vdf to generate the EXACT ID Steam expects.
        Uses zlib.crc32(exe+name) | 0x80000000.
        """
        import zlib
        from core.steam_vdf import VdfParser

        userdata_path = SteamPathDetector.get_userdata_path()
        if not userdata_path:
            return None

        # Iterate all users to find the shortcut
        for user_dir in userdata_path.iterdir():
            if not user_dir.is_dir() or not user_dir.name.isdigit():
                continue

            shortcuts_path = user_dir / "config" / "shortcuts.vdf"
            if not shortcuts_path.exists():
                continue

            try:
                data = VdfParser.load_binary(str(shortcuts_path))
                shortcuts = data.get("shortcuts", {})

                for key, entry in shortcuts.items():
                    if not isinstance(entry, dict): continue

                    app_name = entry.get("AppName") or entry.get("appname")
                    exe_path = entry.get("Exe") or entry.get("exe")

                    # Name must match exactly (case-sensitive usually in VDF logic, but verify?)
                    # We'll assume the scanner found it by name, so we match by name.
                    if app_name == target_name:
                        if not exe_path: exe_path = ""
                        
                        # GENERATION LOGIC STRICT
                        # f"{exe}{name}"
                        combined = f"{exe_path}{app_name}"
                        result_int = zlib.crc32(combined.encode("utf-8")) | 0x80000000
                        result_str = str(result_int)
                        
                        logger.debug(f"Live Resolve: '{app_name}' : '{exe_path}' -> {result_str}")
                        return result_str

            except Exception as e:
                logger.warning(f"Error reading shortcuts in {user_dir.name}: {e}")

        return None

#    def _get_grid_target_dir(self, game: DetectedGame) -> Optional[Path]:
#       Removed - we now Iterate all.


