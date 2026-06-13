<template>
  <div class="category-header">
    <div class="tabs-wrapper">
      <button 
        v-for="tab in categories" 
        :key="tab" 
        :class="{ active: activeCategory === tab }"
        @click="selectCategory(tab)"
      >
        {{ tab }}
      </button>
    </div>

    <div class="filter-search-bar">
      <div class="total-count">전체 게시글 <span>1,248</span></div>
      <div class="right-controls">
        <select v-model="sortBy" class="sort-select">
          <option value="latest">최신순</option>
          <option value="popular">인기순</option>
        </select>
        <div class="search-box">
          <input type="text" placeholder="게시글 검색" v-model="searchQuery" @keyup.enter="handleSearch" />
          <span class="search-icon">🔍</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const emit = defineEmits(['filter', 'search']);

const categories = ['🛍️ 인생템 공유', '✨ 발색 리뷰', '💬 메이크업 질문', '🎁 제품 추천'];
const activeCategory = ref('🛍️ 인생템 공유');
const sortBy = ref('latest');
const searchQuery = ref('');

const selectCategory = (category) => {
  activeCategory.value = category;
  emit('filter', { category, sortBy: sortBy.value });
};

const handleSearch = () => {
  emit('search', searchQuery.value);
};
</script>

<style scoped>
.category-header { display: flex; flex-direction: column; gap: 20px; width: 100%; }
.tabs-wrapper { display: flex; gap: 12px; width: 100%; }
.tabs-wrapper button {
  flex: 1; padding: 14px; border: 1px solid #e8e8e8; background: white;
  border-radius: 12px; font-size: 0.95rem; font-weight: 600; color: #666; cursor: pointer;
}
.tabs-wrapper button.active {
  background-color: #8b3a4a; color: white; border-color: #8b3a4a;
}

.filter-search-bar { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 15px; }
.total-count { font-size: 0.95rem; font-weight: bold; }
.total-count span { color: #8b3a4a; }
.right-controls { display: flex; gap: 12px; }
.sort-select { padding: 8px 12px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 0.85rem; color: #555; outline: none; }
.search-box { position: relative; display: flex; align-items: center; }
.search-box input { padding: 8px 36px 8px 16px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 0.85rem; width: 200px; outline: none; }
.search-icon { position: absolute; right: 12px; color: #aaa; cursor: pointer; font-size: 0.9rem; }
</style>