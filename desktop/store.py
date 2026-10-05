"""桌面悬浮版数据访问层

直接读写与网页版共用的 SQLite 数据库（表结构与 backend/models.py 保持一致），
因此桌面悬浮窗和网页版看到的是同一份数据，不需要启动后端服务。
"""
import os
import sqlite3
import sys
from contextlib import closing
from datetime import date, datetime, timedelta

INCOME_CATEGORIES = ['生活费', '奖学金', '兼职', '实习工资', '红包', '其他']
EXPENSE_CATEGORIES = ['餐饮', '交通', '购物', '学习', '娱乐', '房租', '医疗', '其他']

TYPE_INCOME = 'income'
TYPE_EXPENSE = 'expense'

# 定时统计的时间范围（天）
QUERY_DAYS = 30

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id INTEGER NOT NULL PRIMARY KEY,
    type VARCHAR(10) NOT NULL,
    amount FLOAT NOT NULL,
    category VARCHAR(32) NOT NULL,
    note VARCHAR(200),
    record_date DATE NOT NULL,
    created_at DATETIME
);
CREATE INDEX IF NOT EXISTS ix_records_type ON records (type);
CREATE INDEX IF NOT EXISTS ix_records_record_date ON records (record_date);
CREATE TABLE IF NOT EXISTS scheduled_reports (
    id INTEGER NOT NULL PRIMARY KEY,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    income_total FLOAT NOT NULL,
    expense_total FLOAT NOT NULL,
    balance FLOAT NOT NULL,
    record_count INTEGER NOT NULL,
    created_at DATETIME
);
"""


def db_path():
    """数据库位置：打包后为 exe 所在目录，开发时为 backend 目录（与网页版一致）"""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
    return os.path.join(base, 'money_schedule.db')


def connect():
    conn = sqlite3.connect(db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(connect()) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def _row_to_dict(row):
    return {
        'id': row['id'],
        'type': row['type'],
        'amount': round(float(row['amount']), 2),
        'category': row['category'],
        'note': row['note'] or '',
        'date': str(row['record_date'])[:10],
        'createdAt': str(row['created_at'] or '')[:19],
    }


def add_record(record_type, amount, category, note='', record_date=None):
    """新增一条收入或支出记录，返回新记录 id"""
    record_date = record_date or date.today().isoformat()
    with closing(connect()) as conn:
        cursor = conn.execute(
            'INSERT INTO records (type, amount, category, note, record_date, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (
                record_type,
                round(float(amount), 2),
                category,
                (note or '').strip()[:200],
                record_date,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def delete_record(record_id):
    with closing(connect()) as conn:
        conn.execute('DELETE FROM records WHERE id = ?', (record_id,))
        conn.commit()


def list_records(start=None, end=None, record_type=None):
    """按时间范围与类型查询记录，返回 (记录列表, 汇总)"""
    sql = 'SELECT * FROM records WHERE 1 = 1'
    params = []
    if start:
        sql += ' AND record_date >= ?'
        params.append(start)
    if end:
        sql += ' AND record_date <= ?'
        params.append(end)
    if record_type in (TYPE_INCOME, TYPE_EXPENSE):
        sql += ' AND type = ?'
        params.append(record_type)
    sql += ' ORDER BY record_date DESC, id DESC'

    with closing(connect()) as conn:
        rows = [_row_to_dict(row) for row in conn.execute(sql, params).fetchall()]

    income = sum(r['amount'] for r in rows if r['type'] == TYPE_INCOME)
    expense = sum(r['amount'] for r in rows if r['type'] == TYPE_EXPENSE)
    summary = {
        'income': round(income, 2),
        'expense': round(expense, 2),
        'balance': round(income - expense, 2),
        'count': len(rows),
    }
    return rows, summary


def totals():
    """全部时间的总余额、总收入、总支出，以及今日/本月收支"""
    with closing(connect()) as conn:
        rows = conn.execute('SELECT * FROM records').fetchall()

    records = [_row_to_dict(row) for row in rows]
    income = sum(r['amount'] for r in records if r['type'] == TYPE_INCOME)
    expense = sum(r['amount'] for r in records if r['type'] == TYPE_EXPENSE)

    today_str = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()
    today_records = [r for r in records if r['date'] == today_str]
    month_records = [r for r in records if month_start <= r['date'] <= today_str]

    def _sum(items, rtype):
        return round(sum(r['amount'] for r in items if r['type'] == rtype), 2)

    return {
        'income': round(income, 2),
        'expense': round(expense, 2),
        'balance': round(income - expense, 2),
        'count': len(records),
        'todayIncome': _sum(today_records, TYPE_INCOME),
        'todayExpense': _sum(today_records, TYPE_EXPENSE),
        'monthIncome': _sum(month_records, TYPE_INCOME),
        'monthExpense': _sum(month_records, TYPE_EXPENSE),
    }


def trend(start=None, end=None):
    """按天（跨度超过 3 个月时按月）聚合收支，用于绘制趋势图"""
    end = end or date.today().isoformat()
    rows, _ = list_records(start=start, end=end)

    try:
        span = (date.fromisoformat(end) - date.fromisoformat(start)).days if start else 0
    except ValueError:
        span = 0
    by_month = span > 92

    buckets = {}
    for record in rows:
        key = record['date'][:7] if by_month else record['date']
        bucket = buckets.setdefault(key, {TYPE_INCOME: 0.0, TYPE_EXPENSE: 0.0})
        bucket[record['type']] += record['amount']

    labels = sorted(buckets)
    return {
        'byMonth': by_month,
        'labels': labels,
        'income': [round(buckets[k][TYPE_INCOME], 2) for k in labels],
        'expense': [round(buckets[k][TYPE_EXPENSE], 2) for k in labels],
    }


def run_snapshot(query_days=QUERY_DAYS):
    """执行一次定时查询：统计最近若干天的收支并写入快照表"""
    end = date.today()
    start = end - timedelta(days=query_days - 1)
    _, summary = list_records(start=start.isoformat(), end=end.isoformat())

    with closing(connect()) as conn:
        cursor = conn.execute(
            'INSERT INTO scheduled_reports '
            '(start_date, end_date, income_total, expense_total, balance, record_count, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                start.isoformat(),
                end.isoformat(),
                summary['income'],
                summary['expense'],
                summary['balance'],
                summary['count'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid

    print(f'[定时查询] {datetime.now():%Y-%m-%d %H:%M:%S} 近 {query_days} 天：'
          f'收入 {summary["income"]:.2f} / 支出 {summary["expense"]:.2f} / 结余 {summary["balance"]:.2f}')
    return {
        'id': new_id,
        'startDate': start.isoformat(),
        'endDate': end.isoformat(),
        'incomeTotal': summary['income'],
        'expenseTotal': summary['expense'],
        'balance': summary['balance'],
        'recordCount': summary['count'],
        'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }


def snapshot_history(limit=10):
    with closing(connect()) as conn:
        rows = conn.execute(
            'SELECT * FROM scheduled_reports ORDER BY created_at DESC, id DESC LIMIT ?', (limit,)
        ).fetchall()
    return [
        {
            'id': row['id'],
            'startDate': str(row['start_date'])[:10],
            'endDate': str(row['end_date'])[:10],
            'incomeTotal': round(float(row['income_total']), 2),
            'expenseTotal': round(float(row['expense_total']), 2),
            'balance': round(float(row['balance']), 2),
            'recordCount': row['record_count'],
            'createdAt': str(row['created_at'] or '')[:19],
        }
        for row in rows
    ]
