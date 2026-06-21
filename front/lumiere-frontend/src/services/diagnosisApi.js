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
