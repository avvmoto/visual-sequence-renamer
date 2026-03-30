"""アプリケーションのエントリポイント。"""

from __future__ import annotations

import logging
import signal
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def main() -> None:
    """アプリを起動する。"""
    logging.basicConfig(level=logging.INFO)
    app = QApplication.instance() or QApplication(sys.argv)

    def _on_sigint(_signum: int, _frame: object | None) -> None:
        """ターミナルで Ctrl+C (SIGINT) が来たらイベントループを終了する。"""
        logger.info("中断 (SIGINT) を受け取りました。終了します。")
        app.quit()

    signal.signal(signal.SIGINT, _on_sigint)
    # Qt のイベントループ中は Python が SIGINT を処理しにくいため、短い間隔で一度ずつ
    # 制御を戻し KeyboardInterrupt / シグナルハンドラが動くようにする。
    _sig_poll = QTimer(app)
    _sig_poll.timeout.connect(lambda: None)
    _sig_poll.start(200)

    window = MainWindow()
    window.show()
    try:
        code = app.exec()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt を受け取りました。終了します。")
        code = 0
    raise SystemExit(code)


if __name__ == "__main__":
    main()
