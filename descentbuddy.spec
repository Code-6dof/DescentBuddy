# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('data/notifications', 'data/notifications'),
        ('build/descentbuddy.png', '.'),
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

_drop_lib_prefixes = (
    'libQt6Quick',
    'libQt6Qml',
    'libQt6QmlModels',
    'libQt6QmlWorkerScript',
    'libQt6QuickTemplates2',
    'libQt6QuickWidgets',
    'libKF6BreezeIcons',
    'libkwin',
    'liblapack',
    'libSvtAv1Enc',
    'libx265',
    'libcodec2',
    'libplacebo',
    'libaom',
)
a.binaries = [
    b for b in a.binaries
    if not any(b[0].startswith(p) for p in _drop_lib_prefixes)
]

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
    strip=True,
    upx=False,
    name='descentbuddy',
)
