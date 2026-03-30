"""カスタム Qt ウィジェット。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QMimeData, QModelIndex, QPersistentModelIndex, QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QIcon,
    QPainter,
    QPalette,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QListView,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)


class FileListItemRoles:
    """``QListWidgetItem`` に保存するカスタム ``DataRole``。"""

    PATH = int(Qt.ItemDataRole.UserRole)
    CREATED_TS = int(Qt.ItemDataRole.UserRole) + 1
    MODIFIED_TS = int(Qt.ItemDataRole.UserRole) + 2
    INSERT_ORDER = int(Qt.ItemDataRole.UserRole) + 3


def file_stat_timestamps(path: Path) -> tuple[float, float]:
    """ファイルの作成・更新時刻（エポック秒）を返す。

    作成時刻は OS により取得できない場合があり、そのときは更新時刻にフォールバックする。

    Args:
        path: ファイルパス（存在する想定）。

    Returns:
        ``(作成時刻, 更新時刻)`` のタプル。
    """
    st = path.stat()
    mtime = float(st.st_mtime)
    if sys.platform == "darwin":
        birth = getattr(st, "st_birthtime", None)
        ctime = float(birth) if birth is not None else float(st.st_ctime)
    elif os.name == "nt":
        ctime = float(st.st_ctime)
    else:
        birth = getattr(st, "st_birthtime", None)
        ctime = float(birth) if birth is not None else mtime
    return ctime, mtime


def apply_file_item_metadata(item: QListWidgetItem, path: Path, insert_order: int) -> None:
    """パスに応じたタイムスタンプと追加順をアイテムに格納する。

    Args:
        item: リストアイテム。
        path: 参照するファイルパス。
        insert_order: 追加順の連番。
    """
    ctime, mtime = file_stat_timestamps(path)
    item.setData(FileListItemRoles.CREATED_TS, ctime)
    item.setData(FileListItemRoles.MODIFIED_TS, mtime)
    item.setData(FileListItemRoles.INSERT_ORDER, insert_order)


def _accept_file_url_drop(event: QDragEnterEvent | QDragMoveEvent | QDropEvent) -> None:
    """Finder 等からのファイル URL ドロップを受け入れる。

    proposed が Ignore の場合でも Copy で受け付ける（macOS での取りこぼし防止）。

    Args:
        event: ドラッグ / ドロップイベント。
    """
    if event.proposedAction() == Qt.DropAction.IgnoreAction:
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
    else:
        event.acceptProposedAction()


# QListWidget 内部の並べ替えドラッグで使われる MIME（外部ファイルの URL とは別）。
_QT_ITEM_MODEL_MIME = "application/x-qabstractitemmodeldatalist"


def _drag_originates_from_this_widget(
    widget: QWidget,
    event: QDragEnterEvent | QDragMoveEvent | QDropEvent,
) -> bool:
    """ドラッグ元がこのリスト（またはその子ウィジェット）かどうか。

    QListWidget 内部の並べ替えでは MIME 形式が環境で異なることがあるため、
    ``event.source()`` でも内部ドラッグと判定する。

    Args:
        widget: この ``QListWidget`` インスタンス。
        event: ドラッグ / ドロップイベント。

    Returns:
        このリスト起点のドラッグなら True。外部（Finder 等）は False。
    """
    src = event.source()
    if src is None:
        return False
    if src is widget:
        return True
    return isinstance(src, QWidget) and widget.isAncestorOf(src)


class ThumbnailBelowFilenameDelegate(QStyledItemDelegate):
    """サムネイルを上・ファイル名を下に描画し、名前はサムネイル幅で右省略する。"""

    def __init__(self, list_widget: QListWidget) -> None:
        """デリゲートを初期化する。

        Args:
            list_widget: 親の ``QListWidget``（アイコンサイズの参照に使う）。
        """
        super().__init__(list_widget)
        self._list = list_widget

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        """選択背景のあと、アイコンと省略済みテキストを描画する。

        Args:
            painter: ペインター。
            option: スタイルオプション。
            index: モデルインデックス。
        """
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        widget = opt.widget
        style = widget.style() if widget is not None else QApplication.style()

        opt.text = ""
        opt.icon = QIcon()
        style.drawPrimitive(
            QStyle.PrimitiveElement.PE_PanelItemViewItem,
            opt,
            painter,
            widget,
        )

        rect = option.rect
        icon_sz = self._list.iconSize()
        iw = icon_sz.width()
        ih = icon_sz.height()
        margin_top = 4
        gap_below_icon = 4

        icon_x = rect.left() + max(0, (rect.width() - iw) // 2)
        icon_y = rect.top() + margin_top

        dec = index.data(Qt.ItemDataRole.DecorationRole)
        pm = QPixmap()
        if isinstance(dec, QIcon):
            pm = dec.pixmap(icon_sz)
        elif isinstance(dec, QPixmap):
            pm = dec.scaled(
                icon_sz,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        if not pm.isNull():
            # アイコンをセル内で中央寄せ（縦横）
            px = icon_x + max(0, (iw - pm.width()) // 2)
            py = icon_y + max(0, (ih - pm.height()) // 2)
            painter.drawPixmap(px, py, pm)

        label = index.data(Qt.ItemDataRole.DisplayRole)
        if isinstance(label, str) and label:
            fm = opt.fontMetrics
            elided = fm.elidedText(label, Qt.TextElideMode.ElideRight, iw)
            text_y = icon_y + ih + gap_below_icon
            text_rect = QRect(icon_x, text_y, iw, fm.height())
            painter.setFont(opt.font)
            if option.state & QStyle.StateFlag.State_Selected:
                painter.setPen(opt.palette.color(QPalette.ColorRole.HighlightedText))
            else:
                painter.setPen(opt.palette.color(QPalette.ColorRole.Text))
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                elided,
            )

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QSize:
        """グリッドセルサイズに合わせる。

        Args:
            option: スタイルオプション。
            index: モデルインデックス。

        Returns:
            ``QListWidget`` に設定された ``gridSize``。
        """
        _ = option, index
        return self._list.gridSize()


def _mime_has_local_file_urls(mime: QMimeData) -> bool:
    """MIME データにローカルファイルを指す URL が含まれるか判定する。

    Args:
        mime: ドラッグ中の MIME データ。

    Returns:
        ローカルファイル URL が1件以上あれば True。
    """
    if not mime.hasUrls():
        return False
    return any(u.isLocalFile() for u in mime.urls())


class FileDropListWidget(QListWidget):
    """ファイルのドロップ受け付けと、リスト内ドラッグによる並べ替えが可能なリストウィジェット。"""

    #: 第1引数: ローカルファイルパス一覧。第2引数: 挿入位置の行（0〜件数、件数は末尾相当）。
    files_dropped = Signal(list, int)
    #: リスト内ドラッグで並べが変わった直後（プログラムによる並べ替え中は送出しない）。
    order_manually_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """ウィジェットを初期化する。

        Args:
            parent: 親ウィジェット。省略時は None。
        """
        super().__init__(parent)
        self.setAcceptDrops(True)
        # ビューポートに setAcceptDrops(True) すると、ドロップが子ウィジェット側で処理され、
        # 本クラスの drag*/dropEvent が呼ばれず Finder からのドロップが無視されることがある。

        # IconMode では Qt の QListView 実装が別経路となり、InternalMove の並べ替えが
        # 効かない / 禁止カーソルになる既知の挙動がある（Qt フォーラム等）。
        # ListMode + 左→右フロー + 折り返しでサムネイルがグリッド状に並び、内部 D&D が安定する。
        self.setViewMode(QListView.ViewMode.ListMode)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setWrapping(True)
        self.setWordWrap(True)

        self.setGridSize(QSize(140, 160))
        self.setIconSize(QSize(120, 120))
        self.setSpacing(10)
        self.setUniformItemSizes(True)
        self.setWordWrap(False)
        self.setItemDelegate(ThumbnailBelowFilenameDelegate(self))

        # DragDrop にすると内部ドラッグ開始も確実。外部ファイルは dropEvent 側で URL のみ処理。
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragEnabled(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)
        self.setAutoScroll(True)

        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._insert_order_seq = 0
        self._suppress_manual_order_notification = False

    def set_suppress_manual_order_notification(self, suppress: bool) -> None:
        """``True`` の間は手動並べ替えシグナルを送出しない（ソート処理用）。

        Args:
            suppress: 抑制するなら True。
        """
        self._suppress_manual_order_notification = suppress

    def next_insert_order(self) -> int:
        """追加順ソート用の連番を返し、内部カウンタを進める。

        Returns:
            1 始まりの追加順番号。
        """
        self._insert_order_seq += 1
        return self._insert_order_seq

    def reset_insert_order_counter(self) -> None:
        """リストを空にしたあとなどに追加順カウンタをリセットする。"""
        self._insert_order_seq = 0

    def _insert_row_for_external_file_drop(self, event: QDropEvent) -> int:
        """ドロップ座標に応じた挿入行を返す（アイテム上はその行の直前に挿入）。

        空白部に落とした場合は末尾に追加（``count()``）。

        Args:
            event: 外部ファイルのドロップイベント。

        Returns:
            ``insertItem(row, ...)`` に渡す行インデックス。
        """
        pos = event.position().toPoint()
        viewport_pos = self.viewport().mapFrom(self, pos)
        idx = self.indexAt(viewport_pos)
        if idx.isValid():
            return int(idx.row())
        return self.count()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """外部からの URL ドラッグを受け入れ可能にし、それ以外は既定の処理に任せる。

        Args:
            event: ドラッグ Enter イベント。
        """
        mime = event.mimeData()
        if _drag_originates_from_this_widget(self, event) or mime.hasFormat(_QT_ITEM_MODEL_MIME):
            super().dragEnterEvent(event)
            return
        if _mime_has_local_file_urls(mime):
            _accept_file_url_drop(event)
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """ドラッグ中にローカルファイル URL であれば受け入れ可能とする。

        Args:
            event: ドラッグ Move イベント。
        """
        mime = event.mimeData()
        if _drag_originates_from_this_widget(self, event) or mime.hasFormat(_QT_ITEM_MODEL_MIME):
            super().dragMoveEvent(event)
            return
        if _mime_has_local_file_urls(mime):
            _accept_file_url_drop(event)
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """ローカルファイルがドロップされたらパスを通知し、内部移動は親に委譲する。

        リスト内ドラッグは ``super().dropEvent`` に任せ、QListWidget の行順（上から順の
        インデックス）がそのまま並べ替え後の順序になる。

        Args:
            event: ドロップイベント。
        """
        mime = event.mimeData()
        if _drag_originates_from_this_widget(self, event) or mime.hasFormat(_QT_ITEM_MODEL_MIME):
            super().dropEvent(event)
            if not self._suppress_manual_order_notification:
                self.order_manually_changed.emit()
            return
        if _mime_has_local_file_urls(mime):
            paths: list[Path] = []
            for q in mime.urls():
                if q.isLocalFile():
                    paths.append(Path(q.toLocalFile()))
            if paths:
                insert_row = self._insert_row_for_external_file_drop(event)
                self.files_dropped.emit(paths, insert_row)
                _accept_file_url_drop(event)
                return
        super().dropEvent(event)
