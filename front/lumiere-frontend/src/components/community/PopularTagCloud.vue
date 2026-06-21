<template>
  <div class="popular-tag-cloud">
    <p v-if="description" class="tag-cloud-desc">{{ description }}</p>

    <div class="tag-chip-wrap" aria-label="인기 제품 태그">
      <PopularTagChip
        v-for="tag in visibleTags"
        :key="tag.id || tag.key"
        :tag="tag"
        :active="selectedKeys.has(tag.key)"
        @select="$emit('select-tag', $event)"
      />
    </div>

    <button v-if="showMoreButton" class="text-link" type="button" @click="$emit('open-tag-explorer')">
      더 많은 태그 보기 &gt;
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import PopularTagChip from '@/components/community/PopularTagChip.vue'
import { getTagSearchKey, normalizePopularTags } from '@/utils/communityTags'

const props = defineProps({
  tags: {
    type: Array,
    default: () => [],
  },
  selectedTags: {
    type: Array,
    default: () => [],
  },
  previewLimit: {
    type: Number,
    default: 8,
  },
  description: {
    type: String,
    default: '',
  },
  showMoreButton: {
    type: Boolean,
    default: true,
  },
})

defineEmits(['select-tag', 'open-tag-explorer'])

const normalizedTags = computed(() => normalizePopularTags(props.tags))
const visibleTags = computed(() => normalizedTags.value.slice(0, props.previewLimit))
const selectedKeys = computed(() => new Set(props.selectedTags.map(getTagSearchKey)))
</script>

<style scoped>
.popular-tag-cloud {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tag-cloud-desc {
  margin: -4px 0 0;
  color: #7c706c;
  font-size: 0.76rem;
  line-height: 1.5;
}

.tag-chip-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.text-link {
  display: block;
  margin-left: auto;
  border: none;
  background: transparent;
  color: #c65367;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 700;
}

.text-link:focus-visible {
  outline: 3px solid rgba(198, 83, 103, 0.22);
  outline-offset: 3px;
  border-radius: 6px;
}
</style>
