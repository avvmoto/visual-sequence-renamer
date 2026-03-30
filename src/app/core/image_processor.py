"""画像サムネイルとファイルアイコンの生成。"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from PySide6.QtCore import QFileInfo
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFileIconProvider

_icon_provider = QFileIconProvider()


def icon_for_path(
    path: Path,
    *,
    max_width: int = 120,
    max_height: int = 120,
) -> QIcon:
    """パスに応じたアイコンを返す。

    画像として開けた場合は Pillow でサムネイル（アスペクト比維持）を生成し、
    それ以外は OS / Qt が提供するファイルアイコンを返す。

    Args:
        path: ファイルパス。
        max_width: サムネイルの最大幅（ピクセル）。
        max_height: サムネイルの最大高さ（ピクセル）。

    Returns:
        表示用の QIcon。
    """
    resolved = path.expanduser()
    thumb = _try_thumbnail_icon(resolved, max_width=max_width, max_height=max_height)
    if thumb is not None:
        return thumb
    return _icon_provider.icon(QFileInfo(str(resolved)))


def _try_thumbnail_icon(path: Path, *, max_width: int, max_height: int) -> QIcon | None:
    """画像ファイルからサムネイル用 QIcon を生成する。失敗時は None。

    Args:
        path: ファイルパス。
        max_width: サムネイルの最大幅（ピクセル）。
        max_height: サムネイルの最大高さ（ピクセル）。

    Returns:
        生成に成功した QIcon。非画像・読み込み失敗時は None。
    """
    if not path.is_file():
        return None
    try:
        with Image.open(path) as img:
            img.load()
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            rgba = img.convert("RGBA")
            buf = BytesIO()
            rgba.save(buf, format="PNG")
            raw = buf.getvalue()
        pix = QPixmap()
        if not pix.loadFromData(raw):
            return None
        return QIcon(pix)
    except (OSError, UnidentifiedImageError, ValueError):
        return None
