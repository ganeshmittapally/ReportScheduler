<template>
  <div>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-4">
          <div>
            <h1 class="text-h4">Artifact Gallery</h1>
            <p class="text-subtitle-1 text-medium-emphasis">
              Browse and download generated report artifacts
            </p>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Filters -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  v-model="filters.file_format"
                  :items="formatOptions"
                  label="Format"
                  variant="outlined"
                  density="compact"
                  clearable
                  @update:model-value="applyFilters"
                ></v-select>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="searchQuery"
                  label="Search by filename"
                  variant="outlined"
                  density="compact"
                  clearable
                  append-inner-icon="mdi-magnify"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Artifacts Grid -->
    <v-row>
      <v-col
        v-for="artifact in filteredArtifacts"
        :key="artifact.id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <v-card hover class="artifact-card">
          <div class="artifact-preview">
            <v-icon :color="getFormatColor(artifact.file_format)" size="80">
              {{ getFormatIcon(artifact.file_format) }}
            </v-icon>
          </div>
          <v-card-title class="text-truncate">
            {{ filenameFromPath(artifact.blob_path) }}
          </v-card-title>
          <v-card-text>
            <div class="text-caption text-medium-emphasis mb-1">
              <v-chip :color="getFormatColor(artifact.file_format)" size="x-small" class="mr-2">
                {{ artifact.file_format.toUpperCase() }}
              </v-chip>
              {{ formatFileSize(artifact.file_size_bytes) }}
            </div>
            <div class="text-caption">
              Created: {{ formatDate(artifact.created_at) }}
            </div>
            <div class="text-caption text-medium-emphasis">
              Expires: {{ formatDate(artifact.signed_url_expires_at) }}
            </div>
          </v-card-text>
          <v-card-actions>
            <v-btn
              icon="mdi-eye"
              size="small"
              variant="text"
              color="primary"
              @click="previewArtifact(artifact)"
              title="Preview"
            ></v-btn>
            <v-btn
              icon="mdi-download"
              size="small"
              variant="text"
              color="primary"
              @click="downloadArtifact(artifact)"
              title="Download"
            ></v-btn>
            <v-btn
              icon="mdi-refresh"
              size="small"
              variant="text"
              @click="refreshUrl(artifact.id)"
              title="Refresh URL"
              :disabled="!isExpiringSoon(artifact.signed_url_expires_at)"
            ></v-btn>
            <v-spacer></v-spacer>
            <v-btn
              icon="mdi-delete"
              size="small"
              variant="text"
              color="error"
              @click="confirmDelete(artifact)"
              title="Delete"
            ></v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-row v-if="filteredArtifacts.length === 0 && !loading">
      <v-col cols="12">
        <v-card>
          <v-card-text class="text-center py-12">
            <v-icon size="80" color="grey-lighten-2">mdi-folder-open-outline</v-icon>
            <div class="text-h6 mt-4 text-medium-emphasis">No artifacts found</div>
            <div class="text-body-2 text-medium-emphasis mt-2">
              Generated reports will appear here
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Preview Dialog -->
    <v-dialog v-model="previewDialog" max-width="1200px">
      <v-card v-if="previewArtifactData">
        <v-card-title class="d-flex justify-space-between">
          <span>{{ filenameFromPath(previewArtifactData.blob_path) }}</span>
          <v-btn icon="mdi-close" variant="text" @click="previewDialog = false"></v-btn>
        </v-card-title>
        <v-card-text>
          <div v-if="previewArtifactData.file_format === 'pdf'" style="height: 70vh">
            <iframe
              :src="previewArtifactData.signed_url"
              style="width: 100%; height: 100%; border: none"
            ></iframe>
          </div>
          <div v-else class="text-center py-8">
            <v-icon size="80" :color="getFormatColor(previewArtifactData.file_format)">
              {{ getFormatIcon(previewArtifactData.file_format) }}
            </v-icon>
            <div class="text-h6 mt-4">Preview not available for {{ previewArtifactData.file_format.toUpperCase() }} files</div>
            <v-btn
              color="primary"
              class="mt-4"
              prepend-icon="mdi-download"
              @click="downloadArtifact(previewArtifactData)"
            >
              Download File
            </v-btn>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400px">
      <v-card>
        <v-card-title>Delete Artifact</v-card-title>
        <v-card-text>
          Are you sure you want to delete "{{ artifactToDelete ? filenameFromPath(artifactToDelete.blob_path) : '' }}"? This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" :loading="loading" @click="deleteArtifact">
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

    <!-- Loading Overlay -->
    <v-overlay :model-value="loading" class="align-center justify-center">
      <v-progress-circular indeterminate size="64"></v-progress-circular>
    </v-overlay>
  </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiService } from '@/services/api'
import type { Artifact } from '@/types'

const artifacts = ref<Artifact[]>([])
const loading = ref(false)
const searchQuery = ref('')
const previewDialog = ref(false)
const deleteDialog = ref(false)
const previewArtifactData = ref<Artifact | null>(null)
const artifactToDelete = ref<Artifact | null>(null)

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const filters = ref<{ file_format?: string }>({})

const formatOptions = [
  { title: 'PDF', value: 'pdf' },
  { title: 'Excel (XLSX)', value: 'xlsx' },
  { title: 'CSV', value: 'csv' }
]

const filteredArtifacts = computed(() => {
  let result = artifacts.value

  if (filters.value.file_format) {
    result = result.filter((a) => a.file_format === filters.value.file_format)
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter((a) => filenameFromPath(a.blob_path).toLowerCase().includes(query))
  }

  return result
})

function getFormatIcon(format: string): string {
  const icons: Record<string, string> = {
    pdf: 'mdi-file-pdf-box',
    xlsx: 'mdi-file-excel-box',
    csv: 'mdi-file-delimited-outline'
  }
  return icons[format] || 'mdi-file'
}

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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function isExpiringSoon(expiresAt: string): boolean {
  const expiryDate = new Date(expiresAt)
  const now = new Date()
  const hoursDiff = (expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60)
  return hoursDiff < 24
}

function filenameFromPath(path: string): string {
  const parts = path.split('/')
  return parts[parts.length - 1] || path
}

async function fetchArtifacts() {
  loading.value = true
  try {
    const response = await apiService.getArtifacts(undefined, 1, 100)
    artifacts.value = response.items
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to fetch artifacts', 'error')
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  // Filters are applied through computed property
}

function previewArtifact(artifact: Artifact) {
  previewArtifactData.value = artifact
  previewDialog.value = true
}

function downloadArtifact(artifact: Artifact) {
  window.open(artifact.signed_url, '_blank')
}

async function refreshUrl(artifactId: string) {
  loading.value = true
  try {
    const updatedArtifact = await apiService.refreshArtifactUrl(artifactId)
    const index = artifacts.value.findIndex((a) => a.id === artifactId)
    if (index !== -1) {
      artifacts.value[index] = updatedArtifact
    }
    showSnackbar('URL refreshed successfully')
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to refresh URL', 'error')
  } finally {
    loading.value = false
  }
}

function confirmDelete(artifact: Artifact) {
  artifactToDelete.value = artifact
  deleteDialog.value = true
}

async function deleteArtifact() {
  if (!artifactToDelete.value) return
  loading.value = true
  try {
    await apiService.deleteArtifact(artifactToDelete.value.id)
    artifacts.value = artifacts.value.filter((a) => a.id !== artifactToDelete.value!.id)
    showSnackbar('Artifact deleted')
    deleteDialog.value = false
    artifactToDelete.value = null
  } catch (error: any) {
    showSnackbar(error.detail || 'Failed to delete artifact', 'error')
  } finally {
    loading.value = false
  }
}

function showSnackbar(text: string, color = 'success') {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(async () => {
  await fetchArtifacts()
})
</script>

<style scoped>
.artifact-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.artifact-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 150px;
  background-color: rgba(0, 0, 0, 0.02);
}
</style>
