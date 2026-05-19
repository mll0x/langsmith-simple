# LangSmith-Simple 技术栈

## 后端

### 语言与框架

| 类别 | 技术 | 版本要求 |
|------|------|----------|
| 语言 | Python | >=3.10 |
| Web 框架 | FastAPI | >=0.115.4 |
| ASGI 服务器 | Uvicorn | >=0.29.0 |
| 数据验证 | Pydantic v2 | >=2,<3 |
| 序列化 | orjson | >=3.9.14 |

### 数据存储

| 类别 | 技术 | 说明 |
|------|------|------|
| 主数据库 | PostgreSQL | traces / runs / datasets / feedback |
| 缓存 | Redis | 会话缓存、速率限制、任务队列 |
| 对象存储 | MinIO / S3 | trace 附件、大 payload |

### 中间件与工具

| 类别 | 技术 | 版本要求 | 说明 |
|------|------|----------|------|
| 异步 HTTP | httpx | >=0.23.0,<1 | 异步客户端通信 |
| 同步 HTTP | requests | >=2.0.0 | 同步客户端通信 |
| 压缩 | zstandard | >=0.23.0 | trace 数据压缩传输 |
| 哈希 | xxhash | >=3.0.0 | 数据指纹 |
| UUID | uuid-utils | >=0.12.0,<1.0 | 高性能 UUID 生成 |
| HTTP 工具 | requests-toolbelt | >=1.0.0 | multipart 上传 |
| 包管理 | packaging | >=23.2 | 版本号解析 |
| 任务队列 | Celery + Redis | - | 异步评估、批量操作 |
| ORM | SQLAlchemy 2.0 | - | 数据库操作层 |
| 数据库迁移 | Alembic | - | PostgreSQL schema 版本管理 |

### 可观测性集成

| 类别 | 技术 | 版本要求 |
|------|------|----------|
| OpenTelemetry SDK | opentelemetry-sdk | >=1.30.0 |
| OpenTelemetry API | opentelemetry-api | >=1.30.0 |
| OTLP Exporter | opentelemetry-exporter-otlp-proto-http | >=1.30.0 |

---

## 前端

### 语言与框架

| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | TypeScript | 严格类型 |
| UI 框架 | React | SPA |
| 构建 | Vite | 开发与打包 |
| 包管理 | pnpm | workspace monorepo |

### UI 组件与样式

| 类别 | 技术 | 说明 |
|------|------|------|
| 组件库 | shadcn/ui + Radix | 无障碍 + 可定制 |
| 样式 | Tailwind CSS | 实用优先 |
| 图表 | Recharts | trace 延迟、token 用量 |
| 代码高亮 | Shiki | JSON / Python 展示 |
| 树形组件 | 自定义 React Tree | Run trace 树形结构 |

### 数据与状态

| 类别 | 技术 | 说明 |
|------|------|------|
| 服务端状态 | TanStack Query | trace 列表、dataset 等服务端数据 |
| 客户端状态 | Zustand | UI 状态 |
| 路由 | React Router | SPA 路由 |

---

## SDK 层

| 类别 | Python SDK | JS SDK |
|------|-----------|--------|
| 语言 | Python 3.10+ | TypeScript |
| 包管理 | uv | pnpm |
| 构建 | hatchling | tsc + babel |
| 测试 | pytest + pytest-asyncio | vitest + jest |
| Lint | ruff + mypy | oxlint + oxfmt |
| HTTP | requests / httpx | fetch API |

---

## DevOps 与基础设施

| 类别 | 技术 | 说明 |
|------|------|------|
| 容器化 | Podman + Podman Compose | 本地开发环境 |
| CI/CD | GitHub Actions | 自动测试与发布 |
| API 规范 | OpenAPI 3.0 | 接口文档与代码生成 |
| 项目文档 | Mintlify | API 与使用文档 |
| 监控 | Prometheus + Grafana | 后端指标 |

---

## 包管理统一方案

| 层级 | 工具 | 配置文件 |
|------|------|----------|
| Python 后端 + SDK | uv | pyproject.toml + uv.lock |
| JS 前端 + SDK | pnpm | package.json + pnpm-lock.yaml |
| Python 虚拟环境 | uv venv | .python-version |
| Node 版本 | nvm / fnm | .node-version / .nvmrc |

---

## 核心数据模型

```
Workspace → Project → Run (trace)
                      ├── span (子 run)
                      ├── feedback
                      └── attachments

Dataset → Example → TestRun (evaluation)
                    └── feedback

Prompt → PromptVersion
```

---

## MVP 开发优先级

1. **Run/Trace 写入与查询** — LangSmith 核心功能
2. **Trace 树形展示** — 前端 span 可视化
3. **Dataset + 评估** — 离线评测能力
4. **Prompt 管理** — 版本化 prompt 存储
5. **Sandbox** — 安全执行环境（websockets>=15.0）
