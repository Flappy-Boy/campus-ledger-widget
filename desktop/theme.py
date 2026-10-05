"""悬浮窗配色与全局样式"""
from PySide6.QtGui import QColor, QPalette

INCOME_COLOR = '#67c23a'
EXPENSE_COLOR = '#f56c6c'
PRIMARY_COLOR = '#409eff'
TEXT_COLOR = '#303133'
SUB_COLOR = '#909399'
CARD_BG = '#ffffff'
BORDER_COLOR = '#dcdfe6'

WINDOW_RADIUS = 14


def light_palette():
    """强制浅色配色：避免系统开启深色模式时表格、下拉弹层底色变黑"""
    palette = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, CARD_BG),
        (QPalette.ColorRole.WindowText, TEXT_COLOR),
        (QPalette.ColorRole.Base, CARD_BG),
        (QPalette.ColorRole.AlternateBase, '#fafafa'),
        (QPalette.ColorRole.Text, TEXT_COLOR),
        (QPalette.ColorRole.Button, CARD_BG),
        (QPalette.ColorRole.ButtonText, TEXT_COLOR),
        (QPalette.ColorRole.ToolTipBase, CARD_BG),
        (QPalette.ColorRole.ToolTipText, TEXT_COLOR),
        (QPalette.ColorRole.Highlight, PRIMARY_COLOR),
        (QPalette.ColorRole.HighlightedText, '#ffffff'),
        (QPalette.ColorRole.PlaceholderText, '#a8abb2'),
    ):
        palette.setColor(role, QColor(color))
    return palette


STYLE = """
* {
    font-family: 'Microsoft YaHei UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
}
QLabel {
    font-size: 12px;
    color: #606266;
}
QLabel#appTitle {
    font-size: 13px;
    font-weight: 600;
    color: #303133;
}
QLabel#pageTitle {
    font-size: 14px;
    font-weight: 600;
    color: #303133;
}
QLabel#balanceLabel {
    font-size: 12px;
    color: #909399;
}
QLabel#balanceValue {
    font-size: 28px;
    font-weight: 700;
}
QLabel#hint {
    font-size: 11px;
    color: #909399;
}
QLabel#fieldLabel {
    font-size: 12px;
    color: #606266;
}
QLabel#toast {
    font-size: 12px;
}
QLabel#summaryStrong {
    font-size: 12px;
    font-weight: 600;
}
QLabel#summaryPlain {
    font-size: 12px;
    color: #606266;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #dcdfe6;
    border-radius: 6px;
    padding: 5px 12px;
    color: #303133;
    font-size: 12px;
}
QPushButton:hover {
    border-color: #409eff;
    color: #409eff;
}
QPushButton:pressed {
    background: #ecf5ff;
}

QPushButton#navIncome, QPushButton#navExpense, QPushButton#navQuery {
    font-size: 14px;
    font-weight: 600;
    padding: 14px 0;
    border-radius: 10px;
}
QPushButton#navIncome {
    background: #f0f9eb;
    border: 1px solid #c2e7b0;
    color: #67c23a;
}
QPushButton#navIncome:hover {
    background: #e1f3d8;
}
QPushButton#navExpense {
    background: #fef0f0;
    border: 1px solid #fbc4c4;
    color: #f56c6c;
}
QPushButton#navExpense:hover {
    background: #fde2e2;
}
QPushButton#navQuery {
    background: #ecf5ff;
    border: 1px solid #b3d8ff;
    color: #409eff;
}
QPushButton#navQuery:hover {
    background: #d9ecff;
}

QPushButton#addIncome {
    background: #67c23a;
    border: none;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 0;
}
QPushButton#addIncome:hover {
    background: #85ce61;
}
QPushButton#addExpense {
    background: #f56c6c;
    border: none;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 0;
}
QPushButton#addExpense:hover {
    background: #f78989;
}
QPushButton#searchBtn {
    background: #409eff;
    border: none;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#searchBtn:hover {
    background: #66b1ff;
}
QPushButton#dangerBtn {
    color: #f56c6c;
    border-color: #fbc4c4;
}
QPushButton#dangerBtn:hover {
    background: #fef0f0;
}

QPushButton#closeBtn {
    border: none;
    background: transparent;
    color: #909399;
    font-size: 15px;
    font-weight: 600;
    padding: 0;
}
QPushButton#closeBtn:hover {
    color: #f56c6c;
}
QPushButton#backBtn {
    border: none;
    background: transparent;
    color: #409eff;
    font-size: 12px;
    padding: 2px 4px;
}
QPushButton#backBtn:hover {
    color: #66b1ff;
}

QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit {
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    padding: 2px 6px;
    min-height: 22px;
    background: #ffffff;
    font-size: 12px;
    color: #303133;
}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
    border-color: #409eff;
}
QComboBox::drop-down {
    border: none;
    width: 16px;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    color: #303133;
    border: 1px solid #dcdfe6;
    selection-background-color: #ecf5ff;
    selection-color: #409eff;
    outline: none;
}

QTableWidget {
    background: #ffffff;
    alternate-background-color: #fafafa;
    border: 1px solid #ebeef5;
    gridline-color: #ebeef5;
    font-size: 12px;
    color: #303133;
}
QTableWidget::item {
    padding: 2px 4px;
}
QTableWidget::item:selected {
    background: #ecf5ff;
    color: #303133;
}
QHeaderView::section {
    background: #f5f7fa;
    border: none;
    border-bottom: 1px solid #ebeef5;
    padding: 5px;
    color: #606266;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #ebeef5;
    border-radius: 4px;
    background: #ffffff;
}
QTabBar::tab {
    padding: 5px 14px;
    font-size: 12px;
    color: #606266;
    background: #f5f7fa;
    border: 1px solid #ebeef5;
    border-bottom: none;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #409eff;
}
QTabBar::tab:hover {
    color: #409eff;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
}
QScrollBar::handle:vertical {
    background: #dcdfe6;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""
