import { computed, ref, unref } from 'vue'

import { DEFAULT_PROFILE_IMAGE } from '@/constants/images'
import { getLatestDiagnosisToneImageUrl } from '@/data/toneImages'
import { getLatestDiagnosis } from '@/services/diagnosisApi'
import { getSavedMockDiagnosisResult } from '@/utils/diagnosisMockStorage'

export const PROFILE_IMAGE_SOURCE = {
  USER_UPLOAD: 'USER_UPLOAD',
  PERSONAL_COLOR_DEFAULT: 'PERSONAL_COLOR_DEFAULT',
  SYSTEM_DEFAULT: 'SYSTEM_DEFAULT',
}

export const useResolvedProfileImage = (userRef) => {
  const latestDiagnosis = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const customProfileImageUrl = computed(() => unref(userRef)?.profileImageUrl || null)

  const toneProfileImage = computed(() => {
    if (!latestDiagnosis.value) return null
    return getLatestDiagnosisToneImageUrl(latestDiagnosis.value)
  })

  const profileImageSource = computed(() => {
    if (customProfileImageUrl.value) return PROFILE_IMAGE_SOURCE.USER_UPLOAD
    if (toneProfileImage.value) return PROFILE_IMAGE_SOURCE.PERSONAL_COLOR_DEFAULT
    return PROFILE_IMAGE_SOURCE.SYSTEM_DEFAULT
  })

  const resolvedProfileImageUrl = computed(() => {
    return customProfileImageUrl.value || toneProfileImage.value || DEFAULT_PROFILE_IMAGE
  })

  const loadLatestDiagnosisForProfile = async () => {
    if (!localStorage.getItem('access_token')) {
      latestDiagnosis.value = null
      return null
    }

    loading.value = true
    error.value = null

    try {
      latestDiagnosis.value = await getLatestDiagnosis()
      return latestDiagnosis.value
    } catch (err) {
      error.value = err
      latestDiagnosis.value = getSavedMockDiagnosisResult()
      return null
    } finally {
      loading.value = false
    }
  }

  const clearResolvedProfileImage = () => {
    latestDiagnosis.value = null
    error.value = null
  }

  return {
    latestDiagnosis,
    loading,
    error,
    toneProfileImage,
    profileImageSource,
    resolvedProfileImageUrl,
    loadLatestDiagnosisForProfile,
    clearResolvedProfileImage,
  }
}
