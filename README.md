# MyMz

MyMz 是一个本地单机部署的进销存 BS 系统。当前已完成项目骨架、真实登录、JWT 认证、初始化管理员账号、基础用户管理和客户管理；供应商、产品、库存、销售单、采购单等业务模块仍保持占位。

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

## 默认管理员

- 默认用户名：`admin`
- 默认密码：`admin123456`
- 默认显示名：`系统管理员`

首次部署后请立即修改默认管理员密码。

可以通过环境变量修改默认管理员：

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123456
ADMIN_DISPLAY_NAME=系统管理员
```

登录地址：`http://localhost:8080/login`

用户管理入口：登录后左侧菜单 `用户管理`

## 客户模块

客户模块入口：登录后左侧菜单 `客户`，页面路径为 `http://localhost:8080/customers`。

当前客户模块包含：

- 客户分类列表、新增、编辑、软删除。
- 客户列表、搜索、分类筛选、启用状态筛选、分页。
- 客户新增、编辑、启用/禁用、软删除。
- 客户金额字段：`opening_receivable`、`current_receivable`、`credit_limit` 后端使用 `Decimal / Numeric(18, 2)`，API 以字符串格式返回，避免前端浮点误差。

客户接口均需要登录。当前阶段不包含销售单产生的应收自动计算，`current_receivable` 仅作为客户资料字段保存。

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
alembic upgrade head
python -m app.scripts.create_admin
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

### 运行数据库迁移

```bash
cd backend
alembic upgrade head
```

### 初始化管理员

```bash
cd backend
python -m app.scripts.create_admin
```

## Docker Compose 启动

```bash
docker compose up -d --build
```

启动后访问：

- 前端：`http://localhost:8080`
- 后端 API：`http://localhost:8000/api/health`

Docker Compose 启动后会自动执行数据库迁移并初始化默认管理员账号。

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
docker compose up -d --build
```

## 数据文件

- 数据库文件默认位置：`data/app.db`
- 上传文件目录：`data/uploads/`
- 备份目录：`data/backups/`

这些本地运行数据不会提交到 GitHub。
