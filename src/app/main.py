"""アプリケーションのエントリポイント。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.core.image_processor import icon_for_path
from app.core.rename import pairs_from_serializable
from app.core.rename_thread import RenameThread, UndoRenameThread
from app.ui.widgets import FileDropListWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """メインウィンドウ。"""

    def __init__(self) -> None:
        """ウィンドウと子ウィジェットを構築する。"""
        super().__init__()
        self.setWindowTitle("Smart File Renamer")
        self.resize(800, 520)

        self._allowed_root: Path | None = None
        self._undo_pairs: list[tuple[Path, Path]] | None = None
        self._worker_thread: RenameThread | UndoRenameThread | None = None
        self._suppress_undo_invalidate = False

        central = QWidget()
        layout = QVBoxLayout(central)

        self._list = FileDropListWidget()
        self._list.files_dropped.connect(self._on_files_dropped)
        self._list.model().rowsRemoved.connect(self._on_list_rows_removed)

        self._folder_label = QLabel()
        self._folder_label.setWordWrap(True)
        self._sync_folder_label()

        btn_row = QHBoxLayout()
        self._rename_btn = QPushButton("リネーム実行")
        self._rename_btn.clicked.connect(self._on_rename_clicked)
        self._undo_btn = QPushButton("元に戻す")
        self._undo_btn.setEnabled(False)
        self._undo_btn.clicked.connect(self._on_undo_clicked)
        btn_row.addWidget(self._rename_btn)
        btn_row.addWidget(self._undo_btn)
        btn_row.addStretch(1)

        layout.addWidget(self._list, stretch=1)
        layout.addWidget(self._folder_label)
        layout.addLayout(btn_row)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

    def _sync_folder_label(self) -> None:
        """登録フォルダの説明を更新する。"""
        if self._allowed_root is None:
            self._folder_label.setText(
                "登録フォルダ: 未設定（先頭ファイルのフォルダに固定。他フォルダは追加不可）"
            )
        else:
            self._folder_label.setText(f"登録フォルダ: {self._allowed_root}")

    def _clear_undo(self) -> None:
        """元に戻し情報を破棄する。"""
        self._undo_pairs = None
        self._undo_btn.setEnabled(False)

    def _on_list_rows_removed(self) -> None:
        """リストが空になったら登録フォルダをリセットする。編集時は元に戻しを無効化。"""
        if self._suppress_undo_invalidate:
            return
        if self._list.count() == 0:
            self._allowed_root = None
            self._sync_folder_label()
        self._clear_undo()

    def _list_paths_in_order(self) -> list[Path]:
        """リスト表示順のソースファイルパスを返す。"""
        paths: list[Path] = []
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item is None:
                continue
            raw = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(raw, str) and raw:
                paths.append(Path(raw))
        return paths

    def _set_busy(self, busy: bool) -> None:
        """バックグラウンド処理中の UI 状態。"""
        self._list.setEnabled(not busy)
        self._rename_btn.setEnabled(not busy)
        self._undo_btn.setEnabled(not busy and self._undo_pairs is not None)

    def _registered_path_keys(self) -> set[str]:
        """リストに既に登録されているファイルパス（``resolve()`` 済み文字列）の集合。"""
        keys: set[str] = set()
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item is None:
                continue
            raw = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(raw, str) and raw:
                keys.add(raw)
        return keys

    def _on_files_dropped(self, paths: list[Path], insert_at: int) -> None:
        """ドロップされた各パスをリストに追加する。"""
        registered = self._registered_path_keys()
        row = max(0, min(insert_at, self._list.count()))
        skipped: list[str] = []
        for path in paths:
            if path.is_file():
                parent = path.resolve().parent
                if self._allowed_root is not None and parent != self._allowed_root:
                    skipped.append(path.name)
                    continue
            row = self._add_file_item(path, registered, row)
        if skipped:
            names = "\n".join(skipped[:30])
            extra = f"\n… 他 {len(skipped) - 30} 件" if len(skipped) > 30 else ""
            QMessageBox.warning(
                self,
                "登録できませんでした",
                "最初のファイルと異なるフォルダ内のためスキップしました:\n"
                f"{names}{extra}",
            )

    def _add_file_item(
        self,
        path: Path,
        registered: set[str] | None = None,
        insert_at: int | None = None,
    ) -> int:
        """サムネイル付きでリストアイテムを1件追加する。"""
        if not path.is_file():
            self.statusBar().showMessage(f"ファイルではありません: {path.name}", 5000)
            return insert_at if insert_at is not None else self._list.count()
        resolved = path.resolve()
        parent = resolved.parent
        if self._allowed_root is None:
            self._allowed_root = parent
            self._sync_folder_label()
        elif parent != self._allowed_root:
            self.statusBar().showMessage(
                f"登録フォルダ外のため追加できません: {path.name}",
                8000,
            )
            return insert_at if insert_at is not None else self._list.count()

        key = str(resolved)
        active = registered if registered is not None else self._registered_path_keys()
        if key in active:
            return insert_at if insert_at is not None else self._list.count()
        if self._undo_pairs is not None:
            self._clear_undo()
        if registered is not None:
            registered.add(key)

        icon = icon_for_path(path)
        item = QListWidgetItem(icon, path.name)
        item.setData(Qt.ItemDataRole.UserRole, key)
        item.setToolTip(path.name)
        if insert_at is None:
            self._list.addItem(item)
            return self._list.count()
        r = max(0, min(insert_at, self._list.count()))
        self._list.insertItem(r, item)
        return r + 1

    def _worker_failed(self, message: str) -> None:
        """ワーカー失敗メッセージ。"""
        QMessageBox.critical(self, "エラー", message)

    def _on_rename_clicked(self) -> None:
        """同一フォルダ内で連番リネームする。"""
        paths = self._list_paths_in_order()
        if not paths:
            QMessageBox.warning(self, "リネーム", "ファイルが追加されていません。")
            return
        if self._worker_thread is not None and self._worker_thread.isRunning():
            return

        sources = [p.resolve() for p in paths]
        self._set_busy(True)
        self.statusBar().showMessage("リネーム処理中…", 0)

        thread = RenameThread(sources, self)
        self._worker_thread = thread
        thread.finished_ok.connect(self._on_rename_finished_ok)
        thread.failed.connect(self._worker_failed)
        thread.finished.connect(self._worker_finished)
        thread.start()

    def _on_rename_finished_ok(self, raw: object) -> None:
        """リネーム成功: リストのパス表示を更新し、元に戻しを有効にする。"""
        pairs = pairs_from_serializable(raw)
        if not pairs:
            QMessageBox.warning(self, "リネーム", "結果が空です。")
            return
        self._undo_pairs = pairs
        old_to_new = {b.resolve(): a.resolve() for a, b in pairs}
        self._suppress_undo_invalidate = True
        try:
            for i in range(self._list.count()):
                item = self._list.item(i)
                if item is None:
                    continue
                ur = item.data(Qt.ItemDataRole.UserRole)
                if not isinstance(ur, str):
                    continue
                old_p = Path(ur).resolve()
                new_p = old_to_new.get(old_p)
                if new_p is None:
                    continue
                item.setData(Qt.ItemDataRole.UserRole, str(new_p))
                item.setText(new_p.name)
                item.setToolTip(new_p.name)
                item.setIcon(icon_for_path(new_p))
        finally:
            self._suppress_undo_invalidate = False

        self._undo_btn.setEnabled(True)
        folder = pairs[0][0].parent.resolve()
        QMessageBox.information(
            self,
            "完了",
            f"フォルダ内でリネームしました。\n\n{folder}",
        )
        url = QUrl.fromLocalFile(str(folder))
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(
                self,
                "フォルダを開けませんでした",
                f"次のフォルダを手動で開いてください:\n{folder}",
            )

    def _on_undo_clicked(self) -> None:
        """直前のリネームを元に戻す。"""
        if self._undo_pairs is None:
            return
        if self._worker_thread is not None and self._worker_thread.isRunning():
            return

        pairs = list(self._undo_pairs)
        self._set_busy(True)
        self.statusBar().showMessage("元に戻しています…", 0)

        thread = UndoRenameThread(pairs, self)
        self._worker_thread = thread
        thread.finished_ok.connect(self._on_undo_finished_ok)
        thread.failed.connect(self._worker_failed)
        thread.finished.connect(self._worker_finished)
        thread.start()

    def _on_undo_finished_ok(self) -> None:
        """元に戻し成功: リストのパスを更新する。"""
        if self._undo_pairs is None:
            return
        new_to_old = {a.resolve(): b.resolve() for a, b in self._undo_pairs}
        self._suppress_undo_invalidate = True
        try:
            for i in range(self._list.count()):
                item = self._list.item(i)
                if item is None:
                    continue
                ur = item.data(Qt.ItemDataRole.UserRole)
                if not isinstance(ur, str):
                    continue
                cur = Path(ur).resolve()
                orig = new_to_old.get(cur)
                if orig is None:
                    continue
                item.setData(Qt.ItemDataRole.UserRole, str(orig))
                item.setText(orig.name)
                item.setToolTip(orig.name)
                item.setIcon(icon_for_path(orig))
        finally:
            self._suppress_undo_invalidate = False

        self._clear_undo()
        QMessageBox.information(self, "完了", "元のファイル名に戻しました。")

    def _worker_finished(self) -> None:
        """ワーカースレッド終了後の後片付け。"""
        self.statusBar().clearMessage()
        self._set_busy(False)
        sender = self.sender()
        if sender is self._worker_thread:
            self._worker_thread = None
        if isinstance(sender, QThread):
            sender.deleteLater()


def main() -> None:
    """アプリを起動する。"""
    logging.basicConfig(level=logging.INFO)
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
