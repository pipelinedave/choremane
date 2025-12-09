import api from '@/plugins/axios'

const hasVersionFields = (payload) =>
  payload &&
  typeof payload === 'object' &&
  'version_tag' in payload &&
  'backend_image' in payload &&
  'frontend_image' in payload

export async function fetchVersionInfo() {
  const response = await api.get('/version')
  const payload = response.data

  if (!hasVersionFields(payload)) {
    throw new Error('Unexpected /version response shape')
  }

  return payload
}

export function safeVersionInfo(payload) {
  return hasVersionFields(payload) ? payload : null
}
