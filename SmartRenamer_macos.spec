# -*- mode: python ; coding: utf-8 -*-
"""macOS 用 PyInstaller 定義（onefile + .app バンドル・未使用 Qt モジュール除外）。"""

from __future__ import annotations

from pathlib import Path

try:
    _root = Path(SPEC).resolve().parent  # noqa: F821
except NameError:
    _root = Path.cwd()

block_cipher = None

_PYSIDE_EXCLUDES = [
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtBluetooth",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtGraphs",
    "PySide6.QtGraphsWidgets",
    "PySide6.QtHttpServer",
    "PySide6.QtLocation",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtNetworkAuth",
    "PySide6.QtNfc",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuickTest",
    "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialBus",
    "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtStateMachine",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtUiTools",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.QtWebView",
    "PySide6.QtXml",
    "PySide6.QtHelp",
    "PySide6.QtDesigner",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtDBus",
    "PySide6.QtConcurrent",
    "PySide6.QtCanvasPainter",
]

_MISC_EXCLUDES = [
    "tkinter",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "PIL.ImageTk",
    "IPython",
    "jupyter",
    "pytest",
    "doctest",
    "pydoc",
    "xmlrpc",
    "unittest",
]

_datas: list[tuple[str, str]] = []
_resources = _root / "src" / "app" / "resources"
if _resources.is_dir():
    _datas.append((str(_resources), "app/resources"))

_icns = _resources / "app_icon.icns"
_icon_mac = str(_icns) if _icns.is_file() else None

a = Analysis(
    [str(_root / "src" / "app" / "main.py")],
    pathex=[str(_root / "src")],
    binaries=[],
    datas=_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=_PYSIDE_EXCLUDES + _MISC_EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SmartRenamer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon_mac,
)

app = BUNDLE(
    exe,
    name="SmartRenamer.app",
    icon=_icon_mac,
    bundle_identifier="io.github.visualsequencerenamer.smartrenamer",
    info_plist={
        "CFBundleName": "SmartRenamer",
        "CFBundleDisplayName": "Visual Sequence Renamer",
        "NSHighResolutionCapable": True,
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
    },
)
