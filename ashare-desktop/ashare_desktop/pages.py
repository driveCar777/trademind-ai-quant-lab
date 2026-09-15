"""The four application pages, all bound to a read-only Snapshot."""
from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from .data import Snapshot, Name
from .theme import Color
from .widgets import Card, KpiCard, Badge, LiveDot


def _label(text: str, role: str = "") -> QtWidgets.QLabel:
    lb = QtWidgets.QLabel(text)
    if role:
        lb.setProperty("role", role)
    return lb


class PageHeader(QtWidgets.QWidget):
    def __init__(self, title: str, subtitle: str, right: QtWidgets.QWidget | None = None):
        super().__init__()
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        left = QtWidgets.QVBoxLayout()
        left.setSpacing(2)
        t = _label(title); t.setProperty("role", "h1")
        s = _label(subtitle, "dim")
        left.addWidget(t)
        left.addWidget(s)
        lay.addLayout(left)
        lay.addStretch(1)
        if right is not None:
            lay.addWidget(right, 0, Qt.AlignVCenter)


def _yuan(v) -> str:
    if v is None:
        return "—"
    return f"¥{v:,.0f}"


# --------------------------------------------------------------------------- #
class TodayPage(QtWidgets.QWidget):
    def __init__(self, snap: Snapshot):
        super().__init__()
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        dot = LiveDot(Color.LIVE)
        root.addWidget(PageHeader("今日操作台", f"数据基准日 {snap.asof} · 合同 {snap.contract}", dot))

        # Hero state card
        hero = Card()
        hl = QtWidgets.QVBoxLayout(hero)
        hl.setContentsMargins(26, 24, 26, 24)
        hl.setSpacing(10)
        state_row = QtWidgets.QHBoxLayout()
        big = _label("本期持仓进行中", "h2")
        big.setStyleSheet("font-size:22px;font-weight:800;")
        state_row.addWidget(big)
        state_row.addSpacing(12)
        state_row.addWidget(Badge(f"{snap.ledger_state}", Color.OK))
        state_row.addStretch(1)
        state_row.addWidget(Badge(f"板块 {snap.boards}", Color.ACCENT))
        hl.addLayout(state_row)
        act = snap.act or "到卖出日开盘全部卖出，当晚更新名单，次日开盘按名单买入。"
        tip = _label("操作规则：" + act, "dim")
        tip.setWordWrap(True)
        hl.addWidget(tip)
        nxt = _label(f"下一信号日：{snap.next_signal}", "faint")
        hl.addWidget(nxt)
        root.addWidget(hero)

        # KPI row
        kpis = QtWidgets.QHBoxLayout()
        kpis.setSpacing(16)
        k1 = KpiCard("练手本金", "", Color.GOLD)
        k1.set_target(snap.capital_top20 or 0, 0, "¥")
        k2 = KpiCard("预计投入", "", Color.ACCENT)
        k2.set_target(snap.est_invested or 0, 0, "¥")
        k3 = KpiCard("持仓周期(进行/已结)", "", Color.LIVE)
        k3.set_value(0)
        k3._num.setText(f"{snap.n_periods_open} / {snap.n_periods_closed}")
        k4 = KpiCard("短名单只数", " 只", Color.ACCENT_2)
        k4.set_target(snap.n_names or 0, 0)
        for k in (k1, k2, k3, k4):
            kpis.addWidget(k)
        root.addLayout(kpis)

        # Discipline banner
        banner = Card()
        bl = QtWidgets.QHBoxLayout(banner)
        bl.setContentsMargins(22, 16, 22, 16)
        shield = _label("🛡")
        shield.setStyleSheet("font-size:22px;")
        bl.addWidget(shield)
        bl.addSpacing(10)
        msg = _label(
            f"纸面演练模式 · money = {snap.money} · orders_sent = {str(snap.orders_sent).lower()} · "
            f"本人手工下单，无 API / 无自动化 / 不发单",
            "dim",
        )
        msg.setWordWrap(True)
        bl.addWidget(msg, 1)
        banner.setStyleSheet(
            f"QFrame#Card{{background:rgba(38,208,124,0.06);border:1px solid {Color.OK};border-radius:16px;}}"
        )
        root.addWidget(banner)
        root.addStretch(1)


# --------------------------------------------------------------------------- #
class ScoreBarDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, vmax: float, parent=None):
        super().__init__(parent)
        self._vmax = vmax or 1.0

    def paint(self, p, opt, idx):
        val = idx.data(Qt.UserRole)
        if val is None:
            return super().paint(p, opt, idx)
        p.save()
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r = opt.rect.adjusted(10, 12, -10, -12)
        p.setBrush(QtGui.QColor(Color.BG_3))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(r, 5, 5)
        frac = max(0.06, min(1.0, val / self._vmax))
        fr = QtCore.QRectF(r.x(), r.y(), r.width() * frac, r.height())
        grad = QtGui.QLinearGradient(fr.topLeft(), fr.topRight())
        grad.setColorAt(0, QtGui.QColor(Color.ACCENT))
        grad.setColorAt(1, QtGui.QColor(Color.ACCENT_2))
        p.setBrush(grad)
        p.drawRoundedRect(fr, 5, 5)
        p.setPen(QtGui.QColor(Color.TEXT))
        f = p.font(); f.setPixelSize(11); p.setFont(f)
        p.drawText(opt.rect.adjusted(12, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft, f"{val:.4f}")
        p.restore()


class ShortlistPage(QtWidgets.QWidget):
    def __init__(self, snap: Snapshot):
        super().__init__()
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(18)
        right = Badge(f"预计投入 {_yuan(snap.est_invested)}", Color.GOLD)
        root.addWidget(PageHeader(
            "短名单 SHORTLIST",
            f"{snap.shortlist_date} · {snap.n_names} 只 · 收盘≤¥100 · 每只 1 手起（100 股）",
            right,
        ))

        card = Card(flat=True)
        cl = QtWidgets.QVBoxLayout(card)
        cl.setContentsMargins(10, 8, 10, 10)
        table = QtWidgets.QTableView()
        table.setModel(self._model(snap.names))
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        vmax = max((n.score for n in snap.names), default=1.0)
        table.setItemDelegateForColumn(2, ScoreBarDelegate(vmax, table))
        table.verticalHeader().setDefaultSectionSize(40)
        cl.addWidget(table)
        root.addWidget(card, 1)

    @staticmethod
    def _model(names: list[Name]) -> QtGui.QStandardItemModel:
        cols = ["排名", "代码", "模型分数", "最新价", "手数(100股)", "预计金额"]
        m = QtGui.QStandardItemModel(len(names), len(cols))
        m.setHorizontalHeaderLabels(cols)
        for row, n in enumerate(names):
            rank = QtGui.QStandardItem(f"#{n.rank}")
            rank.setForeground(QtGui.QColor(Color.GOLD if n.rank <= 3 else Color.TEXT_DIM))
            sym = QtGui.QStandardItem(n.symbol)
            sym.setForeground(QtGui.QColor(Color.TEXT))
            f = sym.font(); f.setBold(True); sym.setFont(f)
            score = QtGui.QStandardItem("")
            score.setData(n.score, Qt.UserRole)
            price = QtGui.QStandardItem(f"¥{n.last_close:.2f}")
            price.setForeground(QtGui.QColor(Color.UP))
            price.setTextAlignment(Qt.AlignCenter)
            lots = QtGui.QStandardItem(str(n.lots))
            lots.setTextAlignment(Qt.AlignCenter)
            est = QtGui.QStandardItem(f"¥{n.est_yuan:,.0f}")
            est.setTextAlignment(Qt.AlignCenter)
            for c, it in enumerate((rank, sym, score, price, lots, est)):
                m.setItem(row, c, it)
        return m


# --------------------------------------------------------------------------- #
class LedgerPage(QtWidgets.QWidget):
    def __init__(self, snap: Snapshot):
        super().__init__()
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(18)
        root.addWidget(PageHeader(
            "持仓 & 影子账本",
            f"影子链锚点 · 状态 {snap.ledger_state} · money {snap.money}",
            Badge("SHADOW", Color.LIVE),
        ))

        kpis = QtWidgets.QHBoxLayout()
        kpis.setSpacing(16)
        k1 = KpiCard("影子权益", "", Color.GOLD)
        k1.set_target(snap.equity_shadow or 0, 0, "¥")
        k2 = KpiCard("进行中周期", "", Color.LIVE)
        k2.set_target(snap.n_periods_open, 0)
        k3 = KpiCard("已结算周期", "", Color.ACCENT)
        k3.set_target(snap.n_periods_closed, 0)
        for k in (k1, k2, k3):
            kpis.addWidget(k)
        root.addLayout(kpis)

        card = Card(flat=True)
        cl = QtWidgets.QVBoxLayout(card)
        cl.setContentsMargins(10, 8, 10, 10)
        table = QtWidgets.QTableView()
        table.setModel(self._model(snap.periods))
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setShowGrid(False)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        table.verticalHeader().setDefaultSectionSize(40)
        cl.addWidget(table)
        root.addWidget(card, 1)

    @staticmethod
    def _model(periods: list[dict]) -> QtGui.QStandardItemModel:
        cols = ["信号日", "建仓日", "预计平仓", "选中/成交", "状态"]
        m = QtGui.QStandardItemModel(len(periods), len(cols))
        m.setHorizontalHeaderLabels(cols)
        for row, pr in enumerate(periods):
            sig = QtGui.QStandardItem(str(pr.get("signal_date", "—")))
            entry = QtGui.QStandardItem(str(pr.get("entry", "—")))
            ex = QtGui.QStandardItem(str(pr.get("exit_expected", "—")))
            fill = QtGui.QStandardItem(f"{pr.get('n_sel', '—')} / {pr.get('n_fill_entry', '—')}")
            fill.setTextAlignment(Qt.AlignCenter)
            st = QtGui.QStandardItem(str(pr.get("status", "—")))
            st.setForeground(QtGui.QColor(Color.OK if pr.get("status") == "OPEN" else Color.TEXT_DIM))
            f = st.font(); f.setBold(True); st.setFont(f)
            for c, it in enumerate((sig, entry, ex, fill, st)):
                m.setItem(row, c, it)
        return m


# --------------------------------------------------------------------------- #
class HealthPage(QtWidgets.QWidget):
    def __init__(self, snap: Snapshot):
        super().__init__()
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(18)
        ok = snap.ok
        dot = LiveDot(Color.OK if ok else Color.BAD)
        root.addWidget(PageHeader("运行健康", "数据冻结 / 增量 / 影子账本状态", dot))

        # status pills row
        pills = QtWidgets.QHBoxLayout()
        pills.setSpacing(12)
        pills.addWidget(Badge("数据已加载" if ok else "数据缺失", Color.OK if ok else Color.BAD))
        pills.addWidget(Badge(f"账本 {snap.ledger_state}", Color.OK))
        pills.addWidget(Badge(f"orders_sent={str(snap.orders_sent).lower()}", Color.LIVE))
        pills.addStretch(1)
        root.addLayout(pills)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(16)
        rows = [
            ("冻结数据集", snap.frozen_id),
            ("冻结哈希", (snap.frozen_hash[:24] + "…") if snap.frozen_hash else "—"),
            ("冻结截止", snap.frozen_end),
            ("股票数 / 交易日", f"{snap.n_symbols or '—'} / {snap.n_dates or '—'}"),
            ("增量构建于", snap.built_at),
            ("步骤 fetch / features", f"{snap.steps.get('fetch','—')} / {snap.steps.get('features_rebuilt','—')}"),
            ("数据目录", snap.source_dir),
            ("合同", snap.contract),
        ]
        for i, (k, v) in enumerate(rows):
            grid.addWidget(self._kv(k, v), i // 2, i % 2)
        root.addLayout(grid)
        root.addStretch(1)

    @staticmethod
    def _kv(key: str, val: str) -> Card:
        card = Card()
        l = QtWidgets.QVBoxLayout(card)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(4)
        l.addWidget(_label(key, "faint"))
        v = _label(str(val))
        v.setStyleSheet("font-size:15px;font-weight:700;")
        v.setWordWrap(True)
        l.addWidget(v)
        return card
