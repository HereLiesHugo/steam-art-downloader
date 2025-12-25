import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from core.settings import SettingsManager
from core.game_scanner import GameScanner

def verify_scanning():
    print("--- Verifying Game Scanning Logic ---")
    
    # 1. Load Settings
    settings = SettingsManager()
    steam_path_setting = settings.steam_path
    print(f"Settings 'steam_path': '{steam_path_setting}'")
    
    # 2. Initialize Scanner
    # Logic from manager_tab.py
    steam_path = None
    if steam_path_setting:
         path = Path(steam_path_setting)
         if path.exists():
             steam_path = path
             print(f"Using override path: {steam_path}")
         else:
             print(f"Override path does not exist: {path}")
    
    scanner = GameScanner(steam_install_path=steam_path)
    print(f"Scanner initialized. Detected Steam Path: {scanner.steam_path}")
    
    if not scanner.steam_path or not scanner.steam_path.exists():
        print("ERROR: Steam path not found/detected.")
        return

    # 3. Scan Installed Games
    print("\nScanning Installed Games...")
    installed_games = scanner.get_installed_games()
    print(f"Found {len(installed_games)} installed games.")
    for game in installed_games[:5]:
        print(f" - {game.name} ({game.app_id})")
    if len(installed_games) > 5:
        print(f" ... and {len(installed_games) - 5} more.")

    # 4. Scan Non-Steam Games
    print("\nScanning Non-Steam Games...")
    non_steam_games = scanner.get_non_steam_games()
    print(f"Found {len(non_steam_games)} non-steam games.")
    for game in non_steam_games[:5]:
        print(f" - {game.name} ({game.app_id})")
        
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify_scanning()
