<template>
  <div>
      <v-container fluid>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-2">Dashboard</h1>
        <p class="text-subtitle-1 text-medium-emphasis mb-4">
          Overview of your report scheduling system
        </p>
      </v-col>
    </v-row>

    <!-- Main Metrics -->
    <v-row>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-overline text-medium-emphasis">Total Schedules</div>
                <div class="text-h4">{{ metrics?.total_schedules || 0 }}</div>
              </div>
              <v-icon size="48" color="primary">mdi-file-document-multiple</v-icon>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-overline text-medium-emphasis">Active Schedules</div>
                <div class="text-h4">{{ metrics?.active_schedules || 0 }}</div>
              </div>
              <v-icon size="48" color="success">mdi-calendar-check</v-icon>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-overline text-medium-emphasis">Total Executions</div>
                <div class="text-h4">{{ metrics?.total_executions || 0 }}</div>
              </div>
              <v-icon size="48" color="info">mdi-play-circle</v-icon>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-overline text-medium-emphasis">Success Rate</div>
                <div class="text-h4">
                  {{ successRate }}%
                </div>
              </div>
              <v-icon size="48" :color="getSuccessRateColor(successRate)">
                mdi-chart-line
              </v-icon>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Cache and Burst Protection Stats -->
    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Cache Statistics</v-card-title>
          <v-card-text v-if="cacheStats">
            <v-row dense>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">Hit Rate</div>
                <div class="text-h5">{{ cacheStats.hit_rate.toFixed(1) }}%</div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">Total Keys</div>
                <div class="text-h5">{{ cacheStats.total_keys }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">Hits</div>
                <div class="text-body-1">{{ cacheStats.hits }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">Misses</div>
                <div class="text-body-1">{{ cacheStats.misses }}</div>
              </v-col>
            </v-row>
          </v-card-text>
          <v-card-text v-else>
            <v-progress-circular indeterminate></v-progress-circular>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Burst Protection Status</v-card-title>
          <v-card-text v-if="burstStatus && burstStatus.length > 0">
            <v-list density="compact">
              <v-list-item v-for="tenant in burstStatus" :key="tenant.tenant_id">
                <v-list-item-title>{{ tenant.tenant_id }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ tenant.active_tasks }} / {{ tenant.max_concurrent }} tasks
                  <v-progress-linear
                    :model-value="(tenant.active_tasks / tenant.max_concurrent) * 100"
                    :color="tenant.active_tasks >= tenant.max_concurrent ? 'error' : 'success'"
                    class="mt-1"
                  ></v-progress-linear>
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
          <v-card-text v-else>
            <div class="text-center text-medium-emphasis">No active tasks</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent Activity -->
    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Recent Executions</v-card-title>
          <v-list density="compact" v-if="recentExecutions.length > 0">
            <v-list-item v-for="execution in recentExecutions" :key="execution.id">
              <template v-slot:prepend>
                <v-icon :color="getStatusColor(execution.status)">
                  {{ getStatusIcon(execution.status) }}
                </v-icon>
              </template>
              <v-list-item-title>
                Execution {{ execution.id.substring(0, 8) }}
              </v-list-item-title>
              <v-list-item-subtitle>
                {{ formatDate(execution.started_at) }}
              </v-list-item-subtitle>
              <template v-slot:append>
                <v-chip :color="getStatusColor(execution.status)" size="x-small">
                  {{ execution.status }}
                </v-chip>
              </template>
            </v-list-item>
          </v-list>
          <v-card-text v-else>
            <div class="text-center text-medium-emphasis py-4">
              No recent executions
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Active Schedules</v-card-title>
          <v-list density="compact" v-if="activeSchedules.length > 0">
            <v-list-item v-for="schedule in activeSchedules" :key="schedule.id">
              <template v-slot:prepend>
                <v-icon color="success">mdi-calendar-check</v-icon>
              </template>
              <v-list-item-title>{{ schedule.name }}</v-list-item-title>
              <v-list-item-subtitle>
                Next run: {{ schedule.next_run_at ? formatDate(schedule.next_run_at) : 'Not scheduled' }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
          <v-card-text v-else>
            <div class="text-center text-medium-emphasis py-4">
              No active schedules
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Quick Actions -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>Quick Actions</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" sm="6" md="3">
                <v-btn
                  block
                  color="primary"
                  prepend-icon="mdi-plus"
                  to="/schedules"
                  variant="outlined"
                >
                  New Schedule
                </v-btn>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-btn
                  block
                  color="primary"
                  prepend-icon="mdi-file-document-plus"
                  to="/reports"
                  variant="outlined"
                >
                  New Report
                </v-btn>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-btn
                  block
                  color="primary"
                  prepend-icon="mdi-history"
                  to="/executions"
                  variant="outlined"
                >
                  View Executions
                </v-btn>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-btn
                  block
                  color="primary"
                  prepend-icon="mdi-image-multiple"
                  to="/gallery"
                  variant="outlined"
                >
                  Browse Gallery
                </v-btn>
              </v-col>
            </v-row>
            </v-container>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useSchedulesStore } from '@/stores/schedules'
import { useExecutionsStore } from '@/stores/executions'
import { apiService } from '@/services/api'
import type { DashboardMetrics } from '@/types'

const schedulesStore = useSchedulesStore()
const executionsStore = useExecutionsStore()

const metrics = ref<DashboardMetrics | null>(null)
const cacheStats = ref<any | null>(null)
const burstStatus = ref<any[]>([])

async function fetchDashboardData() {
  try {
    const [metricsData, cacheData, burstData] = await Promise.all([
      apiService.getDashboardMetrics(),
      apiService.getCacheStats(),
      apiService.getBurstProtectionStatus()
    ])
    metrics.value = metricsData
    cacheStats.value = cacheData
    burstStatus.value = burstData
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

const activeSchedules = computed(() => schedulesStore.activeSchedules.slice(0, 5))
const recentExecutions = computed(() => executionsStore.executions.slice(0, 5))
const successRate = computed(() => {
  if (!metrics.value || metrics.value.total_executions === 0) return 0
  return Math.round((metrics.value.successful_executions / metrics.value.total_executions) * 100)
})

function getSuccessRateColor(rate: number): string {
  if (rate >= 90) return 'success'
  if (rate >= 70) return 'warning'
  return 'error'
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'grey',
    running: 'blue',
    completed: 'success',
    failed: 'error'
  }
  return colors[status] || 'grey'
}

function getStatusIcon(status: string): string {
  const icons: Record<string, string> = {
    pending: 'mdi-clock-outline',
    running: 'mdi-loading',
    completed: 'mdi-check-circle',
    failed: 'mdi-alert-circle'
  }
  return icons[status] || 'mdi-help-circle'
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString()
}

onMounted(async () => {
  await Promise.all([
    fetchDashboardData(),
    schedulesStore.fetchSchedules(),
    executionsStore.fetchExecutions(1, 5)
  ])
})
</script>
