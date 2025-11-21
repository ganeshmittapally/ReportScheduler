/**
 * Pinia store for report definitions management
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ReportDefinition, ReportDefinitionFormData, PaginatedResponse } from '@/types'
import apiService from '@/services/api'

export const useReportsStore = defineStore('reports', () => {
  // State
  const reports = ref<ReportDefinition[]>([])
  const currentReport = ref<ReportDefinition | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const pagination = ref({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0
  })

  // Getters
  const reportCount = computed(() => reports.value.length)
  const pdfReports = computed(() => reports.value.filter((r) => r.output_format === 'pdf'))
  const excelReports = computed(() => reports.value.filter((r) => r.output_format === 'xlsx'))

  // Actions
  async function fetchReports(page = 1, pageSize = 20) {
    loading.value = true
    error.value = null
    try {
      const response: PaginatedResponse<ReportDefinition> = await apiService.getReportDefinitions(
        page,
        pageSize
      )
      reports.value = response.items
      pagination.value = {
        page: response.page,
        pageSize: response.page_size,
        total: response.total,
        totalPages: response.total_pages
      }
    } catch (err: any) {
      error.value = err.detail || 'Failed to fetch reports'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchReport(id: string) {
    loading.value = true
    error.value = null
    try {
      currentReport.value = await apiService.getReportDefinition(id)
      return currentReport.value
    } catch (err: any) {
      error.value = err.detail || 'Failed to fetch report'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createReport(data: ReportDefinitionFormData) {
    loading.value = true
    error.value = null
    try {
      const newReport = await apiService.createReportDefinition(data)
      reports.value.unshift(newReport)
      pagination.value.total++
      return newReport
    } catch (err: any) {
      error.value = err.detail || 'Failed to create report'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateReport(id: string, data: Partial<ReportDefinitionFormData>) {
    loading.value = true
    error.value = null
    try {
      const updated = await apiService.updateReportDefinition(id, data)
      const index = reports.value.findIndex((r) => r.id === id)
      if (index !== -1) {
        reports.value[index] = updated
      }
      if (currentReport.value?.id === id) {
        currentReport.value = updated
      }
      return updated
    } catch (err: any) {
      error.value = err.detail || 'Failed to update report'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteReport(id: string) {
    loading.value = true
    error.value = null
    try {
      await apiService.deleteReportDefinition(id)
      reports.value = reports.value.filter((r) => r.id !== id)
      pagination.value.total--
      if (currentReport.value?.id === id) {
        currentReport.value = null
      }
    } catch (err: any) {
      error.value = err.detail || 'Failed to delete report'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    reports,
    currentReport,
    loading,
    error,
    pagination,
    // Getters
    reportCount,
    pdfReports,
    excelReports,
    // Actions
    fetchReports,
    fetchReport,
    createReport,
    updateReport,
    deleteReport,
    clearError
  }
})
