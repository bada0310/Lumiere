<template>
  <div class="analysis-container">
    <div class="search-section">
      <h1>제품 분석</h1>
      <p>제품의 색상 옵션을 추출해 내 피부톤과 비교해요</p>
      
      <div class="input-wrapper">
        <input v-model="query" placeholder="브랜드명 또는 제품명을 검색하세요" />
        <button @click="searchProduct">검색</button>
      </div>
      
      <div class="url-wrapper">
        <input v-model="url" placeholder="올리브영 URL을 입력해주세요" />
        <button @click="analyzeUrl" class="analyze-btn">분석하기</button>
      </div>
    </div>

    <RecentAnalysis :history="analysisHistory" />

    <SearchResult v-if="result" :data="result" />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import RecentAnalysis from '@/components/analysis/RecentAnalysis.vue';
import SearchResult from '@/components/analysis/SearchResult.vue';

const query = ref('');
const url = ref('');
const result = ref(null);
const analysisHistory = ref([]); // ExternalAnalysis 데이터 리스트

const searchProduct = () => {
  // 백엔드 API 연동 로직
  console.log('검색어:', query.value);
};

const analyzeUrl = () => {
  // 백엔드 API 연동 로직 (URL 분석)
  console.log('분석할 URL:', url.value);
};
</script>

<style scoped>
.analysis-container { max-width: 800px; margin: 0 auto; padding: 40px; }
.search-section { display: flex; flex-direction: column; gap: 20px; margin-bottom: 50px; }
.input-wrapper, .url-wrapper { display: flex; gap: 10px; }
input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 8px; }
.analyze-btn { background-color: #8b3a4a; color: white; border: none; padding: 10px 20px; border-radius: 8px; }
</style>