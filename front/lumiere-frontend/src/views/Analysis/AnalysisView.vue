<template>
  <div class="analysis-view-container">
    <SearchBar
      :is-analyzing-url="isAnalyzingUrl"
      :is-searching-product="isSearchingProduct"
      @search-product="handleSearchProduct"
      @analyze-url="handleAnalyzeUrl"
    />

    <div v-if="errorMessage" class="message-panel error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="message-panel success">{{ successMessage }}</div>

    <RecentAnalysis
      :items="recentAnalyses"
      :loading="isLoadingRecentAnalyses"
      :selected-id="selectedAnalysisId"
      @select-analysis="handleSelectRecentAnalysis"
      @delete-analysis="handleDeleteRecentAnalysis"
    />

    <SearchResult
      :products="searchPreviewResults"
      :loading="isSearchingProduct"
      :searched="hasSearchedProduct"
      :keyword="productSearchInput"
      :selected-product-id="selectedProductId"
      @select-product="handleSelectSearchPreviewProduct"
      @show-more="handleGoToMoreSearchResults"
    />

    <section ref="resultSectionRef" class="analysis-result-section">
      <div v-if="isResultLoading" class="result-state">분석 결과를 불러오는 중입니다.</div>

      <template v-else-if="analysisProduct">
        <article class="result-summary">
          <div class="image-box">
            <img v-if="productImage" :src="productImage" :alt="analysisProduct.name" />
            <div v-else class="image-fallback"></div>
          </div>

          <div class="summary-body">
            <p class="brand">{{ analysisProduct.brand || '브랜드 미상' }}</p>
            <h2>{{ analysisProduct.name }}</h2>
            <p>{{ analysisProduct.description || '분석한 제품의 색상 옵션을 퍼스널컬러 기준으로 비교했습니다.' }}</p>
            <a v-if="analysisProduct.product_url" :href="analysisProduct.product_url" target="_blank" rel="noreferrer">
              원본 링크 열기
            </a>
          </div>

          <aside v-if="selectedOption" class="best-summary">
            <span :class="{ pending: isPendingOption(selectedOption) }" :style="{ backgroundColor: selectedColor }"></span>
            <p>선택 옵션</p>
            <strong>{{ optionLabel(selectedOption) }}</strong>
            <em>{{ scoreLabel(selectedOption) }}</em>
          </aside>
        </article>

        <div v-if="!hasPersonalizedResult" class="primary-missing-box">
          메인 퍼스널컬러가 설정되어 있지 않습니다. 진단 결과 목록에서 메인 결과를 선택하면 개인화 추천 이유를 확인할 수 있습니다.
        </div>

        <div v-if="!analysisOptions.length" class="result-state">색상 옵션 정보가 없습니다.</div>

        <template v-else>
          <section class="chart-section">
            <div class="section-head">
              <div>
                <h2>옵션 색상 차트</h2>
                <p>Warm-Cool 축은 coolness, Light-Deep 축은 brightness 기준으로 배치합니다.</p>
              </div>
              <strong>{{ toneLabel }}</strong>
            </div>
            <ProductColorChart
              v-model="selectedOption"
              :product="analysisProduct"
              :options="analysisOptions"
              :user-tone-profile="userToneProfile"
            />
          </section>

          <section class="result-grid">
            <RecommendationAccordion
              :options="personalizedOptions"
              :selected-option="selectedOption"
              @select="selectedOption = $event"
            />

            <aside v-if="selectedOption" class="detail-panel">
              <div class="swatch" :class="{ pending: isPendingOption(selectedOption) }" :style="{ backgroundColor: selectedColor }"></div>
              <p class="eyebrow">{{ optionGrade(selectedOption) || 'COLOR' }}</p>
              <h2>{{ optionLabel(selectedOption) }}</h2>
              <p>{{ selectedOption.detail_reason || selectedOption.reason || '선택한 옵션의 색상 분석값을 기준으로 추천 점수를 계산했습니다.' }}</p>
              <p v-if="selectedOption.usage_tip" class="usage-tip">{{ selectedOption.usage_tip }}</p>
              <dl>
                <div v-for="metric in selectedMetrics" :key="metric.label">
                  <dt>{{ metric.label }}</dt>
                  <dd>{{ metric.value }}</dd>
                </div>
              </dl>
            </aside>
          </section>

          <p class="disclaimer">{{ disclaimer }}</p>
        </template>
      </template>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import RecentAnalysis from '@/components/analysis/RecentAnalysis.vue'
import SearchBar from '@/components/analysis/SearchBar.vue'
import SearchResult from '@/components/analysis/SearchResult.vue'
import ProductColorChart from '@/components/products/ProductColorChart.vue'
import RecommendationAccordion from '@/components/products/RecommendationAccordion.vue'
import { deleteUrlAnalysisRecord, getUrlAnalysisRecord, getUrlAnalysisRecords } from '@/services/engagementApi'
import { analyzeProductColorUrl, getProductColorAnalysis, searchProducts } from '@/services/productApi'
import { readUserColorProfile } from '@/utils/colorRecommendationHelpers'

const route = useRoute()
const router = useRouter()

const urlInput = ref('')
const productSearchInput = ref('')
const isAnalyzingUrl = ref(false)
const isSearchingProduct = ref(false)
const isLoadingProductAnalysis = ref(false)
const isLoadingRecentAnalyses = ref(false)
const isLoadingRecentAnalysisDetail = ref(false)
const recentAnalyses = ref([])
const selectedAnalysisId = ref('')
const searchPreviewResults = ref([])
const selectedProductId = ref('')
const analysisResult = ref(null)
const selectedOption = ref(null)
const errorMessage = ref('')
const successMessage = ref('')
const hasSearchedProduct = ref(false)
const resultSectionRef = ref(null)

const isResultLoading = computed(() => isLoadingProductAnalysis.value || isLoadingRecentAnalysisDetail.value)
const analysisProduct = computed(() => normalizeProductFromResult(analysisResult.value))
const analysisOptions = computed(() => {
  if (!analysisResult.value?.options) return []
  return analysisResult.value.options.map(normalizeOption)
})
const personalizedOptions = computed(() => analysisOptions.value.filter((option) => optionGrade(option)))
const hasPersonalizedResult = computed(() => Boolean(analysisResult.value?.personalized))
const userToneProfile = computed(() => normalizeToneProfile(analysisResult.value?.user_tone))
const toneLabel = computed(() => {
  return hasPersonalizedResult.value ? userToneProfile.value.toneName || '메인 퍼스널컬러' : '메인 퍼스널컬러 미설정'
})
const productImage = computed(() => selectedOption.value?.image_url || analysisProduct.value?.representative_image_url || '')
const selectedColor = computed(() => optionColor(selectedOption.value))
const disclaimer = computed(() => analysisResult.value?.disclaimer || '화면의 색상은 실제와 다를 수 있으며, 개인차가 있을 수 있습니다.')
const selectedMetrics = computed(() => {
  const option = selectedOption.value
  if (!option) return []
  return [
    { label: 'Hex', value: option.hex_code || '-' },
    { label: 'Brightness', value: metricValue(option.brightness) },
    { label: 'Saturation', value: metricValue(option.saturation) },
    { label: 'Coolness', value: metricValue(option.coolness) },
    { label: 'Warmth', value: metricValue(option.warmth) },
    { label: 'Depth', value: metricValue(option.depth) },
    { label: 'Softness', value: metricValue(option.softness) },
    { label: 'Contrast', value: metricValue(option.contrast) },
  ]
})

const handleAnalyzeUrl = async (url) => {
  clearMessages()
  const normalizedUrl = String(url || '').trim()
  urlInput.value = normalizedUrl

  if (!normalizedUrl) {
    errorMessage.value = '제품 URL을 입력해주세요.'
    return
  }
  if (!isValidUrl(normalizedUrl)) {
    errorMessage.value = '올바른 제품 링크를 입력해주세요.'
    return
  }

  isAnalyzingUrl.value = true
  selectedProductId.value = ''
  selectedAnalysisId.value = ''

  try {
    const result = await analyzeProductColorUrl(normalizedUrl)
    if (result?.success === false) {
      errorMessage.value = safeAnalysisErrorMessage({ response: { data: result } })
      return
    }
    applyAnalysisResult(result)
    successMessage.value = '제품 분석이 완료되었습니다.'
    await fetchRecentAnalyses()
    await scrollToResult()
  } catch (error) {
    console.error('product URL analysis failed:', error)
    errorMessage.value = safeAnalysisErrorMessage(error)
  } finally {
    isAnalyzingUrl.value = false
  }
}

const handleSearchProduct = async (keyword) => {
  clearMessages()
  const query = String(keyword || '').trim()
  productSearchInput.value = query
  hasSearchedProduct.value = true

  if (!query) {
    errorMessage.value = '검색할 제품명을 입력해주세요.'
    searchPreviewResults.value = []
    return
  }

  isSearchingProduct.value = true
  selectedProductId.value = ''

  try {
    const results = await searchProducts(query)
    searchPreviewResults.value = results.slice(0, 5).map(normalizeSearchProduct)
    if (!searchPreviewResults.value.length) {
      errorMessage.value = ''
    }
  } catch (error) {
    console.error('product search failed:', error)
    searchPreviewResults.value = []
    errorMessage.value = '제품 검색 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.'
  } finally {
    isSearchingProduct.value = false
  }
}

const handleSelectSearchPreviewProduct = async (product) => {
  clearMessages()
  const productId = product?.id
  if (!productId) {
    errorMessage.value = '선택한 제품 정보를 찾을 수 없습니다.'
    return
  }

  selectedProductId.value = productId
  selectedAnalysisId.value = ''
  isLoadingProductAnalysis.value = true

  try {
    const result = await getProductColorAnalysis(productId)
    applyAnalysisResult(result)
    await scrollToResult()
  } catch (error) {
    console.error('selected product analysis failed:', error)
    errorMessage.value = '선택한 제품의 컬러 분석 정보를 불러오지 못했습니다.'
  } finally {
    isLoadingProductAnalysis.value = false
  }
}

const handleSelectRecentAnalysis = async (analysis) => {
  clearMessages()
  const analysisId = analysis?.id
  if (!analysisId) {
    errorMessage.value = '최근 분석 결과를 찾을 수 없습니다.'
    return
  }

  selectedAnalysisId.value = analysisId
  selectedProductId.value = ''
  isLoadingRecentAnalysisDetail.value = true

  try {
    const record = await getUrlAnalysisRecord(analysisId)
    const resultPayload = record?.result_payload
    if (isAnalysisPayload(resultPayload)) {
      applyAnalysisResult(resultPayload)
    } else if (record?.source_url) {
      const fallbackResult = await analyzeProductColorUrl(record.source_url)
      applyAnalysisResult(fallbackResult)
    } else {
      throw new Error('recent analysis payload is empty')
    }
    await scrollToResult()
  } catch (error) {
    console.error('recent analysis load failed:', error)
    errorMessage.value = '최근 분석 결과를 불러오지 못했습니다.'
  } finally {
    isLoadingRecentAnalysisDetail.value = false
  }
}

const handleDeleteRecentAnalysis = async (analysis) => {
  clearMessages()
  if (!analysis?.id) return
  try {
    await deleteUrlAnalysisRecord(analysis.id)
    recentAnalyses.value = recentAnalyses.value.filter((item) => String(item.id) !== String(analysis.id))
    if (String(selectedAnalysisId.value) === String(analysis.id)) selectedAnalysisId.value = ''
    successMessage.value = '최근 분석 기록을 삭제했습니다.'
  } catch (error) {
    console.error('delete recent analysis failed:', error)
    errorMessage.value = '최근 분석 기록을 삭제하지 못했습니다.'
  }
}

const handleGoToMoreSearchResults = () => {
  clearMessages()
  const keyword = productSearchInput.value.trim()
  if (!keyword) {
    errorMessage.value = '검색어를 입력해주세요.'
    return
  }
  router.push({ name: 'products', query: { keyword } })
}

const fetchRecentAnalyses = async () => {
  if (!localStorage.getItem('access_token')) {
    recentAnalyses.value = []
    return
  }

  isLoadingRecentAnalyses.value = true
  try {
    const response = await getUrlAnalysisRecords({ limit: 8 })
    const records = Array.isArray(response) ? response : response.results || []
    recentAnalyses.value = records.map(normalizeRecentAnalysis)
  } catch (error) {
    console.error('recent analyses load failed:', error)
    recentAnalyses.value = []
  } finally {
    isLoadingRecentAnalyses.value = false
  }
}

const loadRouteAnalysis = async () => {
  const analysisId = route.params.id
  if (!analysisId) return
  await handleSelectRecentAnalysis({ id: analysisId })
}

const applyAnalysisResult = (result) => {
  analysisResult.value = result
  selectedOption.value = selectInitialOption(result)
}

const selectInitialOption = (result) => {
  const options = Array.isArray(result?.options) ? result.options.map(normalizeOption) : []
  if (!options.length) return null
  const bestId = result?.best_option?.id
  return options.find((option) => String(option.id) === String(bestId)) || options[0]
}

const normalizeProductFromResult = (result) => {
  if (!result?.product) return null
  return {
    id: result.product.id || result.product.product_id || result.product.url || 'analysis-product',
    brand: result.product.brand_name || result.product.brandName || result.product.brand || '',
    name: result.product.product_name || result.product.productName || result.product.name || '분석한 제품',
    category: result.product.category || 'PRODUCT',
    description: result.product.description || '',
    representative_image_url: result.product.thumbnail_url || result.product.thumbnailUrl || result.product.image_url || '',
    product_url: result.product.url || result.product.product_url || '',
  }
}

const normalizeOption = (option) => ({
  ...option,
  id: option.id || option.option_id || option.option_no || option.option_name,
  option_no: option.option_no || option.optionId || '',
  option_name: option.option_name || option.optionName || option.name || '',
  display_name: option.display_name || option.displayName || option.option_name || option.optionName || option.name || '',
  hex_code: option.hex_code || option.hex || null,
  analysis_status: option.analysis_status || option.analysisStatus || '',
  color_metrics: option.color_metrics || option.colorMetrics || null,
  match_score: option.match_score ?? option.matchScore ?? null,
  grade: option.grade || option.recommendation || '',
})

const normalizeSearchProduct = (product) => {
  const options = Array.isArray(product.options) ? product.options : []
  return {
    id: product.id || product.product_id,
    brandName: product.brand || product.brandName || '',
    productName: product.name || product.productName || '',
    thumbnailUrl: product.representative_image_url || product.image || product.image_url || '',
    category: product.category || '',
    optionCount: options.length,
    colors: options.slice(0, 5).map((option) => option.hex_code).filter(Boolean),
  }
}

const normalizeRecentAnalysis = (record) => {
  const payload = record.result_payload || {}
  const product = payload.product || {}
  const colors = Array.isArray(record.colors)
    ? record.colors.map((color) => color.hex_code || color.hex || color).filter(Boolean).slice(0, 5)
    : []
  return {
    id: record.id,
    brandName: record.brand || product.brand_name || product.brandName || '',
    productName: record.product_name || product.product_name || product.productName || record.title || '',
    title: record.title,
    thumbnailUrl: record.image_url || product.thumbnail_url || product.thumbnailUrl || '',
    analyzedAt: record.created_at,
    colors,
    sourceUrl: record.source_url,
  }
}

const normalizeToneProfile = (tone) => {
  if (!tone) return readUserColorProfile()
  return {
    toneName: tone.tone_label || tone.tone_name || tone.tone_key || '메인 퍼스널컬러',
    toneTag: tone.tone_key,
    secondToneTag: tone.second_tone_key,
    axis_profile: tone.axis_profile || {},
    range_profile: tone.range_profile || {},
  }
}

const isAnalysisPayload = (payload) => {
  return Boolean(payload?.product && Array.isArray(payload?.options))
}

const optionLabel = (option) => {
  return [option?.option_no, option?.display_name || option?.option_name].filter(Boolean).join(' ') || option?.option || '기본 옵션'
}

const isPendingOption = (option) => {
  const status = String(option?.analysis_status || option?.analysisStatus || '').toUpperCase()
  const grade = String(option?.grade || '').toUpperCase()
  return status === 'PENDING_COLOR_ANALYSIS' || grade === 'PENDING'
}

const optionColor = (option) => {
  if (!option) return '#d9d3cf'
  if (option.hex_code || option.hex) return option.hex_code || option.hex
  return '#d9d3cf'
}

const optionGrade = (option) => {
  if (isPendingOption(option)) return 'PENDING'
  const grade = String(option?.grade || '').toUpperCase()
  if (grade === 'BEST' || grade === 'GOOD' || grade === 'CAUTION') return grade
  const rawScore = option?.match_score
  if (rawScore === null || rawScore === undefined || rawScore === '') return ''
  const score = Number(rawScore)
  if (!Number.isFinite(score)) return ''
  if (score >= 85) return 'BEST'
  if (score >= 70) return 'GOOD'
  return 'CAUTION'
}

const scoreLabel = (option) => {
  if (isPendingOption(option)) return 'Pending analysis'
  const rawScore = option?.match_score
  const grade = optionGrade(option)
  if (rawScore === null || rawScore === undefined || rawScore === '') return grade || '분석 완료'
  const score = Number(rawScore)
  if (!Number.isFinite(score)) return grade || '분석 완료'
  return `${Math.round(score)}점 · ${grade || '분석'}`
}

const metricValue = (value) => {
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? Math.round(numberValue) : '-'
}

const isValidUrl = (value) => {
  try {
    const url = new URL(value)
    return ['http:', 'https:'].includes(url.protocol)
  } catch {
    return false
  }
}

const safeAnalysisErrorMessage = (error) => {
  const data = error?.response?.data
  const fallbackMessage = '상품 정보를 가져올 수 없습니다. URL을 다시 확인해주세요.'
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    if (data.code === 'SHORT_URL_RESOLVE_FAILED') {
      return '단축 링크를 분석하지 못했습니다. 올리브영 상품 상세 페이지의 전체 URL을 입력해주세요.'
    }
    return fallbackMessage
  }
  return fallbackMessage
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    if (data.code === 'SHORT_URL_RESOLVE_FAILED') {
      return '단축 링크를 분석하지 못했습니다. 올리브영 상품 상세 페이지의 전체 URL을 입력해주세요.'
    }
    if (data.code === 'invalid_url') {
      return '올바른 제품 링크를 입력해주세요.'
    }
    if (data.code) {
      return '상품 URL 분석에 실패했습니다. 잠시 후 다시 시도해주세요.'
    }
    const message = data.message || data.detail
    if (typeof message === 'string' && !looksLikeHtml(message)) {
      return `${message} 올리브영 링크는 상품 상세 URL 또는 단축 링크를 사용할 수 있습니다.`
    }
  }
  return '상품 URL 분석에 실패했습니다. 링크를 확인하거나 잠시 후 다시 시도해주세요. 올리브영 링크는 상품 상세 URL 또는 단축 링크를 사용할 수 있습니다.'
}

const looksLikeHtml = (value) => {
  const text = String(value || '').trim().toLowerCase()
  return text.includes('<!doctype html') || text.includes('<html') || text.includes('traceback')
}

const clearMessages = () => {
  errorMessage.value = ''
  successMessage.value = ''
}

const scrollToResult = async () => {
  await nextTick()
  resultSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

watch(
  () => route.params.id,
  () => {
    loadRouteAnalysis()
  },
)

onMounted(async () => {
  await fetchRecentAnalyses()
  await loadRouteAnalysis()
})
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

.message-panel {
  width: calc(100% - 40px);
  max-width: 1200px;
  margin: 0 auto;
  border-radius: 14px;
  padding: 14px 18px;
  font-weight: 800;
  line-height: 1.5;
}

.message-panel.error {
  border: 1px solid #f1c4cc;
  background: #fff4f6;
  color: #9d495f;
}

.message-panel.success {
  border: 1px solid #d8e7c0;
  background: #f6fbef;
  color: #6f8f2d;
}

.analysis-result-section {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  scroll-margin-top: 24px;
}

.result-state,
.result-summary,
.chart-section,
.detail-panel {
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.94);
}

.result-state {
  padding: 44px 20px;
  color: #8e7e79;
  text-align: center;
}

.result-summary {
  display: grid;
  grid-template-columns: 210px minmax(0, 1fr) 230px;
  gap: 22px;
  padding: 22px;
  align-items: stretch;
}

.image-box {
  display: grid;
  place-items: center;
  height: 210px;
  border-radius: 8px;
  background: #fff1f3;
  overflow: hidden;
}

.image-box img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: white;
}

.image-fallback {
  width: 78px;
  height: 116px;
  border-radius: 12px;
  background: linear-gradient(160deg, #f5b7c3, #c65367);
}

.brand,
.eyebrow {
  color: #c65367;
  font-size: 13px;
  font-weight: 900;
}

.summary-body h2 {
  margin: 6px 0 12px;
  font-size: 28px;
}

.summary-body p,
.detail-panel p {
  color: #5f5754;
  line-height: 1.6;
}

.summary-body a {
  display: inline-flex;
  margin-top: 14px;
  color: #b75a73;
  font-weight: 900;
  text-decoration: none;
}

.best-summary {
  padding: 22px;
  border-radius: 8px;
  background: #fff8f6;
}

.best-summary span,
.swatch {
  display: block;
  width: 54px;
  height: 54px;
  border: 1px solid rgba(45, 37, 36, 0.1);
  border-radius: 50%;
}

.best-summary span.pending,
.swatch.pending {
  background-color: #d9d3cf !important;
  border: 1px dashed rgba(94, 74, 70, 0.45);
}

.best-summary strong,
.best-summary em {
  display: block;
  margin-top: 8px;
}

.best-summary em {
  color: #c65367;
  font-style: normal;
  font-weight: 900;
}

.primary-missing-box {
  margin-top: 18px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: #fff8f6;
  color: #8b3a4a;
  font-weight: 800;
  line-height: 1.6;
  padding: 14px 18px;
}

.chart-section {
  margin-top: 18px;
  padding: 24px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-end;
  margin-bottom: 18px;
}

.section-head h2,
.detail-panel h2 {
  margin: 0 0 8px;
}

.section-head p {
  margin: 0;
  color: #6b625f;
}

.section-head strong {
  color: #c65367;
}

.result-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 18px;
  margin-top: 18px;
}

.detail-panel {
  align-self: start;
  padding: 24px;
}

.usage-tip {
  border-left: 3px solid #c65367;
  padding-left: 10px;
}

.detail-panel dl {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 22px 0 0;
}

.detail-panel dl div {
  padding: 10px;
  border-radius: 8px;
  background: #fff8f6;
}

.detail-panel dt {
  color: #8e7e79;
  font-size: 12px;
  font-weight: 800;
}

.detail-panel dd {
  margin: 4px 0 0;
  font-weight: 900;
}

.disclaimer {
  margin: 18px 0 0;
  color: #8e7e79;
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 980px) {
  .result-summary,
  .result-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .section-head {
    display: block;
  }
}
</style>
