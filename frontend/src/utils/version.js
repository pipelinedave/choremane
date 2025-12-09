import api from '@/plugins/axios'

const hasVersionFields = (payload) =>
  payload &&
  typeof payload === 'object' &&
  'version_tag' in payload &&
  'backend_image' in payload &&
  'frontend_image' in payload

export async function fetchVersionInfo() {
  try {
    // Do not prefix with a leading slash so Axios baseURL (/api) is preserved in production
    const response = await api.get('version')
    const payload = response.data

    if (hasVersionFields(payload)) {
      return payload
    }

    console.warn('Unexpected /version response shape', payload)
    return null
  } catch (err) {
    console.warn('Failed to fetch version info', err)
    return null
  }
}

export function safeVersionInfo(payload) {
  return hasVersionFields(payload) ? payload : null
}
