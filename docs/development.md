# 开发指南

## 开发环境设置

### 后端开发

```bash
# 克隆项目
git clone <repository>
cd CheckInApp

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r backend/requirements.txt

# 安装开发依赖
pip install pytest pytest-asyncio black flake8

python3 run.py
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 代码格式化
npm run lint
npm run format
```

## 项目结构

### 后端目录说明

```
backend/
├── main.py              # FastAPI 应用入口，CORS、路由注册
├── config.py            # Pydantic Settings 配置
├── dependencies.py      # 依赖注入（认证、权限）
├── exceptions.py        # 自定义异常类
│
├── models/              # SQLAlchemy 数据模型
│   ├── database.py      # 数据库连接、Session
│   ├── user.py
│   ├── check_in_task.py
│   ├── check_in_record.py
│   └── task_template.py
│
├── schemas/             # Pydantic 请求响应模型
│   ├── user.py
│   ├── task.py
│   ├── auth.py
│   └── response.py      # 标准化响应
│
├── api/                 # API 路由（按模块划分）
│   ├── auth.py          # 认证相关
│   ├── users.py         # 用户管理
│   ├── tasks.py         # 任务管理
│   ├── check_in.py      # 打卡功能
│   ├── admin.py         # 管理员功能
│   └── templates.py     # 模板管理
│
├── services/            # 业务逻辑层
│   ├── auth_service.py
│   ├── user_service.py
│   ├── task_service.py
│   ├── check_in_service.py
│   ├── scheduler_service.py
│   ├── template_service.py
│   └── registration_manager.py
│
└── workers/             # Selenium 自动化
    ├── token_refresher.py    # QQ 登录
    ├── check_in_worker.py    # 打卡执行
    └── email_notifier.py     # 邮件发送
```

### 前端目录说明

```
frontend/src/
├── main.js              # Vue 应用入口
├── App.vue              # 根组件
│
├── api/                 # API 封装
│   ├── client.js        # Axios 实例、拦截器
│   └── index.js         # API 模块（auth, user, task 等）
│
├── views/               # 页面组件
│   ├── LoginView.vue
│   ├── DashboardView.vue
│   ├── TasksView.vue
│   ├── RecordsView.vue
│   └── admin/           # 管理员页面
│
├── components/          # 可复用组件
│   ├── TaskCard.vue
│   ├── RecordTable.vue
│   └── ...
│
├── stores/              # Pinia 状态管理
│   ├── auth.js          # 认证状态
│   ├── user.js          # 用户信息
│   └── task.js          # 任务列表
│
├── router/              # Vue Router
│   └── index.js         # 路由配置、导航守卫
│
└── composables/         # 组合式函数
    ├── useAuth.js
    └── useTask.js
```

## 开发流程

### 添加新功能

#### 1. 后端 API 开发

**步骤**:

1. 在 `models/` 定义数据模型
2. 在 `schemas/` 定义请求响应模型
3. 在 `services/` 实现业务逻辑
4. 在 `api/` 创建路由端点
5. 在 `main.py` 注册路由

**示例**: 添加一个新的"任务标签"功能

```python
# models/task_tag.py
class TaskTag(Base):
    __tablename__ = "task_tags"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("check_in_tasks.id"))
    tag_name = Column(String(50))

# schemas/tag.py
class TaskTagCreate(BaseModel):
    tag_name: str

# services/tag_service.py
def create_tag(db: Session, task_id: int, tag_data: TaskTagCreate):
    tag = TaskTag(task_id=task_id, tag_name=tag_data.tag_name)
    db.add(tag)
    db.commit()
    return tag

# api/tags.py
@router.post("/tasks/{task_id}/tags")
def add_tag(task_id: int, tag: TaskTagCreate, db: Session = Depends(get_db)):
    return tag_service.create_tag(db, task_id, tag)

# main.py
from api import tags
app.include_router(tags.router, prefix="/api")
```

#### 2. 前端开发

**步骤**:

1. 在 `api/index.js` 添加 API 调用
2. 在 `stores/` 创建或更新状态
3. 创建或更新 Vue 组件
4. 配置路由（如需要）

**示例**: 添加标签管理页面

```javascript
// api/index.js
export const tagApi = {
  addTag: (taskId, data) => client.post(`/tasks/${taskId}/tags`, data),
  getTags: (taskId) => client.get(`/tasks/${taskId}/tags`)
}

// stores/tag.js
export const useTagStore = defineStore('tag', {
  state: () => ({
    tags: []
  }),
  actions: {
    async fetchTags(taskId) {
      const { data } = await tagApi.getTags(taskId)
      this.tags = data
    }
  }
})

// components/TagManager.vue
<template>
  <div>
    <a-tag v-for="tag in tags" :key="tag.id">{{ tag.tag_name }}</a-tag>
    <a-button @click="addTag">添加标签</a-button>
  </div>
</template>
```

### 数据库迁移

```bash
# 修改模型后生成迁移脚本
# 手动创建脚本在 backend/scripts/migrate_*.py

# 执行迁移
python backend/scripts/migrate_xxx.py
```

### 测试

#### 后端测试

```python
# tests/test_task_service.py
import pytest
from backend.services import task_service

def test_create_task():
    task = task_service.create_task(db, user_id=1, task_data)
    assert task.name == "Test Task"
    assert task.is_active == True

# 运行测试
pytest backend/tests/
```

#### 前端测试

```javascript
// tests/TaskCard.spec.js
import { mount } from '@vue/test-utils'
import TaskCard from '@/components/TaskCard.vue'

test('displays task name', () => {
  const wrapper = mount(TaskCard, {
    props: { task: { name: 'Test Task' } }
  })
  expect(wrapper.text()).toContain('Test Task')
})

// 运行测试
npm run test
```

## 代码规范

### 后端规范

- 使用 Black 格式化: `black backend/`
- 遵循 PEP 8
- 函数添加类型注解
- API 路由使用 Pydantic 模型验证
- 使用 dependency injection

```python
# 好的示例
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """创建新任务"""
    return task_service.create_task(db, current_user.id, task_data)
```

### 前端规范

- 使用 ESLint + Prettier
- 组件使用 Composition API
- 使用 `<script setup>` 语法
- Props 添加类型验证
- 统一使用 Ant Design Vue 组件

```vue
<!-- 好的示例 -->
<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

const isActive = computed(() => props.task.is_active)
</script>
```

## 调试技巧

### 后端调试

```python
# 使用 logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Creating task for user {user_id}")

# 使用 pdb
import pdb; pdb.set_trace()

# 查看 SQL 查询
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 前端调试

```javascript
// 使用 Vue Devtools
// Chrome 扩展安装

// console 输出
console.log('Task data:', task.value)

// 调试 API 请求
axios.interceptors.request.use(request => {
  console.log('Request:', request)
  return request
})
```

## 常见问题

### CORS 错误

在 `.env` 添加前端地址:

```env
CORS_ORIGINS=http://localhost:3000
```

### 数据库锁定

使用 connection pool:

```python
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10
)
```

### Selenium 超时

增加等待时间:

```python
WebDriverWait(driver, 30).until(...)
```

## Git 工作流

```bash
# 创建功能分支
git checkout -b feature/task-tags

# 提交代码
git add .
git commit -m "feat: add task tag functionality"

# 合并到主分支
git checkout main
git merge feature/task-tags

# 推送
git push origin main
```

## 性能优化

### 后端优化

- 使用 SQLAlchemy 的 `joinedload` 避免 N+1 查询
- 添加数据库索引
- 使用异步任务处理耗时操作
- 启用 gzip 压缩

### 前端优化

- 使用虚拟滚动处理大列表
- 路由懒加载
- 图片懒加载
- 使用 `keep-alive` 缓存组件
