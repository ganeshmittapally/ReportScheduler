/**
 * Type definitions for the ReportScheduler application
 */

export interface Schedule {
  id: string
  tenant_id: string
  name: string
  description?: string
  report_definition_id: string
  cron_expression: string
  timezone: string
  is_active: boolean
  email_delivery_config?: EmailDeliveryConfig
  date_range_config?: DateRangeConfig
  last_run_at?: string
  next_run_at?: string
  created_at: string
  updated_at: string
}

export interface EmailDeliveryConfig {
  recipients: string[]
  cc?: string[]
  bcc?: string[]
  subject?: string
}

export interface DateRangeConfig {
  range_type: string
  custom_start_date?: string
  custom_end_date?: string
}

export interface ReportDefinition {
  id: string
  tenant_id: string
  name: string
  description?: string
  query_spec: Record<string, any>
  template_ref: string
  output_format: 'pdf' | 'xlsx' | 'csv'
  execution_metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ExecutionRun {
  id: string
  tenant_id: string
  schedule_id?: string
  report_definition_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  started_at: string
  completed_at?: string
  duration_seconds?: number
  error_message?: string
  execution_metadata?: Record<string, any>
  created_at: string
}

export interface Artifact {
  id: string
  tenant_id: string
  execution_run_id: string
  blob_path: string
  file_size_bytes: number
  file_format: string
  signed_url: string
  signed_url_expires_at: string
  created_at: string
}

export interface DeliveryReceipt {
  id: string
  tenant_id: string
  artifact_id: string
  channel: string
  recipient: string
  status: 'sent' | 'failed'
  sent_at?: string
  error_message?: string
  created_at: string
}

export interface AuditEvent {
  id: string
  tenant_id: string
  event_type: string
  event_metadata: Record<string, any>
  created_at: string
}

export interface CronPreview {
  is_valid: boolean
  error_message?: string
  next_5_runs?: string[]
}

export interface DashboardMetrics {
  total_schedules: number
  active_schedules: number
  total_executions: number
  successful_executions: number
  failed_executions: number
  running_executions: number
  total_artifacts: number
  total_storage_mb: number
  cache_hit_ratio?: number
  avg_execution_duration?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ApiError {
  detail: string
  status_code?: number
}

// Form types
export interface ScheduleFormData {
  name: string
  description?: string
  report_definition_id: string
  cron_expression: string
  timezone: string
  is_active: boolean
  email_delivery_config?: EmailDeliveryConfig
  date_range_config?: DateRangeConfig
}

export interface ReportDefinitionFormData {
  name: string
  description?: string
  query_spec: Record<string, any>
  template_ref: string
  output_format: 'pdf' | 'xlsx' | 'csv'
  execution_metadata?: Record<string, any>
}

// Filter types
export interface ExecutionFilters {
  status?: string
  schedule_id?: string
  report_definition_id?: string
  start_date?: string
  end_date?: string
}

export interface ArtifactFilters {
  execution_run_id?: string
  file_format?: string
  start_date?: string
  end_date?: string
}
