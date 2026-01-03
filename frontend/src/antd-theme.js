import { theme } from 'ant-design-vue'

/**
 * Ant Design Vue 主题配置
 * 匹配现有 Material Design 3 色彩系统
 * @param {boolean} isDark - 是否为暗色模式
 */
export default function getAntdTheme(isDark = false) {
  return {
    token: {
      // 主色调 - 绿色（与 MD3 primary 保持一致）
      colorPrimary: isDark ? '#81c784' : '#4caf50',

      // 成功色
      colorSuccess: isDark ? '#81c784' : '#4caf50',

      // 警告色
      colorWarning: '#ff9800',

      // 错误色
      colorError: '#f56c6c',

      // 信息色 - 蓝色（与 MD3 secondary 保持一致）
      colorInfo: isDark ? '#64b5f6' : '#2196f3',

      // 背景色
      colorBgBase: isDark ? '#121212' : '#ffffff',
      colorBgContainer: isDark ? '#1c1c1e' : '#ffffff',
      colorBgElevated: isDark ? '#2c2c2e' : '#ffffff',
      colorBgLayout: isDark ? '#121212' : '#fafafa',
      colorBgSpotlight: isDark ? '#2c2c2e' : '#ffffff',

      // 文字色
      colorText: isDark ? '#e5e5e7' : '#1c1b1f',
      colorTextSecondary: isDark ? '#a0a0a3' : '#64748b',
      colorTextTertiary: isDark ? '#808083' : '#94a3b8',
      colorTextQuaternary: isDark ? '#606063' : '#cbd5e1',

      // 边框色
      colorBorder: isDark ? '#3a3a3c' : '#e5e7eb',
      colorBorderSecondary: isDark ? '#2c2c2e' : '#f3f4f6',

      // 分割线颜色
      colorSplit: isDark ? '#3a3a3c' : '#e5e7eb',

      // 边框圆角 - 与 Material Design 3 一致
      borderRadius: 12,

      // 字体家族
      fontFamily: "'Inter', 'Segoe UI', 'Roboto', system-ui, -apple-system, sans-serif",

      // 链接色
      colorLink: isDark ? '#64b5f6' : '#2196f3',
      colorLinkHover: isDark ? '#90caf9' : '#1976d2',
      colorLinkActive: isDark ? '#42a5f5' : '#1565c0',

      // 字体大小
      fontSize: 14,

      // 行高
      lineHeight: 1.5715,

      // 控制组件高度
      controlHeight: 40,
    },

    components: {
      // Card 组件定制
      Card: {
        borderRadiusLG: 16,
        boxShadowTertiary: isDark
          ? '0 1px 3px 1px rgba(0, 0, 0, 0.5)'
          : '0 1px 3px 1px rgba(0, 0, 0, 0.08)',
        paddingLG: 24,
        colorBgContainer: isDark ? '#1c1c1e' : '#ffffff',
        colorBorderSecondary: isDark ? '#3a3a3c' : '#f0f0f0',
        colorTextHeading: isDark ? '#e5e5e7' : '#1c1b1f',
      },

      // Button 组件定制
      Button: {
        borderRadius: 24, // 圆角按钮，类似 MD3
        controlHeight: 40,
        fontSize: 14,
        colorText: isDark ? '#e5e5e7' : '#1c1b1f',
        colorBgContainer: isDark ? '#2c2c2e' : '#ffffff',
      },

      // Input 组件定制
      Input: {
        borderRadius: 12,
        controlHeight: 40,
        colorBgContainer: isDark ? '#2c2c2e' : '#ffffff',
        colorText: isDark ? '#e5e5e7' : '#1c1b1f',
        colorTextPlaceholder: isDark ? '#808083' : '#94a3b8',
        colorBorder: isDark ? '#3a3a3c' : '#e5e7eb',
      },

      // Select 组件定制
      Select: {
        borderRadius: 12,
        controlHeight: 40,
        colorBgContainer: isDark ? '#2c2c2e' : '#ffffff',
        colorBgElevated: isDark ? '#2c2c2e' : '#ffffff',
        colorText: isDark ? '#e5e5e7' : '#1c1b1f',
        colorTextPlaceholder: isDark ? '#808083' : '#94a3b8',
        colorBorder: isDark ? '#3a3a3c' : '#e5e7eb',
      },

      // Modal 组件定制
      Modal: {
        borderRadiusLG: 16,
        colorBgElevated: isDark ? '#1c1c1e' : '#ffffff',
        colorText: isDark ? '#e5e5e7' : '#1c1b1f',
        colorTextHeading: isDark ? '#e5e5e7' : '#1c1b1f',
      },

      // Table 组件定制
      Table: {
        borderRadius: 12,
        colorBgContainer: isDark ? '#1c1c1e' : '#ffffff',
        colorFillAlter: isDark ? '#2c2c2e' : '#f5f7fa',
        colorText: isDark ? '#e5e5e7' : '#1c1b1f',
        colorTextHeading: isDark ? '#e5e5e7' : '#1c1b1f',
        colorBorderSecondary: isDark ? '#3a3a3c' : '#f0f0f0',
      },

      // Tabs 组件定制
      Tabs: {
        borderRadius: 12,
        colorText: isDark ? '#e5e5e7' : '#1c1b1f',
        colorBgContainer: isDark ? '#1c1c1e' : '#ffffff',
      },

      // Menu 组件定制
      Menu: {
        colorItemBg: isDark ? '#1c1c1e' : '#ffffff',
        colorItemBgHover: isDark ? '#2c2c2e' : '#f5f7fa',
        colorItemBgSelected: isDark ? '#2c2c2e' : '#e8f5e9',
        colorItemText: isDark ? '#e5e5e7' : '#1c1b1f',
        colorItemTextSelected: isDark ? '#81c784' : '#4caf50',
      },

      // Dropdown 组件定制
      Dropdown: {
        colorBgElevated: isDark ? '#2c2c2e' : '#ffffff',
        colorText: isDark ? '#e5e5e7' : '#1c1b1f',
      },

      // Descriptions 组件定制
      Descriptions: {
        colorText: isDark ? '#e5e5e7' : '#1c1b1f',
        colorTextSecondary: isDark ? '#a0a0a3' : '#64748b',
        colorBgContainer: isDark ? '#1c1c1e' : '#ffffff',
        colorFillAlter: isDark ? '#2c2c2e' : '#f5f7fa',
      },

      // Alert 组件定制
      Alert: {
        borderRadiusLG: 12,
        colorText: isDark ? '#e5e5e7' : '#1c1b1f',
      },

      // Drawer 组件定制
      Drawer: {
        colorBgElevated: isDark ? '#1c1c1e' : '#ffffff',
        colorText: isDark ? '#e5e5e7' : '#1c1b1f',
      },

      // Form 组件定制
      Form: {
        colorText: isDark ? '#e5e5e7' : '#1c1b1f',
        colorTextHeading: isDark ? '#e5e5e7' : '#1c1b1f',
      },

      // Empty 组件定制
      Empty: {
        colorTextDescription: isDark ? '#a0a0a3' : '#94a3b8',
      },
    },

    // 算法配置 - 使用 Ant Design 内置的暗黑算法
    algorithm: isDark ? [theme.darkAlgorithm] : [],
  }
}
