<template>
  <span
    v-if="showPlaceholder"
    :class="['user-avatar', 'user-avatar--placeholder', `user-avatar--${size}`, className]"
    role="img"
    :aria-label="alt"
  >
    {{ initials }}
  </span>

  <img
    v-else
    :src="displaySrc"
    :alt="alt"
    :class="['user-avatar', `user-avatar--${size}`, className]"
    @error="handleError"
  />
</template>

<script setup>
import { computed, ref, watch } from 'vue'

import { DEFAULT_PROFILE_IMAGE } from '@/constants/images'

const props = defineProps({
  src: {
    type: String,
    default: null,
  },
  alt: {
    type: String,
    default: '프로필 이미지',
  },
  name: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'md',
  },
  className: {
    type: String,
    default: '',
  },
})

const useFallbackImage = ref(false)
const fallbackFailed = ref(false)

watch(
  () => props.src,
  () => {
    useFallbackImage.value = false
    fallbackFailed.value = false
  },
)

const displaySrc = computed(() => {
  if (useFallbackImage.value || !props.src) return DEFAULT_PROFILE_IMAGE
  return props.src
})

const showPlaceholder = computed(() => fallbackFailed.value)

const initials = computed(() => {
  const source = props.name || props.alt || ''
  const first = source.trim().replace('프로필 이미지', '').trim().charAt(0)
  return first || 'L'
})

const handleError = () => {
  if (!useFallbackImage.value && props.src) {
    useFallbackImage.value = true
    return
  }

  fallbackFailed.value = true
}
</script>

<style scoped>
.user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  object-fit: cover;
  aspect-ratio: 1 / 1;
  background: #f5dcd6;
  color: #bf4f63;
  flex-shrink: 0;
  overflow: hidden;
  font-weight: 800;
  line-height: 1;
}

.user-avatar--sm {
  width: 32px;
  height: 32px;
  font-size: 13px;
}

.user-avatar--md {
  width: 42px;
  height: 42px;
  font-size: 16px;
}

.user-avatar--lg {
  width: 64px;
  height: 64px;
  font-size: 22px;
}

.user-avatar--xl {
  width: 100px;
  height: 100px;
  font-size: 34px;
}

.user-avatar--placeholder {
  border: 1px solid #eaded8;
  background: linear-gradient(135deg, #fff6f2, #f2d5dc);
}
</style>
