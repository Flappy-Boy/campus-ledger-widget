"""桌面悬浮版：校园记账小窗口

常驻桌面置顶、无边框、可拖动，三个按钮进入收入 / 支出 / 查询界面。
数据与网页版共用同一个 SQLite 文件，两者可随时切换使用。
"""
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from PySide6.QtCore import (QEasingCurve, QPoint, QPropertyAnimation, QRect,
                            QSize, Qt)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QGraphicsOpacityEffect, QHBoxLayout,
                               QLabel, QStackedWidget, QVBoxLayout, QWidget)

import store
from anim import BouncyButton
from pages import HomePage, QueryPage, RecordPage
from theme import BORDER_COLOR, STYLE, WINDOW_RADIUS, light_palette

JOB_ID = 'daily_income_expense_query'

# 页面切换动画时长（毫秒）
TRANSITION_MS = 220

# 每个界面切换时的窗口尺寸
PAGE_SIZES = {
    'home': (320, 292),
    'income': (380, 400),
    'expense': (380, 400),
    'query': (760, 620),
}


class FloatingWindow(QWidget):
    """置顶悬浮面板：主界面 + 三个功能界面在同一面板内切换"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('校园记账')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._drag_offset = None

        self.home = HomePage()
        self.income = RecordPage(store.TYPE_INCOME)
        self.expense = RecordPage(store.TYPE_EXPENSE)
        self.query = QueryPage()
        self._pages = {
            'home': (0, self.home),
            'income': (1, self.income),
            'expense': (2, self.expense),
            'query': (3, self.query),
        }

        self.stack = QStackedWidget()
        for _, page in self._pages.values():
            self.stack.addWidget(page)

        for page in (self.home, self.income, self.expense, self.query):
            page.navigate.connect(self.show_page)
        self.income.data_changed.connect(self.on_data_changed)
        self.expense.data_changed.connect(self.on_data_changed)
        self.query.data_changed.connect(self.home.refresh)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 8, 14, 12)
        root.setSpacing(4)
        root.addLayout(self._build_title_bar())
        root.addWidget(self.stack, 1)

        # 页面切换：窗口尺寸平滑过渡 + 内容淡入
        self._fade = QGraphicsOpacityEffect(self.stack)
        self._fade.setOpacity(1.0)
        self.stack.setGraphicsEffect(self._fade)

        self._size_animation = QPropertyAnimation(self, b'geometry', self)
        self._size_animation.setDuration(TRANSITION_MS)
        self._size_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._size_animation.finished.connect(self._on_size_animation_finished)

        self._fade_animation = QPropertyAnimation(self._fade, b'opacity', self)
        self._fade_animation.setDuration(TRANSITION_MS)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._pending_size = None
        self.show_page('home', animate=False)
        self._move_to_default_position()

    def _build_title_bar(self):
        bar = QHBoxLayout()
        bar.setSpacing(4)

        title = QLabel('校园记账')
        title.setObjectName('appTitle')
        hint = QLabel('·  常驻桌面')
        hint.setObjectName('hint')

        close_button = BouncyButton('×', scale=0.88)
        close_button.setObjectName('closeBtn')
        close_button.setFixedSize(20, 20)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.close)

        bar.addWidget(title)
        bar.addWidget(hint)
        bar.addStretch(1)
        bar.addWidget(close_button)
        return bar

    def _move_to_default_position(self):
        """默认停在屏幕右侧偏上位置"""
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 40, screen.top() + 120)

    def show_page(self, name, animate=True):
        index, page = self._pages[name]
        size = PAGE_SIZES[name]
        self.stack.setCurrentIndex(index)
        page.refresh()

        if not animate or not self.isVisible():
            self._size_animation.stop()
            self.setFixedSize(*size)
            self._clamp_to_screen()
            return

        # 尺寸平滑过渡：先把固定尺寸解除，再动画到目标位置与大小
        self._size_animation.stop()
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self._pending_size = size
        self._size_animation.setStartValue(self.geometry())
        self._size_animation.setEndValue(QRect(self._target_top_left(*size), QSize(*size)))
        self._size_animation.start()

        self._fade_animation.stop()
        self._fade_animation.setStartValue(0.35)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.start()

    def _on_size_animation_finished(self):
        if self._pending_size is not None:
            self.setFixedSize(*self._pending_size)
            self._pending_size = None

    def _target_top_left(self, width, height):
        """动画目标位置：保持当前位置，超出屏幕时向屏幕内收"""
        screen = QApplication.primaryScreen().availableGeometry()
        x = min(max(self.x(), screen.left()), screen.right() - width)
        y = min(max(self.y(), screen.top()), screen.bottom() - height)
        return QPoint(x, y)

    def _clamp_to_screen(self):
        point = self._target_top_left(self.width(), self.height())
        if point != self.pos():
            self.move(point)

    def on_data_changed(self):
        self.home.refresh()

    def set_schedule_text(self, text):
        self.home.set_schedule_text(text)

    def paintEvent(self, event):
        """自绘圆角白色底板"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor('#ffffff'))
        painter.setPen(QPen(QColor(BORDER_COLOR), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), WINDOW_RADIUS, WINDOW_RADIUS)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None


def start_scheduler():
    """每天 08:00 自动统计一次近 30 天收支"""
    scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
    scheduler.add_job(
        store.run_snapshot,
        trigger='cron',
        hour=8,
        minute=0,
        id=JOB_ID,
        replace_existing=True,
    )
    scheduler.start()
    return scheduler


def next_run_text(scheduler):
    job = scheduler.get_job(JOB_ID)
    if job is None or job.next_run_time is None:
        return '未启动'
    return job.next_run_time.strftime('%m-%d %H:%M')


def main():
    store.init_db()
    scheduler = start_scheduler()

    app = QApplication(sys.argv)
    app.setApplicationName('校园记账')
    app.setStyle('Fusion')
    app.setPalette(light_palette())
    app.setStyleSheet(STYLE)

    window = FloatingWindow()
    window.set_schedule_text(
        f'定时统计：每天 08:00 自动统计近 {store.QUERY_DAYS} 天收支\n'
        f'下次执行 {next_run_text(scheduler)}'
    )
    window.show()

    print(f'桌面悬浮窗已启动，数据文件：{store.db_path()}')
    exit_code = app.exec()
    scheduler.shutdown(wait=False)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
