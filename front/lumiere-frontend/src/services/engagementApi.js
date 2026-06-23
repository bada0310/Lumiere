import axios from 'axios'

import { API_BASE_URL } from '@/services/userApi'

const authHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const getLikedProductOptions = async (params = {}) => {
  const response = await axios.get(`${API_BASE_URL}/api/engagements/liked-options/`, {
    headers: authHeaders(),
    params,
  })
  return response.data
}

export const createLikedProductOption = async (payload) => {
  const response = await axios.post(`${API_BASE_URL}/api/engagements/liked-options/`, payload, {
    headers: authHeaders(),
  })
  return response.data
}

export const toggleLikedProductOption = async (payload) => {
  const response = await axios.post(`${API_BASE_URL}/api/engagements/liked-options/toggle/`, payload, {
    headers: authHeaders(),
  })
  return response.data
}

export const deleteLikedProductOption = async (id) => {
  await axios.delete(`${API_BASE_URL}/api/engagements/liked-options/${id}/`, {
    headers: authHeaders(),
  })
}

export const getUrlAnalysisRecords = async (params = {}) => {
  const response = await axios.get(`${API_BASE_URL}/api/engagements/url-analyses/`, {
    headers: authHeaders(),
    params,
  })
  return response.data
}

export const getUrlAnalysisRecord = async (id) => {
  const response = await axios.get(`${API_BASE_URL}/api/engagements/url-analyses/${id}/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const createUrlAnalysisRecord = async (payload) => {
  const response = await axios.post(`${API_BASE_URL}/api/engagements/url-analyses/`, payload, {
    headers: authHeaders(),
  })
  return response.data
}

export const deleteUrlAnalysisRecord = async (id) => {
  await axios.delete(`${API_BASE_URL}/api/engagements/url-analyses/${id}/`, {
    headers: authHeaders(),
  })
}
