# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('data/notifications', 'data/notifications'),
    ],
    hiddenimports=[
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
                'xcbglintegrations',
                'imageformats',
                'styles',
                'platforminputcontexts',
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
    name='descentbuddy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
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
    name='descentbuddy',
)
