"""Q 弹动画：按下缩小、松手回弹的按钮"""

from PySide6.QtCore import QEasingCurve, QVariantAnimation
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QPushButton


class BouncyButton(QPushButton):
    """按下时整体缩小、松手时弹过原始大小再落回的按钮

    做法：点击时先把按钮当前外观截成一张图，动画期间按比例把这张图重绘出来。
    缩放只发生在绘制阶段，控件在布局里的真实尺寸不变，因此不会挤动旁边的控件。
    """

    PRESS_MS = 90
    RELEASE_MS = 300
    RELEASE_OVERSHOOT = 1.05

    def __init__(self, text='', parent=None, scale=0.92):
        super().__init__(text, parent)
        self._scale = 1.0
        self._press_scale = scale
        self._snapshot = None

        self._animation = QVariantAnimation(self)
        self._animation.valueChanged.connect(self._apply_scale)

        # 用 pressed / released 信号，鼠标点击和键盘回车都能触发
        self.pressed.connect(self._play_press)
        self.released.connect(self._play_release)

    # ---------------- 动画 ----------------
    def _play_press(self):
        """按下：快速缩到 press_scale"""
        self._take_snapshot()
        self._animate(
            [(0.0, self._scale), (1.0, self._press_scale)],
            self.PRESS_MS,
            QEasingCurve.Type.OutQuad,
        )

    def _play_release(self):
        """松手：先弹过原始大小，再落回原位"""
        self._take_snapshot()
        self._animate(
            [(0.0, self._scale), (0.45, self.RELEASE_OVERSHOOT), (1.0, 1.0)],
            self.RELEASE_MS,
            QEasingCurve.Type.OutCubic,
        )

    def _take_snapshot(self):
        """在事件回调里截取按钮当前外观（此时不在绘制过程中，可以安全截取）"""
        scale, self._scale = self._scale, 1.0
        self._snapshot = self.grab()
        self._scale = scale

    def _animate(self, frames, duration, easing):
        self._animation.stop()
        self._animation.setStartValue(float(frames[0][1]))
        self._animation.setEndValue(float(frames[-1][1]))
        for step, value in frames[1:-1]:
            self._animation.setKeyValueAt(step, float(value))
        self._animation.setDuration(duration)
        self._animation.setEasingCurve(easing)
        self._animation.start()

    def _apply_scale(self, value):
        self._scale = float(value)
        self.update()

    # ---------------- 绘制 ----------------
    def paintEvent(self, event):
        if self._snapshot is None or abs(self._scale - 1.0) < 0.002:
            super().paintEvent(event)
            return

        pixmap = self._snapshot
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        # 以中心为原点等比缩放
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._scale, self._scale)
        painter.translate(-self.width() / 2, -self.height() / 2)
        painter.drawPixmap(
            0, 0, self.width(), self.height(),
            pixmap, 0, 0, pixmap.width(), pixmap.height(),
        )
