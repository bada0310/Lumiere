import axios from 'axios'

import { API_BASE_URL } from '@/services/userApi'

const authHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const getProducts = async (params = {}) => {
  const response = await axios.get(`${API_BASE_URL}/api/products/`, {
    headers: authHeaders(),
    params,
  })
  return response.data
}

export const searchProducts = async (keyword, params = {}) => {
  const query = String(keyword || '').trim()
  if (!query) return []
  const response = await getProducts({ ...params, q: query })
  return Array.isArray(response) ? response : response.results || response.products || []
}

export const getProduct = async (productId, params = {}) => {
  const response = await axios.get(`${API_BASE_URL}/api/products/${productId}/`, {
    headers: authHeaders(),
    params,
  })
  return response.data
}

export const getProductColorAnalysis = async (productId, params = {}) => {
  const response = await axios.get(`${API_BASE_URL}/api/products/${productId}/color-analysis/`, {
    headers: authHeaders(),
    params,
  })
  return response.data
}

export const analyzeProductColorUrl = async (productUrl) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/products/color-analysis/`,
    { product_url: productUrl },
    { headers: authHeaders() },
  )
  return response.data
}
