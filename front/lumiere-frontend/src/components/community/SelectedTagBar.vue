<template>
  <section v-if="normalizedTags.length" class="selected-tag-bar" aria-label="적용된 태그 필터">
    <div class="selected-tag-copy">
      <strong>{{ tagSummary }} 태그가 포함된 게시글</strong>
      <p>선택한 태그 조건으로 게시글을 보고 있어요.</p>
    </div>

    <div class="selected-tag-actions">
      <button
        v-for="tag in normalizedTags"
        :key="tag"
        type="button"
        class="selected-filter-chip"
        :aria-label="`${tag} 필터 해제`"
        @click="$emit('remove', tag)"
      >
        {{ tag }} <span aria-hidden="true">×</span>
      </button>
      <button type="button" class="clear-button" @click="$emit('clear')">필터 초기화</button>
      <button type="button" class="explore-button" @click="$emit('explore')">전체 태그 다시 탐색</button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { dedupeTagNames } from '@/utils/communityTags'

const props = defineProps({
  tags: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['remove', 'clear', 'explore'])

const normalizedTags = computed(() => dedupeTagNames(props.tags))
const tagSummary = computed(() => normalizedTags.value.join(', '))
</script>

<style scoped>
.selected-tag-bar {
  background: #fffaf8;
  border: 1px solid #eaded8;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.selected-tag-copy strong {
  display: block;
  color: #3f3633;
  font-size: 0.94rem;
  font-weight: 800;
}

.selected-tag-copy p {
  margin-top: 4px;
  color: #7c706c;
  font-size: 0.82rem;
}

.selected-tag-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.selected-filter-chip,
.clear-button,
.explore-button {
  min-height: 34px;
  border-radius: 9999px;
  cursor: pointer;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 800;
}

.selected-filter-chip {
  border: 1px solid #f0c9d1;
  background: #fff5f6;
  color: #9d4054;
  padding: 6px 10px;
}

.clear-button {
  border: 1px solid #eaded8;
  background: #ffffff;
  color: #6d5f5b;
  padding: 6px 12px;
}

.explore-button {
  border: 1px solid #c65367;
  background: #c65367;
  color: #ffffff;
  padding: 6px 12px;
}

.selected-filter-chip:focus-visible,
.clear-button:focus-visible,
.explore-button:focus-visible {
  outline: 3px solid rgba(198, 83, 103, 0.22);
  outline-offset: 2px;
}
</style>
