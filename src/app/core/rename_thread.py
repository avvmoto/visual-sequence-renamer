"""リネーム / 元に戻しをバックグラウンドで実行するスレッド。"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from app.core.rename import (
    pairs_to_serializable,
    perform_rename_in_place,
    perform_undo_rename,
)

logger = logging.getLogger(__name__)


class RenameThread(QThread):
    """リスト順に同一フォルダ内で連番リネームする。"""

    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        sources: list[Path],
        parent: QObject | None = None,
    ) -> None:
        """スレッドを初期化する。

        Args:
            sources: リネーム対象（表示順・解決済み想定）。
            parent: 親オブジェクト。
        """
        super().__init__(parent)
        self._sources = list(sources)

    def run(self) -> None:
        """リネームし、元に戻し用ペアをシグナルで渡す。"""
        try:
            undo_pairs = perform_rename_in_place(self._sources)
        except OSError as exc:
            self.failed.emit(str(exc))
        except Exception:
            logger.exception("リネーム処理中に予期しないエラー")
            self.failed.emit("予期しないエラーが発生しました。ログを確認してください。")
        else:
            self.finished_ok.emit(pairs_to_serializable(undo_pairs))


class UndoRenameThread(QThread):
    """直前の連番リネームを元に戻す。"""

    finished_ok = Signal()
    failed = Signal(str)

    def __init__(
        self,
        pairs: list[tuple[Path, Path]],
        parent: QObject | None = None,
    ) -> None:
        """スレッドを初期化する。

        Args:
            pairs: ``(リネーム後, リネーム前)`` のリスト。
            parent: 親オブジェクト。
        """
        super().__init__(parent)
        self._pairs = list(pairs)

    def run(self) -> None:
        """元に戻しを実行する。"""
        try:
            perform_undo_rename(self._pairs)
        except OSError as exc:
            self.failed.emit(str(exc))
        except Exception:
            logger.exception("元に戻す処理中に予期しないエラー")
            self.failed.emit("予期しないエラーが発生しました。ログを確認してください。")
        else:
            self.finished_ok.emit()
