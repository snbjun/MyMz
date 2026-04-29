const messages = {
  appName: "进销存系统",
  appSubtitle: "本地单机部署",
  loginTitle: "登录",
  username: "用户名",
  password: "密码",
  loginButton: "进入系统",
  loginTip: "当前为项目骨架阶段，登录只做本地跳转。",
  dashboard: "首页",
  customers: "客户",
  suppliers: "供应商",
  products: "产品",
  inventory: "库存",
  salesOrders: "销售单",
  purchaseOrders: "采购单",
  expenseIncome: "费用收入",
  reports: "报表",
  users: "用户管理",
  settings: "系统设置",
  logout: "退出",
  scaffoldReady: "项目骨架已就绪",
  scaffoldIntro: "当前只包含静态导航、占位页面和后端健康检查。",
  backendHealth: "后端健康检查",
  openModuleLater: "该模块将在后续阶段实现。",
};

export type MessageKey = keyof typeof messages;

export function t(key: MessageKey): string {
  return messages[key];
}
