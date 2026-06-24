import axios from 'axios'

import { API_BASE_URL } from '@/services/userApi'

const authHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const getNotifications = async (params = {}) => {
  const response = await axios.get(`${API_BASE_URL}/api/notifications/`, {
    headers: authHeaders(),
    params,
  })
  return response.data
}

export const getNotificationUnreadCount = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/notifications/unread-count/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const markAllNotificationsRead = async () => {
  const response = await axios.post(`${API_BASE_URL}/api/notifications/mark-all-read/`, null, {
    headers: authHeaders(),
  })
  return response.data
}

export const markNotificationRead = async (notificationId) => {
  const response = await axios.patch(`${API_BASE_URL}/api/notifications/${notificationId}/read/`, null, {
    headers: authHeaders(),
  })
  return response.data
}
