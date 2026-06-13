<template>
  <div class="analysis-view-container">
    
    <SearchBar 
      @search-product="handleSearchProduct" 
      @analyze-url="handleAnalyzeUrl" 
    />

    <RecentAnalysis />

    <SearchResult v-if="showResult" :data="resultData" />
    
  </div>
</template>

<script setup>
import { ref } from 'vue';

// 세 가지 조각(컴포넌트)을 모두 불러옵니다.
import SearchBar from '@/components/analysis/SearchBar.vue';
import RecentAnalysis from '@/components/analysis/RecentAnalysis.vue';
import SearchResult from '@/components/analysis/SearchResult.vue';

// 화면 상태 관리
const showResult = ref(true); // 💡 퍼블리싱 화면을 바로 확인하기 위해 일단 true로 둡니다. 나중엔 false로 시작하세요.
const resultData = ref(null);

// SearchBar.vue 에서 제품 검색 버튼을 눌렀을 때 실행되는 함수
const handleSearchProduct = (keyword) => {
  console.log('백엔드로 보낼 검색어:', keyword);
  // TODO: 여기서 백엔드 API (axios 등)를 호출하여 데이터를 받아옵니다.
  // resultData.value = response.data;
  showResult.value = true; // 결과를 화면에 띄웁니다.
};

// SearchBar.vue 에서 URL 분석 버튼을 눌렀을 때 실행되는 함수
const handleAnalyzeUrl = (url) => {
  console.log('백엔드로 보낼 URL:', url);
  // TODO: 여기서 백엔드 API (axios 등)를 호출하여 데이터를 받아옵니다.
  // resultData.value = response.data;
  showResult.value = true; // 결과를 화면에 띄웁니다.
};
</script>

<style scoped>
/* 앱 전체의 배경색이나 페이지 전체 레이아웃을 잡아주는 래퍼 */
.analysis-view-container {
  width: 100%;
  min-height: 100vh;
  /* 목업 이미지의 은은한 배경색과 유사한 컬러를 깔아줍니다 */
  background-color: #fffafb; 
  padding: 40px 0 80px 0;
  display: flex;
  flex-direction: column;
  gap: 20px; /* 각 컴포넌트 사이의 간격 */
}
</style>