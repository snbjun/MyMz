# MyMz

MyMz 是一个本地单机部署的进销存 BS 系统。本阶段只初始化可运行项目骨架，包含 FastAPI 后端健康检查、Vue 3 前端静态登录页、后台主布局、占位菜单、数据目录和 Docker Compose。

## 技术栈

- Frontend: Vue 3、TypeScript、Vite、Element Plus、Vue Router、Pinia、Axios
- Backend: Python 3.12+、FastAPI、SQLAlchemy 2.x、Alembic、Pydantic、SQLite、Pytest
- Deployment: Docker Compose

## 目录说明

- `backend/`：FastAPI 后端项目
- `frontend/`：Vue 前端项目
- `data/app.db`：默认 SQLite 数据库文件，已被 `.gitignore` 排除
- `data/uploads/`：本地上传文件目录，目录内容默认不提交
- `data/backups/`：本地备份文件目录，目录内容默认不提交
- `docs/`：需求分析和设计文档
- `design_files/`：本地参考资料，禁止发布，已被 `.gitignore` 排除

## 本地开发启动

### 安装后端依赖

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

### 启动后端

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端健康检查地址：

```text
http://localhost:8000/api/health
```

### 安装前端依赖

```bash
cd frontend
npm install
```

### 启动前端

```bash
cd frontend
npm run dev
```

前端访问地址：

```text
http://localhost:8080
```

## Docker Compose 启动

```bash
docker compose up --build
```

启动后访问：

- 前端：`http://localhost:8080`
- 后端 API：`http://localhost:8000/api/health`

## 常用命令

### 运行后端测试

```bash
cd backend
pytest
```

### 前端构建

```bash
cd frontend
npm run build
```

### Docker 启动

```bash
docker compose up --build
```

## 数据文件

- 数据库文件默认位置：`data/app.db`
- 上传文件目录：`data/uploads/`
- 备份目录：`data/backups/`

这些本地运行数据不会提交到 GitHub。
