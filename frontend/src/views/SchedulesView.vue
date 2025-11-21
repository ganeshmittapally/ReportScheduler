<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-4">
          <div>
            <h1 class="text-h4">Schedules</h1>
            <p class="text-subtitle-1 text-medium-emphasis">
              Manage automated report generation schedules
            </p>
          </div>
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
            New Schedule
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Stats Cards -->
    <v-row>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">Total Schedules</div>
            <div class="text-h5">{{ schedulesStore.scheduleCount }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">Active</div>
            <div class="text-h5 text-success">{{ schedulesStore.activeSchedules.length }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">Paused</div>
            <div class="text-h5 text-warning">{{ schedulesStore.inactiveSchedules.length }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">Page</div>
            <div class="text-h5">
              {{ schedulesStore.pagination.page }} / {{ schedulesStore.pagination.totalPages }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Schedules Table -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-text-field
              v-model="search"
              append-inner-icon="mdi-magnify"
              label="Search schedules"
              single-line
              hide-details
              variant="outlined"
              density="compact"
              class="mb-2"
            ></v-text-field>
          </v-card-title>

          <v-data-table
            :headers="headers"
            :items="filteredSchedules"
            :loading="schedulesStore.loading"
            :items-per-page="20"
            class="elevation-0"
          >
            <template v-slot:item.name="{ item }">
              <div class="font-weight-medium">{{ item.name }}</div>
              <div class="text-caption text-medium-emphasis">{{ item.description }}</div>
            </template>

            <template v-slot:item.is_active="{ item }">
              <v-chip :color="item.is_active ? 'success' : 'warning'" size="small">
                {{ item.is_active ? 'Active' : 'Paused' }}
              </v-chip>
            </template>

            <template v-slot:item.cron_expression="{ item }">
              <code class="text-caption">{{ item.cron_expression }}</code>
            </template>

            <template v-slot:item.last_run_at="{ item }">
              <div v-if="item.last_run_at" class="text-caption">
                {{ formatDate(item.last_run_at) }}
              </div>
              <div v-else class="text-caption text-medium-emphasis">Never</div>
            </template>

            <template v-slot:item.next_run_at="{ item }">
              <div v-if="item.next_run_at" class="text-caption">
                {{ formatDate(item.next_run_at) }}
              </div>
              <div v-else class="text-caption text-medium-emphasis">-</div>
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                v-if="item.is_active"
                icon="mdi-pause"
                size="small"
                variant="text"
                @click="pauseSchedule(item.id)"
                title="Pause"
              ></v-btn>
              <v-btn
                v-else
                icon="mdi-play"
                size="small"
                variant="text"
                color="success"
                @click="resumeSchedule(item.id)"
                title="Resume"
              ></v-btn>
              <v-btn
                icon="mdi-play-circle"
                size="small"
                variant="text"
                color="primary"
                @click="triggerSchedule(item.id)"
                title="Trigger Now"
              ></v-btn>
              <v-btn
                icon="mdi-pencil"
                size="small"
                variant="text"
                @click="openEditDialog(item)"
                title="Edit"
              ></v-btn>
              <v-btn
                icon="mdi-delete"
                size="small"
                variant="text"
                color="error"
                @click="confirmDelete(item)"
                title="Delete"
              ></v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="800px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editMode ? 'Edit Schedule' : 'New Schedule' }}</span>
        </v-card-title>
        <v-card-text>
          <v-form ref="form" v-model="formValid">
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="formData.name"
                  label="Name"
                  :rules="[rules.required]"
                  variant="outlined"
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="formData.description"
                  label="Description"
                  variant="outlined"
                  rows="2"
                ></v-textarea>
              </v-col>
              <v-col cols="12" md="8">
                <v-text-field
                  v-model="formData.cron_expression"
                  label="Cron Expression"
                  :rules="[rules.required]"
                  variant="outlined"
                  hint="Example: 0 9 * * MON (Every Monday at 9 AM)"
                  persistent-hint
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-btn block color="primary" @click="previewCron" :disabled="!formData.cron_expression">
                  Preview
                </v-btn>
              </v-col>
              <v-col cols="12" v-if="cronPreview">
                <v-alert v-if="cronPreview.is_valid" type="success" density="compact">
                  <div class="text-caption">Next 5 runs:</div>
                  <div v-for="(run, i) in cronPreview.next_5_runs" :key="i" class="text-caption">
                    {{ i + 1 }}. {{ formatDate(run) }}
                  </div>
                </v-alert>
                <v-alert v-else type="error" density="compact">
                  {{ cronPreview.error_message }}
                </v-alert>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="formData.timezone"
                  :items="timezones"
                  label="Timezone"
                  :rules="[rules.required]"
                  variant="outlined"
                  required
                ></v-select>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="formData.report_definition_id"
                  :items="reportOptions"
                  label="Report Definition"
                  :rules="[rules.required]"
                  variant="outlined"
                  required
                ></v-select>
              </v-col>
              <v-col cols="12">
                <v-switch
                  v-model="formData.is_active"
                  label="Active"
                  color="success"
                  hide-details
                ></v-switch>
              </v-col>
              <v-col cols="12">
                <v-divider></v-divider>
                <div class="text-subtitle-2 mt-2 mb-2">Email Delivery (Optional)</div>
              </v-col>
              <v-col cols="12">
                <v-combobox
                  v-model="emailRecipients"
                  label="Recipients"
                  hint="Press Enter after each email"
                  persistent-hint
                  multiple
                  chips
                  variant="outlined"
                ></v-combobox>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="closeDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            :disabled="!formValid"
            :loading="schedulesStore.loading"
            @click="saveSchedule"
          >
            {{ editMode ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400px">
      <v-card>
        <v-card-title>Delete Schedule</v-card-title>
        <v-card-text>
          Are you sure you want to delete "{{ scheduleToDelete?.name }}"? This action cannot be
          undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" :loading="schedulesStore.loading" @click="deleteSchedule">
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar for notifications -->
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
import { useSchedulesStore } from '@/stores/schedules'
import { useReportsStore } from '@/stores/reports'
import type { Schedule, ScheduleFormData, CronPreview } from '@/types'

const schedulesStore = useSchedulesStore()
const reportsStore = useReportsStore()

const search = ref('')
const dialog = ref(false)
const deleteDialog = ref(false)
const editMode = ref(false)
const formValid = ref(false)
const form = ref()
const scheduleToDelete = ref<Schedule | null>(null)
const cronPreview = ref<CronPreview | null>(null)

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const emailRecipients = ref<string[]>([])

const formData = ref<ScheduleFormData>({
  name: '',
  description: '',
  report_definition_id: '',
  cron_expression: '0 9 * * MON',
  timezone: 'UTC',
  is_active: true
})

const currentScheduleId = ref<string | null>(null)

const headers: any[] = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Status', key: 'is_active', sortable: true },
  { title: 'Schedule', key: 'cron_expression', sortable: false },
  { title: 'Last Run', key: 'last_run_at', sortable: true },
  { title: 'Next Run', key: 'next_run_at', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'center' }
]

const rules = {
  required: (v: string) => !!v || 'This field is required'
}

const timezones = ['UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Asia/Tokyo']

const reportOptions = computed(() =>
  reportsStore.reports.map((r) => ({
    title: r.name,
    value: r.id
  }))
)

const filteredSchedules = computed(() => {
  if (!search.value) return schedulesStore.schedules
  const searchLower = search.value.toLowerCase()
  return schedulesStore.schedules.filter(
    (s) =>
      s.name.toLowerCase().includes(searchLower) ||
      s.description?.toLowerCase().includes(searchLower)
  )
})

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString()
}

async function previewCron() {
  if (!formData.value.cron_expression) return
  try {
    cronPreview.value = await schedulesStore.previewCron(
      formData.value.cron_expression,
      formData.value.timezone
    )
  } catch (error) {
    showSnackbar('Failed to preview cron expression', 'error')
  }
}

function openCreateDialog() {
  editMode.value = false
  currentScheduleId.value = null
  formData.value = {
    name: '',
    description: '',
    report_definition_id: '',
    cron_expression: '0 9 * * MON',
    timezone: 'UTC',
    is_active: true
  }
  emailRecipients.value = []
  cronPreview.value = null
  dialog.value = true
}

function openEditDialog(schedule: Schedule) {
  editMode.value = true
  currentScheduleId.value = schedule.id
  formData.value = {
    name: schedule.name,
    description: schedule.description,
    report_definition_id: schedule.report_definition_id,
    cron_expression: schedule.cron_expression,
    timezone: schedule.timezone,
    is_active: schedule.is_active
  }
  emailRecipients.value = schedule.email_delivery_config?.recipients || []
  cronPreview.value = null
  dialog.value = true
}

function closeDialog() {
  dialog.value = false
  cronPreview.value = null
}

async function saveSchedule() {
  if (!form.value) return
  const { valid } = await form.value.validate()
  if (!valid) return

  const payload: ScheduleFormData = {
    ...formData.value
  }

  if (emailRecipients.value.length > 0) {
    payload.email_delivery_config = {
      recipients: emailRecipients.value
    }
  }

  try {
    if (editMode.value && currentScheduleId.value) {
      await schedulesStore.updateSchedule(currentScheduleId.value, payload)
      showSnackbar('Schedule updated successfully')
    } else {
      await schedulesStore.createSchedule(payload)
      showSnackbar('Schedule created successfully')
    }
    closeDialog()
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to save schedule', 'error')
  }
}

async function pauseSchedule(id: string) {
  try {
    await schedulesStore.pauseSchedule(id)
    showSnackbar('Schedule paused')
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to pause schedule', 'error')
  }
}

async function resumeSchedule(id: string) {
  try {
    await schedulesStore.resumeSchedule(id)
    showSnackbar('Schedule resumed')
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to resume schedule', 'error')
  }
}

async function triggerSchedule(id: string) {
  try {
    const executionId = await schedulesStore.triggerSchedule(id)
    showSnackbar(`Report generation triggered (${executionId})`)
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to trigger schedule', 'error')
  }
}

function confirmDelete(schedule: Schedule) {
  scheduleToDelete.value = schedule
  deleteDialog.value = true
}

async function deleteSchedule() {
  if (!scheduleToDelete.value) return
  try {
    await schedulesStore.deleteSchedule(scheduleToDelete.value.id)
    showSnackbar('Schedule deleted')
    deleteDialog.value = false
    scheduleToDelete.value = null
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to delete schedule', 'error')
  }
}

function showSnackbar(text: string, color = 'success') {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(async () => {
  await Promise.all([schedulesStore.fetchSchedules(), reportsStore.fetchReports(1, 100)])
})
</script>
