# 数据库设计

## 设计约定

- 数据库：SQLite，通过 SQLAlchemy 2.x 管理模型和 Alembic 迁移。
- 主键：默认使用 `INTEGER` 自增主键。
- 金额字段：统一使用 `NUMERIC(18, 2)`，业务层使用 `Decimal`，禁止 float。
- 数量字段：统一使用 `NUMERIC(18, 4)`，支持小数。
- 成本/单价字段：统一使用 `NUMERIC(18, 4)`，金额合计落 `NUMERIC(18, 2)`。
- 软删除：业务主表默认包含 `deleted_at DATETIME NULL`。
- 审计字段：主要业务表包含 `created_at`、`updated_at`、`created_by_id`、`updated_by_id`。
- 状态字段：使用短字符串枚举，如 `draft`、`confirmed`、`voided`。

## 用户与权限

### users

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| username | VARCHAR(64) | 是 | 无 | 登录名，唯一 |
| password_hash | VARCHAR(255) | 是 | 无 | 密码哈希 |
| full_name | VARCHAR(64) | 是 | 无 | 姓名 |
| phone | VARCHAR(32) | 否 | NULL | 手机号 |
| email | VARCHAR(128) | 否 | NULL | 邮箱 |
| gender | VARCHAR(16) | 否 | NULL | 性别 |
| is_active | BOOLEAN | 是 | 1 | 是否启用 |
| is_admin | BOOLEAN | 是 | 0 | 是否管理员 |
| created_at | DATETIME | 是 | 当前时间 | 创建时间 |
| updated_at | DATETIME | 是 | 当前时间 | 更新时间 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 主键：`id`
- 索引：`uq_users_username` 唯一索引；`idx_users_phone`

### roles

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| name | VARCHAR(64) | 是 | 无 | 角色名称，唯一 |
| description | VARCHAR(255) | 否 | NULL | 描述 |
| created_at | DATETIME | 是 | 当前时间 | 创建时间 |
| updated_at | DATETIME | 是 | 当前时间 | 更新时间 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 主键：`id`
- 索引：`uq_roles_name`

### permissions

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| code | VARCHAR(128) | 是 | 无 | 权限编码，唯一 |
| name | VARCHAR(64) | 是 | 无 | 权限名称 |
| module | VARCHAR(64) | 是 | 无 | 所属模块 |

- 主键：`id`
- 索引：`uq_permissions_code`、`idx_permissions_module`

### user_roles

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| user_id | INTEGER | 是 | 无 | 外键到 users.id |
| role_id | INTEGER | 是 | 无 | 外键到 roles.id |

- 主键：`user_id, role_id`
- 外键：`user_id -> users.id`、`role_id -> roles.id`

### role_permissions

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| role_id | INTEGER | 是 | 无 | 外键到 roles.id |
| permission_id | INTEGER | 是 | 无 | 外键到 permissions.id |

- 主键：`role_id, permission_id`
- 外键：`role_id -> roles.id`、`permission_id -> permissions.id`

## 客户与供应商

### customer_categories

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| name | VARCHAR(64) | 是 | 无 | 分类名称 |
| sort_order | INTEGER | 是 | 0 | 排序 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 索引：`uq_customer_categories_name`

### customers

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| name | VARCHAR(128) | 是 | 无 | 客户名称 |
| category_id | INTEGER | 否 | NULL | 外键到 customer_categories.id |
| opening_receivable | NUMERIC(18,2) | 是 | 0 | 期初应收，金额字段 |
| phone | VARCHAR(32) | 否 | NULL | 电话 |
| backup_phone | VARCHAR(32) | 否 | NULL | 备用电话 |
| fax | VARCHAR(64) | 否 | NULL | 传真 |
| email | VARCHAR(128) | 否 | NULL | 邮箱 |
| remark | TEXT | 否 | NULL | 备注 |
| is_active | BOOLEAN | 是 | 1 | 是否启用 |
| created_at | DATETIME | 是 | 当前时间 | 创建时间 |
| updated_at | DATETIME | 是 | 当前时间 | 更新时间 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 外键：`category_id -> customer_categories.id`
- 索引：`idx_customers_name`、`idx_customers_phone`、`idx_customers_category_id`

### customer_addresses

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| customer_id | INTEGER | 是 | 无 | 外键到 customers.id |
| contact_name | VARCHAR(64) | 否 | NULL | 联系人 |
| phone | VARCHAR(32) | 否 | NULL | 联系电话 |
| address | VARCHAR(255) | 是 | 无 | 地址 |
| is_default | BOOLEAN | 是 | 0 | 是否默认 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 外键：`customer_id -> customers.id`
- 索引：`idx_customer_addresses_customer_id`

### supplier_categories

字段同 `customer_categories`，分类名称唯一。

### suppliers

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| name | VARCHAR(128) | 是 | 无 | 供应商名称 |
| category_id | INTEGER | 否 | NULL | 外键到 supplier_categories.id |
| opening_payable | NUMERIC(18,2) | 是 | 0 | 期初应付，金额字段 |
| phone | VARCHAR(32) | 否 | NULL | 电话 |
| backup_phone | VARCHAR(32) | 否 | NULL | 备用电话 |
| fax | VARCHAR(64) | 否 | NULL | 传真 |
| email | VARCHAR(128) | 否 | NULL | 邮箱 |
| remark | TEXT | 否 | NULL | 备注 |
| is_active | BOOLEAN | 是 | 1 | 是否启用 |
| created_at | DATETIME | 是 | 当前时间 | 创建时间 |
| updated_at | DATETIME | 是 | 当前时间 | 更新时间 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 外键：`category_id -> supplier_categories.id`
- 索引：`idx_suppliers_name`、`idx_suppliers_phone`、`idx_suppliers_category_id`

### supplier_addresses

字段同 `customer_addresses`，`supplier_id -> suppliers.id`。

## 产品与库存

### products

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| name | VARCHAR(128) | 是 | 无 | 产品名称 |
| barcode | VARCHAR(64) | 否 | NULL | 条形码 |
| main_image_path | VARCHAR(255) | 否 | NULL | 主图路径 |
| tag_hot | BOOLEAN | 是 | 0 | 爆款 |
| tag_new | BOOLEAN | 是 | 0 | 新品 |
| tag_promotion | BOOLEAN | 是 | 0 | 促销 |
| remark | TEXT | 否 | NULL | 备注 |
| is_active | BOOLEAN | 是 | 1 | 是否启用 |
| created_at | DATETIME | 是 | 当前时间 | 创建时间 |
| updated_at | DATETIME | 是 | 当前时间 | 更新时间 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 索引：`idx_products_name`、`idx_products_barcode`

### product_specs

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| product_id | INTEGER | 是 | 无 | 外键到 products.id |
| spec_name | VARCHAR(128) | 是 | 默认规格 | 规格型号 |
| sale_price | NUMERIC(18,4) | 是 | 0 | 售价，金额相关字段 |
| purchase_price | NUMERIC(18,4) | 是 | 0 | 进价，金额相关字段 |
| stock_lower_limit | NUMERIC(18,4) | 是 | 0 | 库存下限，数量字段 |
| sort_order | INTEGER | 是 | 0 | 排序 |
| is_active | BOOLEAN | 是 | 1 | 是否启用 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 外键：`product_id -> products.id`
- 索引：`idx_product_specs_product_id`、`uq_product_specs_product_spec`

### inventory_balances

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| product_id | INTEGER | 是 | 无 | 外键到 products.id |
| product_spec_id | INTEGER | 是 | 无 | 外键到 product_specs.id |
| quantity | NUMERIC(18,4) | 是 | 0 | 当前库存，数量字段 |
| cost_avg | NUMERIC(18,4) | 是 | 0 | 成本均价 |
| updated_at | DATETIME | 是 | 当前时间 | 更新时间 |

- 外键：`product_id -> products.id`、`product_spec_id -> product_specs.id`
- 索引：`uq_inventory_balances_spec` 唯一索引 `product_spec_id`；`idx_inventory_balances_product_id`

### inventory_transactions

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| transaction_no | VARCHAR(64) | 是 | 无 | 流水号，唯一 |
| product_id | INTEGER | 是 | 无 | 外键到 products.id |
| product_spec_id | INTEGER | 是 | 无 | 外键到 product_specs.id |
| direction | VARCHAR(16) | 是 | 无 | `in` 或 `out` |
| quantity | NUMERIC(18,4) | 是 | 无 | 变动数量，数量字段 |
| before_quantity | NUMERIC(18,4) | 是 | 无 | 变动前数量 |
| after_quantity | NUMERIC(18,4) | 是 | 无 | 变动后数量 |
| unit_cost | NUMERIC(18,4) | 是 | 0 | 单位成本 |
| amount | NUMERIC(18,2) | 是 | 0 | 库存金额 |
| source_type | VARCHAR(32) | 是 | 无 | opening、sale、purchase、adjustment、void_reverse |
| source_id | INTEGER | 否 | NULL | 来源主表 ID |
| source_item_id | INTEGER | 否 | NULL | 来源明细 ID |
| occurred_at | DATETIME | 是 | 当前时间 | 发生时间 |
| remark | TEXT | 否 | NULL | 备注 |
| created_by_id | INTEGER | 否 | NULL | 操作人 |
| deleted_at | DATETIME | 否 | NULL | 软删除，原则上不删除 |

- 外键：`product_id -> products.id`、`product_spec_id -> product_specs.id`、`created_by_id -> users.id`
- 索引：`uq_inventory_transactions_no`、`idx_inventory_transactions_spec_time`、`idx_inventory_transactions_source`

## 销售

### sales_orders

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| order_no | VARCHAR(64) | 是 | 无 | 销售单号，唯一 |
| customer_id | INTEGER | 是 | 无 | 外键到 customers.id |
| order_date | DATE | 是 | 当前日期 | 销售日期 |
| planned_receipt_date | DATE | 否 | NULL | 计划收款日期 |
| delivery_date | DATE | 否 | NULL | 送货日期 |
| delivery_address_id | INTEGER | 否 | NULL | 客户地址 ID |
| status | VARCHAR(16) | 是 | draft | draft、confirmed、voided |
| delivery_status | VARCHAR(16) | 是 | not_delivered | 未送货/部分/全部 |
| receipt_status | VARCHAR(16) | 是 | unpaid | 未收/部分/全部/超收 |
| tax_rate | NUMERIC(9,4) | 是 | 0 | 税率 |
| product_amount | NUMERIC(18,2) | 是 | 0 | 产品金额，金额字段 |
| non_product_amount | NUMERIC(18,2) | 是 | 0 | 非产品费用，金额字段 |
| discount_amount | NUMERIC(18,2) | 是 | 0 | 优惠金额，金额字段 |
| total_amount | NUMERIC(18,2) | 是 | 0 | 合同金额，金额字段 |
| delivered_amount | NUMERIC(18,2) | 是 | 0 | 已送货金额，金额字段 |
| received_amount | NUMERIC(18,2) | 是 | 0 | 已收款，金额字段 |
| receivable_amount | NUMERIC(18,2) | 是 | 0 | 未收款，金额字段 |
| used_advance_amount | NUMERIC(18,2) | 是 | 0 | 使用预收款，金额字段 |
| remark | TEXT | 否 | NULL | 打印备注 |
| confirmed_at | DATETIME | 否 | NULL | 确认时间 |
| voided_at | DATETIME | 否 | NULL | 作废时间 |
| void_reason | TEXT | 否 | NULL | 作废原因 |
| created_at | DATETIME | 是 | 当前时间 | 创建时间 |
| updated_at | DATETIME | 是 | 当前时间 | 更新时间 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 外键：`customer_id -> customers.id`、`delivery_address_id -> customer_addresses.id`
- 索引：`uq_sales_orders_order_no`、`idx_sales_orders_customer_date`、`idx_sales_orders_status`

### sales_order_items

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| sales_order_id | INTEGER | 是 | 无 | 外键到 sales_orders.id |
| product_id | INTEGER | 是 | 无 | 外键到 products.id |
| product_spec_id | INTEGER | 是 | 无 | 外键到 product_specs.id |
| line_no | INTEGER | 是 | 无 | 行号 |
| quantity | NUMERIC(18,4) | 是 | 无 | 总数量，数量字段 |
| delivered_quantity | NUMERIC(18,4) | 是 | 0 | 送货数量，数量字段 |
| unit_price | NUMERIC(18,4) | 是 | 0 | 单价 |
| amount | NUMERIC(18,2) | 是 | 0 | 金额 |
| remark | TEXT | 否 | NULL | 备注 |

- 外键：`sales_order_id -> sales_orders.id`、`product_id -> products.id`、`product_spec_id -> product_specs.id`
- 索引：`idx_sales_order_items_order_id`、`idx_sales_order_items_spec_id`

## 采购

### purchase_orders

字段与 `sales_orders` 对称：

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| order_no | VARCHAR(64) | 是 | 无 | 采购单号，唯一 |
| supplier_id | INTEGER | 是 | 无 | 外键到 suppliers.id |
| order_date | DATE | 是 | 当前日期 | 采购日期 |
| planned_payment_date | DATE | 否 | NULL | 计划付款日期 |
| receive_date | DATE | 否 | NULL | 收货日期 |
| receive_address_id | INTEGER | 否 | NULL | 供应商地址 ID |
| status | VARCHAR(16) | 是 | draft | draft、confirmed、voided |
| receive_status | VARCHAR(16) | 是 | not_received | 未收货/部分/全部 |
| payment_status | VARCHAR(16) | 是 | unpaid | 未付/部分/全部/超付 |
| tax_rate | NUMERIC(9,4) | 是 | 0 | 税率 |
| product_amount | NUMERIC(18,2) | 是 | 0 | 产品金额 |
| non_product_amount | NUMERIC(18,2) | 是 | 0 | 非产品费用 |
| discount_amount | NUMERIC(18,2) | 是 | 0 | 优惠金额 |
| total_amount | NUMERIC(18,2) | 是 | 0 | 合同金额 |
| received_goods_amount | NUMERIC(18,2) | 是 | 0 | 已收货金额 |
| paid_amount | NUMERIC(18,2) | 是 | 0 | 已付款 |
| payable_amount | NUMERIC(18,2) | 是 | 0 | 未付款 |
| used_advance_amount | NUMERIC(18,2) | 是 | 0 | 使用预付款 |
| remark | TEXT | 否 | NULL | 打印备注 |
| confirmed_at | DATETIME | 否 | NULL | 确认时间 |
| voided_at | DATETIME | 否 | NULL | 作废时间 |
| void_reason | TEXT | 否 | NULL | 作废原因 |
| created_at | DATETIME | 是 | 当前时间 | 创建时间 |
| updated_at | DATETIME | 是 | 当前时间 | 更新时间 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 外键：`supplier_id -> suppliers.id`、`receive_address_id -> supplier_addresses.id`
- 索引：`uq_purchase_orders_order_no`、`idx_purchase_orders_supplier_date`、`idx_purchase_orders_status`

### purchase_order_items

字段与 `sales_order_items` 对称，额外将 `received_quantity` 作为收货数量。

- 外键：`purchase_order_id -> purchase_orders.id`、`product_id -> products.id`、`product_spec_id -> product_specs.id`
- 数量字段：`quantity NUMERIC(18,4)`、`received_quantity NUMERIC(18,4)`
- 金额字段：`unit_price NUMERIC(18,4)`、`amount NUMERIC(18,2)`

## 资金与收付款

### fund_accounts

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| name | VARCHAR(64) | 是 | 无 | 账户名称，如现金 |
| account_type | VARCHAR(32) | 是 | cash | cash、bank、other |
| opening_balance | NUMERIC(18,2) | 是 | 0 | 期初余额 |
| current_balance | NUMERIC(18,2) | 是 | 0 | 当前余额 |
| is_active | BOOLEAN | 是 | 1 | 是否启用 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 索引：`uq_fund_accounts_name`

### fund_transactions

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| transaction_no | VARCHAR(64) | 是 | 无 | 资金流水号，唯一 |
| direction | VARCHAR(16) | 是 | 无 | in、out |
| business_type | VARCHAR(32) | 是 | 无 | sales_receipt、purchase_payment、income、expense、advance、void_reverse |
| account_id | INTEGER | 是 | 无 | 外键到 fund_accounts.id |
| amount | NUMERIC(18,2) | 是 | 无 | 金额字段 |
| customer_id | INTEGER | 否 | NULL | 关联客户 |
| supplier_id | INTEGER | 否 | NULL | 关联供应商 |
| source_type | VARCHAR(32) | 否 | NULL | sales_order、purchase_order、expense_income、opening、void_reverse |
| source_id | INTEGER | 否 | NULL | 来源主表 ID |
| source_item_id | INTEGER | 否 | NULL | 来源明细 ID |
| occurred_at | DATETIME | 是 | 当前时间 | 发生时间 |
| remark | TEXT | 否 | NULL | 备注 |
| reverse_of_id | INTEGER | 否 | NULL | 反冲原流水 |
| created_by_id | INTEGER | 否 | NULL | 制单人 |
| deleted_at | DATETIME | 否 | NULL | 软删除，原则上不删除 |

- 外键：`account_id -> fund_accounts.id`、`customer_id -> customers.id`、`supplier_id -> suppliers.id`、`reverse_of_id -> fund_transactions.id`
- 索引：`uq_fund_transactions_no`、`idx_fund_transactions_account_time`、`idx_fund_transactions_source`

## 费用收入

### expense_income_categories

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| name | VARCHAR(64) | 是 | 无 | 类别名称 |
| direction | VARCHAR(16) | 是 | 无 | income、expense |
| parent_id | INTEGER | 否 | NULL | 上级类别 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 索引：`idx_expense_income_categories_direction`

### expense_income_records

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| record_no | VARCHAR(64) | 是 | 无 | 单号，唯一 |
| record_date | DATE | 是 | 当前日期 | 日期 |
| direction | VARCHAR(16) | 是 | 无 | income、expense |
| category_id | INTEGER | 是 | 无 | 外键到 expense_income_categories.id |
| account_id | INTEGER | 是 | 无 | 外键到 fund_accounts.id |
| amount | NUMERIC(18,2) | 是 | 无 | 金额字段 |
| fund_transaction_id | INTEGER | 否 | NULL | 生成的资金流水 |
| status | VARCHAR(16) | 是 | confirmed | confirmed、voided |
| remark | TEXT | 否 | NULL | 备注 |
| created_at | DATETIME | 是 | 当前时间 | 创建时间 |
| updated_at | DATETIME | 是 | 当前时间 | 更新时间 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 外键：`category_id -> expense_income_categories.id`、`account_id -> fund_accounts.id`、`fund_transaction_id -> fund_transactions.id`
- 索引：`uq_expense_income_records_no`、`idx_expense_income_records_date`

## 附件、打印、备份、日志

### attachments

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| owner_type | VARCHAR(32) | 是 | 无 | customer、supplier、product、sales_order、purchase_order、expense_income |
| owner_id | INTEGER | 是 | 无 | 业务对象 ID |
| file_name | VARCHAR(255) | 是 | 无 | 原文件名 |
| storage_path | VARCHAR(255) | 是 | 无 | 本地存储路径 |
| mime_type | VARCHAR(128) | 否 | NULL | 文件类型 |
| file_size | INTEGER | 是 | 0 | 文件大小 |
| uploaded_by_id | INTEGER | 否 | NULL | 上传人 |
| created_at | DATETIME | 是 | 当前时间 | 上传时间 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 索引：`idx_attachments_owner`

### print_templates

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| template_type | VARCHAR(32) | 是 | 无 | sales_order、purchase_order、report |
| name | VARCHAR(64) | 是 | 无 | 模板名称 |
| paper_size | VARCHAR(32) | 是 | A4 | 纸张 |
| config_json | TEXT | 是 | `{}` | 字段显示配置 |
| is_default | BOOLEAN | 是 | 0 | 是否默认 |
| deleted_at | DATETIME | 否 | NULL | 软删除 |

- 索引：`idx_print_templates_type`

### backup_records

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| file_path | VARCHAR(255) | 是 | 无 | 备份文件 |
| file_size | INTEGER | 是 | 0 | 文件大小 |
| backup_type | VARCHAR(16) | 是 | manual | manual、before_restore |
| status | VARCHAR(16) | 是 | success | success、failed |
| error_message | TEXT | 否 | NULL | 错误信息 |
| created_by_id | INTEGER | 否 | NULL | 操作人 |
| created_at | DATETIME | 是 | 当前时间 | 创建时间 |

- 索引：`idx_backup_records_created_at`

### operation_logs

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| occurred_at | DATETIME | 是 | 当前时间 | 操作时间 |
| user_id | INTEGER | 否 | NULL | 操作人 |
| ip_address | VARCHAR(64) | 否 | NULL | IP 地址 |
| location | VARCHAR(128) | 否 | NULL | 登录地点 |
| device | VARCHAR(255) | 否 | NULL | 设备类型 |
| action_type | VARCHAR(64) | 是 | 无 | 操作类型 |
| target_type | VARCHAR(64) | 否 | NULL | 业务类型 |
| target_id | INTEGER | 否 | NULL | 业务 ID |
| target_no | VARCHAR(64) | 否 | NULL | 业务单号 |
| detail | TEXT | 否 | NULL | 操作详情 |

- 索引：`idx_operation_logs_time`、`idx_operation_logs_user`、`idx_operation_logs_target`

### system_settings

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| id | INTEGER | 是 | 自增 | 主键 |
| setting_key | VARCHAR(128) | 是 | 无 | 配置键 |
| setting_value | TEXT | 否 | NULL | 配置值 |
| updated_at | DATETIME | 是 | 当前时间 | 更新时间 |

- 索引：`uq_system_settings_key`

## 核心关系

- `sales_orders -> sales_order_items`：一张销售单包含多条产品明细。
- `sales_orders -> fund_transactions`：销售确认或收款时生成资金收入流水，`source_type = sales_order`。
- `sales_order_items -> inventory_transactions`：送货数量大于 0 时生成库存出库流水，`source_type = sale`。
- `purchase_orders -> purchase_order_items`：一张采购单包含多条产品明细。
- `purchase_orders -> fund_transactions`：采购确认或付款时生成资金支出流水，`source_type = purchase_order`。
- `purchase_order_items -> inventory_transactions`：收货数量大于 0 时生成库存入库流水，`source_type = purchase`。
- `inventory_transactions -> inventory_balances`：每条库存流水更新对应产品规格的当前库存。
- `fund_transactions -> fund_accounts`：每条资金流水更新对应资金账户余额。
- 作废销售/采购单时不删除原流水，生成反向库存流水和反向资金流水，反向流水通过 `reverse_of_id` 或 `source_type = void_reverse` 追溯原业务。
