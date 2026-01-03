import { defineStore } from 'pinia';
import { adminAPI } from '@/api';

export const useAdminStore = defineStore('admin', {
  state: () => ({
    stats: null, // 系统统计信息
    logs: [],
    logsTotal: 0,
    loading: false,
  }),

  getters: {
    totalUsers: state => state.stats?.users?.total || 0,
    activeUsers: state => {
      // Active users = 已审批的用户（is_approved=true）
      return state.stats?.users?.active || 0;
    },
    totalRecords: state => state.stats?.check_in_records?.total || 0,
    todayRecords: state => state.stats?.check_in_records?.today || 0,
  },

  actions: {
    // 获取系统统计信息
    async fetchStats() {
      this.loading = true;
      try {
        const stats = await adminAPI.getStats();
        this.stats = stats;
        return stats;
      } catch (error) {
        throw new Error(error.message || '获取统计信息失败');
      } finally {
        this.loading = false;
      }
    },

    // 批量触发打卡
    async batchCheckIn(userIds) {
      try {
        const result = await adminAPI.batchCheckIn(userIds);
        return result;
      } catch (error) {
        throw new Error(error.message || '批量打卡失败');
      }
    },

    // 获取系统日志
    async fetchLogs(params = {}) {
      this.loading = true;
      try {
        const data = await adminAPI.getLogs(params);
        this.logs = data.logs || data;
        this.logsTotal = data.total || this.logs.length;
        return data;
      } catch (error) {
        throw new Error(error.message || '获取日志失败');
      } finally {
        this.loading = false;
      }
    },
  },
});
