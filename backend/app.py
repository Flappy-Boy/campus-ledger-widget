"""大学生收支管理系统 —— Flask 后端服务

启动后监听本地端口并打开浏览器，前端页面由 Flask 一并托管。
数据保存在程序同目录下的 money_schedule.db（SQLite）。
"""
import os
import socket
import sys
import threading
import webbrowser
from datetime import date, datetime, timedelta

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from models import (EXPENSE_CATEGORIES, INCOME_CATEGORIES, TYPE_EXPENSE,
                    TYPE_INCOME, Record, ScheduledReport, db)
from scheduler import QUERY_DAYS, get_next_run_time, init_scheduler, run_scheduled_query


def resource_path(*parts):
    """获取打包后仍可访问的资源路径"""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def data_dir():
    """数据文件所在目录：打包后为 exe 所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def parse_date(value, default=None):
    if not value:
        return default
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return default


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(data_dir(), 'money_schedule.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.json.ensure_ascii = False
    db.init_app(app)
    CORS(app)

    with app.app_context():
        db.create_all()

    # ---------------- 页面 ----------------
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def index(path):
        static_dir = resource_path('static')
        if path and os.path.isfile(os.path.join(static_dir, path)):
            return send_from_directory(static_dir, path)
        index_file = os.path.join(static_dir, 'index.html')
        if os.path.isfile(index_file):
            return send_from_directory(static_dir, 'index.html')
        return '<h3>前端未构建，请先执行 npm run build</h3>', 404

    # ---------------- 基础数据 ----------------
    @app.get('/api/categories')
    def categories():
        return jsonify({'income': INCOME_CATEGORIES, 'expense': EXPENSE_CATEGORIES})

    # ---------------- 汇总 ----------------
    @app.get('/api/summary')
    def summary():
        records = Record.query.all()
        income = sum(r.amount for r in records if r.type == TYPE_INCOME)
        expense = sum(r.amount for r in records if r.type == TYPE_EXPENSE)

        today = date.today()
        month_start = today.replace(day=1)
        today_records = [r for r in records if r.record_date == today]
        month_records = [r for r in records if month_start <= r.record_date <= today]

        def _sum(items, rtype):
            return round(sum(r.amount for r in items if r.type == rtype), 2)

        return jsonify({
            'income': round(income, 2),
            'expense': round(expense, 2),
            'balance': round(income - expense, 2),
            'recordCount': len(records),
            'today': {
                'income': _sum(today_records, TYPE_INCOME),
                'expense': _sum(today_records, TYPE_EXPENSE),
            },
            'month': {
                'income': _sum(month_records, TYPE_INCOME),
                'expense': _sum(month_records, TYPE_EXPENSE),
            },
        })

    # ---------------- 记录 ----------------
    @app.get('/api/records')
    def list_records():
        query = Record.query
        rtype = request.args.get('type')
        if rtype in (TYPE_INCOME, TYPE_EXPENSE):
            query = query.filter(Record.type == rtype)

        start = parse_date(request.args.get('start'))
        end = parse_date(request.args.get('end'))
        if start:
            query = query.filter(Record.record_date >= start)
        if end:
            query = query.filter(Record.record_date <= end)

        records = query.order_by(Record.record_date.desc(), Record.id.desc()).all()
        income = sum(r.amount for r in records if r.type == TYPE_INCOME)
        expense = sum(r.amount for r in records if r.type == TYPE_EXPENSE)

        return jsonify({
            'items': [r.to_dict() for r in records],
            'income': round(income, 2),
            'expense': round(expense, 2),
            'balance': round(income - expense, 2),
            'total': len(records),
        })

    @app.post('/api/records')
    def create_record():
        data = request.get_json(silent=True) or {}
        rtype = data.get('type')
        if rtype not in (TYPE_INCOME, TYPE_EXPENSE):
            return jsonify({'error': '记录类型必须是 income 或 expense'}), 400

        try:
            amount = round(float(data.get('amount')), 2)
        except (TypeError, ValueError):
            return jsonify({'error': '金额格式不正确'}), 400
        if amount <= 0:
            return jsonify({'error': '金额必须大于 0'}), 400

        valid_categories = INCOME_CATEGORIES if rtype == TYPE_INCOME else EXPENSE_CATEGORIES
        category = data.get('category') or '其他'
        if category not in valid_categories:
            return jsonify({'error': '类型不在可选范围内'}), 400

        record = Record(
            type=rtype,
            amount=amount,
            category=category,
            note=(data.get('note') or '').strip()[:200],
            record_date=parse_date(data.get('date'), date.today()),
            created_at=datetime.now(),
        )
        db.session.add(record)
        db.session.commit()
        return jsonify(record.to_dict()), 201

    @app.delete('/api/records/<int:record_id>')
    def delete_record(record_id):
        record = db.session.get(Record, record_id)
        if record is None:
            return jsonify({'error': '记录不存在'}), 404
        db.session.delete(record)
        db.session.commit()
        return jsonify({'success': True})

    # ---------------- 趋势 ----------------
    @app.get('/api/trend')
    def trend():
        start = parse_date(request.args.get('start'))
        end = parse_date(request.args.get('end'), date.today())

        query = Record.query
        if start:
            query = query.filter(Record.record_date >= start)
        if end:
            query = query.filter(Record.record_date <= end)
        records = query.order_by(Record.record_date).all()

        # 时间跨度超过 3 个月时按月份聚合，否则按天
        granularity = request.args.get('granularity')
        if granularity not in ('day', 'month'):
            span = (end - start).days if start else 0
            granularity = 'month' if span > 92 else 'day'

        buckets = {}
        for record in records:
            key = record.record_date.strftime('%Y-%m') if granularity == 'month' \
                else record.record_date.strftime('%Y-%m-%d')
            bucket = buckets.setdefault(key, {'income': 0.0, 'expense': 0.0})
            bucket[record.type] += record.amount

        labels = sorted(buckets.keys())
        return jsonify({
            'granularity': granularity,
            'labels': labels,
            'income': [round(buckets[k]['income'], 2) for k in labels],
            'expense': [round(buckets[k]['expense'], 2) for k in labels],
        })

    # ---------------- 定时查询 ----------------
    @app.get('/api/scheduled-reports')
    def scheduled_reports():
        limit = request.args.get('limit', 20, type=int)
        reports = ScheduledReport.query.order_by(ScheduledReport.created_at.desc()).limit(limit).all()
        return jsonify({
            'queryDays': QUERY_DAYS,
            'nextRunTime': get_next_run_time(),
            'items': [r.to_dict() for r in reports],
        })

    @app.post('/api/scheduled-reports/run')
    def trigger_scheduled_query():
        return jsonify(run_scheduled_query(app)), 201

    return app


def find_free_port(start_port=5000):
    for port in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port


def main():
    app = create_app()
    init_scheduler(app)

    port = find_free_port()
    url = f'http://127.0.0.1:{port}'
    print(f'大学生收支管理系统已启动：{url}')
    print(f'数据文件：{os.path.join(data_dir(), "money_schedule.db")}')
    if os.environ.get('MONEY_SCHEDULE_NO_BROWSER') != '1':
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
