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

export const getProduct = async (productId, params = {}) => {
  const response = await axios.get(`${API_BASE_URL}/api/products/${productId}/`, {
    headers: authHeaders(),
    params,
  })
  return response.data
}
