"""アプリケーションアイコン（ウィンドウ・タスクバー・Dock）の解決。"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon


def _package_dir() -> Path:
    """`app` パッケージのルートディレクトリ。"""
    return Path(__file__).resolve().parent


def application_icon_png_path() -> Path | None:
    """`app_icon.png` のパス。開発時・PyInstaller 同梱の両方を試す。"""
    direct = _package_dir() / "resources" / "app_icon.png"
    if direct.is_file():
        return direct
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled = Path(sys._MEIPASS) / "app" / "resources" / "app_icon.png"
        if bundled.is_file():
            return bundled
    return None


def build_application_icon() -> QIcon:
    """起動時に `QApplication` / メインウィンドウへ設定する `QIcon` を返す。"""
    path = application_icon_png_path()
    if path is None:
        return QIcon()
    return QIcon(str(path))
