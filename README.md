# LangSmith Simple

一个简化版 [LangSmith](https://smith.langchain.com/) 克隆，聚焦本地可运行的 **Trace 可视化**、**Playground** 和 **Deployments** 三大核心功能。

> 目标：本地运行后能看到 LLM 调用的 token 消耗、调用过程并调试，支持 LangGraph 应用的一键部署。

---

## 学习分支导航

本项目按实现阶段拆分为多个学习分支，建议按以下顺序学习：

| 分支 | 内容 | 学习重点 |
|------|------|---------|
| `master` | 完整代码 | 直接运行，查看最终效果 |
| `learn-01-infra` | 项目初始化 + 基础设施 | uv monorepo、docker-compose、SQLAlchemy 模型设计 |
| `learn-02-trace-api` | Trace 采集 API | FastAPI 路由设计、Pydantic Schema、与官方 SDK 兼容的协议 |
| `learn-03-trace-query` | Trace 查询 + 可视化 | 复杂 SQL 过滤、递归子 span 树、latency/token 计算 |
| `learn-04-realtime` | Redis pub/sub + SSE | 异步消息推送、SSE 长连接、前端实时更新 |
| `learn-05-playground` | Playground LLM 代理 | 多 Provider 路由、流式响应、异步 HTTP 代理 |
| `learn-06-deployments` | 本地部署管理 | subprocess 生命周期、端口分配、日志捕获、环境变量注入 |
| `learn-07-frontend` | React 前端完整实现 | TanStack Query、React Router、Tailwind v4 主题、SSE 消费 |
| `learn-08-sdk` | Python SDK | httpx 客户端、@traceable 装饰器、RunTree 上下文管理 |

**切换分支学习：**
```bash
git checkout learn-01-infra   # 只看基础设施
git checkout learn-02-trace-api  # 只看 Trace 采集
git checkout master           # 完整代码
```

---

## 功能特性

### Studio

| 功能 | 说明 |
|------|------|
| **Trace 采集** | 与官方 LangSmith SDK 线兼容，设 `LANGSMITH_ENDPOINT` 即可接入 |
| **Trace 查询** | 按项目、状态、类型、token 数过滤，支持父子 span 树展开 |
| **实时推送** | 通过 Redis pub/sub + SSE 实时推送新 trace |
| **Playground** | 多 Provider LLM Chat Completion（OpenAI / Anthropic / DeepSeek / Qwen），支持流式响应 |

### Deployments

| 功能 | 说明 |
|------|------|
| **本地部署** | 自动检测入口（`langgraph.json` / `main.py` / `app.py`），自动分配端口 |
| **生命周期管理** | 创建 / 启动 / 停止 / 删除 / 日志查看 |
| **Trace 回流** | 自动注入 `LANGSMITH_ENDPOINT`，部署的应用天然上报 trace |

---

## 技术栈

### Backend
- **FastAPI** — 异步 Web 框架
- **SQLAlchemy 2.0** + **asyncpg** — 异步 ORM
- **PostgreSQL 16** — 主数据库
- **Redis 7** — pub/sub 实时推送
- **Alembic** — 数据库迁移
- **httpx** — 异步 HTTP 客户端（Playground 代理）

### Frontend
- **Vite** + **React 19** + **TypeScript**
- **Tailwind CSS v4** — 样式
- **TanStack Query** — 数据获取
- **React Router** — 路由
- **Lucide React** — 图标

### SDK
- **Python 3.12+**
- **httpx** — HTTP 客户端
- **Pydantic v2** — 数据校验

---

## 项目结构

```
langsmith-simple/
├── backend/
│   ├── langsmith_simple/          # FastAPI 应用
│   │   ├── main.py                # 应用入口（FastAPI 实例创建、CORS、路由注册）
│   │   ├── config.py              # 配置（pydantic-settings，支持 .env 文件）
│   │   ├── database.py            # SQLAlchemy async 引擎 + session 工厂
│   │   ├── redis_client.py        # Redis pub/sub 客户端（发布 run 事件）
│   │   ├── models/                # SQLAlchemy 模型（5 张表）
│   │   │   ├── workspace.py       # 工作空间
│   │   │   ├── project.py         # 项目（属于工作空间）
│   │   │   ├── run.py             # Trace / Span 核心表（parent_run_id 自关联）
│   │   │   ├── feedback.py        # 反馈评分
│   │   │   └── deployment.py      # 部署实例（pid, port, command）
│   │   ├── schemas/               # Pydantic schemas（请求/响应校验）
│   │   │   ├── run.py             # RunCreate, RunUpdate, RunResponse
│   │   │   ├── project.py         # ProjectCreate, ProjectResponse
│   │   │   ├── playground.py      # CompletionRequest, ModelInfo
│   │   │   └── deployment.py      # DeploymentCreate, DeploymentUpdate, DeploymentResponse
│   │   ├── routers/               # API 路由（按资源拆分）
│   │   │   ├── runs.py            # Trace 采集 + 查询（POST/PATCH/GET/DELETE）
│   │   │   ├── projects.py        # 项目 CRUD
│   │   │   ├── playground.py      # LLM Chat Completion 代理
│   │   │   ├── deployments.py     # 部署 CRUD + 生命周期
│   │   │   └── stream.py          # SSE 实时推送端点
│   │   ├── services/              # 业务逻辑层
│   │   │   └── deployment_service.py  # 部署 CRUD + LocalDeploymentManager 编排
│   │   └── deployment/            # 本地部署管理器
│   │       └── local_manager.py   # 端口分配、入口检测、子进程启停、日志捕获
│   ├── migrations/                # Alembic 迁移
│   │   └── versions/481ea6b5b45d_initial.py  # 初始迁移（5 张表 + 索引）
│   ├── tests/                     # 测试（pytest）
│   │   ├── test_runs.py           # run CRUD、列表过滤、404
│   │   ├── test_projects.py       # 项目列表、创建
│   │   └── test_deployments.py    # 部署创建、列表、启动、停止、删除
│   ├── alembic.ini                # Alembic 配置
│   ├── pytest.ini                 # pytest 配置
│   └── pyproject.toml             # backend 依赖
├── frontend/
│   ├── src/
│   │   ├── api/client.ts          # 统一 fetch 封装（GET/POST/PATCH/DELETE）
│   │   ├── components/layout/     # 布局组件
│   │   │   └── AppLayout.tsx      # 侧边栏 + 品牌 + 导航
│   │   ├── pages/                 # 页面组件（React Router 对应路由）
│   │   │   ├── TraceListPage.tsx      # Trace 列表页（过滤、表格、分页）
│   │   │   ├── TraceDetailPage.tsx    # Trace 详情页（元数据、JSON、span 树）
│   │   │   ├── PlaygroundPage.tsx     # Playground 页（模型选择、消息编辑、流式响应）
│   │   │   └── DeploymentsPage.tsx    # 部署页（表格、创建、启停、日志）
│   │   ├── App.tsx                # 路由配置（/traces, /playground, /deployments）
│   │   ├── main.tsx               # React 入口（StrictMode + QueryClientProvider）
│   │   └── index.css              # Tailwind v4 @theme（暗色主题 token）
│   ├── vite.config.ts             # Vite 配置（proxy /api -> localhost:8000）
│   ├── package.json               # frontend 依赖
│   └── tsconfig.json              # TypeScript 配置
├── sdk/python/
│   ├── langsmith_simple_sdk/      # Python SDK
│   │   ├── __init__.py            # 导出 Client, RunTree, traceable
│   │   ├── client.py              # HTTP 客户端（create_run, update_run, batch, list）
│   │   ├── run_tree.py            # RunTree 上下文管理器（手动控制 span 嵌套）
│   │   └── traceable.py           # @traceable 装饰器（自动采集函数输入输出）
│   ├── tests/
│   │   ├── test_client.py         # 环境变量、create_run、update_run、batch、list
│   │   └── test_traceable.py      # 序列化、sync/async 装饰器
│   └── pyproject.toml             # SDK 依赖
├── infra/
│   └── docker-compose.yml         # PostgreSQL 16 + Redis 7
├── pyproject.toml                 # uv workspace root
├── .env.example                   # 环境变量模板
└── README.md                      # 本文件
```

---

## 快速开始

### 前置要求

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) — Python 包管理
- [Podman](https://podman.io/) 或 Docker
- pnpm / npm

### 1. 克隆并初始化

```bash
git clone <repo-url>
cd langsmith-simple

# 安装 Python 依赖
uv sync

# 安装前端依赖
cd frontend && npm install
```

### 2. 启动基础设施

```bash
# 启动 PostgreSQL + Redis
podman compose -f infra/docker-compose.yml up -d

# macOS 上如果 Podman machine 未运行：
# podman machine init
# podman machine start
```

### 3. 数据库迁移

```bash
cd backend
uv run alembic upgrade head
```

### 4. 启动后端

```bash
cd backend
uv run uvicorn langsmith_simple.main:app --reload --port 8000
```

后端将运行在 `http://localhost:8000`。

### 5. 启动前端

```bash
cd frontend
npm run dev
```

前端将运行在 `http://localhost:3000`（如果 3000 被占用会尝试其他端口），自动代理 `/api` 到 `http://localhost:8000`。

### 6. 验证

打开浏览器访问 `http://localhost:3000`，左侧导航栏可见 Traces / Playground / Deployments。

---

## 环境变量

### Backend

创建 `backend/.env`：

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/langsmith_simple
REDIS_URL=redis://localhost:6379/0
PORT=8000
API_KEY=local-dev-key
AUTH_ENABLED=false

# LLM Provider API Keys（Playground 用）
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=

# CORS（开发环境）
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Frontend

前端通过 Vite proxy 转发 `/api` 到后端，无需额外配置。如需修改代理目标，编辑 `frontend/vite.config.ts`。

---

## 核心数据流

```
┌─────────────┐     POST /runs      ┌──────────────┐
│  Your App   │ ──────────────────> │   Backend    │
│  + SDK      │                     │  FastAPI     │
└─────────────┘                     └──────┬───────┘
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                        ┌─────────┐  ┌─────────┐  ┌─────────┐
                        │PostgreSQL│  │  Redis  │  │SSE Stream│
                        └────┬────┘  └────┬────┘  └────┬────┘
                             │            │            │
                             ▼            ▼            ▼
                        ┌─────────┐  ┌─────────┐  ┌─────────┐
                        │ Trace   │  │ pub/sub │  │ Frontend │
                        │ Query   │  │ notify  │  │  React   │
                        └─────────┘  └─────────┘  └─────────┘
```

### Trace 写入流程

1. 用户代码调用 `client.create_run(...)` 或 `@traceable` 装饰的函数
2. SDK 通过 `httpx` 发送 `POST /api/v1/runs` 到后端
3. 后端将 run 写入 PostgreSQL `runs` 表
4. 后端通过 `redis_client.publish_run_event()` 发布到 Redis pub/sub
5. SSE 端点收到消息，推送给所有连接的浏览器
6. 前端 `TraceListPage` 实时更新列表

### Playground 流程

1. 用户在 PlaygroundPage 选择 Provider/Model，输入消息
2. 前端 `POST /api/v1/playground/completion`（`stream: true`）
3. 后端根据 `provider` 路由到对应的 LLM API（OpenAI / Anthropic / DeepSeek / Qwen）
4. 后端将 LLM 的流式响应逐 chunk 转发给前端
5. 前端手动解析 SSE chunk，逐字显示响应

### Deployment 流程

1. 用户在 DeploymentsPage 点击 "New Deployment"，填写 name + config_path
2. 后端创建 deployment 记录（status = created）
3. 用户点击 "Start"，后端调用 `LocalDeploymentManager.start()`
4. `start()` 检测入口文件（langgraph.json / main.py / app.py），分配空闲端口
5. 通过 `subprocess.Popen` 启动子进程，注入 `LANGSMITH_ENDPOINT` 环境变量
6. 子进程stdout/stderr捕获到日志文件
7. 部署的应用内如果使用了 LangChain/LangGraph，自动通过 `LANGSMITH_ENDPOINT` 上报 trace

---

## API 概览

### Trace

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/runs` | 创建 run |
| PATCH | `/api/v1/runs/{id}` | 更新 run |
| POST | `/api/v1/runs/batch` | 批量创建+更新 |
| GET | `/api/v1/runs` | 列表查询（支持过滤） |
| GET | `/api/v1/runs/{id}` | 单条 + 子 span 树 |
| DELETE | `/api/v1/runs/{id}` | 删除 |
| GET | `/api/v1/runs/stream` | SSE 实时推送 |

### Playground

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/v1/playground/models` | 可用模型列表 |
| POST | `/api/v1/playground/completion` | LLM Chat Completion（支持 stream） |

### Deployments

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/v1/deployments` | 列表 |
| POST | `/api/v1/deployments` | 创建 |
| GET | `/api/v1/deployments/{id}` | 详情 |
| PATCH | `/api/v1/deployments/{id}` | 更新 |
| DELETE | `/api/v1/deployments/{id}` | 删除 |
| POST | `/api/v1/deployments/{id}/start` | 启动 |
| POST | `/api/v1/deployments/{id}/stop` | 停止 |
| GET | `/api/v1/deployments/{id}/logs` | 日志（JSON） |
| GET | `/api/v1/deployments/{id}/logs/stream` | 日志（SSE） |

---

## SDK 使用

### 基础用法

```python
from langsmith_simple_sdk import Client

# 自动读取 LANGSMITH_ENDPOINT / LANGSMITH_API_KEY 环境变量
client = Client()

# 创建 run
run = client.create_run(
    name="my-chain",
    run_type="chain",
    inputs={"query": "Hello"},
)

# 更新 run
client.update_run(
    run_id=run["id"],
    outputs={"answer": "Hi there!"},
    status="success",
    total_tokens=42,
)
```

### 使用 @traceable 装饰器

```python
from langsmith_simple_sdk import traceable

@traceable(name="translate", run_type="chain")
def translate(text: str, target_lang: str) -> str:
    return f"[{target_lang}] {text}"

result = translate("hello", "zh")
# 自动创建 run，记录 inputs/outputs
```

### 使用 RunTree（手动控制）

```python
from langsmith_simple_sdk import RunTree

with RunTree(name="parent", run_type="chain", inputs={"x": 1}) as parent:
    child = parent.create_child("llm-call", run_type="llm", inputs={"prompt": "hi"})
    # ... 调用 LLM ...
    child.end(outputs={"response": "hello"}, total_tokens=10)
    parent.end(outputs={"result": "done"})
```

---

## Deployments 使用

### 1. 准备 LangGraph 应用

确保项目目录包含可识别的入口：
- `langgraph.json` → 自动执行 `langgraph dev --port PORT`
- `main.py` → 自动执行 `python main.py`
- `app.py` → 自动执行 `uvicorn app:app --port PORT --host 127.0.0.1`

### 2. 在 UI 中创建部署

1. 打开 `http://localhost:3000/deployments`
2. 点击 "New Deployment"
3. 填写：
   - **Name**: 任意名称
   - **Config path**: 项目目录绝对路径
   - **Command**: 可选，留空则自动检测
4. 点击 "Start" 启动

### 3. 验证

部署启动后，状态变为 `running`，URL 列显示可访问地址。部署的应用会自动上报 trace 到本地后端。

---

## 测试

### Backend

```bash
cd backend
uv run pytest tests/ -v
```

当前覆盖：
- `test_runs.py` — run CRUD、列表过滤、404
- `test_projects.py` — 项目列表、创建
- `test_deployments.py` — 部署创建、列表、启动、停止、删除

### SDK

```bash
cd sdk/python
uv run pytest tests/ -v
```

当前覆盖：
- `test_client.py` — 环境变量、create_run、update_run、batch、list
- `test_traceable.py` — 序列化、sync/async 装饰器

---

## 开发指南

### 添加新 migration

```bash
cd backend
uv run alembic revision --autogenerate -m "description"
```

### 代码风格

- **Backend**: ruff + mypy
- **Frontend**: TypeScript strict + Tailwind CSS
- **Commit**: 遵循 `<type>: <description>` 格式（feat, fix, refactor, docs, test）

---

## 部署到生产

### 使用 Podman/Docker

```bash
# 构建后端镜像
podman build -t langsmith-simple-backend -f infra/Dockerfile.backend .

# 构建前端镜像
podman build -t langsmith-simple-frontend -f infra/Dockerfile.frontend .

# 启动完整栈（backend + frontend + postgres + redis）
podman compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml up -d
```

### Fly.io（可选）

见 `infra/fly.toml` 模板。

---

## 路线图

- [x] Backend 骨架（FastAPI + SQLAlchemy + Alembic）
- [x] Trace 采集与查询（SDK 兼容）
- [x] Playground（多 Provider LLM 代理）
- [x] Deployments（本地子进程部署）
- [x] 前端（Vite + React + Tailwind）
- [x] 单元测试（Backend + SDK）
- [ ] 集成测试（端到端）
- [ ] 生产部署文档
- [ ] API Key 认证中间件

---

## License

MIT
