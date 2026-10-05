# 校园记账 · 大学生收支管理系统

一个面向大学生的收支记录与可视化管理项目，**两个客户端共用同一份数据**：

| 版本 | 形态 | 技术栈 |
|---|---|---|
| 网页版 | 浏览器里打开的完整管理界面 | Flask + SQLite + Vue 3 + Element Plus + ECharts |
| 桌面悬浮版 | 常驻桌面置顶的小窗口，三个按钮切页 | PySide6（Qt） |

两个 exe 放在同一个文件夹里就会读写同一个 `money_schedule.db`，用哪个记都行，数据实时互通。

## 功能

- **记录收入 / 支出**：金额、类型（生活费 / 奖学金 / 兼职 / 餐饮 / 交通…）、日期、备注
- **总余额**：主界面显示当前总余额、累计收入、累计支出、本月收支
- **按时间范围查询**：起止日期 + 「今天 / 近 7 天 / 近 30 天 / 本月 / 全部」快捷选项，可按收入或支出筛选
- **收支趋势**：收入 / 支出双折线图，时间跨度超过 3 个月时自动按月聚合
- **定时查询**：每天 08:00 自动统计最近 30 天的收支并存成快照，可随时回看历史快照
- **删除记录**：录错了可以直接删掉

## 快速开始

### 方式一：直接用打包好的 exe（推荐）

到 [`dist/`](dist) 目录下载，双击即可，不需要装 Python 或 Node.js：

- `money_schedule.exe` — 网页版，启动后自动打开浏览器
- `money_schedule_widget.exe` — 桌面悬浮版，无控制台窗口

> 建议把两个 exe 放在**同一个文件夹**里，这样它们共用一份账本数据。
> 数据文件 `money_schedule.db` 会在首次运行时自动生成在 exe 同目录下；删掉它等于清空所有记录。

### 方式二：从源码运行

环境要求：Python 3.10+；只在需要重新构建前端时才需要 Node.js 18+。

```bash
# 1. 安装依赖
python -m venv .venv
.venv\Scripts\pip install -r backend\requirements.txt -r desktop\requirements.txt

# 2. 构建前端（产物输出到 backend/static）
cd frontend
npm install
npm run build
cd ..

# 3. 启动
.venv\Scripts\python backend\app.py     # 网页版，默认 http://127.0.0.1:5000
.venv\Scripts\python desktop\main.py    # 桌面悬浮版
```

网页版的端口如果被占用会自动往后顺延（本机 5000 被别的程序占用时会自动用 5001），启动时终端会打印实际地址。

### 重新打包成 exe

```bash
.venv\Scripts\python build.py
```

一条命令完成「编译前端 → 打包网页版 exe → 打包桌面悬浮版 exe」，产物在 `dist/`。

## 目录结构

```
money_schedule/
├─ backend/                 网页版后端（Flask）
│  ├─ app.py                  接口：汇总 / 记录增删查 / 趋势 / 定时快照
│  ├─ models.py               SQLite 数据模型
│  ├─ scheduler.py            每天 08:00 的定时统计任务
│  └─ requirements.txt
├─ frontend/                网页版前端（Vue 3 + Element Plus + Vite）
│  ├─ src/App.vue             主界面
│  ├─ src/api.js              接口封装
│  └─ src/components/         余额卡片 / 收支表单 / 记录表格 / 趋势图
├─ desktop/                 桌面悬浮版（PySide6）
│  ├─ main.py                 无边框置顶窗口、页面切换、定时任务
│  ├─ pages.py                主界面 + 收入 / 支出 / 查询三个界面
│  ├─ store.py                直连共用 SQLite 的数据层
│  ├─ trend_chart.py          自绘趋势折线图（不依赖 matplotlib）
│  ├─ anim.py                 按钮点击回弹动画
│  ├─ theme.py                配色与全局样式
│  └─ requirements.txt
├─ dist/                    打包产物（两个 exe）
├─ build.py                 一键构建脚本
└─ AGENT.md                 项目需求文档
```

## 实现要点

- **两个客户端共用数据**：桌面版用标准库 `sqlite3` 直连数据库，网页版走 Flask + SQLAlchemy，两边表结构保持一致，因此桌面版不需要启动后端服务也能记账。
- **定时查询**：用 APScheduler 的 cron 触发器每天 08:00 执行，把最近 30 天的收入 / 支出 / 结余写进 `scheduled_reports` 表；桌面版也可以点「立即统计一次」手动触发。
- **趋势图**：网页版用 ECharts，桌面版用 `QPainter` 自绘，避免把 matplotlib 打进 exe 拖大体积。
- **按钮点击动画**：按下时缩到 92%，松手时弹过原始大小（105%）再落回。缩放只发生在绘制层，控件的布局尺寸不变，所以按钮弹起来不会挤动旁边的按钮。
- **打包**：PyInstaller 单文件模式。前端构建产物通过 `--add-data` 打进网页版 exe；桌面版排除了 QtWebEngine 等用不到的重型模块以控制体积。

## 数据说明

- 数据库为本地单文件 SQLite，`*.db` 已在 `.gitignore` 中排除，**不会提交到仓库**，每台机器一份自己的账本。
- 所有金额记录只保存在本地，不涉及任何联网上传。
