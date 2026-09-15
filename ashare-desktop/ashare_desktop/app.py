"""Main window: sidebar navigation + animated page stack."""
from __future__ import annotations

import sys

from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import Qt

from .data import load_snapshot
from .pages import TodayPage, ShortlistPage, LedgerPage, HealthPage
from .theme import app_qss
from .widgets import Sidebar, FadeStack


NAV = [
    ("⌂", "今日操作台"),
    ("≣", "短名单"),
    ("▤", "持仓 · 账本"),
    ("♥", "运行健康"),
]


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("Root")
        self.setWindowTitle("TradeMind · A股纸面操作台")
        self.resize(1180, 760)
        self.setMinimumSize(980, 640)

        snap = load_snapshot()

        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self.sidebar = Sidebar(NAV)
        row.addWidget(self.sidebar)

        self.stack = FadeStack()
        self.stack.addWidget(TodayPage(snap))
        self.stack.addWidget(ShortlistPage(snap))
        self.stack.addWidget(LedgerPage(snap))
        self.stack.addWidget(HealthPage(snap))
        row.addWidget(self.stack, 1)

        self.sidebar.changed.connect(self.stack.switch)
        self.sidebar.select(0, animate=False)


def main() -> int:
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(app_qss())
    app.setFont(QtGui.QFont("Noto Sans CJK SC", 10))
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
