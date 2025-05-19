# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(SPECPATH)
SRC_DIR = ROOT_DIR / 'src'
DATA_DIR = ROOT_DIR / 'data'
ASSETS_DIR = ROOT_DIR / 'assets'

print(f"SPECPATH: {SPECPATH}")
print(f"ROOT_DIR: {ROOT_DIR}")
print(f"SRC_DIR: {SRC_DIR}")
print(f"Main script path: {SRC_DIR / 'main.py'}")

block_cipher = None

a = Analysis(
    [str(SRC_DIR / 'main.py')],
    pathex=[str(ROOT_DIR), str(SRC_DIR)],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'src',
        'src.ui',
        'src.data',
        'src.utils',
        'src.core',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='每日单词',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ASSETS_DIR / 'logo.ico') if (ASSETS_DIR / 'logo.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='每日单词',
) 