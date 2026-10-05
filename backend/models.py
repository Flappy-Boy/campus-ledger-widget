"""数据模型定义（SQLite）"""
from datetime import date, datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

INCOME_CATEGORIES = ['生活费', '奖学金', '兼职', '实习工资', '红包', '其他']
EXPENSE_CATEGORIES = ['餐饮', '交通', '购物', '学习', '娱乐', '房租', '医疗', '其他']

TYPE_INCOME = 'income'
TYPE_EXPENSE = 'expense'


class Record(db.Model):
    """一条收入或支出记录"""

    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(32), nullable=False, default='其他')
    note = db.Column(db.String(200), default='')
    record_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'amount': round(self.amount, 2),
            'category': self.category,
            'note': self.note or '',
            'date': self.record_date.strftime('%Y-%m-%d'),
            'createdAt': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
        }


class ScheduledReport(db.Model):
    """定时查询生成的一次收支快照"""

    __tablename__ = 'scheduled_reports'

    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    income_total = db.Column(db.Float, nullable=False, default=0)
    expense_total = db.Column(db.Float, nullable=False, default=0)
    balance = db.Column(db.Float, nullable=False, default=0)
    record_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'startDate': self.start_date.strftime('%Y-%m-%d'),
            'endDate': self.end_date.strftime('%Y-%m-%d'),
            'incomeTotal': round(self.income_total, 2),
            'expenseTotal': round(self.expense_total, 2),
            'balance': round(self.balance, 2),
            'recordCount': self.record_count,
            'createdAt': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
        }
