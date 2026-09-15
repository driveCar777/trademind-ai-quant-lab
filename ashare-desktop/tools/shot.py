"""Dev helper: render each page offscreen to PNG so visuals can be reviewed
without a live display. Not part of the shipped app.

Usage: QT_QPA_PLATFORM=offscreen python tools/shot.py /out/dir
"""
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import QtWidgets, QtGui  # noqa: E402
from PySide6.QtCore import Qt, QElapsedTimer  # noqa: E402


def pump(app, ms):
    t = QElapsedTimer()
    t.start()
    while t.elapsed() < ms:
        app.processEvents()
        time.sleep(0.005)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ashare_desktop.app import MainWindow  # noqa: E402
from ashare_desktop.theme import app_qss  # noqa: E402


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ashots"
    os.makedirs(out, exist_ok=True)
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(app_qss())
    app.setFont(QtGui.QFont("Noto Sans CJK SC", 10))
    win = MainWindow()
    win.resize(1180, 760)
    win.show()
    app.processEvents()
    names = ["today", "shortlist", "ledger", "health"]
    for i, nm in enumerate(names):
        win.sidebar.select(i, animate=False)
        win.stack.setCurrentIndex(i)
        pump(app, 900)  # let count-up / transitions settle
        win.grab().save(os.path.join(out, f"{i}_{nm}.png"))
        print("saved", nm)


if __name__ == "__main__":
    main()
