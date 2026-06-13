<template>
  <div class="search-bar-container">
    <div class="page-header">
      <h1 class="title">제품 검색 & URL 분석 ✨</h1>
      <p class="subtitle">
        원하는 제품을 검색하거나 올리브영 URL을 입력하면<br />
        색상 옵션을 분석해 당신의 퍼스널컬러와 비교해드려요.
      </p>
    </div>

    <div class="search-panels-wrapper">
      
      <div class="search-card">
        <div class="card-header">
          <span class="icon">🔍</span>
          <div>
            <h2 class="card-title">제품명으로 검색하기</h2>
            <p class="card-subtitle">브랜드명 또는 제품명을 검색해보세요</p>
          </div>
        </div>
        
        <form @submit.prevent="handleProductSearch" class="input-group">
          <input 
            type="text" 
            v-model="productKeyword"
            placeholder="브랜드명 또는 제품명 입력" 
            class="search-input"
          />
          <button type="submit" class="inside-btn search-icon-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          </button>
        </form>

        <div class="popular-tags">
          <span class="tag-label">인기 검색어</span>
          <div class="tags-list">
            <button 
              v-for="tag in popularTags" 
              :key="tag" 
              type="button"
              class="tag-btn"
              @click="clickPopularTag(tag)"
            >
              {{ tag }}
            </button>
          </div>
        </div>
      </div>

      <div class="search-card">
        <div class="card-header">
          <span class="icon link-icon">🔗</span>
          <div>
            <h2 class="card-title">URL로 분석하기</h2>
            <p class="card-subtitle">올리브영 상품 URL을 입력해보세요</p>
          </div>
        </div>
        
        <form @submit.prevent="handleUrlAnalysis" class="input-group">
          <input 
            type="url" 
            v-model="urlInput"
            placeholder="https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do..." 
            class="search-input"
          />
          <span class="inside-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
          </span>
        </form>

        <button @click="handleUrlAnalysis" class="analyze-btn">
          ✨ 분석하기
        </button>
        <p class="helper-text">ⓘ 제품의 색상 옵션을 추출해 내 피부톤과 비교해요.</p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

// 부모 컴포넌트(AnalysisView.vue)로 이벤트를 전달하기 위한 정의
const emit = defineEmits(['search-product', 'analyze-url']);

const productKeyword = ref('');
const urlInput = ref('');

// 목업에 있는 인기 검색어 데이터
const popularTags = ref([
  '롬앤 틴트', '클리오 섀도우', '에스쁘아 파운데이션', '3CE 블러셔', '데이지크 립'
]);

// 제품 검색 실행 함수
const handleProductSearch = () => {
  if (!productKeyword.value.trim()) return;
  emit('search-product', productKeyword.value);
};

// 인기 검색어 클릭 함수
const clickPopularTag = (tag) => {
  productKeyword.value = tag;
  handleProductSearch();
};

// URL 분석 실행 함수
const handleUrlAnalysis = () => {
  if (!urlInput.value.trim()) return;
  emit('analyze-url', urlInput.value);
};
</script>

<style scoped>
/* 전체 컨테이너 (목업의 부드러운 배경색 느낌을 부모에서 주겠지만 여기서도 여백 설정) */
.search-bar-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: 'Pretendard', sans-serif;
}

/* 상단 타이틀 영역 */
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

/* 패널 래퍼 (그리드로 2열 배치) */
.search-panels-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

@media (max-width: 768px) {
  .search-panels-wrapper {
    grid-template-columns: 1fr; /* 모바일에서는 세로로 배치 */
  }
}

/* 개별 검색 카드 스타일 */
.search-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
}

/* 카드 헤더 (아이콘 + 제목) */
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}
.icon {
  font-size: 1.5rem;
  background: #fff0f4;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #A64B62;
}
.card-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
  margin: 0 0 4px 0;
}
.card-subtitle {
  font-size: 0.85rem;
  color: #888;
  margin: 0;
}

/* 입력 필드 공통 */
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
  border-color: #A64B62;
  background-color: #ffffff;
}

/* 인풋창 내부 아이콘/버튼 */
.inside-btn, .inside-icon {
  position: absolute;
  right: 16px;
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
}
.inside-icon {
  cursor: default;
}

/* 인기 검색어 영역 */
.popular-tags {
  margin-top: auto; /* 카드의 남은 공간을 밀어내어 하단에 배치 */
}
.tag-label {
  font-size: 0.8rem;
  color: #A64B62;
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
  color: #A64B62;
  border-color: #fbdce4;
}

/* URL 분석 버튼 */
.analyze-btn {
  width: 100%;
  background-color: #b75a73; /* 목업의 버건디/핑크 컬러 */
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
.analyze-btn:hover {
  background-color: #9d495f;
}

/* 하단 안내 문구 */
.helper-text {
  text-align: center;
  font-size: 0.8rem;
  color: #888;
  margin: 0;
}
</style>