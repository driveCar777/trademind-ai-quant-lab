"""Reusable, animated UI building blocks."""
from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Property, QRect

from .theme import Color


class Card(QtWidgets.QFrame):
    """Rounded panel. By default it has a soft drop shadow that lifts on hover.

    Pass flat=True for containers that host item-views (QTableView); a
    QGraphicsDropShadowEffect forces children into a cached pixmap and corrupts
    item-view painting, so table cards must stay flat.
    """

    def __init__(self, parent=None, flat: bool = False):
        super().__init__(parent)
        self.setObjectName("Card")
        self._anim = None
        if flat:
            return
        self._shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self._shadow.setColor(QtGui.QColor(0, 0, 0, 150))
        self._shadow.setBlurRadius(24)
        self._shadow.setOffset(0, 10)
        self.setGraphicsEffect(self._shadow)
        self._anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._anim.setDuration(180)

    def enterEvent(self, e):
        self._animate(38)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate(24)
        super().leaveEvent(e)

    def _animate(self, to):
        if self._anim is None:
            return
        self._anim.stop()
        self._anim.setEndValue(to)
        self._anim.start()


class LiveDot(QtWidgets.QWidget):
    """A pulsing status dot used in the header."""

    def __init__(self, color: str = Color.LIVE, parent=None):
        super().__init__(parent)
        self._color = QtGui.QColor(color)
        self._radius = 5.0
        self.setFixedSize(18, 18)
        self._anim = QPropertyAnimation(self, b"radius", self)
        self._anim.setStartValue(3.5)
        self._anim.setEndValue(7.0)
        self._anim.setDuration(900)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.setLoopCount(-1)
        self._anim.start()

    def set_color(self, color: str):
        self._color = QtGui.QColor(color)
        self.update()

    def get_radius(self):
        return self._radius

    def set_radius(self, r):
        self._radius = r
        self.update()

    radius = Property(float, get_radius, set_radius)

    def paintEvent(self, _):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        halo = QtGui.QColor(self._color)
        halo.setAlpha(70)
        p.setBrush(halo)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QtCore.QPointF(cx, cy), self._radius + 3, self._radius + 3)
        p.setBrush(self._color)
        p.drawEllipse(QtCore.QPointF(cx, cy), 3.5, 3.5)


class Badge(QtWidgets.QLabel):
    def __init__(self, text: str, color: str = Color.ACCENT, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"background: rgba(79,140,255,0.12); color: {color};"
            f"border: 1px solid {color}; border-radius: 11px;"
            f"padding: 3px 12px; font-size: 12px; font-weight: 700;"
        )


class KpiCard(Card):
    """A metric card whose numeric value counts up when set."""

    def __init__(self, title: str, unit: str = "", accent: str = Color.GOLD, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._unit = unit
        self._decimals = 0
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(6)
        self._title = QtWidgets.QLabel(title)
        self._title.setProperty("role", "dim")
        self._num = QtWidgets.QLabel("0")
        self._num.setStyleSheet(f"font-size: 30px; font-weight: 800; color: {accent};")
        lay.addWidget(self._title)
        lay.addWidget(self._num)
        lay.addStretch(1)
        # NOTE: distinct name from Card._anim (shadow blurRadius); otherwise the
        # base-class hover animation would drive this count-up property instead.
        self._val_anim = QPropertyAnimation(self, b"value", self)
        self._val_anim.setDuration(700)
        self._val_anim.setEasingCurve(QEasingCurve.OutCubic)

    def set_target(self, value: float, decimals: int = 0, prefix: str = ""):
        self._decimals = decimals
        self._prefix = prefix
        self._val_anim.stop()
        self._val_anim.setStartValue(0.0)
        self._val_anim.setEndValue(float(value))
        self._val_anim.start()

    def get_value(self):
        return self._value

    def set_value(self, v):
        self._value = v
        pfx = getattr(self, "_prefix", "")
        if self._decimals == 0:
            body = f"{int(round(v)):,}"
        else:
            body = f"{v:,.{self._decimals}f}"
        self._num.setText(f"{pfx}{body}{self._unit}")

    value = Property(float, get_value, set_value)


class NavButton(QtWidgets.QAbstractButton):
    def __init__(self, text: str, icon: str, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self._text = text
        self._icon = icon
        self.setFixedHeight(46)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, _):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        active = self.isChecked()
        col = QtGui.QColor(Color.TEXT if active else Color.TEXT_DIM)
        f = self.font()
        f.setPixelSize(20)
        p.setFont(f)
        p.setPen(col)
        p.drawText(QRect(20, 0, 30, self.height()), Qt.AlignVCenter | Qt.AlignLeft, self._icon)
        f.setPixelSize(14)
        f.setBold(active)
        p.setFont(f)
        p.drawText(QRect(54, 0, self.width() - 60, self.height()), Qt.AlignVCenter | Qt.AlignLeft, self._text)


class Sidebar(QtWidgets.QFrame):
    """Navigation rail with a sliding highlight pill behind the active item."""

    changed = QtCore.Signal(int)

    def __init__(self, items: list[tuple[str, str]], parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(232)
        self._buttons: list[NavButton] = []

        self._pill = QtWidgets.QFrame(self)
        self._pill.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 rgba(79,140,255,0.28), stop:1 rgba(124,92,255,0.10));"
            f"border-left: 3px solid {Color.ACCENT}; border-radius: 10px;"
        )
        self._pill.setFixedSize(200, 46)
        self._pill.move(16, 120)
        self._pill_anim = QPropertyAnimation(self._pill, b"pos", self)
        self._pill_anim.setDuration(280)
        self._pill_anim.setEasingCurve(QEasingCurve.OutCubic)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(16, 26, 16, 20)
        lay.setSpacing(6)

        brand = QtWidgets.QLabel("TradeMind")
        brand.setStyleSheet("font-size:20px;font-weight:800;")
        sub = QtWidgets.QLabel("A股 · 纸面操作台")
        sub.setProperty("role", "faint")
        lay.addWidget(brand)
        lay.addWidget(sub)
        lay.addSpacing(18)

        self._group = QtWidgets.QButtonGroup(self)
        self._group.setExclusive(True)
        for idx, (icon, text) in enumerate(items):
            b = NavButton(text, icon)
            self._group.addButton(b, idx)
            self._buttons.append(b)
            lay.addWidget(b)
        lay.addStretch(1)

        ver = QtWidgets.QLabel("只读 · 不发单")
        ver.setProperty("role", "faint")
        lay.addWidget(ver)

        self._group.idClicked.connect(self._on_click)

    def select(self, idx: int, animate: bool = True):
        self._buttons[idx].setChecked(True)
        self._move_pill(idx, animate)
        self.changed.emit(idx)

    def _on_click(self, idx: int):
        self._move_pill(idx, True)
        self.changed.emit(idx)

    def _move_pill(self, idx: int, animate: bool):
        target = self._buttons[idx].pos()
        end = QtCore.QPoint(16, target.y())
        if animate:
            self._pill_anim.stop()
            self._pill_anim.setStartValue(self._pill.pos())
            self._pill_anim.setEndValue(end)
            self._pill_anim.start()
        else:
            self._pill.move(end)
        self._pill.lower()  # keep behind buttons


class FadeStack(QtWidgets.QStackedWidget):
    """QStackedWidget with a fade+rise transition between pages."""

    def switch(self, index: int):
        if index == self.currentIndex():
            return
        new = self.widget(index)
        eff = QtWidgets.QGraphicsOpacityEffect(new)
        new.setGraphicsEffect(eff)
        self.setCurrentIndex(index)
        fade = QPropertyAnimation(eff, b"opacity", new)
        fade.setDuration(320)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)
        pos = QPropertyAnimation(new, b"pos", new)
        start = new.pos() + QtCore.QPoint(0, 18)
        pos.setDuration(320)
        pos.setStartValue(start)
        pos.setEndValue(new.pos())
        pos.setEasingCurve(QEasingCurve.OutCubic)
        self._grp = QtCore.QParallelAnimationGroup(self)
        self._grp.addAnimation(fade)
        self._grp.addAnimation(pos)
        self._grp.finished.connect(lambda: new.setGraphicsEffect(None))
        self._grp.start()
