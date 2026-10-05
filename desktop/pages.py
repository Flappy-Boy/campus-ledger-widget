"""悬浮窗的三个功能界面：收入录入、支出录入、查询账单"""
from PySide6.QtCore import QDate, Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDateEdit,
                               QDoubleSpinBox, QFormLayout, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QMessageBox,
                               QTableWidget, QTableWidgetItem, QTabWidget,
                               QVBoxLayout, QWidget)

import store
from anim import BouncyButton
from theme import EXPENSE_COLOR, INCOME_COLOR, PRIMARY_COLOR, SUB_COLOR
from trend_chart import TrendChart

QUICK_RANGES = [
    ('今天', 0),
    ('近 7 天', 6),
    ('近 30 天', 29),
    ('本月', -1),
    ('全部', -2),
]


class PageHeader(QWidget):
    """功能页顶部：返回按钮 + 标题"""

    back_clicked = Signal()

    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        back = BouncyButton('← 返回', scale=0.97)
        back.setObjectName('backBtn')
        back.setCursor(Qt.PointingHandCursor)
        back.clicked.connect(self.back_clicked)

        title_label = QLabel(title)
        title_label.setObjectName('pageTitle')

        layout.addWidget(back)
        layout.addWidget(title_label)
        layout.addStretch(1)


class HomePage(QWidget):
    """主界面：显示总余额 + 收入 / 支出 / 查询三个按钮"""

    navigate = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 12, 18, 12)
        root.setSpacing(4)

        caption = QLabel('当前总余额')
        caption.setObjectName('balanceLabel')
        caption.setAlignment(Qt.AlignCenter)

        self.balance = QLabel('￥0.00')
        self.balance.setObjectName('balanceValue')
        self.balance.setAlignment(Qt.AlignCenter)

        self.count = QLabel('')
        self.count.setObjectName('hint')
        self.count.setAlignment(Qt.AlignCenter)

        self.month = QLabel('')
        self.month.setObjectName('hint')
        self.month.setAlignment(Qt.AlignCenter)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        for key, text, name in (('income', '收入', 'navIncome'), ('expense', '支出', 'navExpense')):
            button = BouncyButton(text)
            button.setObjectName(name)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _=False, page=key: self.navigate.emit(page))
            buttons.addWidget(button)

        self.query_button = BouncyButton('查询')
        self.query_button.setObjectName('navQuery')
        self.query_button.setCursor(Qt.PointingHandCursor)
        self.query_button.clicked.connect(lambda: self.navigate.emit('query'))

        self.schedule = QLabel('')
        self.schedule.setObjectName('hint')
        self.schedule.setAlignment(Qt.AlignCenter)
        self.schedule.setWordWrap(True)

        root.addWidget(caption)
        root.addWidget(self.balance)
        root.addWidget(self.count)
        root.addWidget(self.month)
        root.addSpacing(10)
        root.addLayout(buttons)
        root.addWidget(self.query_button)
        root.addStretch(1)
        root.addWidget(self.schedule)

    def set_schedule_text(self, text):
        self.schedule.setText(text)

    def refresh(self):
        data = store.totals()
        color = INCOME_COLOR if data['balance'] >= 0 else EXPENSE_COLOR
        self.balance.setText(f'￥{data["balance"]:,.2f}')
        self.balance.setStyleSheet(f'color: {color};')
        self.count.setText(f'共 {data["count"]} 条收支记录')
        self.month.setText(
            f'本月 收入 ￥{data["monthIncome"]:,.2f} · 支出 ￥{data["monthExpense"]:,.2f}'
        )


class RecordPage(QWidget):
    """收入 / 支出录入界面（两种类型共用同一套界面）"""

    navigate = Signal(str)
    data_changed = Signal()

    def __init__(self, record_type, parent=None):
        super().__init__(parent)
        self.record_type = record_type
        is_income = record_type == store.TYPE_INCOME
        color = INCOME_COLOR if is_income else EXPENSE_COLOR
        title = '记录收入' if is_income else '记录支出'

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 12, 18, 14)
        root.setSpacing(10)

        header = PageHeader(title)
        header.back_clicked.connect(lambda: self.navigate.emit('home'))
        root.addWidget(header)

        self.balance_hint = QLabel('')
        self.balance_hint.setObjectName('hint')
        root.addWidget(self.balance_hint)

        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 9_999_999)
        self.amount.setDecimals(2)
        self.amount.setSingleStep(10)
        self.amount.setPrefix('￥ ')
        self.amount.setAlignment(Qt.AlignRight)

        self.category = QComboBox()
        self.category.addItems(store.INCOME_CATEGORIES if is_income else store.EXPENSE_CATEGORIES)

        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat('yyyy-MM-dd')

        self.note = QLineEdit()
        self.note.setPlaceholderText('选填，例如：9 月生活费')
        self.note.setMaxLength(60)

        form = QFormLayout()
        form.setSpacing(9)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.addRow('金额', self.amount)
        form.addRow('类型', self.category)
        form.addRow('日期', self.date)
        form.addRow('备注', self.note)
        root.addLayout(form)

        self.submit_button = BouncyButton(f'添加{title[2:]}')
        self.submit_button.setObjectName('addIncome' if is_income else 'addExpense')
        self.submit_button.setCursor(Qt.PointingHandCursor)
        self.submit_button.clicked.connect(self.submit)
        root.addWidget(self.submit_button)

        self.toast = QLabel('')
        self.toast.setObjectName('toast')
        self.toast.setAlignment(Qt.AlignCenter)
        self.toast.setWordWrap(True)
        root.addWidget(self.toast)
        root.addStretch(1)

        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(lambda: self.toast.setText(''))
        self._color = color

    def refresh(self):
        data = store.totals()
        self.balance_hint.setText(f'当前总余额 ￥{data["balance"]:,.2f}（添加后立即更新）')

    def _show_toast(self, text, color):
        self.toast.setText(text)
        self.toast.setStyleSheet(f'color: {color};')
        self._toast_timer.start(4000)

    def submit(self):
        amount = round(self.amount.value(), 2)
        if amount <= 0:
            self._show_toast('金额必须大于 0，请输入正确的金额', EXPENSE_COLOR)
            return

        record_date = self.date.date().toString('yyyy-MM-dd')
        if record_date > QDate.currentDate().toString('yyyy-MM-dd'):
            self._show_toast('日期不能晚于今天', EXPENSE_COLOR)
            return

        store.add_record(
            self.record_type,
            amount,
            self.category.currentText(),
            self.note.text(),
            record_date,
        )
        label = '收入' if self.record_type == store.TYPE_INCOME else '支出'
        self._show_toast(f'已添加：{label} ￥{amount:,.2f}（{self.category.currentText()}）', self._color)

        self.amount.setValue(0)
        self.note.clear()
        self.refresh()
        self.data_changed.emit()


class QueryPage(QWidget):
    """查询账单：按时间范围查明细、看汇总与趋势、查看定时统计"""

    navigate = Signal(str)
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 12, 18, 14)
        root.setSpacing(8)

        header = PageHeader('查询账单')
        header.back_clicked.connect(lambda: self.navigate.emit('home'))
        root.addWidget(header)

        root.addLayout(self._build_filter_row())
        root.addLayout(self._build_quick_row())

        self.summary = QLabel('')
        self.summary.setObjectName('summaryPlain')
        root.addWidget(self.summary)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_detail_tab(), '明细')
        self.tabs.addTab(self._build_trend_tab(), '趋势')
        self.tabs.addTab(self._build_schedule_tab(), '定时统计')
        root.addWidget(self.tabs, 1)

        self.toast = QLabel('')
        self.toast.setObjectName('toast')
        self.toast.setAlignment(Qt.AlignLeft)
        root.addWidget(self.toast)

        self.reset_range(-1)  # 默认查询本月

    # ---------------- 界面构建 ----------------
    def _build_filter_row(self):
        row = QHBoxLayout()
        row.setSpacing(6)

        today = QDate.currentDate()
        self.start_date = QDateEdit(QDate(today.year(), today.month(), 1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat('yyyy-MM-dd')
        self.end_date = QDateEdit(today)
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat('yyyy-MM-dd')

        self.type_combo = QComboBox()
        self.type_combo.addItems(['全部', '仅收入', '仅支出'])
        self.type_combo.setFixedWidth(88)

        search = BouncyButton('查询')
        search.setObjectName('searchBtn')
        search.setCursor(Qt.PointingHandCursor)
        search.clicked.connect(self.run_query)

        row.addWidget(self.start_date, 1)
        row.addWidget(QLabel('~'))
        row.addWidget(self.end_date, 1)
        row.addWidget(self.type_combo)
        row.addWidget(search)
        return row

    def _build_quick_row(self):
        row = QHBoxLayout()
        row.setSpacing(6)
        for text, offset in QUICK_RANGES:
            button = BouncyButton(text, scale=0.95)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _=False, value=offset: self.reset_range(value))
            row.addWidget(button)
        row.addStretch(1)
        return row

    def _build_detail_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['日期', '类型', '类别', '金额', '备注'])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.delete_button = BouncyButton('删除选中记录')
        self.delete_button.setObjectName('dangerBtn')
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.clicked.connect(self.delete_selected)
        bottom.addWidget(self.delete_button)
        layout.addLayout(bottom)
        return page

    def _build_trend_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        self.chart = TrendChart()
        layout.addWidget(self.chart)
        return page

    def _build_schedule_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        run_now = BouncyButton('立即统计一次')
        run_now.setCursor(Qt.PointingHandCursor)
        run_now.clicked.connect(self.run_snapshot_now)
        layout.addWidget(run_now)

        self.snapshot_table = QTableWidget(0, 5)
        self.snapshot_table.setHorizontalHeaderLabels(['统计时间', '统计区间', '收入', '支出', '结余'])
        self.snapshot_table.verticalHeader().setVisible(False)
        self.snapshot_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.snapshot_table.setAlternatingRowColors(True)
        snapshot_header = self.snapshot_table.horizontalHeader()
        snapshot_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        snapshot_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        snapshot_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        snapshot_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        snapshot_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.snapshot_table, 1)
        return page

    # ---------------- 行为 ----------------
    def reset_range(self, offset):
        today = QDate.currentDate()
        if offset >= 0:
            self.start_date.setDate(today.addDays(-offset))
            self.end_date.setDate(today)
        elif offset == -1:
            self.start_date.setDate(QDate(today.year(), today.month(), 1))
            self.end_date.setDate(today)
        else:
            self.start_date.setDate(QDate(2000, 1, 1))
            self.end_date.setDate(today)
        self.run_query()

    def run_query(self):
        start = self.start_date.date().toString('yyyy-MM-dd')
        end = self.end_date.date().toString('yyyy-MM-dd')
        if start > end:
            self.toast.setStyleSheet(f'color: {EXPENSE_COLOR};')
            self.toast.setText('开始日期不能晚于结束日期，请重新选择')
            return
        self.toast.setText('')

        record_type = {
            '全部': None,
            '仅收入': store.TYPE_INCOME,
            '仅支出': store.TYPE_EXPENSE,
        }[self.type_combo.currentText()]

        rows, summary = store.list_records(start, end, record_type)
        self._rows = rows
        self._fill_table(rows)
        self.summary.setText(
            f'共 {summary["count"]} 条 ｜ 收入 ￥{summary["income"]:,.2f} ｜ '
            f'支出 ￥{summary["expense"]:,.2f} ｜ 结余 ￥{summary["balance"]:,.2f}'
        )
        self.chart.set_data(store.trend(start, end))
        self.refresh_snapshots()

    def _fill_table(self, rows):
        self.table.setRowCount(len(rows))
        for index, record in enumerate(rows):
            is_income = record['type'] == store.TYPE_INCOME
            color = QColor(INCOME_COLOR if is_income else EXPENSE_COLOR)

            date_item = QTableWidgetItem(record['date'])
            date_item.setData(Qt.ItemDataRole.UserRole, record['id'])
            self.table.setItem(index, 0, date_item)

            type_item = QTableWidgetItem('收入' if is_income else '支出')
            type_item.setForeground(color)
            self.table.setItem(index, 1, type_item)

            self.table.setItem(index, 2, QTableWidgetItem(record['category']))

            amount_item = QTableWidgetItem(f'{"+" if is_income else "-"}￥{record["amount"]:,.2f}')
            amount_item.setForeground(color)
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(index, 3, amount_item)

            self.table.setItem(index, 4, QTableWidgetItem(record['note']))

    def delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            self.toast.setStyleSheet(f'color: {SUB_COLOR};')
            self.toast.setText('请先在表格中选中一条记录')
            return

        record_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        answer = QMessageBox.question(
            self,
            '删除确认',
            f'确定删除 {self.table.item(row, 0).text()} 的'
            f'{self.table.item(row, 1).text()} {self.table.item(row, 3).text()}'
            f'（{self.table.item(row, 2).text()}）吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        store.delete_record(record_id)
        self.toast.setStyleSheet(f'color: {PRIMARY_COLOR};')
        self.toast.setText('已删除该条记录')
        self.run_query()
        self.data_changed.emit()

    def run_snapshot_now(self):
        store.run_snapshot()
        self.toast.setStyleSheet(f'color: {PRIMARY_COLOR};')
        self.toast.setText('已执行一次定时统计')
        self.refresh_snapshots()
        self.data_changed.emit()

    def refresh_snapshots(self):
        snapshots = store.snapshot_history(10)
        self.snapshot_table.setRowCount(len(snapshots))
        for index, snap in enumerate(snapshots):
            self.snapshot_table.setItem(index, 0, QTableWidgetItem(snap['createdAt']))
            self.snapshot_table.setItem(
                index, 1, QTableWidgetItem(f'{snap["startDate"]} ~ {snap["endDate"]}')
            )
            income_item = QTableWidgetItem(f'￥{snap["incomeTotal"]:,.2f}')
            income_item.setForeground(QColor(INCOME_COLOR))
            self.snapshot_table.setItem(index, 2, income_item)
            expense_item = QTableWidgetItem(f'￥{snap["expenseTotal"]:,.2f}')
            expense_item.setForeground(QColor(EXPENSE_COLOR))
            self.snapshot_table.setItem(index, 3, expense_item)
            self.snapshot_table.setItem(index, 4, QTableWidgetItem(f'￥{snap["balance"]:,.2f}'))

    def refresh(self):
        self.run_query()
