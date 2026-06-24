import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getLikedProductOptions, toggleLikedProductOption } from '@/services/engagementApi'

const asArray = (value) => {
  if (Array.isArray(value)) return value
  return value?.results || []
}

const normalizeId = (value) => {
  const text = String(value ?? '').trim()
  return text && text !== '0' && text !== 'NaN' ? text : ''
}

const keysFromPayload = (payload = {}) => {
  const keys = new Set()
  const groupKey = normalizeId(payload.group_key || payload.groupKey)
  const productId = normalizeId(payload.product_id || payload.productId || payload.id)
  const optionId = normalizeId(payload.product_option_id || payload.productOptionId || payload.optionId || payload.option_id)

  if (groupKey) keys.add(`group:${groupKey}`)
  if (optionId) keys.add(`option:${optionId}`)
  if (productId && optionId) keys.add(`product-option:${productId}:${optionId}`)
  if (productId && !optionId) keys.add(`product:${productId}`)

  return keys
}

const keysFromLikedItem = (item = {}) => {
  const product = item.product || {}
  const productOption = item.product_option || {}
  return keysFromPayload({
    group_key: item.group_key || item.snapshot?.groupKey,
    product_id: product.id || item.product_id || item.snapshot?.productId || item.snapshot?.parentId,
    product_option_id: productOption.id || item.product_option_id,
    option_id: item.option_id || item.snapshot?.optionId,
  })
}

const setHasAny = (set, keys) => [...keys].some((key) => set.has(key))

const removeKeys = (set, keys) => {
  keys.forEach((key) => set.delete(key))
}

const addKeys = (set, keys) => {
  keys.forEach((key) => set.add(key))
}

export const useEngagementStore = defineStore('engagement', () => {
  const likedItems = ref([])
  const likedKeys = ref(new Set())
  const loadingKeys = ref(new Set())
  const loading = ref(false)
  const loaded = ref(false)

  const likedCount = computed(() => likedItems.value.length)

  const rebuildLikedKeys = () => {
    const nextKeys = new Set()
    likedItems.value.forEach((item) => addKeys(nextKeys, keysFromLikedItem(item)))
    likedKeys.value = nextKeys
  }

  const loadLikedOptions = async ({ force = false } = {}) => {
    if (!localStorage.getItem('access_token')) {
      likedItems.value = []
      likedKeys.value = new Set()
      loaded.value = false
      return []
    }

    if (loaded.value && !force) return likedItems.value

    loading.value = true
    try {
      const response = await getLikedProductOptions({ page: 1, page_size: 200 })
      likedItems.value = asArray(response)
      rebuildLikedKeys()
      loaded.value = true
      return likedItems.value
    } finally {
      loading.value = false
    }
  }

  const isLiked = (payload) => setHasAny(likedKeys.value, keysFromPayload(payload))

  const isLiking = (payload) => setHasAny(loadingKeys.value, keysFromPayload(payload))

  const toggleLikedProduct = async (payload) => {
    const keys = keysFromPayload(payload)
    if (!keys.size) throw new Error('product_id or product_option_id is required.')
    if (setHasAny(loadingKeys.value, keys)) return null

    const previousKeys = new Set(likedKeys.value)
    const previousItems = [...likedItems.value]
    const wasLiked = setHasAny(likedKeys.value, keys)

    const nextLoading = new Set(loadingKeys.value)
    addKeys(nextLoading, keys)
    loadingKeys.value = nextLoading

    const optimisticKeys = new Set(likedKeys.value)
    if (wasLiked) removeKeys(optimisticKeys, keys)
    else addKeys(optimisticKeys, keys)
    likedKeys.value = optimisticKeys

    if (!wasLiked) {
      likedItems.value = [
        {
          id: `optimistic-${Date.now()}`,
          group_key: payload.group_key || payload.groupKey,
          option_id: payload.option_id || payload.optionId,
          product: { id: payload.product_id || payload.productId },
          product_option: payload.product_option_id ? { id: payload.product_option_id } : null,
          brand: payload.brand,
          name: payload.name,
          option: payload.option,
          image_url: payload.image_url || payload.imageUrl,
          product_url: payload.product_url || payload.productUrl,
          snapshot: payload.snapshot || {},
        },
        ...likedItems.value,
      ]
    } else {
      likedItems.value = likedItems.value.filter((item) => !setHasAny(keysFromLikedItem(item), keys))
    }

    try {
      const response = await toggleLikedProductOption(payload)
      if (response?.is_liked && response.item) {
        likedItems.value = [response.item, ...likedItems.value.filter((item) => !setHasAny(keysFromLikedItem(item), keys))]
      } else if (!response?.is_liked) {
        likedItems.value = likedItems.value.filter((item) => !setHasAny(keysFromLikedItem(item), keys))
      }
      rebuildLikedKeys()
      loaded.value = true
      return response
    } catch (error) {
      likedKeys.value = previousKeys
      likedItems.value = previousItems
      throw error
    } finally {
      const doneLoading = new Set(loadingKeys.value)
      removeKeys(doneLoading, keys)
      loadingKeys.value = doneLoading
    }
  }

  return {
    likedItems,
    likedKeys,
    loading,
    loaded,
    likedCount,
    loadLikedOptions,
    isLiked,
    isLiking,
    toggleLikedProduct,
  }
})
