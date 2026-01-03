import { ref, computed } from 'vue';

const THEME_STORAGE_KEY = 'checkin-app-theme';

// 全局主题状态（单例模式）
const theme = ref('light');

/**
 * 应用主题到 DOM
 */
const applyTheme = newTheme => {
  const html = document.documentElement;

  if (newTheme === 'dark') {
    html.classList.add('dark');
  } else {
    html.classList.remove('dark');
  }
};

/**
 * 初始化主题
 * 优先级: localStorage > 系统偏好 > 默认亮色
 */
export const initTheme = () => {
  // 1. 尝试从 localStorage 读取
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  if (savedTheme === 'light' || savedTheme === 'dark') {
    theme.value = savedTheme;
    applyTheme(savedTheme);
    return;
  }

  // 2. 检测系统偏好
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    theme.value = 'dark';
    applyTheme('dark');
    return;
  }

  // 3. 默认亮色
  theme.value = 'light';
  applyTheme('light');
};

/**
 * 监听系统主题变化
 */
export const watchSystemTheme = () => {
  if (!window.matchMedia) return;

  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  const handleChange = e => {
    // 仅在用户未手动设置主题时才跟随系统
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    if (!savedTheme) {
      const systemTheme = e.matches ? 'dark' : 'light';
      theme.value = systemTheme;
      applyTheme(systemTheme);
    }
  };

  mediaQuery.addEventListener('change', handleChange);

  // 返回清理函数
  return () => mediaQuery.removeEventListener('change', handleChange);
};

/**
 * 主题管理 Composable
 * 支持亮色/暗色模式切换，并持久化到 localStorage
 */
export function useTheme() {
  /**
   * 切换主题
   */
  const toggleTheme = () => {
    const newTheme = theme.value === 'light' ? 'dark' : 'light';
    theme.value = newTheme;
    applyTheme(newTheme);
    localStorage.setItem(THEME_STORAGE_KEY, newTheme);
  };

  /**
   * 设置指定主题
   */
  const setTheme = newTheme => {
    if (newTheme !== 'light' && newTheme !== 'dark') {
      console.warn(`Invalid theme: ${newTheme}. Using 'light' instead.`);
      newTheme = 'light';
    }

    theme.value = newTheme;
    applyTheme(newTheme);
    localStorage.setItem(THEME_STORAGE_KEY, newTheme);
  };

  return {
    theme,
    toggleTheme,
    setTheme,
    isDark: computed(() => theme.value === 'dark'),
    isLight: computed(() => theme.value === 'light'),
  };
}
