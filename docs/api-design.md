# REST API 设计

## 通用约定

- API 前缀：`/api/v1`
- 认证：除登录接口外均需要 Bearer Token。
- 分页参数：`page` 默认 1，`page_size` 默认 20。
- 列表响应结构：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

- 错误响应结构：

```json
{
  "detail": "错误说明",
  "code": "BUSINESS_ERROR"
}
```

- 金额请求和响应使用字符串，避免前端浮点误差，例如 `"123.45"`。
- 数量请求和响应使用字符串，例如 `"12.5000"`。

## 登录与用户

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/auth/login` | POST | `username`、`password` | `access_token`、`token_type`、`user` | 用户存在、密码正确、未禁用 | 否 |
| `/auth/me` | GET | 无 | 当前用户、角色、权限 | Token 有效 | 否 |
| `/auth/logout` | POST | 无 | `success` | Token 有效 | 否 |
| `/users` | GET | `keyword`、`page`、`page_size` | 用户分页列表 | 需要用户查看权限 | 否 |
| `/users` | POST | 用户名、密码、姓名、手机号、邮箱、角色 | 用户详情 | 用户名唯一、密码强度、手机号格式 | 是 |
| `/users/{id}` | GET | 路径 ID | 用户详情 | 用户存在 | 否 |
| `/users/{id}` | PUT | 姓名、手机号、邮箱、性别、状态、角色 | 用户详情 | 用户存在、不能禁用最后一个管理员 | 是 |
| `/users/{id}/reset-password` | POST | `password` | `success` | 密码强度 | 是 |
| `/roles` | GET | `keyword` | 角色列表 | 需要权限 | 否 |
| `/roles` | POST | `name`、`description`、`permission_ids` | 角色详情 | 名称唯一 | 是 |
| `/roles/{id}` | PUT | 名称、描述、权限 | 角色详情 | 角色存在 | 是 |
| `/permissions` | GET | 无 | 权限树 | 登录有效 | 否 |

## 客户

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/customers` | GET | `keyword`、`category_id`、`page`、`page_size` | 客户分页，含应收汇总 | 需要客户查看权限 | 否 |
| `/customers` | POST | 客户表单、地址、附件 ID | 客户详情 | 客户名称必填、期初欠款为 Decimal | 是 |
| `/customers/{id}` | GET | 路径 ID | 客户详情、地址、附件 | 客户存在 | 否 |
| `/customers/{id}` | PUT | 客户表单、地址 | 客户详情 | 客户存在、金额格式正确 | 是 |
| `/customers/{id}` | DELETE | 无 | `success` | 无未作废单据时才允许删除或改为停用 | 是 |
| `/customer-categories` | GET | 无 | 分类列表 | 登录有效 | 否 |
| `/customer-categories` | POST | `name` | 分类详情 | 名称唯一 | 是 |

## 供应商

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/suppliers` | GET | `keyword`、`category_id`、`page`、`page_size` | 供应商分页，含应付汇总 | 需要供应商查看权限 | 否 |
| `/suppliers` | POST | 供应商表单、地址、附件 ID | 供应商详情 | 供应商名称必填、期初欠款为 Decimal | 是 |
| `/suppliers/{id}` | GET | 路径 ID | 供应商详情、地址、附件 | 供应商存在 | 否 |
| `/suppliers/{id}` | PUT | 供应商表单、地址 | 供应商详情 | 供应商存在、金额格式正确 | 是 |
| `/suppliers/{id}` | DELETE | 无 | `success` | 无未作废单据时才允许删除或改为停用 | 是 |
| `/supplier-categories` | GET | 无 | 分类列表 | 登录有效 | 否 |
| `/supplier-categories` | POST | `name` | 分类详情 | 名称唯一 | 是 |

## 产品

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/products` | GET | `keyword`、`barcode`、`page`、`page_size` | 产品分页 | 需要产品查看权限 | 否 |
| `/products` | POST | 产品表单、规格数组、附件 ID | 产品详情 | 产品名称必填、规格数量至少 1、价格非负 | 是 |
| `/products/{id}` | GET | 路径 ID | 产品详情、规格、库存 | 产品存在 | 否 |
| `/products/{id}` | PUT | 产品表单、规格数组 | 产品详情 | 产品存在、已使用规格不能直接删除 | 是 |
| `/products/{id}` | DELETE | 无 | `success` | 有库存或单据引用时改为停用 | 是 |
| `/products/barcode/{barcode}` | GET | 条形码 | 产品规格候选 | 条形码存在 | 否 |

## 库存

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/inventory` | GET | `keyword`、`low_stock`、`page`、`page_size` | 库存分页 | 需要库存查看权限 | 否 |
| `/inventory/transactions` | GET | `product_id`、`spec_id`、`source_type`、日期范围 | 库存流水分页 | 登录有效 | 否 |
| `/inventory/opening` | POST | `items[{product_spec_id, quantity, unit_cost}]` | 生成的流水 | 数量非负、规格存在 | 是 |
| `/inventory/adjustments` | POST | `items[{product_spec_id, actual_quantity, reason}]` | 调整结果 | 必填原因、数量非负 | 是 |
| `/inventory/export` | POST | 查询条件 | 导出任务 | 需要导出权限 | 否 |

## 销售单

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/sales-orders` | GET | 客户、单号、日期、收款状态、送货状态、状态、分页 | 销售单分页 | 需要销售查看权限 | 否 |
| `/sales-orders` | POST | 表头、明细、收款明细、附件 ID、`save_as_draft` | 销售单详情 | 客户有效、明细数量和金额合法 | 是 |
| `/sales-orders/{id}` | GET | 路径 ID | 销售单详情、明细、收款、附件 | 单据存在 | 否 |
| `/sales-orders/{id}` | PUT | 表头、明细、收款明细 | 销售单详情 | 仅草稿可直接编辑 | 是 |
| `/sales-orders/{id}/confirm` | POST | 无或确认参数 | 销售单详情 | 草稿状态、库存充足、金额合法 | 是 |
| `/sales-orders/{id}/void` | POST | `reason` | 销售单详情 | 已确认且未作废、原因必填 | 是 |
| `/sales-orders/{id}/print-preview` | POST | 打印配置 | HTML/打印数据 | 单据存在 | 否 |
| `/sales-orders/import` | POST | 上传文件 | 导入结果 | 模板格式正确 | 是 |
| `/sales-orders/export` | POST | 查询条件 | 导出任务 | 需要导出权限 | 否 |

销售单详情响应建议：

```json
{
  "id": 1,
  "order_no": "XS202604290001",
  "status": "confirmed",
  "customer": {},
  "items": [],
  "receipts": [],
  "totals": {
    "total_amount": "0.00",
    "received_amount": "0.00",
    "receivable_amount": "0.00"
  }
}
```

## 采购单

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/purchase-orders` | GET | 供应商、单号、日期、付款状态、收货状态、状态、分页 | 采购单分页 | 需要采购查看权限 | 否 |
| `/purchase-orders` | POST | 表头、明细、付款明细、附件 ID、`save_as_draft` | 采购单详情 | 供应商有效、明细数量和金额合法 | 是 |
| `/purchase-orders/{id}` | GET | 路径 ID | 采购单详情、明细、付款、附件 | 单据存在 | 否 |
| `/purchase-orders/{id}` | PUT | 表头、明细、付款明细 | 采购单详情 | 仅草稿可直接编辑 | 是 |
| `/purchase-orders/{id}/confirm` | POST | 无或确认参数 | 采购单详情 | 草稿状态、金额合法 | 是 |
| `/purchase-orders/{id}/void` | POST | `reason` | 采购单详情 | 已确认且未作废、原因必填 | 是 |
| `/purchase-orders/{id}/print-preview` | POST | 打印配置 | HTML/打印数据 | 单据存在 | 否 |
| `/purchase-orders/import` | POST | 上传文件 | 导入结果 | 模板格式正确 | 是 |
| `/purchase-orders/export` | POST | 查询条件 | 导出任务 | 需要导出权限 | 否 |

## 收款付款与资金账户

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/fund-accounts` | GET | 无 | 账户列表 | 登录有效 | 否 |
| `/fund-accounts` | POST | 名称、类型、期初余额 | 账户详情 | 名称唯一、余额为 Decimal | 是 |
| `/fund-accounts/{id}` | PUT | 名称、状态 | 账户详情 | 账户存在 | 是 |
| `/fund-transactions` | GET | 日期、账户、方向、业务类型、分页 | 资金流水分页 | 需要资金查看权限 | 否 |
| `/sales-orders/{id}/receipts` | POST | 收款日期、金额、账户、备注 | 收款结果 | 销售单已确认、金额大于 0 | 是 |
| `/purchase-orders/{id}/payments` | POST | 付款日期、金额、账户、备注 | 付款结果 | 采购单已确认、金额大于 0 | 是 |

## 费用收入

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/expense-income` | GET | 单号、日期、方向、类别、账户、分页 | 费用收入分页 | 需要查看权限 | 否 |
| `/expense-income` | POST | 日期、方向、类别、账户、金额、备注、附件 ID | 记录详情 | 金额大于 0、账户有效、类别方向匹配 | 是 |
| `/expense-income/{id}` | GET | 路径 ID | 记录详情 | 记录存在 | 否 |
| `/expense-income/{id}` | PUT | 日期、类别、账户、金额、备注 | 记录详情 | 未作废才可编辑 | 是 |
| `/expense-income/{id}/void` | POST | `reason` | 作废结果 | 未作废、原因必填 | 是 |
| `/expense-income-categories` | GET | `direction` | 类别列表 | 登录有效 | 否 |
| `/expense-income-categories` | POST | 名称、方向、上级 | 类别详情 | 名称合法 | 是 |

## 报表

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/reports/sales-flow` | GET | 日期、客户、产品、分页 | 销售流水 | 日期范围合法 | 否 |
| `/reports/purchase-flow` | GET | 日期、供应商、产品、分页 | 采购流水 | 日期范围合法 | 否 |
| `/reports/product-sales` | GET | 日期、产品、分页 | 产品销售总览 | 日期范围合法 | 否 |
| `/reports/delivery-reminders` | GET | 日期、客户、分页 | 送货提醒 | 日期范围合法 | 否 |
| `/reports/receive-reminders` | GET | 日期、供应商、分页 | 收货提醒 | 日期范围合法 | 否 |
| `/reports/customer-debts` | GET | 日期、客户、分页 | 销售欠款汇总 | 日期范围合法 | 否 |
| `/reports/supplier-payables` | GET | 日期、供应商、分页 | 采购付款汇总 | 日期范围合法 | 否 |
| `/reports/fund-flow` | GET | 日期、账户、方向、分页 | 资金流水表 | 日期范围合法 | 否 |
| `/reports/profit` | GET | 日期、分页 | 净利润报表 | 日期范围合法 | 否 |
| `/reports/export` | POST | `report_type`、查询条件 | 导出任务 | 报表类型合法 | 否 |

## 打印

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/print-templates` | GET | `template_type` | 模板列表 | 登录有效 | 否 |
| `/print-templates` | POST | 模板名称、类型、纸张、配置 | 模板详情 | 类型合法、配置 JSON 合法 | 是 |
| `/print-templates/{id}` | PUT | 模板名称、纸张、配置、默认状态 | 模板详情 | 模板存在 | 是 |
| `/print/sales-orders/{id}` | POST | 模板 ID、临时配置 | 打印数据/HTML | 单据存在 | 否 |
| `/print/purchase-orders/{id}` | POST | 模板 ID、临时配置 | 打印数据/HTML | 单据存在 | 否 |

## 附件

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/attachments` | POST | 文件、`owner_type`、`owner_id` 可选 | 附件详情 | 文件大小、扩展名、MIME | 是 |
| `/attachments/{id}/download` | GET | 路径 ID | 文件流 | 有权限、文件存在 | 否 |
| `/attachments/{id}` | DELETE | 路径 ID | `success` | 附件存在 | 是 |

## 数据备份

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/backups` | GET | 分页 | 备份记录列表 | 管理员 | 否 |
| `/backups` | POST | 无 | 备份记录 | 管理员 | 否 |
| `/backups/{id}/download` | GET | 路径 ID | 文件流 | 管理员、文件存在 | 否 |
| `/backups/{id}/restore` | POST | 确认参数 | 恢复结果 | 管理员、恢复前自动备份 | 是 |

## 系统设置与日志

| 路径 | 方法 | 请求参数 | 响应结构 | 主要校验 | 事务 |
| --- | --- | --- | --- | --- | --- |
| `/settings` | GET | 无 | 设置键值 | 管理员 | 否 |
| `/settings` | PUT | 设置键值 | 设置键值 | 键名合法 | 是 |
| `/operation-logs` | GET | 关键字、日期、操作人、类型、分页 | 日志分页 | 管理员或审计权限 | 否 |
| `/operation-logs/export` | POST | 查询条件 | 导出任务 | 需要导出权限 | 否 |
