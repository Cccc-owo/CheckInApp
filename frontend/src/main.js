import { createApp } from 'vue';
import { createPinia } from 'pinia';

// Ant Design Vue
import Antd, { message } from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';

import App from './App.vue';
import router from './router';
import './style.css';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

// Ant Design Vue
app.use(Antd);

// 全局未捕获的 Promise 错误处理
window.addEventListener('unhandledrejection', event => {
  console.error('未捕获的 Promise 错误:', event.reason);

  // 显示用户友好的错误提示
  const errorMessage = event.reason?.message || event.reason || '操作失败';

  // 只对非网络错误显示提示（网络错误已在 axios 拦截器中处理）
  if (!errorMessage.includes('网络错误') && !errorMessage.includes('请求超时')) {
    message.error({
      content: `操作失败: ${errorMessage}`,
      duration: 3,
    });
  }

  // 阻止默认的控制台错误输出（已经用 console.error 输出了）
  event.preventDefault();
});

// 全局错误处理（捕获 Vue 组件内的错误）
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue 错误:', err);
  console.error('错误信息:', info);
  console.error('组件实例:', instance);

  // 显示用户友好的错误提示
  message.error({
    content: '应用发生错误，请刷新页面重试',
    duration: 3,
  });
};

app.mount('#app');
