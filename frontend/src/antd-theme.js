/**
 * Ant Design Vue 主题配置
 * 匹配现有 Material Design 3 色彩系统
 */
export default {
  token: {
    // 主色调 - 绿色（与 MD3 primary 保持一致）
    colorPrimary: '#4caf50',

    // 成功色
    colorSuccess: '#4caf50',

    // 警告色
    colorWarning: '#ff9800',

    // 错误色
    colorError: '#f56c6c',

    // 信息色 - 蓝色（与 MD3 secondary 保持一致）
    colorInfo: '#2196f3',

    // 边框圆角 - 与 Material Design 3 一致
    borderRadius: 12,

    // 字体家族
    fontFamily: "'Inter', 'Segoe UI', 'Roboto', system-ui, -apple-system, sans-serif",

    // 链接色
    colorLink: '#2196f3',

    // 字体大小
    fontSize: 14,

    // 行高
    lineHeight: 1.5715,
  },

  components: {
    // Card 组件定制
    Card: {
      borderRadiusLG: 16,
      boxShadowTertiary: '0 1px 3px 1px rgba(0, 0, 0, 0.08)',
      paddingLG: 24,
    },

    // Button 组件定制
    Button: {
      borderRadius: 24, // 圆角按钮，类似 MD3
      controlHeight: 40,
      fontSize: 14,
    },

    // Input 组件定制
    Input: {
      borderRadius: 12,
      controlHeight: 40,
    },

    // Modal 组件定制
    Modal: {
      borderRadiusLG: 16,
    },

    // Table 组件定制
    Table: {
      borderRadius: 12,
    },

    // Tabs 组件定制
    Tabs: {
      borderRadius: 12,
    },
  },

  // 算法配置
  algorithm: [],
}
