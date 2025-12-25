import sys
import os
import zlib
from pathlib import Path
import struct

# Add project root to path
sys.path.append(os.getcwd())

from core.steam_paths import SteamPathDetector
from core.steam_vdf import VdfParser

def calculate_grid_id(exe_path, app_name):
    if not exe_path: exe_path = ""
    if not app_name: app_name = ""
    target = (exe_path + app_name).encode('utf-8')
    crc = zlib.crc32(target) & 0xffffffff
    top_32 = crc | 0x80000000
    full_64 = (top_32 << 32) | 0x02000000
    return str(full_64)

def inspect():
    print("--- Inspecting Steam Grid Configuration ---")
    userdata = SteamPathDetector.get_userdata_path()
    if not userdata:
        print("No userdata found.")
        return

    print(f"Userdata Root: {userdata}")
    
    for user_dir in userdata.iterdir():
        if not user_dir.is_dir() or not user_dir.name.isdigit():
            continue
            
        print(f"\nUser: {user_dir.name}")
        grid_dir = user_dir / "config" / "grid"
        shortcuts_path = user_dir / "config" / "shortcuts.vdf"
        
        # List actual files
        if grid_dir.exists():
            print(f"  Grid Dir: {grid_dir}")
            files = list(grid_dir.glob("*"))
            print(f"  Found {len(files)} files in grid dir.")
            for f in files[:10]:
                print(f"    - {f.name}")
            if len(files) > 10:
                print("    ... (more)")
        else:
            print("  Grid Dir: Not Found")
            
        # Parse Shortcuts and Calc IDs
        if shortcuts_path.exists():
            print(f"  Shortcuts found: {shortcuts_path}")
            try:
                data = VdfParser.load_binary(str(shortcuts_path))
                shortcuts = data.get("shortcuts", {})
                for key, entry in shortcuts.items():
                    if isinstance(entry, dict):
                        name = entry.get("AppName") or entry.get("appname")
                        exe = entry.get("Exe") or entry.get("exe")
                        calc_id = calculate_grid_id(exe, name)
                        print(f"    Shortcut: '{name}'")
                        print(f"      Exe: '{exe}'")
                        print(f"      Calculated ID: {calc_id}")
                        
                        # check if this ID exists in files
                        matches = [f.name for f in (list(grid_dir.glob(f"{calc_id}*")) if grid_dir.exists() else [])]
                        if matches:
                            print(f"      -> MATCH FOUND in Grid: {matches}")
                        else:
                            print(f"      -> No matching files found.")
            except Exception as e:
                print(f"  Error parsing shortcuts: {e}")

if __name__ == "__main__":
    inspect()
