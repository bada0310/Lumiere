<template>
  <section class="tag-explorer" aria-labelledby="tag-explorer-title">
    <button type="button" class="back-button" @click="$emit('back')">
      ← 게시글 목록으로 돌아가기
    </button>

    <header class="explorer-head">
      <div>
        <h2 id="tag-explorer-title">전체 태그 탐색 ✨</h2>
        <p>관심 있는 태그를 선택하고 관련 게시글을 찾아보세요.</p>
      </div>
      <span class="tag-total">{{ filteredTags.length }}개 태그</span>
    </header>

    <div class="explorer-controls">
      <label class="tag-search">
        <span>태그 검색</span>
        <input v-model.trim="searchQuery" type="search" placeholder="태그명을 입력해보세요" />
      </label>

      <label class="sort-select">
        <span>정렬</span>
        <select v-model="sortBy">
          <option value="popular">인기순</option>
          <option value="trending">급상승순</option>
          <option value="latest">최신순</option>
        </select>
      </label>
    </div>

    <div class="category-filters" aria-label="태그 카테고리">
      <button
        v-for="filter in categoryFilters"
        :key="filter.value"
        type="button"
        :class="{ active: activeCategory === filter.value }"
        :aria-pressed="activeCategory === filter.value"
        @click="activeCategory = filter.value"
      >
        {{ filter.label }}
      </button>
    </div>

    <div class="selected-panel" aria-live="polite">
      <strong>선택한 태그</strong>
      <div v-if="selectedTags.length" class="selected-list">
        <button
          v-for="tag in selectedTags"
          :key="tag"
          type="button"
          class="selected-tag"
          @click="toggleTag(tag)"
        >
          {{ tag }} <span aria-hidden="true">×</span>
        </button>
      </div>
      <p v-else>최대 3개까지 선택할 수 있어요.</p>
    </div>

    <p v-if="selectionMessage" class="selection-message" role="status">{{ selectionMessage }}</p>

    <div v-if="filteredTags.length" class="tag-cloud">
      <PopularTagChip
        v-for="tag in filteredTags"
        :key="tag.id || tag.key"
        :tag="tag"
        size="large"
        :active="selectedKeys.has(tag.key)"
        @select="toggleTag($event.name)"
      />
    </div>

    <div v-else class="tag-empty">
      <strong>검색 결과가 없어요.</strong>
      <p>다른 태그명이나 카테고리를 선택해보세요.</p>
    </div>

    <footer class="explorer-actions">
      <button type="button" class="reset-button" @click="clearSelected">선택 초기화</button>
      <button type="button" class="apply-button" @click="$emit('apply', selectedTags)">
        선택 적용하기
      </button>
    </footer>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

import PopularTagChip from '@/components/community/PopularTagChip.vue'
import {
  TAG_CATEGORY,
  dedupeTagNames,
  getTagSearchKey,
  normalizePopularTags,
} from '@/utils/communityTags'

const MAX_SELECTED_TAGS = 3

const props = defineProps({
  tags: {
    type: Array,
    default: () => [],
  },
  initialSelectedTags: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['back', 'apply'])

const searchQuery = ref('')
const activeCategory = ref('ALL')
const sortBy = ref('popular')
const selectedTags = ref(dedupeTagNames(props.initialSelectedTags))
const selectionMessage = ref('')

const categoryFilters = [
  { value: 'ALL', label: '전체' },
  { value: 'PRODUCT_CONCERN', label: '제품/고민' },
  { value: TAG_CATEGORY.BRAND, label: '브랜드' },
  { value: TAG_CATEGORY.TREND, label: '트렌드' },
  { value: TAG_CATEGORY.MAKEUP, label: '메이크업' },
]

const normalizedTags = computed(() => normalizePopularTags(props.tags))
const selectedKeys = computed(() => new Set(selectedTags.value.map(getTagSearchKey)))

const categoryMatches = (tag) => {
  if (activeCategory.value === 'ALL') return true
  if (activeCategory.value === 'PRODUCT_CONCERN') {
    return [TAG_CATEGORY.PRODUCT, TAG_CATEGORY.CONCERN].includes(tag.category)
  }
  return tag.category === activeCategory.value
}

const sortedTags = computed(() => {
  const copied = [...normalizedTags.value]

  if (sortBy.value === 'trending') {
    return copied.sort((a, b) => {
      const statusScore = { HOT: 3, NEW: 2, NORMAL: 1 }
      return (
        (statusScore[b.status] || 0) - (statusScore[a.status] || 0) ||
        b.trendScore - a.trendScore ||
        b.growthRate - a.growthRate ||
        a.sortIndex - b.sortIndex
      )
    })
  }

  if (sortBy.value === 'latest') {
    return copied.sort((a, b) => b.sortIndex - a.sortIndex)
  }

  return copied.sort((a, b) => b.postCount - a.postCount || a.sortIndex - b.sortIndex)
})

const filteredTags = computed(() => {
  const keyword = getTagSearchKey(searchQuery.value)
  return sortedTags.value.filter((tag) => {
    const matchesSearch = !keyword || tag.key.includes(keyword)
    return matchesSearch && categoryMatches(tag)
  })
})

const toggleTag = (tagName) => {
  const [normalizedName] = dedupeTagNames([tagName])
  if (!normalizedName) return

  const key = getTagSearchKey(normalizedName)
  if (selectedKeys.value.has(key)) {
    selectedTags.value = selectedTags.value.filter((tag) => getTagSearchKey(tag) !== key)
    selectionMessage.value = ''
    return
  }

  if (selectedTags.value.length >= MAX_SELECTED_TAGS) {
    selectionMessage.value = '태그는 최대 3개까지 선택할 수 있어요.'
    return
  }

  selectedTags.value = [...selectedTags.value, normalizedName]
  selectionMessage.value = ''
}

const clearSelected = () => {
  selectedTags.value = []
  selectionMessage.value = ''
}

watch(
  () => props.initialSelectedTags,
  (value) => {
    selectedTags.value = dedupeTagNames(value)
    selectionMessage.value = ''
  },
)
</script>

<style scoped>
.tag-explorer {
  background: #ffffff;
  border: 1px solid #eaded8;
  border-radius: 14px;
  padding: 26px;
  color: #2f2826;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.back-button {
  width: fit-content;
  border: none;
  background: transparent;
  color: #6d5f5b;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 700;
}

.back-button:focus-visible,
.category-filters button:focus-visible,
.selected-tag:focus-visible,
.reset-button:focus-visible,
.apply-button:focus-visible,
.tag-search input:focus-visible,
.sort-select select:focus-visible {
  outline: 3px solid rgba(198, 83, 103, 0.22);
  outline-offset: 2px;
}

.explorer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.explorer-head h2 {
  margin: 0;
  color: #231d1b;
  font-size: 1.34rem;
  font-weight: 700;
}

.explorer-head p {
  margin-top: 8px;
  color: #6d5f5b;
  font-size: 0.9rem;
}

.tag-total {
  flex: 0 0 auto;
  padding: 6px 10px;
  border-radius: 9999px;
  background: #fff5f6;
  color: #c65367;
  font-size: 0.78rem;
  font-weight: 800;
}

.explorer-controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 160px;
  gap: 12px;
}

.tag-search,
.sort-select {
  display: flex;
  flex-direction: column;
  gap: 7px;
  color: #4f4542;
  font-size: 0.8rem;
  font-weight: 700;
}

.tag-search input,
.sort-select select {
  width: 100%;
  height: 42px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: #ffffff;
  color: #3f3633;
  font: inherit;
  padding: 0 12px;
}

.category-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.category-filters button {
  height: 36px;
  padding: 0 13px;
  border: 1px solid #eaded8;
  border-radius: 9999px;
  background: #fffaf8;
  color: #6d5f5b;
  cursor: pointer;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 700;
}

.category-filters button.active {
  background: #c65367;
  border-color: #c65367;
  color: #ffffff;
}

.selected-panel {
  border: 1px solid #f1e5df;
  border-radius: 12px;
  background: #fffaf8;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.selected-panel strong {
  color: #3f3633;
  font-size: 0.88rem;
  font-weight: 800;
}

.selected-panel p {
  margin: 0;
  color: #8b807c;
  font-size: 0.82rem;
}

.selected-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.selected-tag {
  min-height: 34px;
  padding: 6px 10px;
  border: 1px solid #f0c9d1;
  border-radius: 9999px;
  background: #fff5f6;
  color: #9d4054;
  cursor: pointer;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 800;
}

.selection-message {
  margin: -8px 0 0;
  color: #b04658;
  font-size: 0.82rem;
  font-weight: 700;
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 9px;
  align-items: flex-start;
}

.tag-cloud :deep(.tag-chip:nth-child(4n + 2)) {
  margin-left: 12px;
}

.tag-cloud :deep(.tag-chip:nth-child(5n + 4)) {
  margin-left: 6px;
}

.tag-empty {
  border: 1px dashed #eaded8;
  border-radius: 12px;
  padding: 28px 18px;
  text-align: center;
  color: #7c706c;
}

.tag-empty strong {
  display: block;
  color: #3f3633;
  font-weight: 800;
  margin-bottom: 6px;
}

.tag-empty p {
  margin: 0;
}

.explorer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.reset-button,
.apply-button {
  height: 42px;
  padding: 0 18px;
  border-radius: 8px;
  cursor: pointer;
  font: inherit;
  font-weight: 800;
}

.reset-button {
  border: 1px solid #eaded8;
  background: #ffffff;
  color: #6d5f5b;
}

.apply-button {
  border: none;
  background: #c65367;
  color: #ffffff;
}

@media (max-width: 760px) {
  .tag-explorer {
    padding: 22px;
  }

  .explorer-head,
  .explorer-controls {
    grid-template-columns: 1fr;
  }

  .explorer-head {
    flex-direction: column;
  }

  .tag-cloud :deep(.tag-chip:nth-child(n)) {
    margin-left: 0;
  }

  .explorer-actions {
    position: sticky;
    bottom: 0;
    margin: 0 -22px -22px;
    padding: 14px 22px;
    background: rgba(255, 250, 248, 0.96);
    border-top: 1px solid #eaded8;
  }

  .reset-button,
  .apply-button {
    flex: 1;
  }
}
</style>
