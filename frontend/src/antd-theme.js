import { theme } from 'ant-design-vue'

/**
 * Ant Design Vue 主题配置
 * 严格遵循 Material Design 3 规范
 * @param {boolean} isDark - 是否为暗色模式
 */
export default function getAntdTheme(isDark = false) {
  return {
    token: {
      // === Material Design 3 Color System ===

      // Primary - 主色调（绿色）
      colorPrimary: isDark ? '#81c784' : '#4caf50',

      // Secondary colors
      colorSuccess: isDark ? '#81c784' : '#4caf50',
      colorWarning: '#ff9800',
      colorError: '#f44336', // MD3 标准错误色
      colorInfo: isDark ? '#64b5f6' : '#2196f3',

      // === Surface & Background (MD3 规范) ===
      colorBgBase: isDark ? '#1c1b1f' : '#ffffff',
      colorBgContainer: isDark ? '#1c1b1f' : '#ffffff',
      colorBgElevated: isDark ? '#26252a' : '#ffffff',
      colorBgLayout: isDark ? '#1c1b1f' : '#fefbff', // MD3 标准背景色
      colorBgSpotlight: isDark ? '#26252a' : '#ffffff',

      // === Typography (MD3 规范) ===
      colorText: isDark ? '#e6e1e5' : '#1c1b1f', // On-surface
      colorTextSecondary: isDark ? '#cac4d0' : '#49454f', // On-surface-variant
      colorTextTertiary: isDark ? '#938f99' : '#79747e',
      colorTextQuaternary: isDark ? '#79747e' : '#938f99',

      // === Borders ===
      colorBorder: isDark ? '#49454f' : '#d1cdd6',
      colorBorderSecondary: isDark ? '#3a3740' : '#e3e1e6',
      colorSplit: isDark ? '#49454f' : '#e3e1e6',

      // === Shape System ===
      borderRadius: 12, // Medium shape
      borderRadiusLG: 16, // Large shape
      borderRadiusSM: 8, // Small shape
      borderRadiusXS: 4, // Extra small shape

      // === Typography ===
      fontFamily: "'Roboto', 'Inter', system-ui, -apple-system, sans-serif",
      fontSize: 14, // Body Medium
      fontSizeLG: 16, // Body Large
      fontSizeSM: 12, // Body Small
      lineHeight: 1.428, // 20/14 = 1.428
      lineHeightLG: 1.5, // 24/16 = 1.5

      // === Links ===
      colorLink: isDark ? '#64b5f6' : '#2196f3',
      colorLinkHover: isDark ? '#90caf9' : '#1976d2',
      colorLinkActive: isDark ? '#42a5f5' : '#1565c0',

      // === Components ===
      controlHeight: 40,
      controlHeightLG: 48,
      controlHeightSM: 32,

      // === Motion (MD3 规范) ===
      motionDurationSlow: '0.3s',
      motionDurationMid: '0.2s',
      motionDurationFast: '0.1s',
    },

    components: {
      // === Card 组件 (MD3 Elevated Card) ===
      Card: {
        borderRadiusLG: 16,
        paddingLG: 24,
        colorBgContainer: isDark ? '#1c1b1f' : '#ffffff',
        colorBorderSecondary: isDark ? '#49454f' : '#e3e1e6',
        colorTextHeading: isDark ? '#e6e1e5' : '#1c1b1f',
      },

      // === Button 组件 (MD3 规范) ===
      Button: {
        borderRadius: 20, // MD3 Filled Button 圆角
        borderRadiusLG: 24,
        borderRadiusSM: 16,
        controlHeight: 40,
        controlHeightLG: 48,
        controlHeightSM: 32,
        fontSize: 14,
        fontSizeLG: 16,
        fontSizeSM: 12,
        paddingContentHorizontal: 24,
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
        colorBgContainer: isDark ? '#26252a' : '#ffffff',
      },

      // === Input 组件 (MD3 Text Field) ===
      Input: {
        borderRadius: 12,
        controlHeight: 40,
        colorBgContainer: isDark ? '#26252a' : '#ffffff',
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
        colorTextPlaceholder: isDark ? '#938f99' : '#79747e',
        colorBorder: isDark ? '#49454f' : '#d1cdd6',
      },

      // === Select 组件 ===
      Select: {
        borderRadius: 12,
        controlHeight: 40,
        colorBgContainer: isDark ? '#26252a' : '#ffffff',
        colorBgElevated: isDark ? '#26252a' : '#ffffff',
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
        colorTextPlaceholder: isDark ? '#938f99' : '#79747e',
        colorBorder: isDark ? '#49454f' : '#d1cdd6',
      },

      // === Modal 组件 (MD3 Dialog) ===
      Modal: {
        borderRadiusLG: 28, // MD3 Dialog 使用 Extra Large 圆角
        colorBgElevated: isDark ? '#1c1b1f' : '#ffffff',
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
        colorTextHeading: isDark ? '#e6e1e5' : '#1c1b1f',
      },

      // === Table 组件 ===
      Table: {
        borderRadius: 12,
        colorBgContainer: isDark ? '#1c1b1f' : '#ffffff',
        colorFillAlter: isDark ? '#26252a' : '#f5f5f5',
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
        colorTextHeading: isDark ? '#e6e1e5' : '#1c1b1f',
        colorBorderSecondary: isDark ? '#49454f' : '#e3e1e6',
      },

      // === Tabs 组件 ===
      Tabs: {
        borderRadius: 12,
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
        colorBgContainer: isDark ? '#1c1b1f' : '#ffffff',
      },

      // === Menu 组件 ===
      Menu: {
        colorItemBg: isDark ? '#1c1b1f' : '#ffffff',
        colorItemBgHover: isDark ? '#26252a' : '#f5f5f5',
        colorItemBgSelected: isDark ? '#3a4a3f' : '#e8f5e9',
        colorItemText: isDark ? '#e6e1e5' : '#1c1b1f',
        colorItemTextSelected: isDark ? '#81c784' : '#4caf50',
        borderRadius: 12,
      },

      // === Dropdown 组件 ===
      Dropdown: {
        colorBgElevated: isDark ? '#26252a' : '#ffffff',
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
        borderRadiusLG: 12,
      },

      // === Descriptions 组件 ===
      Descriptions: {
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
        colorTextSecondary: isDark ? '#cac4d0' : '#49454f',
        colorBgContainer: isDark ? '#1c1b1f' : '#ffffff',
        colorFillAlter: isDark ? '#201f24' : '#f3f4f6', // Label 背景色 = surface-container
        colorSplit: isDark ? '#49454f' : '#e3e1e6',
        borderRadiusLG: 8, // 设置 Descriptions 容器圆角
      },

      // === Alert 组件 ===
      Alert: {
        borderRadiusLG: 12,
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
      },

      // === Drawer 组件 ===
      Drawer: {
        colorBgElevated: isDark ? '#1c1b1f' : '#ffffff',
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
        borderRadiusLG: 16,
      },

      // === Form 组件 ===
      Form: {
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
        colorTextHeading: isDark ? '#e6e1e5' : '#1c1b1f',
      },

      // === Empty 组件 ===
      Empty: {
        colorTextDescription: isDark ? '#938f99' : '#79747e',
      },

      // === Tag 组件 ===
      Tag: {
        borderRadiusSM: 16, // 药丸形
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
      },

      // === Switch 组件 ===
      Switch: {
        colorPrimary: isDark ? '#81c784' : '#4caf50',
        colorText: isDark ? '#e6e1e5' : '#1c1b1f',
      },

      // === Tooltip 组件 ===
      Tooltip: {
        colorBgSpotlight: isDark ? '#313033' : '#f5f5f5',  // Tooltip 背景色（跟随主题）
        colorTextLightSolid: isDark ? '#ffffff' : '#1c1b1f',  // Tooltip 文本颜色（跟随主题）
        borderRadius: 8,
      },
    },

    // 算法配置 - 使用 Ant Design 内置的暗黑算法
    algorithm: isDark ? [theme.darkAlgorithm] : [],
  }
}
