export const MOCK_SAVED_DIAGNOSIS_RESULT_KEY = 'lumiere_mock_saved_diagnosis_result'

export const canUseMockDiagnosisStorage = () => Boolean(import.meta.env.DEV)

export const getSavedMockDiagnosisResult = () => {
  if (!canUseMockDiagnosisStorage()) return null

  try {
    const raw = localStorage.getItem(MOCK_SAVED_DIAGNOSIS_RESULT_KEY)
    return raw ? JSON.parse(raw) : null
  } catch (error) {
    console.warn('Saved mock diagnosis result could not be parsed.', error)
    return null
  }
}

export const saveMockDiagnosisResult = (result) => {
  if (!canUseMockDiagnosisStorage() || !result) return false
  localStorage.setItem(MOCK_SAVED_DIAGNOSIS_RESULT_KEY, JSON.stringify(result))
  return true
}

export const clearSavedMockDiagnosisResult = () => {
  if (!canUseMockDiagnosisStorage()) return
  localStorage.removeItem(MOCK_SAVED_DIAGNOSIS_RESULT_KEY)
}
