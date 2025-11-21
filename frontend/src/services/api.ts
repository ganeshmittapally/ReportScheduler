/**
 * API service layer for backend communication
 */

import axios, { type AxiosInstance, type AxiosError } from 'axios'
import type {
  Schedule,
  ScheduleFormData,
  ReportDefinition,
  ReportDefinitionFormData,
  ExecutionRun,
  Artifact,
  DeliveryReceipt,
  AuditEvent,
  CronPreview,
  DashboardMetrics,
  PaginatedResponse,
  ExecutionFilters,
  ArtifactFilters,
  ApiError
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class ApiService {
  private client: AxiosInstance
  private tenantId: string = 'default-tenant' // TODO: Get from auth context

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 30000
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add tenant header
        config.headers['X-Tenant-ID'] = this.tenantId
        // TODO: Add auth token
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        const apiError: ApiError = {
          detail: error.response?.data?.detail || error.message || 'An error occurred',
          status_code: error.response?.status
        }
        return Promise.reject(apiError)
      }
    )
  }

  setTenantId(tenantId: string) {
    this.tenantId = tenantId
  }

  // Health check
  async healthCheck() {
    const response = await this.client.get('/health')
    return response.data
  }

  // Schedules API
  async getSchedules(page = 1, pageSize = 20): Promise<PaginatedResponse<Schedule>> {
    const response = await this.client.get('/api/v1/schedules', {
      params: { page, page_size: pageSize }
    })
    return response.data
  }

  async getSchedule(id: string): Promise<Schedule> {
    const response = await this.client.get(`/api/v1/schedules/${id}`)
    return response.data
  }

  async createSchedule(data: ScheduleFormData): Promise<Schedule> {
    const payload = {
      ...data,
      tenant_id: this.tenantId
    }
    const response = await this.client.post('/api/v1/schedules', payload)
    return response.data
  }

  async updateSchedule(id: string, data: Partial<ScheduleFormData>): Promise<Schedule> {
    const response = await this.client.put(`/api/v1/schedules/${id}`, data)
    return response.data
  }

  async deleteSchedule(id: string): Promise<void> {
    await this.client.delete(`/api/v1/schedules/${id}`)
  }

  async pauseSchedule(id: string): Promise<Schedule> {
    const response = await this.client.post(`/api/v1/schedules/${id}/pause`)
    return response.data
  }

  async resumeSchedule(id: string): Promise<Schedule> {
    const response = await this.client.post(`/api/v1/schedules/${id}/resume`)
    return response.data
  }

  async previewCron(cronExpression: string, timezone: string): Promise<CronPreview> {
    const response = await this.client.post('/api/v1/schedules/cron/preview', {
      cron_expression: cronExpression,
      timezone
    })
    return response.data
  }

  async triggerSchedule(id: string): Promise<{ execution_run_id: string }> {
    const response = await this.client.post(`/api/v1/schedules/${id}/trigger`)
    return response.data
  }

  // Report Definitions API
  async getReportDefinitions(
    page = 1,
    pageSize = 20
  ): Promise<PaginatedResponse<ReportDefinition>> {
    const response = await this.client.get('/api/v1/reports', {
      params: { page, page_size: pageSize }
    })
    return response.data
  }

  async getReportDefinition(id: string): Promise<ReportDefinition> {
    const response = await this.client.get(`/api/v1/reports/${id}`)
    return response.data
  }

  async createReportDefinition(data: ReportDefinitionFormData): Promise<ReportDefinition> {
    const payload = {
      ...data,
      tenant_id: this.tenantId
    }
    const response = await this.client.post('/api/v1/reports', payload)
    return response.data
  }

  async updateReportDefinition(
    id: string,
    data: Partial<ReportDefinitionFormData>
  ): Promise<ReportDefinition> {
    const response = await this.client.put(`/api/v1/reports/${id}`, data)
    return response.data
  }

  async deleteReportDefinition(id: string): Promise<void> {
    await this.client.delete(`/api/v1/reports/${id}`)
  }

  // Executions API
  async getExecutions(
    filters?: ExecutionFilters,
    page = 1,
    pageSize = 20
  ): Promise<PaginatedResponse<ExecutionRun>> {
    const response = await this.client.get('/api/v1/executions', {
      params: { ...filters, page, page_size: pageSize }
    })
    return response.data
  }

  async getExecution(id: string): Promise<ExecutionRun> {
    const response = await this.client.get(`/api/v1/executions/${id}`)
    return response.data
  }

  async getExecutionArtifact(executionId: string): Promise<Artifact | null> {
    try {
      const response = await this.client.get(`/api/v1/executions/${executionId}/artifact`)
      return response.data
    } catch (error) {
      return null
    }
  }

  async getExecutionReceipts(executionId: string): Promise<DeliveryReceipt[]> {
    const response = await this.client.get(`/api/v1/executions/${executionId}/receipts`)
    return response.data
  }

  async retryExecution(id: string): Promise<{ execution_run_id: string }> {
    const response = await this.client.post(`/api/v1/executions/${id}/retry`)
    return response.data
  }

  // Artifacts API
  async getArtifacts(
    filters?: ArtifactFilters,
    page = 1,
    pageSize = 20
  ): Promise<PaginatedResponse<Artifact>> {
    const response = await this.client.get('/api/v1/artifacts', {
      params: { ...filters, page, page_size: pageSize }
    })
    return response.data
  }

  async getArtifact(id: string): Promise<Artifact> {
    const response = await this.client.get(`/api/v1/artifacts/${id}`)
    return response.data
  }

  async refreshArtifactUrl(id: string): Promise<Artifact> {
    const response = await this.client.post(`/api/v1/artifacts/${id}/refresh-url`)
    return response.data
  }

  async deleteArtifact(id: string): Promise<void> {
    await this.client.delete(`/api/v1/artifacts/${id}`)
  }

  // Audit API
  async getAuditEvents(
    artifactId?: string,
    page = 1,
    pageSize = 20
  ): Promise<PaginatedResponse<AuditEvent>> {
    const response = await this.client.get('/api/v1/audit/events', {
      params: { artifact_id: artifactId, page, page_size: pageSize }
    })
    return response.data
  }

  async getComplianceReport(startDate: string, endDate: string): Promise<any> {
    const response = await this.client.get('/api/v1/audit/compliance', {
      params: { start_date: startDate, end_date: endDate }
    })
    return response.data
  }

  // Dashboard API
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const response = await this.client.get('/api/v1/dashboard/metrics')
    return response.data
  }

  async getCacheStats(): Promise<any> {
    const response = await this.client.get('/api/v1/cache/stats')
    return response.data
  }

  async getBurstProtectionStatus(): Promise<any> {
    const response = await this.client.get('/api/v1/burst-protection/status')
    return response.data
  }
}

export const apiService = new ApiService()
export default apiService
