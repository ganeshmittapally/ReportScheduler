<template>
  <div>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-4">
          <div>
            <h1 class="text-h4">Report Definitions</h1>
            <p class="text-subtitle-1 text-medium-emphasis">
              Manage report templates and configurations
            </p>
          </div>
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
            New Report Definition
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Stats Cards -->
    <v-row>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">Total Reports</div>
            <div class="text-h5">{{ reportsStore.reportCount }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">PDF Reports</div>
            <div class="text-h5 text-primary">{{ reportsStore.pdfReports.length }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">Excel Reports</div>
            <div class="text-h5 text-success">{{ reportsStore.excelReports.length }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline text-medium-emphasis">Page</div>
            <div class="text-h5">
              {{ reportsStore.pagination.page }} / {{ reportsStore.pagination.totalPages }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Reports Table -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-text-field
              v-model="search"
              append-inner-icon="mdi-magnify"
              label="Search report definitions"
              single-line
              hide-details
              variant="outlined"
              density="compact"
              class="mb-2"
            ></v-text-field>
          </v-card-title>

          <v-data-table
            :headers="headers"
            :items="filteredReports"
            :loading="reportsStore.loading"
            :items-per-page="20"
            class="elevation-0"
          >
            <template v-slot:item.name="{ item }">
              <div class="font-weight-medium">{{ item.name }}</div>
              <div class="text-caption text-medium-emphasis">{{ item.description }}</div>
            </template>

            <template v-slot:item.output_format="{ item }">
              <v-chip :color="getFormatColor(item.output_format)" size="small">
                {{ item.output_format.toUpperCase() }}
              </v-chip>
            </template>

            <template v-slot:item.template_ref="{ item }">
              <code class="text-caption">{{ item.template_ref }}</code>
            </template>

            <template v-slot:item.created_at="{ item }">
              <div class="text-caption">{{ formatDate(item.created_at) }}</div>
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                icon="mdi-pencil"
                size="small"
                variant="text"
                @click="openEditDialog(item)"
                title="Edit"
              ></v-btn>
              <v-btn
                icon="mdi-eye"
                size="small"
                variant="text"
                color="primary"
                @click="viewDetails(item)"
                title="View Details"
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
    <v-dialog v-model="dialog" max-width="900px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editMode ? 'Edit Report Definition' : 'New Report Definition' }}</span>
        </v-card-title>
        <v-card-text>
          <v-form ref="form" v-model="formValid">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="formData.name"
                  label="Name"
                  :rules="[rules.required]"
                  variant="outlined"
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="formData.output_format"
                  :items="formatOptions"
                  label="Output Format"
                  :rules="[rules.required]"
                  variant="outlined"
                  required
                ></v-select>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="formData.description"
                  label="Description"
                  variant="outlined"
                  rows="2"
                ></v-textarea>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="formData.template_ref"
                  label="Template Reference"
                  :rules="[rules.required]"
                  variant="outlined"
                  hint="Path to the template file (e.g., templates/sales_report.html)"
                  persistent-hint
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="querySpecJson"
                  label="Query Specification (JSON)"
                  :rules="[rules.required, rules.validJson]"
                  variant="outlined"
                  rows="8"
                  hint="JSON object defining the data query and parameters"
                  persistent-hint
                  required
                  auto-grow
                ></v-textarea>
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
            :loading="reportsStore.loading"
            @click="saveReport"
          >
            {{ editMode ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Details Dialog -->
    <v-dialog v-model="detailsDialog" max-width="800px">
      <v-card v-if="reportsStore.currentReport">
        <v-card-title>Report Details</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis">Name</div>
              <div class="text-body-1 font-weight-medium">{{ reportsStore.currentReport.name }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis">Output Format</div>
              <v-chip :color="getFormatColor(reportsStore.currentReport.output_format)" class="mt-1">
                {{ reportsStore.currentReport.output_format.toUpperCase() }}
              </v-chip>
            </v-col>
            <v-col cols="12">
              <div class="text-caption text-medium-emphasis">Description</div>
              <div class="text-body-2">{{ reportsStore.currentReport.description || '-' }}</div>
            </v-col>
            <v-col cols="12">
              <div class="text-caption text-medium-emphasis">Template Reference</div>
              <code class="text-body-2">{{ reportsStore.currentReport.template_ref }}</code>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis">Created At</div>
              <div class="text-body-2">{{ formatDate(reportsStore.currentReport.created_at) }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis">Updated At</div>
              <div class="text-body-2">{{ formatDate(reportsStore.currentReport.updated_at) }}</div>
            </v-col>
            <v-col cols="12">
              <v-divider class="mb-3"></v-divider>
              <div class="text-subtitle-2 mb-2">Query Specification</div>
              <v-card variant="outlined">
                <v-card-text>
                  <pre class="text-caption">{{ JSON.stringify(reportsStore.currentReport.query_spec, null, 2) }}</pre>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="detailsDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400px">
      <v-card>
        <v-card-title>Delete Report Definition</v-card-title>
        <v-card-text>
          Are you sure you want to delete "{{ reportToDelete?.name }}"? This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" :loading="reportsStore.loading" @click="deleteReport">
            Delete
          </v-btn>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useReportsStore } from '@/stores/reports'
import type { ReportDefinition, ReportDefinitionFormData } from '@/types'

const reportsStore = useReportsStore()

const search = ref('')
const dialog = ref(false)
const detailsDialog = ref(false)
const deleteDialog = ref(false)
const editMode = ref(false)
const formValid = ref(false)
const form = ref()
const reportToDelete = ref<ReportDefinition | null>(null)
const querySpecJson = ref('')

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const formData = ref<ReportDefinitionFormData>({
  name: '',
  description: '',
  template_ref: '',
  query_spec: {},
  output_format: 'pdf'
})

const currentReportId = ref<string | null>(null)

const headers: any[] = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Format', key: 'output_format', sortable: true },
  { title: 'Template', key: 'template_ref', sortable: false },
  { title: 'Created', key: 'created_at', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'center' }
]

const formatOptions = [
  { title: 'PDF', value: 'pdf' },
  { title: 'Excel (XLSX)', value: 'xlsx' },
  { title: 'CSV', value: 'csv' }
]

const rules = {
  required: (v: string) => !!v || 'This field is required',
  validJson: (v: string) => {
    try {
      JSON.parse(v)
      return true
    } catch (e) {
      return 'Must be valid JSON'
    }
  }
}

const filteredReports = computed(() => {
  if (!search.value) return reportsStore.reports
  const searchLower = search.value.toLowerCase()
  return reportsStore.reports.filter(
    (r) =>
      r.name.toLowerCase().includes(searchLower) ||
      r.description?.toLowerCase().includes(searchLower)
  )
})

function getFormatColor(format: string): string {
  const colors: Record<string, string> = {
    pdf: 'red',
    xlsx: 'green',
    csv: 'blue'
  }
  return colors[format] || 'grey'
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString()
}

function openCreateDialog() {
  editMode.value = false
  currentReportId.value = null
  formData.value = {
    name: '',
    description: '',
    template_ref: '',
    query_spec: {},
    output_format: 'pdf'
  }
  querySpecJson.value = JSON.stringify(
    {
      sql: 'SELECT * FROM table_name',
      parameters: {}
    },
    null,
    2
  )
  dialog.value = true
}

function openEditDialog(report: ReportDefinition) {
  editMode.value = true
  currentReportId.value = report.id
  formData.value = {
    name: report.name,
    description: report.description,
    template_ref: report.template_ref,
    query_spec: report.query_spec,
    output_format: report.output_format
  }
  querySpecJson.value = JSON.stringify(report.query_spec, null, 2)
  dialog.value = true
}

function closeDialog() {
  dialog.value = false
}

async function saveReport() {
  if (!form.value) return
  const { valid } = await form.value.validate()
  if (!valid) return

  try {
    formData.value.query_spec = JSON.parse(querySpecJson.value)
  } catch (e) {
    showSnackbar('Invalid JSON in query specification', 'error')
    return
  }

  try {
    if (editMode.value && currentReportId.value) {
      await reportsStore.updateReport(currentReportId.value, formData.value)
      showSnackbar('Report definition updated successfully')
    } else {
      await reportsStore.createReport(formData.value)
      showSnackbar('Report definition created successfully')
    }
    closeDialog()
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to save report definition', 'error')
  }
}

async function viewDetails(report: ReportDefinition) {
  try {
    await reportsStore.fetchReport(report.id)
    detailsDialog.value = true
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to load report details', 'error')
  }
}

function confirmDelete(report: ReportDefinition) {
  reportToDelete.value = report
  deleteDialog.value = true
}

async function deleteReport() {
  if (!reportToDelete.value) return
  try {
    await reportsStore.deleteReport(reportToDelete.value.id)
    showSnackbar('Report definition deleted')
    deleteDialog.value = false
    reportToDelete.value = null
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to delete report definition', 'error')
  }
}

function showSnackbar(text: string, color = 'success') {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(async () => {
  await reportsStore.fetchReports()
})
</script>
