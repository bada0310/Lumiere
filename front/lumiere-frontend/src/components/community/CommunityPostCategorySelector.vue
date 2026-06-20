<template>
  <div class="category-tabs" role="tablist" aria-label="게시글 카테고리">
    <button
      v-for="category in categories"
      :key="category.key"
      type="button"
      role="tab"
      :aria-selected="modelValue === category.apiValue"
      :class="{ active: modelValue === category.apiValue }"
      @click="$emit('update:modelValue', category.apiValue)"
    >
      <span>{{ category.icon }}</span>
      {{ category.label }}
    </button>
  </div>
</template>

<script setup>
import { COMMUNITY_CATEGORIES } from '@/data/communityCategories'

defineProps({
  modelValue: {
    type: String,
    required: true,
  },
})

defineEmits(['update:modelValue'])

const categories = COMMUNITY_CATEGORIES.filter((category) => category.boardType === 'post-category')
</script>

<style scoped>
.category-tabs {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
  margin-bottom: 22px;
}

.category-tabs button {
  height: 42px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: white;
  color: #3f3633;
  cursor: pointer;
  font: inherit;
}

.category-tabs button.active {
  background: #c65367;
  color: white;
  border-color: #c65367;
}

@media (max-width: 760px) {
  .category-tabs {
    grid-template-columns: 1fr;
  }
}
</style>
