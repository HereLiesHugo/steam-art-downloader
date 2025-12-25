import os
import zlib
from pathlib import Path
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass

from core.steam_paths import SteamPathDetector
from core.steam_vdf import VdfParser

logger = logging.getLogger(__name__)

@dataclass
class DetectedGame:
    app_id: str
    name: str
    is_steam: bool
    install_path: Optional[Path] = None
    icon_path: Optional[Path] = None
    
    # For Non-Steam games, we need to know which User ID they belong to 
    # so we can save art to the correct userdata folder.
    user_id: Optional[str] = None
    
    # real_id used for fetching art from SteamDB (matches official AppID)
    # For Steam games, this is equal to app_id. For non-Steam, it must be matched manually.
    real_id: Optional[str] = None
    
    @property
    def display_name(self):
        return self.name

class GameScanner:
    def __init__(self, steam_install_path: Optional[Path] = None):
        self.steam_path = steam_install_path
        if not self.steam_path:
            self.steam_path = SteamPathDetector.get_steam_install_path()
            
    def get_installed_games(self) -> List[DetectedGame]:
        """
        Scans all Steam Libraries (from libraryfolders.vdf) for installed games.
        """
        games = []
        if not self.steam_path:
            return games
            
        library_vdf_path = self.steam_path / "steamapps" / "libraryfolders.vdf"
        if not library_vdf_path.exists():
            # Fallback: maybe just check steamapps directly if vdf missing (rare)
            return self._scan_dir_for_manifests(self.steam_path / "steamapps")
            
        data = VdfParser.load_text(str(library_vdf_path))
        
        # Structure is typically: "libraryfolders" { "0" { "path" "..." "apps" { "id" "size" ... } } ... }
        root = data.get("libraryfolders", {})
        
        for key, lib_data in root.items():
            if not isinstance(lib_data, dict):
                continue
                
            path_str = lib_data.get("path")
            if not path_str:
                continue
                
            lib_path = Path(path_str)
            steamapps = lib_path / "steamapps"
            
            # Scan manifests in this library
            games.extend(self._scan_dir_for_manifests(steamapps))
            
        return games

    def _scan_dir_for_manifests(self, steamapps_dir: Path) -> List[DetectedGame]:
        results = []
        if not steamapps_dir.exists():
            return results
            
        for file in steamapps_dir.glob("appmanifest_*.acf"):
            try:
                data = VdfParser.load_text(str(file))
                app_state = data.get("AppState", {})
                
                app_id = app_state.get("appid")
                name = app_state.get("name")
                install_dir = app_state.get("installdir")
                
                if app_id and name:
                    full_install_path = steamapps_dir / "common" / install_dir if install_dir else None
                    results.append(DetectedGame(
                        app_id=str(app_id),
                        name=name,
                        is_steam=True,
                        install_path=full_install_path,
                        real_id=str(app_id)
                    ))
            except Exception as e:
                logger.warning(f"Failed to parse manifest {file}: {e}")
                
        return results

    def get_non_steam_games(self) -> List[DetectedGame]:
        """
        Scans userdata folders for shortcuts.vdf.
        """
        games = []
        if not self.steam_path:
            return games
            
        userdata = self.steam_path / "userdata"
        if not userdata.exists():
            return games
            
        for user_dir in userdata.iterdir():
            if not user_dir.is_dir() or not user_dir.name.isdigit():
                continue
                
            shortcuts_path = user_dir / "config" / "shortcuts.vdf"
            if shortcuts_path.exists():
                games.extend(self._parse_shortcuts(shortcuts_path, user_dir.name))
                
        return games

    def _parse_shortcuts(self, vdf_path: Path, user_id: str) -> List[DetectedGame]:
        results = []
        try:
            data = VdfParser.load_binary(str(vdf_path))
            # Format: 'shortcuts' { '0' { 'appid' ... 'AppName' ... } }
            
            shortcuts = data.get("shortcuts", {})
            for key, entry in shortcuts.items():
                if not isinstance(entry, dict):
                    continue
                    
                app_name = entry.get("AppName") or entry.get("appname")
                exe_path = entry.get("Exe") or entry.get("exe")
                
                # Try to get AppID. 
                # In parsed binary VDF implementation, keys might be case-sensitive depending on how I wrote it.
                # My VDF parser preserves exact keys. shortcuts.vdf usually uses Title Case "AppName", "Exe".
                # But let's be safe.
                
                if app_name:
                    # User Instruction: Generate AppID exactly like Steam using Exe and AppName.
                    # Ignore stored AppID to ensure correctness.
                    
                    grid_id = self._calculate_grid_id(exe_path, app_name)
                    logger.debug(f"Computed Non-Steam ID: {grid_id} (Name: '{app_name}', Exe: '{exe_path}')")
                    
                    results.append(DetectedGame(
                        app_id=str(grid_id),
                        name=app_name,
                        is_steam=False,
                        install_path=Path(exe_path) if exe_path else None,
                        user_id=user_id
                    ))
                    
        except Exception as e:
            logger.error(f"Error parsing shortcuts {vdf_path}: {e}")
            
        return results

    @staticmethod
    def _calculate_grid_id(exe_path: str, app_name: str) -> str:
        """
        Calculates the Steam ID for a non-Steam game.
        User specified strict logic: crc32(exe+name) | 0x80000000
        This result is used for the filename in config/grid.
        """
        if not exe_path:
            exe_path = ""
        if not app_name:
            app_name = ""
            
        target = (exe_path + app_name).encode('utf-8')
        crc = zlib.crc32(target) & 0xffffffff # unsigned 32-bit
        
        # Legacy/Shortcut ID (unsigned 32-bit with high bit set)
        shortcut_id = crc | 0x80000000
        
        # User requested using this generated ID directly.
        # Note: In some contexts Steam uses the 64-bit ID (shortcut_id << 32 | 0x02000000).
        # But if the user insists this is the one for filenames, we use this.
        # Actually, many sources say filenames use the 32-bit ID.
        # Let's rely on the user instructions "Generate the AppID exactly like Steam ... return str(zlib.crc32...)"
        
        return str(shortcut_id)

