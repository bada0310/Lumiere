<template>
  <div class="category-header">
    <div class="tabs-shell" ref="tabsRef">
      <div class="tabs-wrapper">
        <button
          v-for="tab in visibleCategories"
          :key="tab.key"
          :class="{ active: activeCategory === tab.key }"
          class="tab-btn"
          type="button"
          @click="selectCategory(tab.key)"
        >
          <span class="icon" aria-hidden="true">{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
        </button>

        <button
          ref="moreButtonRef"
          class="grid-btn"
          type="button"
          aria-haspopup="menu"
          :aria-expanded="isMoreOpen"
          aria-label="커뮤니티 카테고리 더보기"
          @click.stop="toggleMore"
        >
          <span></span>
          <span></span>
          <span></span>
          <span></span>
        </button>
      </div>

      <div v-if="isMoreOpen" class="more-popover" role="menu">
        <button
          v-for="tab in hiddenCategories"
          :key="tab.key"
          type="button"
          role="menuitem"
          @click="selectCategory(tab.key)"
        >
          <span>{{ tab.icon }}</span>
          {{ tab.label }}
        </button>
      </div>
    </div>

    <div class="filter-search-bar">
      <div class="total-count">전체 게시글 <span>{{ totalCount }}</span></div>
      <div class="right-controls">
        <select v-model="sortBy" class="sort-select" @change="emitFilter">
          <option value="latest">최신순</option>
          <option value="popular">인기순</option>
        </select>
        <div class="search-box">
          <input
            type="text"
            placeholder="게시글 검색"
            v-model="searchQuery"
            @keyup.enter="handleSearch"
          />
          <button class="search-icon" type="button" @click="handleSearch">🔍</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { COMMUNITY_CATEGORIES } from '@/data/communityCategories'

const props = defineProps({
  totalCount: {
    type: Number,
    default: 0,
  },
  modelValue: {
    type: String,
    default: 'life-item',
  },
  sort: {
    type: String,
    default: 'latest',
  },
})

const emit = defineEmits(['filter', 'search', 'update:modelValue'])

const tabsRef = ref(null)
const moreButtonRef = ref(null)
const isMoreOpen = ref(false)
const activeCategory = ref(props.modelValue)
const sortBy = ref(props.sort)
const searchQuery = ref('')

const visibleCategories = computed(() => COMMUNITY_CATEGORIES.filter((category) => category.visible))
const hiddenCategories = computed(() => COMMUNITY_CATEGORIES.filter((category) => !category.visible))

watch(
  () => props.modelValue,
  (value) => {
    activeCategory.value = value
  },
)

const emitFilter = () => {
  emit('filter', { category: activeCategory.value, sortBy: sortBy.value })
}

const selectCategory = (category) => {
  activeCategory.value = category
  isMoreOpen.value = false
  emit('update:modelValue', category)
  emitFilter()
}

const toggleMore = () => {
  isMoreOpen.value = !isMoreOpen.value
}

const closeMore = () => {
  isMoreOpen.value = false
}

const handleSearch = () => {
  emit('search', searchQuery.value.trim())
}

const onDocumentClick = (event) => {
  if (!tabsRef.value?.contains(event.target)) {
    closeMore()
  }
}

const onKeydown = (event) => {
  if (event.key === 'Escape') {
    closeMore()
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.category-header {
  display: flex;
  flex-direction: column;
  gap: 22px;
  width: 100%;
  font-family: "Pretendard", "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
  letter-spacing: 0;
}

.tabs-shell {
  position: relative;
  width: 100%;
}

.tabs-wrapper {
  display: flex;
  width: 100%;
  min-height: 54px;
  align-items: stretch;
  overflow: hidden;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #ffffff;
}

.tab-btn,
.grid-btn {
  min-height: 54px;
  border: none;
  background: #ffffff;
  color: #2f2826;
  cursor: pointer;
  transition: background-color 0.18s, color 0.18s;
}

.tab-btn {
  flex: 1;
  padding: 0 18px;
  border-right: 1px solid #eaded8;
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.tab-btn.active {
  background: linear-gradient(180deg, #c95570 0%, #bd4662 100%);
  color: #ffffff;
  border-right-color: transparent;
  box-shadow: 0 1px 0 rgba(255,255,255,0.16) inset;
}

.tab-btn.active + .tab-btn {
  border-left-color: transparent;
}

.tab-btn:not(.active):hover,
.grid-btn:hover {
  background: #fff8f8;
  color: #8b3a4a;
}

.icon {
  font-size: 1rem;
  line-height: 1;
}

.grid-btn {
  width: 58px;
  flex: 0 0 58px;
  display: grid;
  grid-template-columns: repeat(2, 5px);
  grid-template-rows: repeat(2, 5px);
  gap: 5px;
  place-content: center;
}

.grid-btn span {
  width: 5px;
  height: 5px;
  border-radius: 2px;
  background: currentColor;
}

.more-popover {
  position: absolute;
  top: 62px;
  right: 0;
  z-index: 30;
  min-width: 180px;
  padding: 8px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 12px 26px rgba(88, 55, 45, 0.08);
}

.more-popover button {
  width: 100%;
  height: 40px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #3f3633;
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  padding: 0 10px;
}

.more-popover button:hover {
  background: #fff5f6;
  color: #8b3a4a;
}

.filter-search-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 0 16px;
  border-bottom: 1px solid #f0e5e0;
  gap: 16px;
}

.total-count {
  font-size: 0.95rem;
  font-weight: 600;
  color: #333;
}

.total-count span {
  color: #8b3a4a;
  font-weight: 700;
}

.right-controls {
  display: flex;
  gap: 10px;
}

.sort-select {
  height: 42px;
  min-width: 132px;
  padding: 0 32px 0 12px;
  border: 1px solid #e0d6d2;
  border-radius: 8px;
  font-size: 0.85rem;
  font-family: inherit;
  color: #555;
  outline: none;
  background: white;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-box input {
  height: 42px;
  padding: 0 38px 0 14px;
  border: 1px solid #e0d6d2;
  border-radius: 8px;
  font-size: 0.85rem;
  font-family: inherit;
  width: 210px;
  outline: none;
  background: #ffffff;
}

.search-icon {
  position: absolute;
  right: 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.95rem;
}

@media (max-width: 760px) {
  .tabs-shell {
    overflow-x: auto;
    padding-bottom: 4px;
  }

  .tabs-wrapper {
    min-width: 690px;
  }

  .tab-btn {
    min-width: 140px;
  }

  .filter-search-bar,
  .right-controls {
    align-items: stretch;
    flex-direction: column;
  }

  .search-box input {
    width: 100%;
  }
}
</style>
