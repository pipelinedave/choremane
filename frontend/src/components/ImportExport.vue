<template>
  <div class="import-export-modal" role="dialog" aria-modal="true" aria-label="Import/Export Data">
    <div class="modal-content">
      <h2>Import/Export Chores & Logs</h2>
      <button @click="exportData">Export Data</button>
      <input type="file" ref="importInput" style="display:none" @change="importData" accept="application/json" />
      <button @click="triggerImport">Import Data</button>
      <div v-if="importError" class="import-error">{{ importError }}</div>
      <div class="actions">
        <button @click="$emit('close')">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useChoreStore } from '@/store/choreStore'
import { useLogStore } from '@/store/logStore'
import { ref } from 'vue'

const choreStore = useChoreStore()
const logStore = useLogStore()
const importInput = ref(null)
const importError = ref('')

const exportData = () => {
  const data = {
    chores: choreStore.chores,
    logs: logStore.logEntries,
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `choremane-backup-${new Date().toISOString().slice(0,10)}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const triggerImport = () => {
  importInput.value.click()
}

const importData = (event) => {
  importError.value = ''
  const file = event.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result)
      if (!Array.isArray(data.chores) || !Array.isArray(data.logs)) {
        throw new Error('Invalid file structure')
      }
      // Replace current data (could be merged if desired)
      choreStore.chores = data.chores
      logStore.logEntries = data.logs
      localStorage.setItem('logEntries', JSON.stringify(data.logs))
      importError.value = 'Import successful!'
    } catch (err) {
      importError.value = 'Import failed: ' + err.message
    }
  }
  reader.readAsText(file)
}
</script>

<style scoped>
.import-export-modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-content {
  background: var(--color-surface);
  color: var(--color-text);
  padding: 2rem;
  border-radius: var(--radius-md);
  min-width: 280px;
  width: 100%;
  max-width: 500px;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-content button {
  padding: 0.75rem;
  border-radius: var(--radius-sm);
  background: var(--color-surface-light);
  color: var(--color-text);
  border: none;
  cursor: pointer;
}

.import-error {
  color: var(--color-danger);
  margin-top: 1rem;
  word-break: break-word;
}

.actions {
  margin-top: 1.5rem;
  text-align: right;
}

@media (max-width: 576px) {
  .modal-content {
    padding: 1.5rem 1rem;
  }
  
  .actions button, 
  .modal-content > button {
    width: 100%;
    margin-bottom: 0.5rem;
  }
}
</style>
