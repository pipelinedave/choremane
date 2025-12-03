<template>
  <div class="modal-overlay" role="dialog" aria-modal="true" aria-label="Import/Export Data" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Import/Export Chores & Logs</h2>
      </div>
      <div class="modal-body">
        <button class="action-button export-button" @click="exportData">
          <i class="fas fa-download"></i> Export Data
        </button>
        <input type="file" ref="importInput" style="display:none" @change="importData" accept="application/json" />
        <button class="action-button import-button" @click="triggerImport">
          <i class="fas fa-upload"></i> Import Data
        </button>
        <div v-if="importError" class="import-error">{{ importError }}</div>
      </div>
      <div class="modal-footer">
        <button class="primary-button" @click="$emit('close')">
          <i class="fas fa-check"></i> Done
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useChoreStore } from '@/store/choreStore'
import { useLogStore } from '@/store/logStore'
import { ref } from 'vue'
import api from '@/plugins/axios'

const choreStore = useChoreStore()
const logStore = useLogStore()
const importInput = ref(null)
const importError = ref('')

const exportData = () => {
  // Use the backend API for export
  api.get('/export')
    .then(response => {
      const data = response.data
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `choremane-backup-${new Date().toISOString().slice(0,10)}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    })
    .catch(error => {
      console.error('Export error:', error)
      importError.value = 'Failed to export data. Please try again.'
    })
}

const triggerImport = () => {
  importInput.value.click()
}

const importData = (event) => {
  importError.value = ''
  const file = event.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const data = JSON.parse(e.target.result)
      if (!Array.isArray(data.chores)) {
        throw new Error('Invalid file structure')
      }
      
      const payload = { chores: data.chores }
      if (Array.isArray(data.logs)) {
        payload.logs = data.logs
      }
      
      // Send payload to the backend import API so chores/logs are shared across users
      const response = await api.post('/import', payload)
      
      // Refresh the chore list and log list from the server
      await choreStore.fetchChores()
      await logStore.fetchLogs()
      
      // Show import results to user
      const logCount = response.data?.imported_logs ?? (payload.logs ? payload.logs.length : 0)
      importError.value = `Import successful! ${response.data.imported_chores} chores and ${logCount} logs imported.`
    } catch (err) {
      console.error('Import error:', err)
      importError.value = `Import failed: ${err.message}`
    }
  }
  reader.readAsText(file)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  backdrop-filter: blur(2px);
}

.modal-content {
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: var(--radius-md);
  min-width: 280px;
  width: 100%;
  max-width: 500px;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  background: var(--color-surface-light);
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-surface-lighter);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.close-button {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.25rem;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.close-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-text);
  transform: none;
}

.modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--color-surface-lighter);
  gap: 0.75rem;
}

.action-button {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  background: var(--color-surface-light);
  color: var(--color-text);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: background-color var(--transition-fast);
}

.action-button:hover {
  background: var(--color-surface-lighter);
  transform: none;
}

.export-button {
  background: var(--color-primary);
  color: white;
}

.export-button:hover {
  background: var(--color-primary-hover);
}

.import-button {
  background: var(--color-warning);
  color: white;
}

.import-button:hover {
  background: var(--color-warning-hover);
}

.primary-button {
  background: var(--color-surface-light);
  color: var(--color-text);
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.primary-button:hover {
  background: var(--color-surface-lighter);
  transform: none;
}

.import-error {
  color: var(--color-danger);
  padding: 0.5rem;
  background-color: rgba(231, 76, 60, 0.1);
  border-radius: var(--radius-sm);
  margin-top: 0.5rem;
  word-break: break-word;
}

@media (max-width: 576px) {
  .modal-content {
    max-width: 95%;
  }
  
  .modal-header, .modal-body, .modal-footer {
    padding: 1rem;
  }
  
  .action-button, .primary-button {
    width: 100%;
  }
}
</style>
