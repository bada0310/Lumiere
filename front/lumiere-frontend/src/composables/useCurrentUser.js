import { computed, ref } from 'vue'

import { DEFAULT_PROFILE_IMAGE } from '@/constants/images'
import { getCurrentUser, updateCurrentUser } from '@/services/userApi'

const currentUser = ref(null)
const loading = ref(false)
const error = ref(null)

const normalizeUser = (user) => {
  if (!user) return null

  return {
    id: user.id,
    username: user.username || '',
    nickname: user.nickname || user.username || '',
    email: user.email || '',
    profileImageUrl: user.profile_image_url || null,
  }
}

export const useCurrentUser = () => {
  const isLoggedIn = computed(() => Boolean(localStorage.getItem('access_token')))

  const loadCurrentUser = async ({ force = false } = {}) => {
    if (!isLoggedIn.value) {
      currentUser.value = null
      return null
    }

    if (currentUser.value && !force) return currentUser.value

    loading.value = true
    error.value = null

    try {
      currentUser.value = normalizeUser(await getCurrentUser())
      return currentUser.value
    } catch (err) {
      error.value = err
      currentUser.value = null
      throw err
    } finally {
      loading.value = false
    }
  }

  const saveCurrentUser = async (payload) => {
    const updated = normalizeUser(await updateCurrentUser(payload))
    currentUser.value = updated
    return updated
  }

  const clearCurrentUser = () => {
    currentUser.value = null
  }

  return {
    currentUser,
    loading,
    error,
    isLoggedIn,
    defaultProfileImage: DEFAULT_PROFILE_IMAGE,
    loadCurrentUser,
    saveCurrentUser,
    clearCurrentUser,
  }
}
