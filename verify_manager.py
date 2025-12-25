import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

print("Verifying imports...")

try:
    from core.steam_vdf import VdfParser
    from core.game_scanner import GameScanner
    from core.image_cache import ImageCache
    from ui.manager_tab import ManagerTab
    from ui.main_window import MainWindow
    print("Imports successful.")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

print("Verifying Class Instantiation...")
try:
    # Test VDF Parser
    parser = VdfParser()
    
    # Test Cache
    cache = ImageCache()
    if os.path.exists("cache"):
        print(" - Cache dir created.")
        
    print("Class instantiation successful.")
except Exception as e:
    print(f"Instantiation failed: {e}")
    sys.exit(1)

print("VERIFICATION PASSED")
