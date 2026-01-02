import { ref, onMounted, onUnmounted } from 'vue'

/**
 * 响应式断点检测 Composable
 * 基于 Ant Design 的断点系统
 * - xs: <576px (手机)
 * - sm: ≥576px (平板竖屏)
 * - md: ≥768px (平板横屏)
 * - lg: ≥992px (桌面)
 * - xl: ≥1200px (大屏)
 * - xxl: ≥1600px (超大屏)
 */
export function useBreakpoint() {
  const isMobile = ref(window.innerWidth < 768)
  const isTablet = ref(window.innerWidth >= 768 && window.innerWidth < 992)
  const isDesktop = ref(window.innerWidth >= 992)

  // Ant Design 断点
  const isXs = ref(window.innerWidth < 576)
  const isSm = ref(window.innerWidth >= 576 && window.innerWidth < 768)
  const isMd = ref(window.innerWidth >= 768 && window.innerWidth < 992)
  const isLg = ref(window.innerWidth >= 992 && window.innerWidth < 1200)
  const isXl = ref(window.innerWidth >= 1200 && window.innerWidth < 1600)
  const isXxl = ref(window.innerWidth >= 1600)

  const updateBreakpoints = () => {
    const width = window.innerWidth

    // 简化断点
    isMobile.value = width < 768
    isTablet.value = width >= 768 && width < 992
    isDesktop.value = width >= 992

    // Ant Design 断点
    isXs.value = width < 576
    isSm.value = width >= 576 && width < 768
    isMd.value = width >= 768 && width < 992
    isLg.value = width >= 992 && width < 1200
    isXl.value = width >= 1200 && width < 1600
    isXxl.value = width >= 1600
  }

  onMounted(() => {
    window.addEventListener('resize', updateBreakpoints)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateBreakpoints)
  })

  return {
    // 简化断点（常用）
    isMobile,
    isTablet,
    isDesktop,

    // Ant Design 断点（详细）
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    isXxl,
  }
}
