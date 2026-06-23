import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000'

const authHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const requireResultId = (resultId) => {
  if (resultId === undefined || resultId === null || resultId === '') {
    throw new Error('diagnosis result id is required')
  }
  return resultId
}

export const getLatestDiagnosis = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/diagnosis/latest/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const getDiagnosisResults = async (params = {}) => {
  const response = await axios.get(`${API_BASE_URL}/api/diagnosis/results/`, {
    headers: authHeaders(),
    params,
  })
  return response.data
}

export const createDiagnosis = async (imageFile) => {
  const formData = new FormData()
  formData.append('image', imageFile)

  const response = await axios.post(`${API_BASE_URL}/api/diagnosis/analyze/`, formData, {
    headers: authHeaders(),
  })
  return response.data
}

export const getDiagnosisResult = async (resultId) => {
  const response = await axios.get(`${API_BASE_URL}/api/diagnosis/results/${resultId}/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const setPrimaryDiagnosis = async (resultId) => {
  const id = requireResultId(resultId)
  const response = await axios.post(
    `${API_BASE_URL}/api/diagnosis/results/${id}/set-primary/`,
    null,
    {
      headers: authHeaders(),
    },
  )
  return response.data
}

export const unsetPrimaryDiagnosis = async (resultId) => {
  const id = requireResultId(resultId)
  const response = await axios.post(
    `${API_BASE_URL}/api/diagnosis/results/${id}/unset-primary/`,
    null,
    {
      headers: authHeaders(),
    },
  )
  return response.data
}

export const deleteDiagnosisResult = async (resultId) => {
  const id = requireResultId(resultId)
  const response = await axios.delete(`${API_BASE_URL}/api/diagnosis/results/${id}/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const startMakeoverGeneration = async (resultId) => {
  const response = await axios.post(`${API_BASE_URL}/api/diagnosis/results/${resultId}/makeovers/`, null, {
    headers: authHeaders(),
  })
  return response.data
}

export const getMakeoverStatus = async (resultId) => {
  const response = await axios.get(`${API_BASE_URL}/api/diagnosis/results/${resultId}/makeovers/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const retryMakeoverStyle = async (resultId, styleKey) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/diagnosis/results/${resultId}/makeovers/${styleKey}/retry/`,
    null,
    {
      headers: authHeaders(),
    },
  )
  return response.data
}

export const getDemoDiagnosis = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/diagnosis/demo/`)
  return response.data
}

