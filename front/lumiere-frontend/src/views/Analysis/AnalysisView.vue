<template>
  <div class="analysis-view-container">
    <ProductImageAnalysisForm
      :loading="isAnalyzingImage"
      @submit-analysis="handleAnalyzeImage"
    />

    <div v-if="errorMessage" class="message-panel error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="message-panel success">{{ successMessage }}</div>
    <div v-if="warningMessage" class="message-panel warning">{{ warningMessage }}</div>

    <RecentAnalysis
      :items="recentAnalyses"
      :loading="isLoadingRecentAnalyses"
      :selected-id="selectedAnalysisId"
      @select-analysis="handleSelectRecentAnalysis"
      @delete-analysis="handleDeleteRecentAnalysis"
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
            <p class="brand">{{ analysisProduct.brand || '브랜드 미확인' }}</p>
            <h2>{{ analysisProduct.name }}</h2>
            <p>{{ analysisCopy }}</p>
            <div class="summary-badges">
              <span class="status-chip">{{ confirmedLabel }}</span>
              <span v-if="analysisCategoryLabel" class="status-chip soft">{{ analysisCategoryLabel }}</span>
            </div>
          </div>

          <aside v-if="selectedOption" class="best-summary">
            <span :class="{ pending: isPendingOption(selectedOption) }" :style="{ backgroundColor: selectedColor }"></span>
            <p>선택 옵션</p>
            <strong>{{ optionLabel(selectedOption) }}</strong>
            <em>{{ scoreLabel(selectedOption) }}</em>
          </aside>
        </article>

        <div v-if="!hasPersonalizedResult" class="primary-missing-box">
          메인 퍼스널컬러가 설정되어 있지 않아 개인화 점수는 표시하지 않습니다. 색상 추출과 차트 위치는 그대로 확인할 수 있습니다.
        </div>

        <section class="review-panel">
            <div class="section-head review-head">
              <div>
                <h2>검토 및 수정</h2>
                <p>옵션명과 HEX 색상을 검토한 뒤 저장하고 확정합니다.</p>
              </div>
              <div class="action-row">
                <button type="button" class="secondary-btn" :disabled="isSavingReview || !hasReviewChanges" @click="handleSaveReview">
                  {{ isSavingReview ? '저장 중...' : '수정 저장' }}
                </button>
                <button type="button" class="primary-btn" :disabled="isConfirmingAnalysis" @click="handleConfirmAnalysis">
                  {{ isConfirmingAnalysis ? '확정 중...' : '분석 확정' }}
                </button>
              </div>
            </div>

            <div class="review-meta">
              <label>
                <span>제품명</span>
                <input v-model="editableProduct.product_name" type="text" />
              </label>
              <label>
                <span>브랜드명</span>
                <input v-model="editableProduct.brand_name" type="text" />
              </label>
              <label>
                <span>카테고리</span>
                <select v-model="editableProduct.category">
                  <option value="LIP">립</option>
                  <option value="EYE">아이</option>
                  <option value="CHEEK">치크</option>
                  <option value="BASE">베이스</option>
                  <option value="LENS">렌즈</option>
                  <option value="ETC">기타</option>
                </select>
              </label>
            </div>

            <div class="review-list">
              <article v-for="(option, index) in editableOptions" :key="option.localId" class="review-item">
                <div class="review-item-top">
                  <span class="dot" :style="{ backgroundColor: option.hex_code || '#d9d3cf' }"></span>
                  <strong>{{ option.display_name || option.option_name || `옵션 ${index + 1}` }}</strong>
                  <span class="confidence-badge">{{ confidenceLabel(option.confidence) }}</span>
                  <span class="source-badge">{{ colorSourceLabel(option.color_source) }}</span>
                  <button type="button" class="remove-btn" @click="removeEditableOption(index)">삭제</button>
                </div>

                <div class="review-fields">
                  <label>
                    <span>원본 옵션명</span>
                    <input v-model="option.option_name" type="text" />
                  </label>
                  <label>
                    <span>표시 이름</span>
                    <input v-model="option.display_name" type="text" />
                  </label>
                  <label>
                    <span>HEX</span>
                    <input v-model="option.hex_code" type="text" placeholder="#B95F55" />
                  </label>
                  <label>
                    <span>차트 X</span>
                    <input v-model.number="option.chart_x" type="number" min="0" max="100" />
                  </label>
                  <label>
                    <span>차트 Y</span>
                    <input v-model.number="option.chart_y" type="number" min="0" max="100" />
                  </label>
                </div>
              </article>
            </div>

            <button type="button" class="secondary-btn add-btn" @click="addEditableOption">누락 옵션 추가</button>
        </section>

        <div v-if="!analysisOptions.length" class="result-state">추출된 옵션이 없습니다. 위에서 옵션을 직접 추가한 뒤 저장할 수 있습니다.</div>

        <template v-else>
          <section class="chart-section">
            <div class="section-head">
              <div>
                <h2>옵션 색상 차트</h2>
                <p>업로드 이미지에서 읽은 위치를 기준으로 Warm/Cool, Light/Deep 차트에 배치했습니다.</p>
              </div>
              <strong>{{ toneLabel }}</strong>
            </div>
            <ProductOptionColorChart
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
              <p>{{ selectedOption.reason || pendingReason }}</p>
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
import { useRoute } from 'vue-router'

import ProductImageAnalysisForm from '@/components/analysis/ProductImageAnalysisForm.vue'
import RecentAnalysis from '@/components/analysis/RecentAnalysis.vue'
import ProductOptionColorChart from '@/components/products/ProductOptionColorChart.vue'
import RecommendationAccordion from '@/components/products/RecommendationAccordion.vue'
import { API_ORIGIN } from '@/config/api'
import {
  analyzeProductColorImage,
  confirmProductImageAnalysis,
  deleteProductImageAnalysis,
  getProductImageAnalyses,
  getProductImageAnalysis,
  updateProductImageAnalysis,
} from '@/services/productApi'
import { readUserColorProfile } from '@/utils/colorRecommendationHelpers'

const route = useRoute()

const isAnalyzingImage = ref(false)
const isSavingReview = ref(false)
const isConfirmingAnalysis = ref(false)
const isLoadingRecentAnalyses = ref(false)
const isLoadingAnalysisDetail = ref(false)
const recentAnalyses = ref([])
const selectedAnalysisId = ref('')
const analysisResult = ref(null)
const selectedOption = ref(null)
const errorMessage = ref('')
const successMessage = ref('')
const resultSectionRef = ref(null)
const editableProduct = ref({ product_name: '', brand_name: '', category: 'ETC' })
const editableOptions = ref([])
const reviewSnapshot = ref('')

const pendingReason = '색상 확인 필요'
const isResultLoading = computed(() => isLoadingAnalysisDetail.value)
const analysisProduct = computed(() => normalizeProductFromResult(analysisResult.value))
const analysisOptions = computed(() => (analysisResult.value?.options || []).map(normalizeOption))
const personalizedOptions = computed(() => analysisOptions.value.filter((option) => optionGrade(option)))
const hasPersonalizedResult = computed(() => Boolean(analysisResult.value?.personalized))
const userToneProfile = computed(() => normalizeToneProfile(analysisResult.value?.user_tone))
const toneLabel = computed(() => {
  return hasPersonalizedResult.value ? userToneProfile.value.toneName || '메인 퍼스널컬러' : '메인 퍼스널컬러 미설정'
})
const selectedColor = computed(() => optionColor(selectedOption.value))
const productImage = computed(() => resolveMediaUrl(analysisResult.value?.uploaded_image_url || analysisProduct.value?.representative_image_url || ''))
const disclaimer = computed(() => analysisResult.value?.disclaimer || '')
const confirmedLabel = computed(() => (analysisResult.value?.confirmed ? '확정 완료' : '검토 중'))
const warningMessage = computed(() => {
  if (analysisResult.value?.warning?.code === 'AI_VISION_UNAVAILABLE_FALLBACK_USED') {
    return 'AI 옵션명 인식은 실패했지만, 이미지에서 색상 후보를 추출했습니다. 옵션명을 확인해주세요.'
  }
  return ''
})
const analysisCopy = computed(() => {
  if (warningMessage.value) {
    return 'AI 옵션명 인식은 실패했지만 색상 후보는 추출했습니다. 아래에서 옵션명과 HEX를 확인하고 수정해주세요.'
  }
  return analysisOptions.value.length
    ? `${analysisOptions.value.length}개 옵션을 추출했습니다. 필요하면 아래에서 직접 수정한 뒤 확정하세요.`
    : '추출된 옵션이 없습니다. 아래에서 직접 추가해 저장할 수 있습니다.'
})
const analysisCategoryLabel = computed(() => categoryLabel(analysisProduct.value?.category))
const hasReviewChanges = computed(() => reviewSnapshot.value !== buildReviewSnapshot())
const selectedMetrics = computed(() => {
  const option = selectedOption.value
  if (!option) return []
  return [
    { label: 'HEX', value: option.hex_code || '-' },
    { label: 'Confidence', value: confidenceLabel(option.confidence) },
    { label: 'Source', value: colorSourceLabel(option.color_source) },
    { label: 'Chart X', value: metricValue(option.chart_x) },
    { label: 'Chart Y', value: metricValue(option.chart_y) },
    { label: 'Brightness', value: metricValue(option.brightness) },
    { label: 'Saturation', value: metricValue(option.saturation) },
    { label: 'Coolness', value: metricValue(option.coolness) },
    { label: 'Warmth', value: metricValue(option.warmth) },
    { label: 'Depth', value: metricValue(option.depth) },
  ]
})

const handleAnalyzeImage = async (payload) => {
  clearMessages()
  isAnalyzingImage.value = true
  try {
    const result = await analyzeProductColorImage(payload)
    applyAnalysisResult(result)
    successMessage.value = '제품 색상표 분석이 완료되었습니다.'
    await fetchRecentAnalyses()
    await scrollToResult()
  } catch (error) {
    errorMessage.value = safeAnalysisErrorMessage(error)
  } finally {
    isAnalyzingImage.value = false
  }
}

const fetchRecentAnalyses = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    recentAnalyses.value = []
    return
  }
  isLoadingRecentAnalyses.value = true
  try {
    const response = await getProductImageAnalyses({ limit: 8 })
    const records = Array.isArray(response) ? response : response.results || []
    recentAnalyses.value = records.map(normalizeRecentAnalysis)
  } catch (error) {
    console.error('recent image analyses load failed:', error)
    recentAnalyses.value = []
  } finally {
    isLoadingRecentAnalyses.value = false
  }
}

const handleSelectRecentAnalysis = async (analysis) => {
  if (!analysis?.id) return
  clearMessages()
  isLoadingAnalysisDetail.value = true
  selectedAnalysisId.value = String(analysis.id)
  try {
    const result = await getProductImageAnalysis(analysis.id)
    applyAnalysisResult(result)
    await scrollToResult()
  } catch (error) {
    console.error('image analysis detail load failed:', error)
    errorMessage.value = '저장된 분석 결과를 불러오지 못했습니다.'
  } finally {
    isLoadingAnalysisDetail.value = false
  }
}

const handleDeleteRecentAnalysis = async (analysis) => {
  if (!analysis?.id) return
  clearMessages()
  try {
    await deleteProductImageAnalysis(analysis.id)
    recentAnalyses.value = recentAnalyses.value.filter((item) => String(item.id) !== String(analysis.id))
    if (String(selectedAnalysisId.value) === String(analysis.id)) {
      selectedAnalysisId.value = ''
      analysisResult.value = null
      selectedOption.value = null
      editableOptions.value = []
    }
    successMessage.value = '분석 기록을 삭제했습니다.'
  } catch (error) {
    console.error('delete image analysis failed:', error)
    errorMessage.value = '분석 기록을 삭제하지 못했습니다.'
  }
}

const handleSaveReview = async ({ silent = false } = {}) => {
  if (!analysisResult.value?.analysis_id) return
  isSavingReview.value = true
  clearMessages()
  try {
    const result = await updateProductImageAnalysis(analysisResult.value.analysis_id, buildReviewPayload())
    applyAnalysisResult(result)
    if (!silent) successMessage.value = '수정 사항을 저장했습니다.'
  } catch (error) {
    errorMessage.value = safeAnalysisErrorMessage(error)
    throw error
  } finally {
    isSavingReview.value = false
  }
}

const handleConfirmAnalysis = async () => {
  if (!analysisResult.value?.analysis_id) return
  isConfirmingAnalysis.value = true
  clearMessages()
  try {
    if (hasReviewChanges.value) {
      await handleSaveReview({ silent: true })
    }
    const result = await confirmProductImageAnalysis(analysisResult.value.analysis_id)
    applyAnalysisResult(result)
    successMessage.value = '분석 결과를 확정했습니다.'
    await fetchRecentAnalyses()
  } catch (error) {
    errorMessage.value = safeAnalysisErrorMessage(error)
  } finally {
    isConfirmingAnalysis.value = false
  }
}

const applyAnalysisResult = (result) => {
  analysisResult.value = result
  selectedAnalysisId.value = String(result?.analysis_id || '')
  selectedOption.value = selectInitialOption(result)
  initializeEditableState(result)
}

const selectInitialOption = (result) => {
  const options = Array.isArray(result?.options) ? result.options.map(normalizeOption) : []
  if (!options.length) return null
  const bestId = result?.best_option?.id
  return options.find((option) => String(option.id) === String(bestId)) || options[0]
}

const initializeEditableState = (result) => {
  const product = normalizeProductFromResult(result)
  editableProduct.value = {
    product_name: product?.name || '',
    brand_name: product?.brand || '',
    category: product?.category || 'ETC',
  }
  editableOptions.value = (result?.options || []).map((option, index) => ({
    localId: `${option.id || 'option'}-${index}`,
    id: option.id,
    option_name: option.option_name || '',
    display_name: option.display_name || option.option_name || '',
    hex_code: option.hex_code || '',
    chart_x: option.chart_x ?? null,
    chart_y: option.chart_y ?? null,
    confidence: option.confidence ?? null,
    color_source: option.color_source || '',
  }))
  reviewSnapshot.value = buildReviewSnapshot()
}

const buildReviewPayload = () => ({
  product_name: editableProduct.value.product_name.trim(),
  brand_name: editableProduct.value.brand_name.trim(),
  category: editableProduct.value.category || 'ETC',
  options: editableOptions.value.map((option) => ({
    id: option.id,
    option_name: option.option_name.trim(),
    display_name: option.display_name.trim(),
    hex_code: option.hex_code.trim(),
    chart_x: numericOrNull(option.chart_x),
    chart_y: numericOrNull(option.chart_y),
    confidence: option.confidence,
  })),
})

const buildReviewSnapshot = () => JSON.stringify(buildReviewPayload())

const addEditableOption = () => {
  editableOptions.value.push({
    localId: `new-${Date.now()}-${editableOptions.value.length}`,
    id: null,
    option_name: '',
    display_name: '',
    hex_code: '',
    chart_x: null,
    chart_y: null,
    confidence: null,
    color_source: 'USER_EDITED',
  })
}

const removeEditableOption = (index) => {
  editableOptions.value.splice(index, 1)
}

const normalizeProductFromResult = (result) => {
  if (!result?.product) return null
  return {
    id: result.product.id || result.analysis_id || 'analysis-product',
    brand: result.product.brand_name || result.product.brand || '',
    name: result.product.product_name || result.product.name || '분석한 제품',
    category: result.product.category || 'ETC',
    description: result.product.description || '',
    representative_image_url: resolveMediaUrl(
  result.product.thumbnail_url || result.product.image_url || result.product.uploaded_image_url || ''),
  }
}

const normalizeOption = (option) => ({
  ...option,
  id: option.id || option.option_id,
  option_no: option.option_no || '',
  option_name: option.option_name || '',
  display_name: option.display_name || option.option_name || '',
  hex_code: option.hex_code || '',
  color_source: option.color_source || '',
  confidence: option.confidence ?? null,
  chart_x: option.chart_x ?? null,
  chart_y: option.chart_y ?? null,
  match_score: option.match_score ?? null,
  grade: option.grade || '',
  analysis_status: option.analysis_status || '',
})

const resolveMediaUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('blob:')) return url
  if (url.startsWith('/')) return `${API_ORIGIN}${url}`
  return `${API_ORIGIN}/${url}`
}

const normalizeRecentAnalysis = (record) => ({
  id: record.id,
  brandName: record.brand_name || '',
  productName: record.product_name || '',
  title: record.product_name || '제품 색상 분석',
  thumbnailUrl: resolveMediaUrl(record.uploaded_image_url || record.thumbnail_url || record.image_url || ''),
  analyzedAt: record.created_at,
  colors: Array.isArray(record.colors) ? record.colors : [],
})

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

const optionLabel = (option) => {
  return [option?.option_no, option?.display_name || option?.option_name].filter(Boolean).join(' ') || '기본 옵션'
}

const isPendingOption = (option) => {
  const status = String(option?.analysis_status || '').toUpperCase()
  const grade = String(option?.grade || '').toUpperCase()
  return status === 'PENDING_COLOR_ANALYSIS' || grade === 'PENDING'
}

const optionColor = (option) => {
  if (!option?.hex_code) return '#d9d3cf'
  return option.hex_code
}

const optionGrade = (option) => {
  if (isPendingOption(option)) return 'PENDING'
  const grade = String(option?.grade || '').toUpperCase()
  if (grade === 'BEST' || grade === 'GOOD' || grade === 'CAUTION') return grade
  const score = Number(option?.match_score)
  if (!Number.isFinite(score)) return ''
  if (score >= 85) return 'BEST'
  if (score >= 55) return 'GOOD'
  return 'CAUTION'
}

const scoreLabel = (option) => {
  if (isPendingOption(option)) return '분석 대기'
  const score = Number(option?.match_score)
  if (!Number.isFinite(score)) return hasPersonalizedResult.value ? '점수 없음' : '개인화 점수 없음'
  return `${Math.round(score)}점 · ${optionGrade(option)}`
}

const confidenceLabel = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? `신뢰도 ${Math.round(number * 100)}%` : '신뢰도 없음'
}

const colorSourceLabel = (value) => {
  if (value === 'IMAGE_EXTRACTED') return '이미지 추출'
  if (value === 'AI_ESTIMATED') return 'AI 추정'
  if (value === 'USER_EDITED') return '사용자 수정'
  return '확인 필요'
}

const categoryLabel = (value) => {
  const map = {
    LIP: '립',
    EYE: '아이',
    CHEEK: '치크',
    BASE: '베이스',
    LENS: '렌즈',
    ETC: '기타',
  }
  return map[value] || ''
}

const metricValue = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? Math.round(number) : '-'
}

const numericOrNull = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? Math.max(0, Math.min(100, Math.round(number))) : null
}

const safeAnalysisErrorMessage = (error) => {
  const data = error?.response?.data
  if (data?.message) return String(data.message)
  if (data?.detail) return String(data.detail)
  return '제품 색상 분석 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.'
}

const clearMessages = () => {
  errorMessage.value = ''
  successMessage.value = ''
}

const scrollToResult = async () => {
  await nextTick()
  resultSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const loadRouteAnalysis = async () => {
  if (!route.params.id) return
  await handleSelectRecentAnalysis({ id: route.params.id })
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
  background: #fffafb;
  padding: 0 0 80px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-panel {
  width: calc(100% - 40px);
  max-width: 1200px;
  margin: 0 auto;
  border-radius: 8px;
  padding: 14px 18px;
  font-weight: 800;
  line-height: 1.5;
}

.message-panel.error {
  border: 1px solid #f1c4cc;
  background: #fff2f4;
  color: #b14a5e;
}

.message-panel.success {
  border: 1px solid #cfe5cc;
  background: #f4fbf2;
  color: #457d38;
}

.message-panel.warning {
  border: 1px solid #f1ddb0;
  background: #fff8e7;
  color: #8a5a00;
}

.analysis-result-section {
  width: calc(100% - 40px);
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  gap: 18px;
}

.result-state,
.primary-missing-box {
  border: 1px dashed #eaded8;
  border-radius: 8px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.9);
  color: #6f6562;
}

.result-summary,
.review-panel,
.chart-section,
.detail-panel {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #eaded8;
  border-radius: 8px;
}

.result-summary {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) 220px;
  gap: 20px;
  padding: 20px;
}

.image-box {
  min-height: 220px;
  border-radius: 8px;
  overflow: hidden;
  background: #f7f3f1;
}

.image-box img,
.image-fallback {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.summary-body {
  display: grid;
  align-content: center;
  gap: 10px;
}

.brand,
.best-summary p,
.detail-panel .eyebrow {
  margin: 0;
  color: #8b7b76;
  font-size: 13px;
  font-weight: 800;
  text-transform: uppercase;
}

.summary-body h2,
.detail-panel h2 {
  margin: 0;
  color: #241d1c;
}

.summary-body p:last-of-type,
.detail-panel p {
  margin: 0;
  color: #5f5653;
  line-height: 1.6;
}

.summary-badges,
.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.status-chip,
.confidence-badge,
.source-badge {
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  font-weight: 800;
}

.status-chip {
  background: #f5ece8;
  color: #6c4d45;
}

.status-chip.soft,
.confidence-badge {
  background: #f4f0ee;
  color: #6b625f;
}

.source-badge {
  background: #fff1f4;
  color: #b05568;
}

.best-summary {
  border-left: 1px solid #efe4df;
  padding-left: 20px;
  display: grid;
  align-content: center;
  gap: 10px;
}

.best-summary span,
.swatch {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid rgba(36, 29, 28, 0.08);
}

.best-summary span.pending,
.swatch.pending {
  background: #d9d3cf !important;
  border-style: dashed;
}

.best-summary strong,
.best-summary em {
  font-style: normal;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 18px;
}

.section-head h2 {
  margin: 0 0 8px;
}

.section-head p {
  margin: 0;
  color: #6b625f;
}

.review-panel,
.chart-section,
.detail-panel {
  padding: 20px;
}

.review-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.review-meta label,
.review-fields label {
  display: grid;
  gap: 8px;
}

.review-meta span,
.review-fields span {
  color: #5b504e;
  font-size: 12px;
  font-weight: 700;
}

.review-meta input,
.review-meta select,
.review-fields input {
  min-height: 42px;
  border: 1px solid #e5d9d5;
  border-radius: 8px;
  padding: 0 12px;
  background: #fffdfc;
}

.review-list {
  display: grid;
  gap: 12px;
}

.review-item {
  border: 1px solid #efe5e1;
  border-radius: 8px;
  padding: 14px;
  background: #fffdfc;
}

.review-item-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.review-item-top .dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid rgba(36, 29, 28, 0.1);
}

.review-fields {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.result-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 18px;
}

.detail-panel {
  display: grid;
  align-content: start;
  gap: 12px;
}

.detail-panel dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
  margin: 0;
}

.detail-panel dt {
  color: #8b7b76;
  font-size: 12px;
  font-weight: 700;
}

.detail-panel dd {
  margin: 0;
  color: #241d1c;
  font-weight: 700;
}

.primary-btn,
.secondary-btn,
.remove-btn {
  min-height: 42px;
  border: none;
  border-radius: 8px;
  padding: 0 14px;
  font-weight: 800;
  cursor: pointer;
}

.primary-btn {
  background: #c25f74;
  color: white;
}

.secondary-btn {
  background: #f4ebe7;
  color: #6b4d45;
}

.secondary-btn:disabled,
.primary-btn:disabled {
  background: #d8c9c5;
  color: #fff8f7;
  cursor: not-allowed;
}

.remove-btn {
  min-height: 30px;
  margin-left: auto;
  background: transparent;
  color: #a45a6a;
}

.add-btn {
  margin-top: 14px;
}

.disclaimer {
  margin: 0;
  color: #8e7e79;
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 980px) {
  .result-summary,
  .result-grid,
  .review-meta,
  .review-fields {
    grid-template-columns: 1fr;
  }

  .best-summary {
    border-left: none;
    border-top: 1px solid #efe4df;
    padding-left: 0;
    padding-top: 16px;
  }
}
</style>
