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
import { ref } from 'vue'

import SearchBar from '@/components/analysis/SearchBar.vue'
import RecentAnalysis from '@/components/analysis/RecentAnalysis.vue'
import SearchResult from '@/components/analysis/SearchResult.vue'
import { createUrlAnalysisRecord } from '@/services/engagementApi'

const showResult = ref(true)
const resultData = ref(null)

const handleSearchProduct = (keyword) => {
  console.log('백엔드로 보낼 검색어:', keyword)
  showResult.value = true
}

const handleAnalyzeUrl = async (url) => {
  console.log('백엔드로 보낼 URL:', url)
  if (localStorage.getItem('access_token')) {
    try {
      await createUrlAnalysisRecord({
        source_url: url,
        title: url,
      })
    } catch (error) {
      console.warn('URL 분석 기록을 저장하지 못했습니다.', error)
    }
  }
  showResult.value = true
}
</script>

<style scoped>
.analysis-view-container {
  width: 100%;
  min-height: 100vh;
  background-color: #fffafb;
  padding: 40px 0 80px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
