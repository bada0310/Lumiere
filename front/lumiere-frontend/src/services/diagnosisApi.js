import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000'

const authHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const getLatestDiagnosis = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/diagnosis/latest/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const getDiagnosisResults = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/diagnosis/results/`, {
    headers: authHeaders(),
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

export const getDemoDiagnosis = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/diagnosis/demo/`)
  return response.data
}

