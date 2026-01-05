import { defineStore } from 'pinia';
import api from '@/api';

export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [], // 当前用户的任务列表
    currentTask: null, // 当前选中的任务
    loading: false,
    error: null,
  }),

  getters: {
    // 启用的任务
    activeTasks: state => state.tasks.filter(t => t.is_active),

    // 禁用的任务
    inactiveTasks: state => state.tasks.filter(t => !t.is_active),

    // 任务数量统计
    taskStats: state => ({
      total: state.tasks.length,
      active: state.tasks.filter(t => t.is_active).length,
      inactive: state.tasks.filter(t => !t.is_active).length,
    }),

    // 根据 ID 获取任务
    getTaskById: state => taskId => {
      return state.tasks.find(t => t.id === taskId);
    },
  },

  actions: {
    // 获取当前用户的所有任务
    async fetchMyTasks(includeInactive = true) {
      this.loading = true;
      this.error = null;
      try {
        const tasks = await api.task.getMyTasks({ include_inactive: includeInactive });
        this.tasks = tasks;
        return tasks;
      } catch (error) {
        this.error = error.message || '获取任务列表失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 更新任务
    async updateTask(taskId, taskData) {
      this.loading = true;
      this.error = null;
      try {
        const updatedTask = await api.task.updateTask(taskId, taskData);
        const index = this.tasks.findIndex(t => t.id === taskId);
        if (index !== -1) {
          this.tasks[index] = updatedTask;
        }
        return updatedTask;
      } catch (error) {
        this.error = error.message || '更新任务失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 删除任务
    async deleteTask(taskId) {
      this.loading = true;
      this.error = null;
      try {
        await api.task.deleteTask(taskId);
        this.tasks = this.tasks.filter(t => t.id !== taskId);
      } catch (error) {
        this.error = error.message || '删除任务失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 切换任务启用状态
    async toggleTask(taskId) {
      this.loading = true;
      this.error = null;
      try {
        const updatedTask = await api.task.toggleTask(taskId);
        const index = this.tasks.findIndex(t => t.id === taskId);
        if (index !== -1) {
          // 保留原任务的 last_check_in_time 和 last_check_in_status
          const originalTask = this.tasks[index];
          this.tasks[index] = {
            ...updatedTask,
            last_check_in_time: updatedTask.last_check_in_time || originalTask.last_check_in_time,
            last_check_in_status:
              updatedTask.last_check_in_status || originalTask.last_check_in_status,
          };
        }
        return updatedTask;
      } catch (error) {
        this.error = error.message || '切换任务状态失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 获取任务详情
    async fetchTask(taskId) {
      this.loading = true;
      this.error = null;
      try {
        const task = await api.task.getTask(taskId);
        this.currentTask = task;
        return task;
      } catch (error) {
        this.error = error.message || '获取任务详情失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 手动触发任务打卡（异步方式，立即返回 record_id）
    async checkInTask(taskId) {
      // Don't set global loading state to avoid blocking UI during long check-in operations
      this.error = null;
      try {
        const result = await api.task.checkInTask(taskId);
        return result;
      } catch (error) {
        this.error = error.message || '打卡失败';
        throw error;
      }
    },

    // 查询打卡记录状态
    async getCheckInRecordStatus(recordId) {
      const result = await api.task.getCheckInRecordStatus(recordId);
      return result;
    },

    // 获取任务的打卡记录
    async fetchTaskRecords(taskId, params = {}) {
      this.loading = true;
      this.error = null;
      try {
        const records = await api.task.getTaskRecords(taskId, params);
        return records;
      } catch (error) {
        this.error = error.message || '获取打卡记录失败';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    // 清空当前任务
    clearCurrentTask() {
      this.currentTask = null;
    },
  },
});
