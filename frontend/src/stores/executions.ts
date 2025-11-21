/**
 * Pinia store for executions management
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ExecutionRun,
  Artifact,
  DeliveryReceipt,
  ExecutionFilters,
  PaginatedResponse
} from '@/types'
import apiService from '@/services/api'

export const useExecutionsStore = defineStore('executions', () => {
  // State
  const executions = ref<ExecutionRun[]>([])
  const currentExecution = ref<ExecutionRun | null>(null)
  const currentArtifact = ref<Artifact | null>(null)
  const currentReceipts = ref<DeliveryReceipt[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const pagination = ref({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0
  })
  const filters = ref<ExecutionFilters>({})

  // Getters
  const completedExecutions = computed(() =>
    executions.value.filter((e) => e.status === 'completed')
  )
  const failedExecutions = computed(() => executions.value.filter((e) => e.status === 'failed'))
  const runningExecutions = computed(() =>
    executions.value.filter((e) => e.status === 'running' || e.status === 'pending')
  )

  const successRate = computed(() => {
    const total = executions.value.length
    if (total === 0) return 0
    const completed = completedExecutions.value.length
    return Math.round((completed / total) * 100)
  })

  // Actions
  async function fetchExecutions(page = 1, pageSize = 20, newFilters?: ExecutionFilters) {
    loading.value = true
    error.value = null
    if (newFilters) {
      filters.value = newFilters
    }
    try {
      const response: PaginatedResponse<ExecutionRun> = await apiService.getExecutions(
        filters.value,
        page,
        pageSize
      )
      executions.value = response.items
      pagination.value = {
        page: response.page,
        pageSize: response.page_size,
        total: response.total,
        totalPages: response.total_pages
      }
    } catch (err: any) {
      error.value = err.detail || 'Failed to fetch executions'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchExecution(id: string, includeDetails = true) {
    loading.value = true
    error.value = null
    try {
      currentExecution.value = await apiService.getExecution(id)

      if (includeDetails && currentExecution.value.status === 'completed') {
        // Fetch artifact and receipts
        currentArtifact.value = await apiService.getExecutionArtifact(id)
        if (currentArtifact.value) {
          currentReceipts.value = await apiService.getExecutionReceipts(id)
        }
      }

      return currentExecution.value
    } catch (err: any) {
      error.value = err.detail || 'Failed to fetch execution'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function retryExecution(id: string) {
    loading.value = true
    error.value = null
    try {
      const result = await apiService.retryExecution(id)
      return result.execution_run_id
    } catch (err: any) {
      error.value = err.detail || 'Failed to retry execution'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearFilters() {
    filters.value = {}
  }

  function clearError() {
    error.value = null
  }

  function clearCurrent() {
    currentExecution.value = null
    currentArtifact.value = null
    currentReceipts.value = []
  }

  return {
    // State
    executions,
    currentExecution,
    currentArtifact,
    currentReceipts,
    loading,
    error,
    pagination,
    filters,
    // Getters
    completedExecutions,
    failedExecutions,
    runningExecutions,
    successRate,
    // Actions
    fetchExecutions,
    fetchExecution,
    retryExecution,
    clearFilters,
    clearError,
    clearCurrent
  }
})
