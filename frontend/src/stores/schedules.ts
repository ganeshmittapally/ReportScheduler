/**
 * Pinia store for schedules management
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Schedule, ScheduleFormData, PaginatedResponse } from '@/types'
import apiService from '@/services/api'

export const useSchedulesStore = defineStore('schedules', () => {
  // State
  const schedules = ref<Schedule[]>([])
  const currentSchedule = ref<Schedule | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const pagination = ref({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0
  })

  // Getters
  const activeSchedules = computed(() => schedules.value.filter((s) => s.is_active))
  const inactiveSchedules = computed(() => schedules.value.filter((s) => !s.is_active))
  const scheduleCount = computed(() => schedules.value.length)

  // Actions
  async function fetchSchedules(page = 1, pageSize = 20) {
    loading.value = true
    error.value = null
    try {
      const response: PaginatedResponse<Schedule> = await apiService.getSchedules(page, pageSize)
      schedules.value = response.items
      pagination.value = {
        page: response.page,
        pageSize: response.page_size,
        total: response.total,
        totalPages: response.total_pages
      }
    } catch (err: any) {
      error.value = err.detail || 'Failed to fetch schedules'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchSchedule(id: string) {
    loading.value = true
    error.value = null
    try {
      currentSchedule.value = await apiService.getSchedule(id)
      return currentSchedule.value
    } catch (err: any) {
      error.value = err.detail || 'Failed to fetch schedule'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createSchedule(data: ScheduleFormData) {
    loading.value = true
    error.value = null
    try {
      const newSchedule = await apiService.createSchedule(data)
      schedules.value.unshift(newSchedule)
      pagination.value.total++
      return newSchedule
    } catch (err: any) {
      error.value = err.detail || 'Failed to create schedule'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateSchedule(id: string, data: Partial<ScheduleFormData>) {
    loading.value = true
    error.value = null
    try {
      const updated = await apiService.updateSchedule(id, data)
      const index = schedules.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        schedules.value[index] = updated
      }
      if (currentSchedule.value?.id === id) {
        currentSchedule.value = updated
      }
      return updated
    } catch (err: any) {
      error.value = err.detail || 'Failed to update schedule'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteSchedule(id: string) {
    loading.value = true
    error.value = null
    try {
      await apiService.deleteSchedule(id)
      schedules.value = schedules.value.filter((s) => s.id !== id)
      pagination.value.total--
      if (currentSchedule.value?.id === id) {
        currentSchedule.value = null
      }
    } catch (err: any) {
      error.value = err.detail || 'Failed to delete schedule'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function pauseSchedule(id: string) {
    loading.value = true
    error.value = null
    try {
      const updated = await apiService.pauseSchedule(id)
      const index = schedules.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        schedules.value[index] = updated
      }
      return updated
    } catch (err: any) {
      error.value = err.detail || 'Failed to pause schedule'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function resumeSchedule(id: string) {
    loading.value = true
    error.value = null
    try {
      const updated = await apiService.resumeSchedule(id)
      const index = schedules.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        schedules.value[index] = updated
      }
      return updated
    } catch (err: any) {
      error.value = err.detail || 'Failed to resume schedule'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function triggerSchedule(id: string) {
    loading.value = true
    error.value = null
    try {
      const result = await apiService.triggerSchedule(id)
      return result.execution_run_id
    } catch (err: any) {
      error.value = err.detail || 'Failed to trigger schedule'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function previewCron(cronExpression: string, timezone: string) {
    try {
      return await apiService.previewCron(cronExpression, timezone)
    } catch (err: any) {
      error.value = err.detail || 'Failed to preview cron'
      throw err
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    schedules,
    currentSchedule,
    loading,
    error,
    pagination,
    // Getters
    activeSchedules,
    inactiveSchedules,
    scheduleCount,
    // Actions
    fetchSchedules,
    fetchSchedule,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    pauseSchedule,
    resumeSchedule,
    triggerSchedule,
    previewCron,
    clearError
  }
})
