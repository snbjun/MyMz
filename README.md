# MyMz

MyMz 是一个本地单机部署的进销存 BS 系统。当前已完成项目骨架、真实登录、JWT 认证、初始化管理员账号、基础用户管理、客户管理、供应商管理、产品管理、库存管理、销售单管理和采购单管理；费用收入等业务模块仍保持占位。

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

## 销售单模块

销售单模块入口：登录后左侧菜单 `销售单`，页面路径为 `http://localhost:8080/sales-orders`。

当前销售单模块包含：

- 销售单列表、关键词搜索、客户筛选、单据状态筛选、送货状态筛选、收款状态筛选、日期筛选和分页。
- 销售单新增、草稿编辑、详情查看、确认、送货出库、收款和作废。
- 销售单明细会冗余保存产品名称、编号、条码、规格、型号和单位，避免产品档案变更影响历史单据。
- 销售单金额字段使用 `Decimal / Numeric(18, 2)`，数量字段使用 `Decimal / Numeric(18, 3)`；API 统一以字符串格式返回，避免前端浮点误差。

销售单接口均需要登录。销售单状态包括：

- `draft`：草稿，可编辑、确认或作废，不影响库存和客户应收。
- `confirmed`：已确认，不可编辑；确认时增加客户 `current_receivable`，但不自动扣减库存。
- `cancelled`：已作废，不能再编辑、确认、送货或收款。

送货出库规则：

- 只有已确认销售单可以送货。
- 每个送货明细都会复用库存服务生成 `sale_out` 库存流水，`source_type` 为 `sales_order`，`source_id` 为销售单 ID。
- 库存不足时禁止送货，送货数量不能超过该行未送数量。

收款规则：

- 只有已确认销售单可以收款。
- 收款会创建 `sales_payments` 记录，更新销售单已收、未收和收款状态，并减少客户 `current_receivable`。
- 第一版不生成资金账户流水，后续资金模块再扩展。

作废规则：

- 草稿销售单可以直接作废。
- 已确认且未收款的销售单可以作废，作废时减少客户未收应收。
- 已送货销售单作废时，会生成 `cancel_reverse` 入库流水冲回已出库数量。
- 第一版禁止作废已有收款的销售单。

当前阶段不包含正式打印模板；销售单详情页仅预留打印入口，点击后提示后续实现。

## 采购单模块

采购单模块入口：登录后左侧菜单 `采购单`，页面路径为 `http://localhost:8080/purchase-orders`。

当前采购单模块包含：

- 采购单列表、关键词搜索、供应商筛选、单据状态筛选、收货状态筛选、付款状态筛选、日期筛选和分页。
- 采购单新增、草稿编辑、详情查看、确认、收货入库、付款和作废。
- 采购单明细会冗余保存产品名称、编号、条码、规格、型号和单位，避免产品档案变更影响历史单据。
- 采购单金额字段使用 `Decimal / Numeric(18, 2)`，数量字段使用 `Decimal / Numeric(18, 3)`；API 统一以字符串格式返回，避免前端浮点误差。

采购单接口均需要登录。采购单状态包括：

- `draft`：草稿，可编辑、确认或作废，不影响库存和供应商应付。
- `confirmed`：已确认，不可编辑；确认时增加供应商 `current_payable`，但不自动增加库存。
- `cancelled`：已作废，不能再编辑、确认、收货或付款。

收货入库规则：

- 只有已确认采购单可以收货。
- 每个收货明细都会复用库存服务生成 `purchase_in` 库存流水，`source_type` 为 `purchase_order`，`source_id` 为采购单 ID。
- 入库单价使用采购明细单价，并按移动加权平均成本规则更新库存成本。
- 收货数量不能超过该行未收数量。

付款规则：

- 只有已确认采购单可以付款。
- 付款会创建 `purchase_payments` 记录，更新采购单已付、未付和付款状态，并减少供应商 `current_payable`。
- 第一版不生成资金账户流水，后续资金模块再扩展。

作废规则：

- 草稿采购单可以直接作废。
- 已确认且未付款的采购单可以作废，作废时减少供应商未付应付。
- 已收货采购单作废时，会生成 `cancel_reverse` 出库流水扣回已入库数量。
- 如果反冲会导致库存为负数，则禁止作废。
- 第一版禁止作废已有付款的采购单。

当前阶段不包含正式打印模板；采购单详情页仅预留打印入口，点击后提示后续实现。

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

## 费用收入模块

费用收入模块入口：登录后左侧菜单 `费用收入`，页面路径为 `http://localhost:8080/finance`。

当前费用收入模块包含：

- 收支流水列表、关键词搜索、类型筛选、分类筛选、账户筛选、状态筛选、日期筛选和分页。
- 手工新增收入、手工新增支出、查看流水详情和作废流水。
- 收支分类管理：新增、编辑、启用/禁用、软删除；收入和支出分类按类型分别维护，同一类型下名称不允许重复。
- 资金账户管理：新增、编辑、启用/禁用、软删除；账户名称未删除状态下不允许重复。
- 金额字段使用 `Decimal / Numeric(18, 2)`；API 统一以字符串格式返回，避免前端浮点误差。

收支流水接口均需要登录。新增流水规则：

- 收入流水会增加账户 `current_balance`。
- 支出流水会减少账户 `current_balance`。
- 第一版允许账户余额为负数，便于补录现金账或银行账，不因录入顺序阻塞业务。
- 分类必须存在、未删除、启用，且分类类型必须与流水类型一致。
- 账户必须存在、未删除、启用。
- 创建流水和更新账户余额在同一数据库事务中完成。

作废规则：

- 收支流水不物理删除，使用 `status=voided` 表示作废。
- 只有 `normal` 状态流水可以作废，已作废流水不能再次作废。
- 作废收入会减少账户余额；作废支出会增加账户余额。
- 作废流水和反向更新账户余额在同一数据库事务中完成。

账户规则：

- 新增账户时 `current_balance = opening_balance`。
- 账户已有流水后不允许修改期初余额。
- 账户已有正常或作废流水后不允许删除。
- 默认账户不允许删除或禁用。

本阶段不包含会计凭证、会计科目、税务处理，也不把销售收款、采购付款自动写入资金账户流水；后续可统一接入资金模块。

运行数据库迁移：

```bash
cd backend
alembic upgrade head
```

## 报表模块

报表模块入口：登录后左侧菜单 `报表`，页面路径为 `http://localhost:8080/reports`。报表接口均需要登录，接口路径以 `/api/reports` 开头，例如：

```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/api/reports/overview"
```

默认日期范围：

- 所有带日期范围的报表如果不传 `start_date` 和 `end_date`，默认统计当前自然月，即本月 1 日至今天。
- 销售报表按 `sales_orders.order_date` 过滤。
- 采购报表按 `purchase_orders.order_date` 过滤。
- 费用收入报表按 `finance_records.record_date` 过滤。
- 库存流水报表按 `stock_movements.created_at` 过滤。

销售统计口径：

- 只统计 `sales_orders.status = confirmed` 的销售单。
- 不统计 `draft` 和 `cancelled`。
- 销售金额使用销售单 `receivable_amount` 汇总。
- 产品销售金额使用 `sales_order_items.line_amount` 汇总。
- 已确认但未送货的销售单仍计入销售报表，库存出库情况由库存报表体现。

采购统计口径：

- 只统计 `purchase_orders.status = confirmed` 的采购单。
- 不统计 `draft` 和 `cancelled`。
- 采购金额使用采购单 `payable_amount` 汇总。
- 产品采购金额使用 `purchase_order_items.line_amount` 汇总。
- 已确认但未收货的采购单仍计入采购报表，库存入库情况由库存报表体现。

应收应付统计口径：

- 客户应收来源于 `customers.current_receivable`，只统计未删除客户。
- 供应商应付来源于 `suppliers.current_payable`，只统计未删除供应商。
- 第一版默认隐藏 0 余额，可通过 `include_zero=true` 查询 0 余额记录。

库存统计口径：

- 库存余额来源于 `inventory`，关联未删除产品。
- 库存金额使用 `inventory.total_cost` 汇总。
- 低库存产品按启用产品、`stock_warning_qty > 0` 且当前库存小于等于预警值统计。
- 库存流水按 `movement_type` 汇总入库/出库数量和金额。

资金统计口径：

- 账户余额来源于 `finance_accounts.current_balance`，只统计未删除账户。
- 收支统计只统计 `finance_records.status = normal` 的流水。
- 收支净额 = 收入合计 - 支出合计。

利润估算口径：

```text
毛利润 = 销售应收金额合计 - 采购应付金额合计
费用收入净额 = 其他收入合计 - 其他支出合计
估算净利润 = 毛利润 + 费用收入净额
```

说明：该利润是经营估算，不是严格会计利润。第一版不包含 Excel 导出、自定义报表设计器和复杂 BI 图表。

## 打印模块

打印模块入口来自销售单和采购单列表中的“打印”按钮，也可以直接访问：

- 销售单打印页面：`http://localhost:8080/sales-orders/{id}/print`
- 采购单打印页面：`http://localhost:8080/purchase-orders/{id}/print`

本阶段打印方式为 HTML/CSS 浏览器打印：

- 前端打印页使用 `window.print()` 调用浏览器打印。
- 使用 `@media print` 隐藏顶部工具栏。
- 使用 `@page` 设置 A4 纸张。
- 草稿、已确认、已作废单据均允许打印；已作废单据会显示“已作废”标记。

支持的打印配置字段：

- 模板名称 `template_name`
- 纸张尺寸 `paper_size`，第一版固定 A4
- 是否显示公司名称 `show_company_name`
- 公司名称 `company_name`
- 是否显示联系方式 `show_contact`
- 联系方式文本 `contact_text`
- 是否显示金额 `show_amount`
- 是否显示单价 `show_unit_price`
- 是否显示优惠 `show_discount`
- 是否显示备注 `show_remark`
- 是否显示签字栏 `show_signature`
- 页脚文字 `footer_text`

打印配置接口均需要登录。每种单据类型第一版维护一个默认配置：

- `sales_order`
- `purchase_order`

后端打印数据接口：

- `GET /api/print-settings`
- `GET /api/print-settings/{doc_type}`
- `PUT /api/print-settings/{doc_type}`
- `GET /api/print/sales-orders/{id}`
- `GET /api/print/purchase-orders/{id}`

本阶段不支持 PDF 生成、不支持复杂模板设计器、不支持套打坐标编辑、不支持批量打印，也没有引入重量级打印库。

运行打印配置迁移：

```bash
cd backend
alembic upgrade head
```

## 备份恢复模块

备份恢复页面路径：`http://localhost:8080/settings/backups`。所有备份恢复接口均需要登录，且只有超级管理员 `is_superuser = true` 可以操作；普通用户会被前端路由守卫拦截，后端也会返回无权限。

备份对象：

- SQLite 数据库文件，默认来自 `DATABASE_URL=sqlite:///../data/app.db`
- 上传文件目录，默认 `data/uploads/`

备份文件位置：

- 默认存放在 `data/backups/`
- Docker 部署时后端挂载 `./data:/app/data`，因此备份文件位于宿主机项目目录的 `data/backups/`
- `data/backups/*.zip` 已被 `.gitignore` 忽略，不会提交到 GitHub

备份文件格式：

- 文件名：`mymz-backup-YYYYMMDD-HHMMSS.zip`
- 恢复前安全备份文件名：`mymz-before-restore-YYYYMMDD-HHMMSS.zip`
- zip 内部结构：

```text
manifest.json
database/app.db
uploads/...
```

`manifest.json` 包含应用名称、备份版本、创建时间、数据库文件名、是否包含上传目录和备注。备份 zip 不包含绝对路径，不包含 `..` 路径，也不会包含 `data/backups/` 或 `design_files/`。

手动备份：

- 前端点击“创建备份”
- 或调用 `POST /api/backups`

下载和删除：

- 下载接口：`GET /api/backups/{filename}/download`
- 删除接口：`DELETE /api/backups/{filename}`
- 后端会限制文件必须位于 `data/backups/` 且必须是 `.zip`，防止路径穿越和误删其他文件

恢复流程：

1. 校验备份文件必须是 `data/backups/` 下的 `.zip`
2. 校验 zip 内部路径不能是绝对路径，不能包含 `..`
3. 校验必须包含 `manifest.json` 和 `database/app.db`
4. 自动创建一次当前数据的恢复前安全备份
5. 替换当前 SQLite 数据库文件
6. 替换 `data/uploads/` 目录内容
7. 返回恢复文件名和安全备份文件名

恢复是文件级恢复，运行中的 SQLite 连接可能仍持有旧状态；恢复完成后建议重启后端服务。本阶段不包含云备份、定时备份和上传 zip 恢复。

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
