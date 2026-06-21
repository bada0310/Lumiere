<template>
  <button
    type="button"
    class="tag-chip"
    :class="[categoryClass, sizeClass, { active }]"
    :aria-pressed="active"
    :aria-label="ariaLabel"
    :title="`${normalizedTag.name} ${categoryLabel}`"
    @click="$emit('select', normalizedTag)"
  >
    <span class="tag-chip-name">{{ normalizedTag.name }}</span>
    <TagStatusBadge :status="normalizedTag.status" />
  </button>
</template>

<script setup>
import { computed } from 'vue'

import TagStatusBadge from '@/components/community/TagStatusBadge.vue'
import { getTagCategoryClass, normalizePopularTag } from '@/utils/communityTags'

const CATEGORY_LABELS = {
  PRODUCT: '제품 태그',
  BRAND: '브랜드 태그',
  CONCERN: '고민 태그',
  TREND: '트렌드 태그',
  MAKEUP: '메이크업 태그',
}

const props = defineProps({
  tag: {
    type: Object,
    required: true,
  },
  active: {
    type: Boolean,
    default: false,
  },
  size: {
    type: String,
    default: 'compact',
  },
})

defineEmits(['select'])

const normalizedTag = computed(() => normalizePopularTag(props.tag))
const categoryClass = computed(() => getTagCategoryClass(normalizedTag.value.category))
const sizeClass = computed(() => (props.size === 'large' ? 'tag-chip--large' : 'tag-chip--compact'))
const categoryLabel = computed(() => CATEGORY_LABELS[normalizedTag.value.category] || '태그')
const ariaLabel = computed(() => {
  const selected = props.active ? '선택됨' : '선택 안 됨'
  const status =
    normalizedTag.value.status === 'HOT'
      ? ', 급상승'
      : normalizedTag.value.status === 'NEW'
        ? ', 신규'
        : ''
  return `${normalizedTag.value.name}, ${categoryLabel.value}, ${selected}${status}`
})
</script>

<style scoped>
.tag-chip {
  min-height: 36px;
  border: 1px solid transparent;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #7d4050;
  cursor: pointer;
  font-family: inherit;
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.2;
  max-width: 100%;
  transition:
    background-color 0.16s ease,
    border-color 0.16s ease,
    box-shadow 0.16s ease,
    transform 0.16s ease;
}

.tag-chip--compact {
  padding: 7px 12px;
  font-size: 0.78rem;
}

.tag-chip--large {
  min-height: 40px;
  padding: 9px 14px;
  font-size: 0.86rem;
}

.tag-chip-name {
  min-width: 0;
  overflow-wrap: anywhere;
}

.tag-chip:hover {
  transform: translateY(-1px);
}

.tag-chip:focus-visible {
  outline: 3px solid rgba(198, 83, 103, 0.24);
  outline-offset: 2px;
}

.tag-chip.active {
  border-color: rgba(139, 58, 74, 0.34);
  box-shadow: 0 0 0 2px rgba(198, 83, 103, 0.12);
}

.tag-chip--product,
.tag-chip--concern {
  background: #fff1f5;
  color: #9d4054;
}

.tag-chip--brand {
  background: #edf5fb;
  color: #496577;
}

.tag-chip--trend {
  background: #fff0ee;
  color: #c65367;
}

.tag-chip--makeup {
  background: #fff6eb;
  color: #8f584c;
}

.tag-chip--product:hover,
.tag-chip--concern:hover,
.tag-chip--product.active,
.tag-chip--concern.active {
  background: #f8dfe7;
}

.tag-chip--brand:hover,
.tag-chip--brand.active {
  background: #dfeaf4;
}

.tag-chip--trend:hover,
.tag-chip--trend.active {
  background: #f7dce0;
}

.tag-chip--makeup:hover,
.tag-chip--makeup.active {
  background: #f7e7d7;
}

@media (prefers-reduced-motion: reduce) {
  .tag-chip {
    transition: none;
  }

  .tag-chip:hover {
    transform: none;
  }
}
</style>
