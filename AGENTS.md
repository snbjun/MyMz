# AGENTS.md

本项目是一个本地单机部署的进销存 BS 系统。

## 参考资料

参考资料位于：

- `design_files/`

该目录中包含从“秒账”软件导出的截图、HTML 和界面参考文件。

这些文件只能用于分析：

- 功能模块
- 字段名称
- 页面流程
- 交互方式
- 打印格式
- 表格列
- 表单字段

禁止：

- 直接复制原 HTML 代码
- 直接复制原 CSS
- 直接复制原 Logo、图片、图标、静态资源
- 直接保留原软件名称、品牌标识或专有文案

需要基于这些参考资料重新实现一个独立的本地系统。

## 技术栈

- Frontend: Vue 3 + TypeScript + Vite + Element Plus
- Backend: FastAPI + SQLAlchemy 2.x + Pydantic + Alembic
- Database: SQLite
- Deployment: Docker Compose
- Tests: Pytest + Playwright

## 后端规则

- 金额字段必须使用 Decimal，禁止使用 float。
- 数量字段必须支持小数。
- 销售单、采购单、库存、收付款相关操作必须使用数据库事务。
- 库存变化必须创建库存流水记录。
- 不允许直接随意覆盖库存数量。
- 路由层只处理请求和响应。
- 业务逻辑放在 service 层。
- 数据库访问放在 repository 层。
- 删除业务数据优先使用软删除 deleted_at。
- 每个主要模块必须包含后端测试。

## 前端规则

- 使用 Vue 3 Composition API。
- 使用 TypeScript。
- UI 使用 Element Plus。
- API 调用集中放在 `frontend/src/api/`。
- 页面集中放在 `frontend/src/views/`。
- 通用组件放在 `frontend/src/components/`。
- 表格页面必须支持搜索、分页、加载状态。
- 表单必须有校验。
- 不允许把多个业务模块堆在一个大文件里。

## 第一版范围

第一版只实现：

- 登录
- 用户管理
- 客户
- 供应商
- 产品
- 库存
- 销售单
- 采购单
- 收款付款
- 费用收入
- 基础报表
- 销售单/采购单打印
- 数据备份

暂不实现：

- 多账套
- 多门店
- 复杂审批
- 消息中心
- 皮肤系统
- 移动端
- 第三方集成