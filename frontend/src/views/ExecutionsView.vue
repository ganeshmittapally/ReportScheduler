<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-4">
          <div>
            <h1 class="text-h4">Execution History</h1>
            <p class="text-subtitle-1 text-medium-emphasis">
              Monitor and track report generation executions
            </p>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Stats Cards -->
    <v-row>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">Total Executions</div>
            <div class="text-h5">{{ executionsStore.executions.length }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">Completed</div>
            <div class="text-h5 text-success">{{ executionsStore.completedExecutions.length }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">Failed</div>
            <div class="text-h5 text-error">{{ executionsStore.failedExecutions.length }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">Success Rate</div>
            <div class="text-h5">{{ executionsStore.successRate.toFixed(1) }}%</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Filters -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="3">
                <v-select
                  v-model="filters.status"
                  :items="statusOptions"
                  label="Status"
                  variant="outlined"
                  density="compact"
                  clearable
                  @update:model-value="applyFilters"
                ></v-select>
              </v-col>
              <v-col cols="12" md="3">
                <v-select
                  v-model="filters.schedule_id"
                  :items="scheduleOptions"
                  label="Schedule"
                  variant="outlined"
                  density="compact"
                  clearable
                  @update:model-value="applyFilters"
                ></v-select>
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model="filters.start_date"
                  label="Start Date"
                  type="date"
                  variant="outlined"
                  density="compact"
                  clearable
                  @update:model-value="applyFilters"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model="filters.end_date"
                  label="End Date"
                  type="date"
                  variant="outlined"
                  density="compact"
                  clearable
                  @update:model-value="applyFilters"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Executions Table -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-data-table
            :headers="headers"
            :items="executionsStore.executions"
            :loading="executionsStore.loading"
            :items-per-page="20"
            class="elevation-0"
          >
            <template v-slot:item.status="{ item }">
              <v-chip :color="getStatusColor(item.status)" size="small">
                {{ item.status }}
              </v-chip>
            </template>

            

            <template v-slot:item.started_at="{ item }">
              <div v-if="item.started_at" class="text-caption">
                {{ formatDate(item.started_at) }}
              </div>
              <div v-else class="text-caption text-medium-emphasis">-</div>
            </template>

            <template v-slot:item.completed_at="{ item }">
              <div v-if="item.completed_at" class="text-caption">
                {{ formatDate(item.completed_at) }}
              </div>
              <div v-else class="text-caption text-medium-emphasis">-</div>
            </template>

            <template v-slot:item.duration="{ item }">
              <div v-if="item.started_at && item.completed_at" class="text-caption">
                {{ calculateDuration(item.started_at, item.completed_at) }}
              </div>
              <div v-else class="text-caption text-medium-emphasis">-</div>
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                icon="mdi-eye"
                size="small"
                variant="text"
                @click="viewDetails(item.id)"
                title="View Details"
              ></v-btn>
              <v-btn
                v-if="item.status === 'completed'"
                icon="mdi-download"
                size="small"
                variant="text"
                color="primary"
                @click="downloadArtifact(item.id)"
                title="Download Report"
              ></v-btn>
              <v-btn
                v-if="item.status === 'failed'"
                icon="mdi-refresh"
                size="small"
                variant="text"
                color="warning"
                @click="retryExecution(item.id)"
                title="Retry"
              ></v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Details Dialog -->
    <v-dialog v-model="detailsDialog" max-width="800px">
      <v-card v-if="executionsStore.currentExecution">
        <v-card-title>Execution Details</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis">Status</div>
              <v-chip :color="getStatusColor(executionsStore.currentExecution.status)" class="mt-1">
                {{ executionsStore.currentExecution.status }}
              </v-chip>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis">Schedule ID</div>
              <code class="text-caption">{{ executionsStore.currentExecution.schedule_id }}</code>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis">Started At</div>
              <div class="text-body-2" v-if="executionsStore.currentExecution.started_at">
                {{ formatDate(executionsStore.currentExecution.started_at) }}
              </div>
              <div v-else class="text-body-2 text-medium-emphasis">-</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis">Completed At</div>
              <div class="text-body-2" v-if="executionsStore.currentExecution.completed_at">
                {{ formatDate(executionsStore.currentExecution.completed_at) }}
              </div>
              <div v-else class="text-body-2 text-medium-emphasis">-</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis">Duration</div>
              <div
                class="text-body-2"
                v-if="
                  executionsStore.currentExecution.started_at &&
                  executionsStore.currentExecution.completed_at
                "
              >
                {{
                  calculateDuration(
                    executionsStore.currentExecution.started_at,
                    executionsStore.currentExecution.completed_at
                  )
                }}
              </div>
              <div v-else class="text-body-2 text-medium-emphasis">-</div>
            </v-col>

            <v-col cols="12" v-if="executionsStore.currentExecution.error_message">
              <v-divider class="mb-3"></v-divider>
              <div class="text-caption text-medium-emphasis">Error Message</div>
              <v-alert type="error" density="compact" class="mt-2">
                {{ executionsStore.currentExecution.error_message }}
              </v-alert>
            </v-col>

            <v-col cols="12" v-if="executionsStore.currentArtifact">
              <v-divider class="mb-3"></v-divider>
              <div class="text-subtitle-2 mb-2">Artifact Details</div>
              <v-row dense>
                <v-col cols="12" md="6">
                  <div class="text-caption text-medium-emphasis">Blob Path</div>
                  <div class="text-body-2">{{ executionsStore.currentArtifact.blob_path }}</div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="text-caption text-medium-emphasis">Format</div>
                  <div class="text-body-2">{{ executionsStore.currentArtifact.file_format }}</div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="text-caption text-medium-emphasis">Size</div>
                  <div class="text-body-2">
                    {{ formatFileSize(executionsStore.currentArtifact.file_size_bytes) }}
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="text-caption text-medium-emphasis">Signed URL Expires</div>
                  <div class="text-body-2">
                    {{ formatDate(executionsStore.currentArtifact.signed_url_expires_at) }}
                  </div>
                </v-col>
              </v-row>
            </v-col>

            <v-col cols="12" v-if="executionsStore.currentReceipts.length > 0">
              <v-divider class="mb-3"></v-divider>
              <div class="text-subtitle-2 mb-2">Delivery Receipts</div>
              <v-list density="compact">
                <v-list-item v-for="receipt in executionsStore.currentReceipts" :key="receipt.id">
                  <template v-slot:prepend>
                    <v-icon :color="receipt.status === 'sent' ? 'success' : 'error'">
                      {{ receipt.status === 'sent' ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                    </v-icon>
                  </template>
                  <v-list-item-title>{{ receipt.recipient }}</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ receipt.status }} - {{ formatDate(receipt.sent_at || receipt.created_at) }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="detailsDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" :timeout="3000">
      {{ snackbarText }}
      <template v-slot:actions>
        <v-btn icon="mdi-close" @click="snackbar = false"></v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useExecutionsStore } from '@/stores/executions'
import { useSchedulesStore } from '@/stores/schedules'
import type { ExecutionFilters } from '@/types'

const executionsStore = useExecutionsStore()
const schedulesStore = useSchedulesStore()

const detailsDialog = ref(false)
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const filters = ref<ExecutionFilters>({})

const headers: any[] = [
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Started At', key: 'started_at', sortable: true },
  { title: 'Completed At', key: 'completed_at', sortable: true },
  { title: 'Duration', key: 'duration', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false, align: 'center' }
]

const statusOptions = [
  { title: 'Pending', value: 'pending' },
  { title: 'Running', value: 'running' },
  { title: 'Completed', value: 'completed' },
  { title: 'Failed', value: 'failed' }
]

const scheduleOptions = computed(() =>
  schedulesStore.schedules.map((s) => ({
    title: s.name,
    value: s.id
  }))
)

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'grey',
    running: 'blue',
    completed: 'success',
    failed: 'error'
  }
  return colors[status] || 'grey'
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString()
}

function calculateDuration(start: string, end: string): string {
  const ms = new Date(end).getTime() - new Date(start).getTime()
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

async function applyFilters() {
  await executionsStore.fetchExecutions(1, 20, filters.value)
}

async function viewDetails(id: string) {
  try {
    await executionsStore.fetchExecution(id)
    detailsDialog.value = true
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to load execution details', 'error')
  }
}

async function downloadArtifact(executionId: string) {
  try {
    await executionsStore.fetchExecution(executionId, true)
    if (executionsStore.currentArtifact?.signed_url) {
      window.open(executionsStore.currentArtifact.signed_url, '_blank')
    } else {
      showSnackbar('No artifact available for download', 'warning')
    }
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to fetch artifact', 'error')
  }
}

async function retryExecution(id: string) {
  try {
    await executionsStore.retryExecution(id)
    showSnackbar('Execution retry triggered')
    await applyFilters()
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to retry execution', 'error')
  }
}

function showSnackbar(text: string, color = 'success') {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(async () => {
  await Promise.all([executionsStore.fetchExecutions(1, 20), schedulesStore.fetchSchedules()])
})
</script>
