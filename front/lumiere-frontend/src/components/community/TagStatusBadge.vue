<template>
  <span v-if="visible" class="tag-status-badge" :class="statusClass" :aria-label="ariaLabel">
    {{ status }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { TAG_STATUS } from '@/utils/communityTags'

const props = defineProps({
  status: {
    type: String,
    default: TAG_STATUS.NORMAL,
  },
})

const visible = computed(() => [TAG_STATUS.HOT, TAG_STATUS.NEW].includes(props.status))
const statusClass = computed(() => `tag-status-badge--${props.status.toLowerCase()}`)
const ariaLabel = computed(() => (props.status === TAG_STATUS.HOT ? '급상승 태그' : '새로운 태그'))
</script>

<style scoped>
.tag-status-badge {
  display: inline-flex;
  align-items: center;
  min-height: 16px;
  padding: 0 5px;
  border-radius: 9999px;
  font-size: 0.62rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: 0;
}

.tag-status-badge--hot {
  background: #f8dce2;
  color: #b64056;
}

.tag-status-badge--new {
  background: #edf2ff;
  color: #51678f;
}
</style>
