import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  getNotificationUnreadCount,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '@/services/notificationApi'

const asArray = (value) => {
  if (Array.isArray(value)) return value
  return value?.results || []
}

export const useNotificationStore = defineStore('notifications', () => {
  const items = ref([])
  const unreadCount = ref(0)
  const loaded = ref(false)
  const loading = ref(false)

  const hasUnread = computed(() => unreadCount.value > 0)

  const loadNotifications = async ({ force = false } = {}) => {
    if (!localStorage.getItem('access_token')) {
      items.value = []
      unreadCount.value = 0
      loaded.value = false
      return []
    }

    if (loaded.value && !force) return items.value

    loading.value = true
    try {
      const response = await getNotifications({ page: 1, page_size: 20 })
      items.value = asArray(response)
      unreadCount.value = items.value.filter((item) => !item.is_read && !item.read_at).length
      loaded.value = true
      return items.value
    } finally {
      loading.value = false
    }
  }

  const refreshUnreadCount = async () => {
    if (!localStorage.getItem('access_token')) {
      unreadCount.value = 0
      return 0
    }

    const response = await getNotificationUnreadCount()
    unreadCount.value = Number(response?.unread_count || 0)
    return unreadCount.value
  }

  const markAllRead = async () => {
    if (!localStorage.getItem('access_token') || unreadCount.value === 0) return

    const previousItems = [...items.value]
    const previousCount = unreadCount.value
    items.value = items.value.map((item) => ({ ...item, is_read: true, read_at: item.read_at || new Date().toISOString() }))
    unreadCount.value = 0

    try {
      await markAllNotificationsRead()
    } catch (error) {
      items.value = previousItems
      unreadCount.value = previousCount
      throw error
    }
  }

  const markRead = async (notificationId) => {
    if (!notificationId) return

    const previousItems = [...items.value]
    const previousCount = unreadCount.value
    const target = items.value.find((item) => item.id === notificationId)
    items.value = items.value.map((item) =>
      item.id === notificationId ? { ...item, is_read: true, read_at: item.read_at || new Date().toISOString() } : item,
    )
    if (target && !target.is_read && !target.read_at) {
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }

    try {
      const response = await markNotificationRead(notificationId)
      if (response?.item) {
        items.value = items.value.map((item) => (item.id === notificationId ? response.item : item))
      }
      unreadCount.value = Number(response?.unread_count ?? unreadCount.value)
    } catch (error) {
      items.value = previousItems
      unreadCount.value = previousCount
      throw error
    }
  }

  return {
    items,
    unreadCount,
    loaded,
    loading,
    hasUnread,
    loadNotifications,
    refreshUnreadCount,
    markAllRead,
    markRead,
  }
})
