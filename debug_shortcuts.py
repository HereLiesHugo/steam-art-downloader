import sys
import os
import zlib
from pathlib import Path
import json

# Add project root to path
sys.path.append(os.getcwd())

from core.steam_paths import SteamPathDetector
from core.steam_vdf import VdfParser

def debug_shortcuts():
    userdata = SteamPathDetector.get_userdata_path()
    if not userdata:
        print("No userdata found.")
        return

    for user_dir in userdata.iterdir():
        if not user_dir.is_dir() or not user_dir.name.isdigit():
            continue
            
        shortcuts_path = user_dir / "config" / "shortcuts.vdf"
        if shortcuts_path.exists():
            print(f"Parsing {shortcuts_path}")
            try:
                data = VdfParser.load_binary(str(shortcuts_path))
                # Dump 'shortcuts' key properly
                shortcuts = data.get("shortcuts", {})
                
                # Manual print to avoid JSON serialization errors if bytes
                for k, v in shortcuts.items():
                    print(f"[{k}]")
                    if isinstance(v, dict):
                        print(f"  AppName: {repr(v.get('AppName') or v.get('appname'))}")
                        print(f"  Exe: {repr(v.get('Exe') or v.get('exe'))}")
                        print(f"  StartDir: {repr(v.get('StartDir') or v.get('startdir'))}")
                        
                        raw_appid = v.get('appid')
                        if raw_appid is None: raw_appid = v.get('AppID')
                        print(f"  Raw AppID in file: {raw_appid} (Type: {type(raw_appid)})")
                        
                        # Test ID Calc
                        name = v.get('AppName') or v.get('appname') or ""
                        exe = v.get('Exe') or v.get('exe') or ""
                        
                        # Generate
                        target = (exe + name).encode('utf-8')
                        crc = zlib.crc32(target) & 0xffffffff
                        top_32 = crc | 0x80000000
                        full_64 = (top_32 << 32) | 0x02000000
                        print(f"  Calculated Grid ID: {str(full_64)}")
            except Exception as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    debug_shortcuts()
