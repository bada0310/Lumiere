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

export const analyzeProductColorImage = async ({ image, product_name = '', brand_name = '', category = '' }) => {
  const formData = new FormData()
  formData.append('image', image)
  if (product_name) formData.append('product_name', product_name)
  if (brand_name) formData.append('brand_name', brand_name)
  if (category) formData.append('category', category)

  const response = await axios.post(`${API_BASE_URL}/api/products/analyze-image/`, formData, {
    headers: authHeaders(),
  })
  return response.data
}

export const getProductImageAnalyses = async (params = {}) => {
  const response = await axios.get(`${API_BASE_URL}/api/products/image-analyses/`, {
    headers: authHeaders(),
    params,
  })
  return response.data
}

export const getProductImageAnalysis = async (analysisId) => {
  const response = await axios.get(`${API_BASE_URL}/api/products/image-analyses/${analysisId}/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const updateProductImageAnalysis = async (analysisId, payload) => {
  const response = await axios.patch(`${API_BASE_URL}/api/products/image-analyses/${analysisId}/`, payload, {
    headers: authHeaders(),
  })
  return response.data
}

export const confirmProductImageAnalysis = async (analysisId) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/products/image-analyses/${analysisId}/confirm/`,
    {},
    { headers: authHeaders() },
  )
  return response.data
}

export const deleteProductImageAnalysis = async (analysisId) => {
  await axios.delete(`${API_BASE_URL}/api/products/image-analyses/${analysisId}/`, {
    headers: authHeaders(),
  })
}
