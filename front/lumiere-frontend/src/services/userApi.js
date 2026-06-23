import axios from 'axios'

export const API_BASE_URL = 'http://127.0.0.1:8000'

const authHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const getCurrentUser = async () => {
  const response = await axios.get(`${API_BASE_URL}/accounts/user/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const updateCurrentUser = async ({ email, nickname, profileImage }) => {
  const formData = new FormData()
  if (email !== undefined) formData.append('email', email)
  if (nickname !== undefined) formData.append('nickname', nickname)
  if (profileImage) formData.append('profile_image', profileImage)

  const response = await axios.patch(`${API_BASE_URL}/accounts/user/update/`, formData, {
    headers: authHeaders(),
  })
  return response.data
}

export const deleteCurrentUser = async ({ confirmation, password }) => {
  const response = await axios.delete(`${API_BASE_URL}/accounts/user/`, {
    headers: authHeaders(),
    data: {
      confirmation,
      password,
    },
  })
  return response.data
}

export const checkNickname = async (nickname) => {
  const response = await axios.post(
    `${API_BASE_URL}/accounts/check-nickname/`,
    { nickname },
    { headers: authHeaders() },
  )
  return response.data
}
