import { defineStore } from 'pinia';
import { checkInAPI } from '@/api';

export const useCheckInStore = defineStore('checkIn', {
  state: () => ({
    myRecords: [],
    allRecords: [], // 管理员查看所有记录
    currentPage: 1,
    pageSize: 20,
    total: 0,
    loading: false,
  }),

  getters: {
    todayRecords: state => {
      const today = new Date().toISOString().split('T')[0];
      return state.myRecords.filter(record => {
        const recordDate = new Date(record.check_in_time).toISOString().split('T')[0];
        return recordDate === today;
      });
    },

    successRate: state => {
      if (state.myRecords.length === 0) return 0;
      const successCount = state.myRecords.filter(r => r.status === 'success').length;
      return ((successCount / state.myRecords.length) * 100).toFixed(2);
    },
  },

  actions: {
    // 手动打卡
    async manualCheckIn() {
      this.loading = true;
      try {
        const result = await checkInAPI.manualCheckIn();
        // 刷新打卡记录
        await this.fetchMyRecords();
        return result;
      } catch (error) {
        throw new Error(error.message || '打卡失败');
      } finally {
        this.loading = false;
      }
    },

    // 获取我的打卡记录
    async fetchMyRecords(params = {}) {
      this.loading = true;
      try {
        const data = await checkInAPI.getMyRecords({
          skip: (this.currentPage - 1) * this.pageSize,
          limit: this.pageSize,
          ...params,
        });
        this.myRecords = data.records || data;
        this.total = data.total || this.myRecords.length;
        return data;
      } catch (error) {
        throw new Error(error.message || '获取打卡记录失败');
      } finally {
        this.loading = false;
      }
    },

    // 获取所有打卡记录（管理员）
    async fetchAllRecords(params = {}) {
      this.loading = true;
      try {
        const data = await checkInAPI.getAllRecords({
          skip: (this.currentPage - 1) * this.pageSize,
          limit: this.pageSize,
          ...params,
        });
        this.allRecords = data.records || data;
        this.total = data.total || this.allRecords.length;
        return data;
      } catch (error) {
        throw new Error(error.message || '获取打卡记录失败');
      } finally {
        this.loading = false;
      }
    },

    // 统计打卡记录
    async getRecordsCount(params = {}) {
      try {
        const count = await checkInAPI.getRecordsCount(params);
        return count;
      } catch (error) {
        throw new Error(error.message || '获取统计信息失败');
      }
    },
  },
});
