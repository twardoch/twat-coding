# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/twat_coding/pystubnik/cli.py'],
    pathex=[],
    binaries=[],
    datas=[('src/twat_coding', 'twat_coding')],
    hiddenimports=['twat_coding.pystubnik.cli', 'twat_coding.pystubnik.config', 'twat_coding.pystubnik.processors.stub_generation', 'twat_coding.pystubnik.backends.ast_backend', 'twat_coding.pystubnik.backends.mypy_backend', 'twat_coding.pystubnik.core.config', 'twat_coding.pystubnik.core.conversion', 'twat_coding.pystubnik.processors.stub_generation', 'twat_coding.pystubnik.utils.ast_utils', 'twat_coding.pystubnik.types.docstring', 'twat_coding.pystubnik.types.type_system'],
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
    name='twat-coding-Linux-X64',
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
)
