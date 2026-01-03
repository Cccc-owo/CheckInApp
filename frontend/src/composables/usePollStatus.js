/**
 * 状态轮询 Composable
 * 支持指数退避、最大重试次数、自动清理
 *
 * @example
 * const { polling, startPolling, stopPolling } = usePollStatus({
 *   interval: 2000,
 *   maxRetries: 15,
 *   backoff: true
 * })
 *
 * startPolling(
 *   async () => {
 *     const status = await api.getStatus(id)
 *     return {
 *       completed: status.status !== 'pending',
 *       success: status.status === 'success',
 *       data: status
 *     }
 *   },
 *   {
 *     onSuccess: (result) => console.log('完成', result),
 *     onFailure: (error) => console.error('失败', error),
 *     onTimeout: () => console.warn('超时')
 *   }
 * )
 */

import { ref, onUnmounted } from 'vue'

export function usePollStatus(options = {}) {
  const {
    interval = 2000,        // 初始轮询间隔（毫秒）
    maxRetries = 15,        // 最大重试次数
    backoff = false,        // 是否使用指数退避
    maxBackoffInterval = 10000  // 最大退避间隔（毫秒）
  } = options

  const polling = ref(false)
  let pollTimer = null
  let retryCount = 0

  /**
   * 开始轮询
   * @param {Function} checkFn - 检查函数，应返回 { completed, success, data }
   * @param {Object} callbacks - 回调函数
   * @param {Function} callbacks.onSuccess - 成功回调
   * @param {Function} callbacks.onFailure - 失败回调
   * @param {Function} callbacks.onTimeout - 超时回调
   */
  const startPolling = async (checkFn, callbacks = {}) => {
    const { onSuccess, onFailure, onTimeout } = callbacks

    // 重置状态
    stopPolling()
    polling.value = true
    retryCount = 0

    const poll = async () => {
      try {
        const result = await checkFn()

        // 检查是否完成
        if (result.completed) {
          stopPolling()

          if (result.success) {
            onSuccess?.(result.data || result)
          } else {
            onFailure?.(result.data || result)
          }
          return
        }

        // 检查是否超时
        retryCount++
        if (retryCount >= maxRetries) {
          stopPolling()
          onTimeout?.()
          return
        }

        // 计算下次轮询间隔（支持指数退避）
        let nextInterval = interval
        if (backoff) {
          // 指数退避：2s -> 4s -> 8s -> 最大10s
          nextInterval = Math.min(
            interval * Math.pow(2, retryCount - 1),
            maxBackoffInterval
          )
        }

        // 继续轮询
        pollTimer = setTimeout(poll, nextInterval)

      } catch (error) {
        stopPolling()
        onFailure?.(error)
      }
    }

    // 立即执行第一次检查
    poll()
  }

  /**
   * 停止轮询
   */
  const stopPolling = () => {
    if (pollTimer) {
      clearTimeout(pollTimer)
      pollTimer = null
    }
    polling.value = false
    retryCount = 0
  }

  // 组件卸载时自动清理
  onUnmounted(() => {
    stopPolling()
  })

  return {
    polling,
    startPolling,
    stopPolling
  }
}
