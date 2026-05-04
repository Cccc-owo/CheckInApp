# 开发指南

## 开发环境设置

### 后端开发

```bash
# 克隆项目
git clone <repository>
cd CheckInApp

# 安装后端依赖
uv sync

uv run python main.py backend
```

### 前端开发

```bash
cd apps/frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 代码检查和格式化
pnpm lint:check
pnpm format:check
```

## 项目结构

### 后端目录说明

```
apps/backend/
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
└── workers/             # Playwright 自动化
    ├── token_refresher.py    # QQ 登录
    ├── check_in_worker.py    # 打卡执行
    └── email_notifier.py     # 邮件发送
```

### 前端目录说明

```
apps/frontend/src/
├── main.ts              # Vue 应用入口
├── App.vue              # 根组件
│
├── api/                 # API 封装
│   ├── client.ts        # fetch 客户端、鉴权存储、错误归一化
│   ├── index.ts         # API 模块（auth, user, task 等）
│   └── types.ts         # API 类型
│
├── app/                 # 应用级状态和路由
│   ├── auth.ts          # 认证状态
│   ├── router.ts        # Vue Router 配置、导航守卫
│   └── theme.ts         # 主题模式
│
├── views/               # 页面组件
│   ├── LoginView.vue
│   ├── DashboardView.vue
│   ├── TasksView.vue
│   ├── RecordsView.vue
│   └── admin/           # 管理员页面
│
├── components/          # 可复用组件
│   ├── AppLayout.vue
│   ├── StateBlock.vue
│   ├── templates/       # 模板结构化编辑器
│   └── ui/              # shadcn-vue primitive
│
├── components/ui.ts     # 本地共享样式 helper
├── style.css            # Tailwind v4 + shadcn token
└── utils/               # 格式化和显示 helper
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

# apps/backend/main.py
from backend.api import tags
app.include_router(tags.router, prefix="/api")
```

#### 2. 前端开发

**步骤**:

1. 在 `apps/frontend/src/api/index.ts` 添加 API 调用和类型引用
2. 在 `apps/frontend/src/app/` 更新认证、路由或主题状态（如需要）
3. 创建或更新 Vue 组件，优先复用现有 shadcn-vue primitive 和 `src/components/ui.ts`
4. 配置路由（如需要）

**示例**: 添加标签管理页面

```typescript
// apps/frontend/src/api/index.ts
export const tagApi = {
  addTag: (taskId, data) => client.post(`/tasks/${taskId}/tags`, data),
  getTags: (taskId) => client.get(`/tasks/${taskId}/tags`)
}

// apps/frontend/src/components/TagManager.vue
<template>
  <div class="grid gap-2">
    <span v-for="tag in tags" :key="tag.id" :class="toneClass('neutral')">
      {{ tag.tag_name }}
    </span>
    <Button type="button" @click="addTag">添加标签</Button>
  </div>
</template>
```

### 数据库迁移

```bash
# 修改模型后生成迁移脚本
# 手动创建脚本在 apps/backend/scripts/migrate_*.py

# 执行迁移
uv run python apps/backend/scripts/migrate_xxx.py
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
uv run pytest tests/
```

#### 前端测试

```bash
cd apps/frontend

pnpm test
pnpm lint:check
pnpm build
```

## 代码规范

### 后端规范

- 使用 Ruff 检查和格式化:
  - `uv run ruff check apps/backend tests main.py`
  - `uv run ruff format apps/backend tests main.py`
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
- 使用 TypeScript 类型定义 Props 和 API 数据
- 优先使用 shadcn-vue primitive、lucide 图标、Tailwind token 和 `src/components/ui.ts` 共享样式
- 保留页面局部 Tailwind 来表达独有布局，不为一次性结构强行抽象

```vue
<!-- 好的示例 -->
<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  task: {
    name: string
    is_active: boolean
  }
}>()

const isActive = computed(() => props.task.is_active)
</script>

<template>
  <article class="rounded-lg border border-border bg-card p-4">
    {{ task.name }}
  </article>
</template>
```

### 前端调试

```typescript
// 使用 Vue Devtools
// Chrome 扩展安装

// console 输出
console.log('Task data:', task.value)

// 调试 API 请求
const response = await fetch('/api/tasks', {
  headers: {
    Authorization: `Bearer ${token}`
  }
})
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

### Playwright 超时

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
