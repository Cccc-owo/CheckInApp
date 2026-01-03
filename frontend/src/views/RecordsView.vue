<template>
  <Layout>
    <div class="records-container">
      <a-card>
        <template #title>
          <div class="card-header">
            <div>
              <UnorderedListOutlined />
              <span>我的打卡记录</span>
            </div>
            <a-button type="primary" @click="handleRefresh">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </div>
        </template>

        <!-- 统计信息 -->
        <div class="stats-container">
          <a-row :gutter="20">
            <a-col :xs="24" :sm="8" :md="8">
              <a-statistic title="总打卡次数" :value="total" />
            </a-col>
            <a-col :xs="24" :sm="8" :md="8">
              <a-statistic
                title="成功次数"
                :value="successCount"
                :value-style="{ color: '#67c23a' }"
              />
            </a-col>
            <a-col :xs="24" :sm="8" :md="8">
              <a-statistic
                title="成功率"
                :value="parseFloat(checkInStore.successRate)"
                suffix="%"
                :precision="2"
              />
            </a-col>
          </a-row>
        </div>

        <a-divider />

        <!-- 桌面端表格 -->
        <a-table
          v-if="!isMobile"
          :data-source="checkInStore.myRecords"
          :columns="columns"
          :loading="checkInStore.loading"
          :pagination="false"
          :row-key="record => record.id"
          :scroll="{ x: 'max-content' }"
          bordered
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'check_in_time'">
              {{ formatDateTime(record.check_in_time) }}
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag v-if="record.status === 'success'" color="success">✅ 打卡成功</a-tag>
              <a-tag v-else-if="record.status === 'out_of_time'" color="default"
                >🕐 时间范围外</a-tag
              >
              <a-tag v-else-if="record.status === 'unknown'" color="warning">❗ 打卡异常</a-tag>
              <a-tag v-else color="error">❌ 打卡失败</a-tag>
            </template>
            <template v-else-if="column.key === 'trigger_type'">
              <a-tag v-if="record.trigger_type === 'manual'" color="blue">手动</a-tag>
              <a-tag v-else-if="record.trigger_type === 'scheduled'" color="default">定时</a-tag>
              <a-tag v-else-if="record.trigger_type === 'admin'" color="orange">管理员</a-tag>
              <a-tag v-else>{{ record.trigger_type }}</a-tag>
            </template>
          </template>
        </a-table>

        <!-- 移动端卡片视图 -->
        <a-space v-else direction="vertical" :size="16" style="width: 100%">
          <a-card
            v-for="record in checkInStore.myRecords"
            :key="record.id"
            size="small"
            :loading="checkInStore.loading"
          >
            <a-descriptions :column="1" size="small" bordered>
              <a-descriptions-item label="ID">{{ record.id }}</a-descriptions-item>
              <a-descriptions-item label="打卡时间">
                {{ formatDateTime(record.check_in_time) }}
              </a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag v-if="record.status === 'success'" color="success">✅ 打卡成功</a-tag>
                <a-tag v-else-if="record.status === 'out_of_time'" color="default"
                  >🕐 时间范围外</a-tag
                >
                <a-tag v-else-if="record.status === 'unknown'" color="warning">❗ 打卡异常</a-tag>
                <a-tag v-else color="error">❌ 打卡失败</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="触发方式">
                <a-tag v-if="record.trigger_type === 'manual'" color="blue">手动</a-tag>
                <a-tag v-else-if="record.trigger_type === 'scheduled'" color="default">定时</a-tag>
                <a-tag v-else-if="record.trigger_type === 'admin'" color="orange">管理员</a-tag>
                <a-tag v-else>{{ record.trigger_type }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="消息">
                {{ record.response_text || '-' }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-space>

        <!-- 分页 -->
        <div class="pagination-container">
          <a-pagination
            v-model:current="checkInStore.currentPage"
            v-model:page-size="checkInStore.pageSize"
            :total="total"
            :page-size-options="['10', '20', '50', '100']"
            show-size-changer
            show-quick-jumper
            :show-total="total => `共 ${total} 条记录`"
            @change="handlePageChange"
            @show-size-change="handleSizeChange"
          />
        </div>
      </a-card>
    </div>
  </Layout>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { UnorderedListOutlined, ReloadOutlined } from '@ant-design/icons-vue';
import Layout from '@/components/Layout.vue';
import { useBreakpoint } from '@/composables/useBreakpoint';
import { useCheckInStore } from '@/stores/checkIn';
import { formatDateTime } from '@/utils/helpers';

const checkInStore = useCheckInStore();
const { isMobile } = useBreakpoint();

const total = computed(() => checkInStore.total);

const successCount = computed(() => {
  return checkInStore.myRecords.filter(r => r.status === 'success').length;
});

// 表格列配置
const columns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: 80,
  },
  {
    title: '打卡时间',
    dataIndex: 'check_in_time',
    key: 'check_in_time',
    width: 180,
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 120,
  },
  {
    title: '触发方式',
    dataIndex: 'trigger_type',
    key: 'trigger_type',
    width: 120,
  },
  {
    title: '消息',
    dataIndex: 'response_text',
    key: 'response_text',
    ellipsis: true,
  },
];

// 刷新数据
const handleRefresh = async () => {
  try {
    await checkInStore.fetchMyRecords();
    message.success('刷新成功');
  } catch (error) {
    message.error(error.message || '刷新失败');
  }
};

// 页码改变
const handlePageChange = () => {
  checkInStore.fetchMyRecords();
};

// 每页数量改变
const handleSizeChange = () => {
  checkInStore.currentPage = 1;
  checkInStore.fetchMyRecords();
};

onMounted(() => {
  checkInStore.fetchMyRecords();
});
</script>

<style scoped>
.records-container {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header > div {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.stats-container {
  padding: 20px 0;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
