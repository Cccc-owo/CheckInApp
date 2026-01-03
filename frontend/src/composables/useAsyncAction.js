/**
 * 通用异步操作 Composable
 * 统一处理 loading、error 状态和消息提示
 *
 * @example
 * const { loading, error, execute } = useAsyncAction()
 *
 * const handleSubmit = async () => {
 *   await execute(
 *     () => api.createTask(formData),
 *     { successMsg: '创建成功', errorMsg: '创建失败' }
 *   )
 * }
 */

import { ref } from 'vue';
import { message } from 'ant-design-vue';

export function useAsyncAction(options = {}) {
  const loading = ref(false);
  const error = ref(null);

  /**
   * 执行异步操作
   * @param {Function} asyncFn - 异步函数
   * @param {Object} config - 配置选项
   * @param {string} config.successMsg - 成功提示消息
   * @param {string} config.errorMsg - 错误提示消息
   * @param {boolean} config.throwOnError - 是否抛出错误
   * @param {boolean} config.silent - 是否静默模式（不显示消息）
   * @returns {Promise} 异步函数的返回值
   */
  const execute = async (asyncFn, config = {}) => {
    const {
      successMsg = options.successMsg,
      errorMsg = options.errorMsg,
      throwOnError = false,
      silent = false,
    } = config;

    loading.value = true;
    error.value = null;

    try {
      const result = await asyncFn();

      if (!silent && successMsg) {
        message.success({ content: successMsg, duration: 3 });
      }

      return result;
    } catch (err) {
      error.value = err;

      if (!silent) {
        const msg = err.message || err.detail || errorMsg || '操作失败';
        message.error({ content: msg, duration: 4 });
      }

      if (throwOnError) {
        throw err;
      }

      return null;
    } finally {
      loading.value = false;
    }
  };

  /**
   * 重置状态
   */
  const reset = () => {
    loading.value = false;
    error.value = null;
  };

  return {
    loading,
    error,
    execute,
    reset,
  };
}
