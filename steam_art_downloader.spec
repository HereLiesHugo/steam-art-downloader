# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller Spec File for Steam Art Downloader

This file configures the build process for creating a standalone executable.
It defines:
1. Analysis: Finding all dependencies and files.
2. PYZ: Creating the Python archive.
3. EXE: Building the executable wrapper.
4. COLLECT: Assembling the final directory (for folder-based distribution).

To build, run:
    pyinstaller steam_art_downloader.spec
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Create the Python Bytecode Archive
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create the Executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SteamArtDownloader', # Name of the generated .exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # Compress using UPX if available
    console=False,      # False = Windowed application (no terminal popup)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='resources/icon.ico', # Uncomment and provide path if you have an icon
)

# Collect all files into a directory (One-Folder Mode)
# This is generally faster to startup than One-File mode.
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SteamArtDownloader',
)
