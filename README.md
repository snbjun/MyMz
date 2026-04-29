# MyMz

MyMz 是一个本地单机部署的进销存 BS 系统。当前已完成项目骨架、真实登录、JWT 认证、初始化管理员账号、基础用户管理、客户管理、供应商管理、产品管理和库存管理；销售单、采购单等业务模块仍保持占位。

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

## 供应商模块

供应商模块入口：登录后左侧菜单 `供应商`，页面路径为 `http://localhost:8080/suppliers`。

当前供应商模块包含：

- 供应商分类列表、新增、编辑、软删除。
- 供应商列表、搜索、分类筛选、启用状态筛选、分页。
- 供应商新增、编辑、启用/禁用、软删除。
- 供应商金额字段：`opening_payable`、`current_payable`、`credit_limit` 后端使用 `Decimal / Numeric(18, 2)`，API 以字符串格式返回，避免前端浮点误差。

供应商接口均需要登录。当前阶段不包含采购单产生的应付自动计算，`current_payable` 仅作为供应商资料字段保存。

## 产品模块

产品模块入口：登录后左侧菜单 `产品`，页面路径为 `http://localhost:8080/products`。

当前产品模块包含：

- 产品分类列表、新增、编辑、软删除。
- 产品单位列表、新增、编辑、软删除。
- 产品列表、搜索、分类筛选、单位筛选、启用状态筛选、分页。
- 产品新增、编辑、启用/禁用、软删除。
- 产品金额字段：`sale_price`、`purchase_price`、`wholesale_price` 后端使用 `Decimal / Numeric(18, 2)`，API 以字符串格式返回，避免前端浮点误差。
- 产品数量字段：`stock_warning_qty` 后端使用 `Decimal / Numeric(18, 3)`，API 以字符串格式返回，支持小数数量。

产品接口均需要登录。当前阶段只实现产品档案，不包含库存数量、库存流水、图片上传、多规格 SKU，也不会在产品新增或编辑时修改库存。

## 库存模块

库存模块入口：登录后左侧菜单 `库存`，页面路径为 `http://localhost:8080/inventory`。

当前库存模块包含：

- 默认仓库查询，第一版初始化 `默认仓库`。
- 库存余额列表，支持关键词、产品分类、仓库和低库存筛选。
- 产品没有库存余额记录时，库存列表仍显示该产品，当前库存、平均成本和库存金额均为 0。
- 期初库存设置，支持期初数量、单位成本和备注。
- 库存调整，支持增加库存、减少库存、盘点设定库存。
- 库存流水查询，支持关键词、产品、仓库、流水类型、方向和日期范围筛选。

库存接口均需要登录。库存数量字段使用 `Decimal / Numeric(18, 3)`，成本字段使用 `Decimal / Numeric(18, 4)`，金额字段使用 `Decimal / Numeric(18, 2)`；API 统一以字符串格式返回，避免前端浮点误差。

期初库存规则：

- 同一产品、同一仓库已经存在库存流水后，不能再次设置期初库存。
- 期初数量可以为 0 或正数，不能为负数。
- 期初成本不能为负数。
- 期初数量大于 0 时创建 `initial` 库存流水；期初数量为 0 时只创建库存余额，不创建流水。

库存调整规则：

- `increase` 增加库存，生成 `adjustment_in` 入库流水。
- `decrease` 减少库存，生成 `adjustment_out` 出库流水。
- `set` 盘点设定库存，目标库存高于当前库存时生成 `stocktaking_gain`，低于当前库存时生成 `stocktaking_loss`，相等时不创建流水。
- 库存调整后不允许为负数。
- 所有库存写操作都在事务中同时更新库存余额和写入库存流水，不允许直接覆盖库存余额。

移动加权平均成本规则：

```text
new_avg_cost = (before_qty * before_avg_cost + in_qty * unit_cost) / after_qty
```

入库类调整如果传入单位成本则使用传入成本，否则使用产品采购价；出库类调整按当前平均成本计算出库金额。出库后库存为 0 时，本系统将平均成本归零，库存金额也归零。

当前阶段不包含销售单、采购单自动出入库，也不模拟销售或采购业务；后续单据模块会复用库存服务生成库存流水。

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
