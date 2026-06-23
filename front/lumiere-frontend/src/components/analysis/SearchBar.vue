<template>
  <div class="search-bar-container">
    <div class="page-header">
      <h1 class="title">제품 검색 & URL 분석</h1>
      <p class="subtitle">
        제품명을 검색하거나 제품 URL을 입력하면<br />
        색상 옵션을 분석해 퍼스널컬러 기준으로 비교합니다.
      </p>
    </div>

    <div class="search-panels-wrapper">
      <section class="search-card">
        <div class="card-header">
          <span class="icon" aria-hidden="true">S</span>
          <div>
            <h2 class="card-title">제품명으로 검색하기</h2>
            <p class="card-subtitle">DB에 저장된 브랜드명 또는 제품명을 검색합니다.</p>
          </div>
        </div>

        <form class="input-group" @submit.prevent="handleProductSearch">
          <input
            v-model="productKeyword"
            type="text"
            placeholder="브랜드명 또는 제품명 입력"
            class="search-input"
            autocomplete="off"
          />
          <button
            type="submit"
            class="inside-btn search-icon-btn"
            :disabled="isProductSearchDisabled"
            aria-label="제품 검색"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          </button>
        </form>

        <button
          type="button"
          class="panel-action-btn"
          :disabled="isProductSearchDisabled"
          @click="handleProductSearch"
        >
          {{ isSearchingProduct ? '검색 중...' : '검색하기' }}
        </button>

        <div class="popular-tags">
          <span class="tag-label">인기 검색어</span>
          <div class="tags-list">
            <button
              v-for="tag in popularTags"
              :key="tag"
              type="button"
              class="tag-btn"
              :disabled="isSearchingProduct"
              @click="clickPopularTag(tag)"
            >
              {{ tag }}
            </button>
          </div>
        </div>
      </section>

      <section class="search-card">
        <div class="card-header">
          <span class="icon link-icon" aria-hidden="true">U</span>
          <div>
            <h2 class="card-title">URL로 분석하기</h2>
            <p class="card-subtitle">제품 상세 페이지 URL을 입력해 옵션 색상을 분석합니다.</p>
          </div>
        </div>

        <form class="input-group" @submit.prevent="handleUrlAnalysis">
          <input
            v-model="urlInput"
            type="url"
            placeholder="https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do..."
            class="search-input"
          />
          <span class="inside-icon" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
            </svg>
          </span>
        </form>

        <button
          type="button"
          class="analyze-btn"
          :disabled="isUrlAnalysisDisabled"
          @click="handleUrlAnalysis"
        >
          {{ isAnalyzingUrl ? '분석 중...' : '분석하기' }}
        </button>
        <p class="helper-text">제품의 색상 옵션을 추출하고 내 퍼스널컬러와 비교합니다.</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  isAnalyzingUrl: {
    type: Boolean,
    default: false,
  },
  isSearchingProduct: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['search-product', 'analyze-url'])

const productKeyword = ref('')
const urlInput = ref('')

const popularTags = ['롬앤 틴트', '페리페라 틴트', '에스쁘아 파운데이션', '3CE 블러셔', '데이지크 섀도우']

const isProductSearchDisabled = computed(() => !productKeyword.value.trim() || props.isSearchingProduct)
const isUrlAnalysisDisabled = computed(() => !urlInput.value.trim() || props.isAnalyzingUrl)

const handleProductSearch = () => {
  const keyword = productKeyword.value.trim()
  if (!keyword || props.isSearchingProduct) return
  emit('search-product', keyword)
}

const clickPopularTag = (tag) => {
  productKeyword.value = tag
  handleProductSearch()
}

const handleUrlAnalysis = () => {
  const url = urlInput.value.trim()
  if (!url || props.isAnalyzingUrl) return
  emit('analyze-url', url)
}
</script>

<style scoped>
.search-bar-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: 'Pretendard', sans-serif;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.title {
  font-size: 1.8rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 12px;
}

.subtitle {
  font-size: 1rem;
  color: #666;
  line-height: 1.5;
}

.search-panels-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.search-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.icon {
  font-size: 0.9rem;
  font-weight: 900;
  background: #fff0f4;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #a64b62;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
  margin: 0 0 4px;
}

.card-subtitle {
  font-size: 0.85rem;
  color: #888;
  margin: 0;
}

.input-group {
  position: relative;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.search-input {
  width: 100%;
  padding: 16px 45px 16px 20px;
  border: 1px solid #eaeaea;
  border-radius: 12px;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.2s;
  background-color: #fafafa;
}

.search-input:focus {
  border-color: #a64b62;
  background-color: #ffffff;
}

.inside-btn,
.inside-icon {
  position: absolute;
  right: 16px;
  background: none;
  border: none;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
}

.inside-btn {
  cursor: pointer;
}

.inside-btn:disabled {
  cursor: not-allowed;
  color: #bbb;
}

.inside-icon {
  pointer-events: none;
}

.panel-action-btn,
.analyze-btn {
  width: 100%;
  background-color: #b75a73;
  color: white;
  border: none;
  padding: 16px 0;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-bottom: 12px;
}

.panel-action-btn:hover,
.analyze-btn:hover {
  background-color: #9d495f;
}

.panel-action-btn:disabled,
.analyze-btn:disabled {
  background-color: #d8c2c9;
  cursor: not-allowed;
}

.popular-tags {
  margin-top: auto;
}

.tag-label {
  font-size: 0.8rem;
  color: #a64b62;
  font-weight: 600;
  margin-bottom: 10px;
  display: block;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-btn {
  background: #f8f8f8;
  border: 1px solid #eeeeee;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  color: #555;
  cursor: pointer;
  transition: all 0.2s;
}

.tag-btn:hover {
  background: #fff0f4;
  color: #a64b62;
  border-color: #fbdce4;
}

.tag-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.helper-text {
  text-align: center;
  font-size: 0.8rem;
  color: #888;
  margin: 0;
}

@media (max-width: 768px) {
  .search-panels-wrapper {
    grid-template-columns: 1fr;
  }
}
</style>
