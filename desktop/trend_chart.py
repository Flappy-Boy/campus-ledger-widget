"""趋势折线图控件：自绘（不依赖 matplotlib，保持 exe 体积小）"""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from theme import BORDER_COLOR, EXPENSE_COLOR, INCOME_COLOR, SUB_COLOR

MARGIN_LEFT = 56
MARGIN_RIGHT = 16
MARGIN_TOP = 32
MARGIN_BOTTOM = 30


def _nice_max(value):
    """把坐标轴最大值取整到好看的刻度"""
    if value <= 0:
        return 100.0
    magnitude = 10 ** int(math.floor(math.log10(value)))
    for step in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if value <= magnitude * step:
            return float(magnitude * step)
    return float(magnitude * 10)


def _format_amount(value):
    if value >= 10000:
        return f'{value / 10000:.1f}万'
    return f'{value:,.0f}'


class TrendChart(QWidget):
    """收入/支出双折线趋势图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self._labels = []
        self._income = []
        self._expense = []
        self._by_month = False

    def set_data(self, trend):
        self._labels = list(trend.get('labels', []))
        self._income = list(trend.get('income', []))
        self._expense = list(trend.get('expense', []))
        self._by_month = bool(trend.get('byMonth'))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor('#ffffff'))

        if not self._labels:
            painter.setPen(QColor(SUB_COLOR))
            painter.setFont(QFont('Microsoft YaHei UI', 9))
            painter.drawText(self.rect(), Qt.AlignCenter, '该时间范围内暂无收支数据')
            return

        plot = QRectF(
            MARGIN_LEFT,
            MARGIN_TOP,
            max(self.width() - MARGIN_LEFT - MARGIN_RIGHT, 10),
            max(self.height() - MARGIN_TOP - MARGIN_BOTTOM, 10),
        )

        max_value = _nice_max(max(self._income + self._expense + [0]))
        self._draw_grid(painter, plot, max_value)

        positions = self._x_positions(plot)
        self._draw_series(painter, positions, plot, self._income, max_value, INCOME_COLOR)
        self._draw_series(painter, positions, plot, self._expense, max_value, EXPENSE_COLOR)
        self._draw_x_labels(painter, positions, plot)
        self._draw_legend(painter, plot)

    def _x_positions(self, plot):
        count = len(self._labels)
        if count == 1:
            return [plot.center().x()]
        step = plot.width() / (count - 1)
        return [plot.left() + index * step for index in range(count)]

    def _y_of(self, value, plot, max_value):
        return plot.bottom() - (value / max_value) * plot.height()

    def _draw_grid(self, painter, plot, max_value):
        painter.setFont(QFont('Microsoft YaHei UI', 8))
        for index in range(5):
            ratio = index / 4
            value = max_value * ratio
            y = self._y_of(value, plot, max_value)
            painter.setPen(QPen(QColor('#ebeef5'), 1))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(QColor(SUB_COLOR))
            painter.drawText(
                QRectF(4, y - 8, MARGIN_LEFT - 10, 16),
                Qt.AlignRight | Qt.AlignVCenter,
                _format_amount(value),
            )
        painter.setPen(QPen(QColor(BORDER_COLOR), 1))
        painter.drawLine(QPointF(plot.left(), plot.bottom()), QPointF(plot.right(), plot.bottom()))
        painter.drawLine(QPointF(plot.left(), plot.top()), QPointF(plot.left(), plot.bottom()))

    def _draw_series(self, painter, positions, plot, values, max_value, color):
        if not values:
            return
        path = QPainterPath()
        for index, value in enumerate(values):
            point = QPointF(positions[index], self._y_of(value, plot, max_value))
            if index == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)

        painter.setPen(QPen(QColor(color), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        if len(values) <= 40:
            painter.setBrush(QColor(color))
            painter.setPen(Qt.NoPen)
            for index, value in enumerate(values):
                point = QPointF(positions[index], self._y_of(value, plot, max_value))
                painter.drawEllipse(point, 3, 3)

    def _draw_x_labels(self, painter, positions, plot):
        painter.setFont(QFont('Microsoft YaHei UI', 8))
        painter.setPen(QColor(SUB_COLOR))
        count = len(self._labels)
        max_labels = max(int(plot.width() // 70), 2)
        step = max(count // max_labels, 1) if count > max_labels else 1
        for index in range(0, count, step):
            label = self._labels[index]
            if self._by_month:
                label = label[5:] + '月'
            else:
                label = label[5:]
            painter.drawText(
                QRectF(positions[index] - 30, plot.bottom() + 6, 60, 16),
                Qt.AlignHCenter | Qt.AlignTop,
                label,
            )

    def _draw_legend(self, painter, plot):
        painter.setFont(QFont('Microsoft YaHei UI', 8))
        x = plot.right() - 96
        for label, color in (('收入', INCOME_COLOR), ('支出', EXPENSE_COLOR)):
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(color))
            painter.drawRect(QRectF(x, plot.top() - 22, 10, 10))
            painter.setPen(QColor(SUB_COLOR))
            painter.setBrush(Qt.NoBrush)
            painter.drawText(QRectF(x + 14, plot.top() - 24, 34, 14), Qt.AlignLeft | Qt.AlignVCenter, label)
            x += 48
