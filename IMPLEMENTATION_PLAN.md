# LangSmith-Simple 实现计划

## Context

用户希望构建一个简化版 LangSmith，聚焦 Studio（Trace 可视化 + Playground）和 Deployments（LangGraph 应用部署）两大功能。目标是本地运行后能看到 token 消耗和大模型调用过程并调试，后续可推到 Fly.io/Railway 部署。

---

## 项目结构

```
langsmith-simple/
├── pyproject.toml                    # uv workspace root
├── .python-version                   # 3.12
├── .node-version                     # 20
├── .env.example
├── .gitignore
├── TECH_STACK.md                     # 已存在
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 001_initial_schema.py
│   │       └── 002_deployments.py
│   └── langsmith_simple/
│       ├── __init__.py
│       ├── main.py                   # FastAPI app
│       ├── config.py                 # pydantic-settings
│       ├── database.py              # SQLAlchemy async
│       ├── dependencies.py          # DI
│       ├── models/
│       │   ├── workspace.py
│       │   ├── project.py
│       │   ├── run.py               # 核心模型
│       │   ├── feedback.py
│       │   └── deployment.py
│       ├── schemas/
│       │   ├── run.py
│       │   ├── project.py
│       │   ├── playground.py
│       │   └── deployment.py
│       ├── routers/
│       │   ├── runs.py             # Trace 写入 + 查询
│       │   ├── projects.py
│       │   ├── playground.py        # Playground 代理
│       │   ├── deployments.py
│       │   └── stream.py           # SSE 实时推送
│       ├── services/
│       │   ├── run_service.py
│       │   ├── playground_service.py
│       │   └── deployment_service.py
│       ├── llm/                    # LLM Provider 适配
│       │   ├── base.py
│       │   ├── openai_provider.py
│       │   ├── anthropic_provider.py
│       │   └── openai_compatible.py # DeepSeek/Qwen
│       └── deployment/
│           ├── local_manager.py    # 本地子进程部署
│           └── fly_deployer.py     # Fly.io 部署
│
├── sdk/
│   └── python/
│       ├── pyproject.toml
│       └── langsmith_simple_sdk/
│           ├── __init__.py
│           ├── client.py
│           ├── run_tree.py         # RunTree 手动 trace
│           └── traceable.py        # @traceable 装饰器
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── routes.tsx
│       ├── api/                    # TanStack Query hooks
│       ├── stores/                 # Zustand
│       ├── components/
│       │   ├── ui/                 # shadcn/ui
│       │   ├── layout/
│       │   ├── trace/              # Trace 可视化组件
│       │   ├── playground/         # Playground 组件
│       │   └── deployment/         # Deployments 组件
│       ├── pages/
│       └── types/
│
└── infra/
    ├── docker-compose.yml          # PostgreSQL + Redis
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    ├── fly.toml
    └── railway.json
```

---

## 核心 API 设计

### Trace 写入（与 LangSmith SDK 兼容）

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/runs` | 创建 run（trace root 或 span） |
| PATCH | `/api/v1/runs/{run_id}` | 更新 run（outputs/error/tokens） |
| POST | `/api/v1/runs/batch` | 批量创建+更新 |

### Trace 查询

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/v1/runs` | 列表，支持 project/status/latency/token 过滤 |
| GET | `/api/v1/runs/{run_id}` | 单条 trace + 子 span 树 |
| GET | `/api/v1/runs/stream` | SSE 实时推送 trace 更新 |

### Playground

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/playground/completions` | 流式 LLM 调用，自动记录为 trace |
| GET | `/api/v1/playground/models` | 可用模型列表 |

### Deployments

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/deployments` | 创建部署 |
| GET | `/api/v1/deployments` | 部署列表 |
| POST | `/api/v1/deployments/{id}/start` | 启动部署 |
| POST | `/api/v1/deployments/{id}/stop` | 停止部署 |
| GET | `/api/v1/deployments/{id}/logs` | 日志流（SSE） |

---

## 数据库 Schema

核心表：`workspaces` → `projects` → `runs`（trace 和 span 共用，`parent_run_id IS NULL` 为 trace 根）→ `feedback`

`runs` 表关键字段：
- `id`, `name`, `run_type`（chain/llm/tool/retriever/embedding）
- `parent_run_id`（null=trace root）
- `status`（running/success/error）
- `inputs`/`outputs`/`error`/`extra`（JSONB）
- `prompt_tokens`, `completion_tokens`, `total_tokens`
- `prompt_cost`, `completion_cost`（NUMERIC，后端按模型价格表计算）
- `start_time`, `end_time`, `first_token_at`

`deployments` 表：`id`, `name`, `config_path`, `source_type`（local/fly）, `status`, `container_id`, `container_url`, `port`, `env_vars`（JSONB）

---

## 关键设计决策

1. **SDK 线兼容** — runs API 端点与官方 LangSmith SDK 的 HTTP 协议一致，用户只需设 `LANGSMITH_ENDPOINT=http://localhost:8000/api/v1` 即可接入
2. **单 runs 表** — trace 和 span 共用一张表，通过 `parent_run_id` 区分
3. **SSE 实时推送** — 通过 Redis pub/sub 解耦写入和推送，前端用 SSE 消费
4. **本地子进程部署** — MVP 用 `uv run langgraph dev` 子进程，生产用 Podman 构建 + Fly.io 部署
5. **自动 trace 注入** — 部署时注入 `LANGSMITH_ENDPOINT`/`LANGSMITH_API_KEY` 环境变量，LangGraph 内部的 langsmith SDK 自动上报
6. **成本计算在后端** — SDK 上报 token 数，后端按硬编码价格表计算 cost

---

## 实现阶段

### Phase 1: 基础设施 (3 天)

1. 初始化 monorepo：`pyproject.toml`（uv workspace）、`pnpm-workspace.yaml`、`.gitignore`、`.env.example`
2. 写 `infra/docker-compose.yml`（PostgreSQL 16 + Redis 7）
3. 创建 `backend/pyproject.toml` 并 `uv sync`
4. 写 `config.py`（pydantic-settings）、`database.py`（async SQLAlchemy）、`main.py`（FastAPI + CORS）
5. 写 SQLAlchemy models：`workspace.py`, `project.py`, `run.py`
6. 写 Alembic 迁移 `001_initial_schema.py` 并执行
7. 写 `routers/runs.py`（POST /runs, PATCH /runs/{id}）
8. 写 `routers/projects.py`（GET/POST /projects）
9. 写 `sdk/python/` 的 Client、RunTree、@traceable
10. **验证**：SDK 发送 trace → PostgreSQL 中可查到

### Phase 2: Trace 可视化 (4 天)

1. 初始化前端：Vite + React + TS + Tailwind + shadcn/ui
2. React Router 路由配置 + AppLayout（侧边栏导航）
3. TanStack Query API 客户端
4. `TraceListPage`：过滤栏（project/status/latency/tokens）+ trace 表格 + 分页
5. `TraceDetailPage`：SpanTree（Gantt 式时间条）+ SpanDetailPanel（JSON viewer + token 图表）
6. 后端 GET /runs 过滤查询 + GET /runs/{id} 递归加载子 span
7. SSE 端点 GET /runs/stream（Redis pub/sub）
8. 前端 SSE hook 接入实时更新
9. **验证**：SDK 发 trace → UI 实时出现 → 点击查看 span 树 + token 详情

### Phase 3: Playground (3 天)

1. 写 LLM Provider 抽象层 + OpenAI/Anthropic/OpenAI-compatible 适配
2. 写 `routers/playground.py`（POST /playground/completions 流式响应，自动创建 trace）
3. 写 `GET /playground/models` 返回可用模型列表
4. 前端 `PlaygroundPage`：ModelSelector + PromptEditor + ParamControls + StreamingResponse
5. RunComparison 侧边对比
6. **验证**：选模型 → 输入 prompt → 流式响应 → trace 列表中可见 → 对比两次运行

### Phase 4: Deployments (4 天)

1. 写 deployment model + Alembic 迁移 `002_deployments.py`
2. 写 `LocalDeploymentManager`：start（找端口 + uv 构建 + 子进程启动）、stop、get_logs
3. 写 `routers/deployments.py` 完整 CRUD
4. 前端 `DeploymentsPage` + `DeploymentDetailPage`（状态 + 日志 + 操作按钮）
5. 自动 trace 注入（环境变量）
6. **验证**：创建 LangGraph 应用 → 部署 → 访问 localhost:PORT → trace 回流到 UI

### Phase 5: 打磨 + 生产部署 (3 天)

1. Dockerfile.backend + Dockerfile.frontend（多阶段构建）
2. 完整 `docker-compose.yml`（backend + frontend + postgres + redis）
3. FlyDeployer（Podman 构建 + Fly.io 推送）
4. `fly.toml` + `railway.json`
5. API Key 认证中间件
6. README.md
7. **验证**：`podman compose up` → 访问 http://localhost:3000 全流程可用

---

## 本地运行方式

```bash
# 1. 基础设施
podman compose up -d postgres redis

# 2. 后端
cd backend && uv sync && uv run alembic upgrade head
uv run uvicorn langsmith_simple.main:app --reload --port 8000

# 3. 前端
cd frontend && pnpm install && pnpm dev  # :3000，代理 /api 到 :8000

# 4. 测试 SDK
cd sdk/python && uv sync
uv run python -c "from langsmith_simple_sdk import Client; c = Client(); c.create_run(name='test', run_type='chain', inputs={'x': 1})"
```
