import { useRoute, useRouter } from 'vue-router'

import { clearAuthTokens, getRedirectPath, isAuthError, isAuthenticated } from '@/utils/auth'

export const useRequireLogin = () => {
  const route = useRoute()
  const router = useRouter()

  const redirectToLogin = ({ message, redirect } = {}) => {
    if (message) alert(message)

    router.push({
      name: 'login',
      query: {
        redirect: redirect || getRedirectPath(route),
      },
    })
  }

  const requireLogin = ({
    message = '로그인이 필요합니다.',
    redirect,
  } = {}) => {
    if (isAuthenticated()) return true

    redirectToLogin({ message, redirect })
    return false
  }

  const handleAuthFailure = (
    error,
    {
      message = '로그인이 만료되었어요. 다시 로그인해주세요.',
      redirect,
    } = {},
  ) => {
    if (!isAuthError(error)) return false

    clearAuthTokens()
    redirectToLogin({ message, redirect })
    return true
  }

  return {
    requireLogin,
    handleAuthFailure,
    redirectToLogin,
  }
}
