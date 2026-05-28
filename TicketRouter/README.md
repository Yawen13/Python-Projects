# TicketRouter — IT 智能报修台

一个 AI 驱动的设备报修工单管理系统。用户提交故障描述后，后端自动调用 DeepSeek AI 进行分类推理，生成标准化工单标签，共覆盖 9 大分类。工单存入 SQLite，前端提供工单大厅和管理员面板进行状态管理与统计分析。管理员还可一键获取 AI 生成的分步骤处理建议。

## 功能特性

- **AI 智能分类**：提交故障描述后自动推理分类标签（9 分类），规则优先——无关输入直接兜底不误判，有线索时才调 AI 精准分类
- **AI 处理建议**：管理员点击按钮即可获取分步骤排查方案，按需生成并缓存，不拖慢工单提交
- **工单大厅**：按时间倒序展示所有工单，9 种分类色彩标识和状态跟踪
- **管理员面板**：工单状态管理（待处理 / 处理中 / 已完成）、筛选和统计概览
- **工业工具感 UI**：完全自定义设计系统（OKLCH 色彩、DM Mono 等宽字体、交错动画），无第三方 CSS 框架依赖
- **轻量架构**：FastAPI + SQLite，单文件前端，无需额外配置即可运行

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python FastAPI |
| 数据库 | SQLite |
| AI 分类 + 建议 | DeepSeek API（兼容 OpenAI 接口） |
| 前端 | 纯 HTML/CSS/JS（无框架，自定义设计系统） |
| 字体 | DM Mono（Google Fonts）+ 系统中文字体栈 |

## 快速开始

### 1. 安装依赖

打开终端，先进入项目目录，再安装依赖：

```bash
cd E:\Python-Projects\TicketRouter
pip install -r requirements.txt
```

### 2. 启动服务

确保终端当前在项目目录下（`E:\Python-Projects\TicketRouter`），然后执行：

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

启动成功后会显示：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 3. 打开浏览器

访问 `http://127.0.0.1:8000/`

> **注意**：不要直接用浏览器打开 `frontend/index.html` 文件，必须通过上面的 uvicorn 服务地址访问，否则 API 请求会失败。

## 目录结构

```
TicketRouter/
├── backend/
│   ├── main.py           # FastAPI 应用，API 路由
│   ├── ai_classifier.py  # AI 分类 + AI 建议 + 规则回退
│   └── db.py             # SQLite 数据库操作
├── frontend/
│   └── index.html        # 单文件前端（自定义设计系统）
├── requirements.txt      # Python 依赖
└── README.md
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 前端页面 |
| `POST` | `/api/tickets` | 创建工单（自动 AI 分类） |
| `GET` | `/api/tickets` | 获取所有工单 |
| `PATCH` | `/api/tickets/{id}/status` | 更新工单状态 |
| `GET` | `/api/tickets/stats` | 获取分类/状态统计数据 |
| `GET` | `/api/tickets/{id}/suggestion` | 获取 AI 处理建议（首次生成并缓存） |

## 分类标签（9 类）

| 类别 | 色彩标识 | 典型场景 |
|------|----------|----------|
| 网络问题 | 蓝色 | 断网、Wi-Fi、VPN 掉线 |
| 硬件故障 | 红铜色 | 蓝屏、主板、风扇、打印机 |
| 软件异常 | 紫色 | 崩溃、卡顿、报错、打不开 |
| 账号权限 | 绿色 | 密码、登录、权限、锁定 |
| 电力照明 | 黄色 | 停电、灯不亮、跳闸 |
| 管道漏水 | 青色 | 漏水、水管、水龙头 |
| 门窗家具 | 棕色 | 门坏了、抽屉卡住、窗关不上 |
| 空调暖通 | 浅蓝 | 不制冷、温度异常、通风 |
| 其他问题 | 灰色 | 无法自动归类的兜底分类 |
