# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Julian\\Desktop\\dev\\projects\\IOS_Compiler\\compiler.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['github', 'requests', 'colorama', 'termcolor', 'PyGithub'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='compiler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\Julian\\Desktop\\dev\\projects\\IOS_Compiler\\assets\\icons\\ico.ico'],
)
