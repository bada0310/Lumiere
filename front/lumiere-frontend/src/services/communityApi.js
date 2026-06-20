import axios from 'axios'

export const API_BASE_URL = 'http://127.0.0.1:8000'

export const getAccessToken = () => localStorage.getItem('access_token')

export const isAuthenticated = () => Boolean(getAccessToken())

export const authHeaders = () => {
  const token = getAccessToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const getCurrentUserId = () => {
  const token = getAccessToken()
  if (!token) return null

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.user_id || null
  } catch {
    return null
  }
}

export const getPosts = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/community/posts/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const getPost = async (postId) => {
  const response = await axios.get(`${API_BASE_URL}/api/community/posts/${postId}/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const createPost = async (payload) => {
  const response = await axios.post(`${API_BASE_URL}/api/community/posts/`, payload, {
    headers: authHeaders(),
  })
  return response.data
}

export const updatePost = async (postId, payload) => {
  const response = await axios.patch(`${API_BASE_URL}/api/community/posts/${postId}/`, payload, {
    headers: authHeaders(),
  })
  return response.data
}

export const deletePostById = async (postId) => {
  await axios.delete(`${API_BASE_URL}/api/community/posts/${postId}/`, {
    headers: authHeaders(),
  })
}

export const togglePostLike = async (postId) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/community/posts/${postId}/like/`,
    {},
    { headers: authHeaders() },
  )
  return response.data
}

export const getPostComments = async (postId) => {
  const response = await axios.get(`${API_BASE_URL}/api/community/posts/${postId}/comments/`, {
    headers: authHeaders(),
  })
  return response.data
}

export const createComment = async (postId, content) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/community/posts/${postId}/comments/`,
    { content },
    { headers: authHeaders() },
  )
  return response.data
}

export const toggleCommentLikeById = async (commentId) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/community/comments/${commentId}/like/`,
    {},
    { headers: authHeaders() },
  )
  return response.data
}
