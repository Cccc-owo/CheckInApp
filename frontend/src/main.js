import { createApp } from 'vue';
import { createPinia } from 'pinia';

// Ant Design Vue
import Antd from 'ant-design-vue';
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

app.mount('#app');
