"""一键构建脚本：编译前端 -> 打包成两个 exe

用法：.venv\\Scripts\\python.exe build.py
产物：
  dist/money_schedule.exe         网页版（Flask + Vue，自动打开浏览器）
  dist/money_schedule_widget.exe  桌面悬浮版（PySide6，常驻桌面）
两者共用同目录下的 money_schedule.db。
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, 'frontend')
BACKEND = os.path.join(ROOT, 'backend')
DESKTOP = os.path.join(ROOT, 'desktop')
STATIC = os.path.join(BACKEND, 'static')
DIST = os.path.join(ROOT, 'dist')
WORK = os.path.join(ROOT, 'build', 'pyinstaller')

# 桌面悬浮版用不到的重型 Qt 模块，排除以减小体积
DESKTOP_EXCLUDES = [
    'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtQml',
    'PySide6.QtQuick', 'PySide6.QtQuickWidgets', 'PySide6.Qt3DCore',
    'PySide6.QtMultimedia', 'PySide6.QtCharts', 'PySide6.QtPdf',
    'PySide6.QtSql', 'PySide6.QtDesigner', 'PySide6.QtTest',
    'tkinter', 'matplotlib', 'flask', 'flask_sqlalchemy',
]


def run(cmd, cwd):
    print('> ' + ' '.join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def npm():
    return 'npm.cmd' if sys.platform == 'win32' else 'npm'


def build_frontend():
    if not os.path.isdir(os.path.join(FRONTEND, 'node_modules')):
        run([npm(), 'install', '--no-audit', '--no-fund'], FRONTEND)
    run([npm(), 'run', 'build'], FRONTEND)
    if not os.path.isfile(os.path.join(STATIC, 'index.html')):
        raise SystemExit('前端构建失败：未找到 backend/static/index.html')


def build_exe(name, script, extra_args):
    args = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm', '--clean', '--onefile',
        '--name', name,
        '--distpath', DIST,
        '--workpath', os.path.join(WORK, name),
        '--specpath', os.path.join(ROOT, 'build'),
    ]
    args += extra_args
    args.append(script)
    run(args, ROOT)


def build_web_exe():
    build_exe('money_schedule', os.path.join(BACKEND, 'app.py'), [
        '--add-data', f'{STATIC}{os.pathsep}static',
        '--paths', BACKEND,
    ])


def build_desktop_exe():
    extra = ['--windowed', '--paths', DESKTOP]
    for module in DESKTOP_EXCLUDES:
        extra += ['--exclude-module', module]
    build_exe('money_schedule_widget', os.path.join(DESKTOP, 'main.py'), extra)


if __name__ == '__main__':
    suffix = '.exe' if sys.platform == 'win32' else ''
    build_frontend()
    build_web_exe()
    print(f'\n网页版完成：{os.path.join(DIST, "money_schedule" + suffix)}')
    build_desktop_exe()
    print(f'桌面悬浮版完成：{os.path.join(DIST, "money_schedule_widget" + suffix)}')
