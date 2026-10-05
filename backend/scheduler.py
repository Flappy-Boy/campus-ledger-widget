"""定时查询任务：每天 08:00 统计最近 30 天的收支情况并保存快照"""
from datetime import date, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from models import TYPE_EXPENSE, TYPE_INCOME, Record, ScheduledReport, db

# 定时统计的时间范围（天）
QUERY_DAYS = 30

_scheduler = None


def run_scheduled_query(app):
    """执行一次定时查询：统计最近 QUERY_DAYS 天的收入、支出与结余，返回快照字典"""
    with app.app_context():
        end = date.today()
        start = end - timedelta(days=QUERY_DAYS - 1)

        records = Record.query.filter(
            Record.record_date >= start, Record.record_date <= end
        ).all()

        income = sum(r.amount for r in records if r.type == TYPE_INCOME)
        expense = sum(r.amount for r in records if r.type == TYPE_EXPENSE)

        report = ScheduledReport(
            start_date=start,
            end_date=end,
            income_total=round(income, 2),
            expense_total=round(expense, 2),
            balance=round(income - expense, 2),
            record_count=len(records),
            created_at=datetime.now(),
        )
        db.session.add(report)
        db.session.commit()

        result = report.to_dict()
        print(f'[定时查询] {datetime.now():%Y-%m-%d %H:%M:%S} '
              f'近 {QUERY_DAYS} 天：收入 {income:.2f} / 支出 {expense:.2f} / 结余 {income - expense:.2f}')
        return result


def init_scheduler(app):
    """启动后台定时任务，每天 08:00 执行一次"""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
    _scheduler.add_job(
        run_scheduled_query,
        trigger='cron',
        hour=8,
        minute=0,
        id='daily_income_expense_query',
        args=[app],
        replace_existing=True,
    )
    _scheduler.start()
    print('[定时查询] 已启动，每天 08:00 自动统计最近 %d 天收支' % QUERY_DAYS)
    return _scheduler


def get_next_run_time():
    """返回下一次定时执行时间，未启动时返回 None"""
    if _scheduler is None:
        return None
    job = _scheduler.get_job('daily_income_expense_query')
    if job is None or job.next_run_time is None:
        return None
    return job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
