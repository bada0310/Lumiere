const rawApiBaseUrl = String(import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').trim()

const withoutApiSuffix = rawApiBaseUrl.replace(/\/api\/?$/, '')
const withoutTrailingSlash = withoutApiSuffix.replace(/\/+$/, '')

export const API_BASE_URL = withoutTrailingSlash || 'http://127.0.0.1:8000'
export const API_ORIGIN = API_BASE_URL
