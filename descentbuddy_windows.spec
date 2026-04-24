# -*- mode: python ; coding: utf-8 -*-
# Windows build spec — produces a single-folder distribution with a .exe launcher.
# Run from the project root on a Windows machine:
#   pyinstaller descentbuddy_windows.spec --noconfirm --clean

import glob
import sys
from pathlib import Path

block_cipher = None

# Collect ICU DLLs that Qt6Core requires. PyInstaller's PyQt6 hook does not
# reliably pick these up on all build hosts, so we find and include them
# explicitly. They live next to Qt6Core.dll in the Qt6 bin directory.
_qt6_bin = Path(sys.prefix) / 'Lib' / 'site-packages' / 'PyQt6' / 'Qt6' / 'bin'
_icu_dlls = [(str(p), 'PyQt6/Qt6/bin') for p in _qt6_bin.glob('icu*.dll')]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=_icu_dlls,
    datas=[
        ('data/notifications', 'data/notifications'),
        ('build/descentbuddy.png', '.'),
    ],
    hiddenimports=[
        'core.api_keys',
        'PyQt6',
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtMultimedia',
        'PyQt6.QtNetwork',
    ],
    hookspath=[],
    hooksconfig={
        'PyQt6': {
            'plugins': [
                'platforms',
                'imageformats',
                'styles',
                'multimedia',
                'tls',
            ],
        }
    },
    runtime_hooks=[],
    excludes=[
        'PyQt6.QtBluetooth',
        'PyQt6.QtLocation',
        'PyQt6.QtPositioning',
        'PyQt6.QtSensors',
        'PyQt6.QtSql',
        'PyQt6.QtTest',
        'PyQt6.Qt3DCore',
        'PyQt6.Qt3DRender',
        'PyQt6.QtCharts',
        'PyQt6.QtDataVisualization',
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DescentBuddy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='build/descentbuddy.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='DescentBuddy',
)
