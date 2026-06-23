export const ACCESS_TOKEN_KEY = 'access_token'
export const REFRESH_TOKEN_KEY = 'refresh_token'

export const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY)

export const isAuthenticated = () => Boolean(getAccessToken())

export const clearAuthTokens = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
}

export const isAuthError = (error) => [401, 403].includes(error?.response?.status)

export const getRedirectPath = (route, fallback = '/') => {
  const fullPath = route?.fullPath || fallback
  return fullPath === '/login' ? fallback : fullPath
}
