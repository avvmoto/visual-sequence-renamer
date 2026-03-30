"""メインウィンドウ（ツールバー・リスト・リネーム操作）。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.application_icon import build_application_icon
from app.core.image_processor import icon_for_path
from app.core.rename import pairs_from_serializable
from app.core.rename_thread import RenameThread, UndoRenameThread
from app.ui.widgets import (
    FileDropListWidget,
    FileListItemRoles,
    apply_file_item_metadata,
)

# QComboBox のソート項目インデックス（「追加順（カスタム）」は手動 D&D 後のみ選択）
IX_SORT_ADD_ORDER = 0
IX_SORT_NAME = 1
IX_SORT_CREATED = 2
IX_SORT_MODIFIED = 3
IX_SORT_CUSTOM = 4


class MainWindow(QMainWindow):
    """メインウィンドウ。"""

    def __init__(self) -> None:
        """ウィンドウと子ウィジェットを構築する。"""
        super().__init__()
        self.setWindowTitle("ならべて連番リネーマー — Visual Sequence Renamer")
        self.resize(800, 520)
        _win_icon = build_application_icon()
        if not _win_icon.isNull():
            self.setWindowIcon(_win_icon)

        self._allowed_root: Path | None = None
        self._undo_pairs: list[tuple[Path, Path]] | None = None
        self._worker_thread: RenameThread | UndoRenameThread | None = None
        self._suppress_undo_invalidate = False
        self._suppress_folder_reset_on_empty = False
        self._sort_descending = False

        toolbar = QToolBar("操作")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        clear_btn = QPushButton("クリア")
        clear_btn.setToolTip("リストを空にします")
        clear_btn.clicked.connect(self._on_toolbar_clear)
        toolbar.addWidget(clear_btn)

        toolbar.addSeparator()

        self._sort_combo = QComboBox()
        self._sort_combo.addItems(
            [
                "追加順",
                "ファイル名",
                "作成日時",
                "更新日時",
                "追加順（カスタム）",
            ]
        )
        self._sort_combo.setCurrentIndex(IX_SORT_ADD_ORDER)
        self._sort_combo.setToolTip("リストの並び基準（ファイルは移動しません）")
        self._sort_combo.currentIndexChanged.connect(self._on_sort_field_changed)
        toolbar.addWidget(self._sort_combo)

        self._order_btn = QPushButton("↑")
        self._order_btn.setFixedWidth(36)
        self._order_btn.setToolTip("昇順（古い順・小さい順）")
        self._order_btn.clicked.connect(self._on_toggle_sort_order)
        toolbar.addWidget(self._order_btn)

        self._sync_order_button_ui()

        central = QWidget()
        layout = QVBoxLayout(central)

        self._list = FileDropListWidget()
        self._list.files_dropped.connect(self._on_files_dropped)
        self._list.order_manually_changed.connect(self._on_list_manually_reordered)
        self._list.model().rowsRemoved.connect(self._on_list_rows_removed)

        self._strip_index_prefix_cb = QCheckBox(
            "先頭の「001_」形式（数字3桁以上＋_）を除いてから連番を付け直す"
        )
        self._strip_index_prefix_cb.setChecked(True)
        self._strip_index_prefix_cb.setToolTip(
            "オンにすると、同じフォルダで何度もリネームしても "
            "001_002_… のように連番が重なりにくくなります。"
        )

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
        layout.addWidget(self._strip_index_prefix_cb)
        layout.addLayout(btn_row)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

        self._update_order_button_enabled()

    def _sync_order_button_ui(self) -> None:
        """昇順/降順ボタンの表示を内部フラグに合わせる。"""
        if self._sort_descending:
            self._order_btn.setText("↓")
            self._order_btn.setToolTip("降順（新しい順・大きい順）— クリックで昇順に")
        else:
            self._order_btn.setText("↑")
            self._order_btn.setToolTip("昇順（古い順・小さい順）— クリックで降順に")

    def _update_order_button_enabled(self) -> None:
        """カスタム順のときは昇降順トグルを無効化する。"""
        custom = self._sort_combo.currentIndex() == IX_SORT_CUSTOM
        self._order_btn.setEnabled(not custom)

    def _on_toggle_sort_order(self) -> None:
        """昇順・降順を切り替え、再ソートする。"""
        self._sort_descending = not self._sort_descending
        self._sync_order_button_ui()
        if self._sort_combo.currentIndex() != IX_SORT_CUSTOM:
            self._apply_sort_from_ui()

    def _on_sort_field_changed(self, _index: int) -> None:
        """ソート基準変更時に即反映する。"""
        self._update_order_button_enabled()
        self._apply_sort_from_ui()

    def _on_list_manually_reordered(self) -> None:
        """リスト内ドラッグ後は「追加順（カスタム）」に切り替える。"""
        self._sort_combo.blockSignals(True)
        try:
            self._sort_combo.setCurrentIndex(IX_SORT_CUSTOM)
        finally:
            self._sort_combo.blockSignals(False)
        self._update_order_button_enabled()

    def _on_toolbar_clear(self) -> None:
        """リストと追加順カウンタをリセットする。"""
        self._sort_combo.blockSignals(True)
        try:
            self._sort_combo.setCurrentIndex(IX_SORT_ADD_ORDER)
        finally:
            self._sort_combo.blockSignals(False)
        self._sort_descending = False
        self._sync_order_button_ui()
        self._list.reset_insert_order_counter()
        self._list.clear()
        self._update_order_button_enabled()

    def _apply_sort_from_ui(self) -> None:
        """現在のソート基準・昇降順で QListWidget の行だけ並べ替える。"""
        ix = self._sort_combo.currentIndex()
        if ix == IX_SORT_CUSTOM:
            return
        n = self._list.count()
        if n <= 1:
            return

        pairs: list[tuple[int, QListWidgetItem]] = []
        for i in range(n):
            it = self._list.item(i)
            if it is not None:
                pairs.append((i, it))

        def sort_key(pair: tuple[int, QListWidgetItem]) -> tuple[object, int]:
            idx, it = pair
            if ix == IX_SORT_ADD_ORDER:
                v = it.data(FileListItemRoles.INSERT_ORDER)
                if isinstance(v, (int, float)):
                    o = float(v)
                else:
                    o = float("inf")
                return (o, idx)
            if ix == IX_SORT_NAME:
                return (it.text().lower(), idx)
            if ix == IX_SORT_CREATED:
                v = it.data(FileListItemRoles.CREATED_TS)
                t = float(v) if v is not None else 0.0
                return (t, idx)
            if ix == IX_SORT_MODIFIED:
                v = it.data(FileListItemRoles.MODIFIED_TS)
                t = float(v) if v is not None else 0.0
                return (t, idx)
            return (float(idx), idx)

        ordered = [p[1] for p in sorted(pairs, key=sort_key, reverse=self._sort_descending)]
        if ordered == [p[1] for p in pairs]:
            return

        self._suppress_folder_reset_on_empty = True
        self._list.set_suppress_manual_order_notification(True)
        try:
            for _ in range(n):
                self._list.takeItem(0)
            for it in ordered:
                self._list.addItem(it)
        finally:
            self._suppress_folder_reset_on_empty = False
            self._list.set_suppress_manual_order_notification(False)

    def _apply_sort_if_not_custom(self) -> None:
        """カスタム順以外のときだけソートを適用する（追加直後用）。"""
        if self._sort_combo.currentIndex() == IX_SORT_CUSTOM:
            return
        self._apply_sort_from_ui()

    def _clear_undo(self) -> None:
        """元に戻し情報を破棄する。"""
        self._undo_pairs = None
        self._undo_btn.setEnabled(False)

    def _on_list_rows_removed(self) -> None:
        """リストが空になったら登録フォルダをリセットする。編集時は元に戻しを無効化。"""
        if self._suppress_undo_invalidate or self._suppress_folder_reset_on_empty:
            return
        if self._list.count() == 0:
            self._allowed_root = None
            self._list.reset_insert_order_counter()
        self._clear_undo()

    def _list_paths_in_order(self) -> list[Path]:
        """リスト表示順のソースファイルパスを返す。"""
        paths: list[Path] = []
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item is None:
                continue
            raw = item.data(FileListItemRoles.PATH)
            if isinstance(raw, str) and raw:
                paths.append(Path(raw))
        return paths

    def _set_busy(self, busy: bool) -> None:
        """バックグラウンド処理中の UI 状態。"""
        self._list.setEnabled(not busy)
        self._strip_index_prefix_cb.setEnabled(not busy)
        self._rename_btn.setEnabled(not busy)
        self._undo_btn.setEnabled(not busy and self._undo_pairs is not None)
        for tb in self.findChildren(QToolBar):
            tb.setEnabled(not busy)

    def _registered_path_keys(self) -> set[str]:
        """リストに既に登録されているファイルパス（``resolve()`` 済み文字列）の集合。"""
        keys: set[str] = set()
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item is None:
                continue
            raw = item.data(FileListItemRoles.PATH)
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
        item.setData(FileListItemRoles.PATH, key)
        item.setToolTip(path.name)
        order = self._list.next_insert_order()
        apply_file_item_metadata(item, resolved, order)

        if insert_at is None:
            self._list.addItem(item)
            self._apply_sort_if_not_custom()
            return self._list.count()
        r = max(0, min(insert_at, self._list.count()))
        self._list.insertItem(r, item)
        self._apply_sort_if_not_custom()
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

        thread = RenameThread(
            sources,
            self,
            strip_leading_index_prefix=self._strip_index_prefix_cb.isChecked(),
        )
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
                ur = item.data(FileListItemRoles.PATH)
                if not isinstance(ur, str):
                    continue
                old_p = Path(ur).resolve()
                new_p = old_to_new.get(old_p)
                if new_p is None:
                    continue
                item.setData(FileListItemRoles.PATH, str(new_p))
                item.setText(new_p.name)
                item.setToolTip(new_p.name)
                item.setIcon(icon_for_path(new_p))
                order_raw = item.data(FileListItemRoles.INSERT_ORDER)
                if isinstance(order_raw, int):
                    o = order_raw
                else:
                    o = self._list.next_insert_order()
                    item.setData(FileListItemRoles.INSERT_ORDER, o)
                apply_file_item_metadata(item, new_p, o)
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
                ur = item.data(FileListItemRoles.PATH)
                if not isinstance(ur, str):
                    continue
                cur = Path(ur).resolve()
                orig = new_to_old.get(cur)
                if orig is None:
                    continue
                item.setData(FileListItemRoles.PATH, str(orig))
                item.setText(orig.name)
                item.setToolTip(orig.name)
                item.setIcon(icon_for_path(orig))
                order_raw = item.data(FileListItemRoles.INSERT_ORDER)
                if isinstance(order_raw, int):
                    o = order_raw
                else:
                    o = self._list.next_insert_order()
                    item.setData(FileListItemRoles.INSERT_ORDER, o)
                apply_file_item_metadata(item, orig, o)
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