<template>
  <main class="matching-page">
    <button v-if="hasRouteProductId" class="back-btn" type="button" @click="router.back()">추천 목록으로 돌아가기</button>

    <ProductInputCard
      v-model="productLink"
      :mode="pageMode"
      :product="product"
      :selected-option="selectedOption"
      :image-url="productImage"
      :loading="isBusy"
      @analyze="analyzeUrl"
      @open-link="openProductLink"
    />

    <section v-if="isBusy" class="loading-layout" role="status" aria-live="polite">
      <article class="state-panel loading-panel">
        <div class="spinner"></div>
        <strong>{{ loadingMessage }}</strong>
        <p>제품 정보와 색상 데이터를 정리하고 있습니다.</p>
      </article>
      <div class="skeleton-grid">
        <div class="skeleton-card"></div>
        <div class="skeleton-card small"></div>
      </div>
    </section>

    <section v-else-if="errorMessage" class="state-panel">{{ errorMessage }}</section>

    <section v-if="!isBusy && product && !hasPrimaryDiagnosis" class="primary-missing-box">
      메인 퍼스널컬러가 설정되어 있지 않습니다. 진단 결과 목록에서 메인 결과를 선택하면 개인화 추천 이유를 확인할 수 있습니다.
    </section>

    <section v-if="!isBusy && product && hasNoOptions" class="state-panel option-empty">
      색상 옵션 정보가 없습니다.
    </section>

    <template v-if="!isBusy && product && !hasNoOptions">
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
          :product="product"
          :options="options"
          :user-tone-profile="userToneProfile"
        />
        <div class="legend-row" aria-label="추천 등급 범례">
          <span><i class="best"></i>BEST</span>
          <span><i class="good"></i>GOOD</span>
          <span><i class="caution"></i>CAUTION</span>
        </div>
      </section>

      <section class="result-grid">
        <RecommendationAccordion
          :options="personalizedOptions"
          :selected-option="selectedOption"
          @select="selectedOption = $event"
        />

        <aside class="detail-panel" v-if="selectedOption">
          <div class="swatch" :style="{ backgroundColor: selectedColor }"></div>
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
          <button type="button" @click="openProductLink">제품 링크 열기</button>
        </aside>
      </section>

      <p class="disclaimer">{{ disclaimer }}</p>
    </template>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ProductColorChart from '@/components/products/ProductColorChart.vue'
import ProductInputCard from '@/components/products/ProductInputCard.vue'
import RecommendationAccordion from '@/components/products/RecommendationAccordion.vue'
import { getLatestDiagnosis } from '@/services/diagnosisApi'
import { analyzeProductColorUrl, getProduct } from '@/services/productApi'
import { clearDiagnosisColorProfile, readUserColorProfile, saveDiagnosisColorProfile } from '@/utils/colorRecommendationHelpers'

const route = useRoute()
const router = useRouter()

const LOADING_STAGES = [
  '제품 정보를 불러오는 중입니다.',
  '옵션 색상을 분석하는 중입니다.',
  '추천 설명을 생성하는 중입니다.',
]

const product = ref(null)
const selectedOption = ref(null)
const productLink = ref('')
const userToneProfile = ref(readUserColorProfile())
const hasPrimaryDiagnosis = ref(false)
const catalogLoading = ref(false)
const analysisLoading = ref(false)
const loadingStageIndex = ref(0)
const loadingTimer = ref(null)
const errorState = ref('')
const analysisPayload = ref(null)

const hasRouteProductId = computed(() => Boolean(route.params.id))
const pageMode = computed(() => (hasRouteProductId.value ? 'detail' : 'analysis'))
const isBusy = computed(() => catalogLoading.value || analysisLoading.value)
const loadingMessage = computed(() => LOADING_STAGES[loadingStageIndex.value] || LOADING_STAGES[0])
const options = computed(() => (Array.isArray(product.value?.options) ? product.value.options : []))
const hasNoOptions = computed(() => Boolean(product.value) && options.value.length === 0)
const personalizedOptions = computed(() => options.value.filter((option) => optionGrade(option)))
const toneLabel = computed(() => {
  return hasPrimaryDiagnosis.value ? userToneProfile.value.toneName || userToneProfile.value.tone_label || '메인 퍼스널컬러' : '메인 퍼스널컬러 미설정'
})
const selectedColor = computed(() => selectedOption.value?.hex_code || selectedOption.value?.hex || '#c65367')
const productImage = computed(() => {
  return (
    selectedOption.value?.image_url ||
    product.value?.representative_image_url ||
    product.value?.thumbnail_url ||
    product.value?.image ||
    product.value?.image_url ||
    ''
  )
})
const selectedOffer = computed(() => selectedOption.value?.representative_offer || selectedOption.value?.offers?.[0] || null)
const disclaimer = computed(() => {
  return (
    analysisPayload.value?.disclaimer ||
    '화면의 색상은 실제와 다를 수 있으며, 개인차가 있을 수 있습니다. AI 분석 결과는 참고용이며 실제 발색은 피부톤, 조명, 모니터 환경에 따라 달라질 수 있습니다.'
  )
})
const errorMessage = computed(() => {
  const messages = {
    'invalid-url': '제품 링크를 확인할 수 없습니다. URL을 다시 확인해주세요.',
    'not-found': '상품 정보를 찾을 수 없습니다.',
    'fetch-error': '제품 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.',
    'analysis-error': '색상 분석 중 문제가 발생했습니다. 다른 상품 링크로 다시 시도해주세요.',
    'api-error': '상품 정보를 불러오지 못했습니다.',
  }
  return messages[errorState.value] || ''
})
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
const requestParams = computed(() => {
  if (!hasPrimaryDiagnosis.value) return {}
  return {
    tone_key: userToneProfile.value.toneTag || userToneProfile.value.tone_key || undefined,
    second_tone_key: userToneProfile.value.secondToneTag || userToneProfile.value.second_tone_key || undefined,
  }
})

const syncPrimaryDiagnosisProfile = async () => {
  if (!localStorage.getItem('access_token')) {
    clearDiagnosisColorProfile()
    userToneProfile.value = readUserColorProfile()
    hasPrimaryDiagnosis.value = false
    return
  }

  try {
    const diagnosis = await getLatestDiagnosis()
    if (!diagnosis) {
      clearDiagnosisColorProfile()
      userToneProfile.value = readUserColorProfile()
      hasPrimaryDiagnosis.value = false
      return
    }
    userToneProfile.value = saveDiagnosisColorProfile(diagnosis)
    hasPrimaryDiagnosis.value = true
  } catch (error) {
    console.warn('메인 퍼스널컬러 정보를 불러오지 못했습니다.', error)
    clearDiagnosisColorProfile()
    userToneProfile.value = readUserColorProfile()
    hasPrimaryDiagnosis.value = false
  }
}

const loadProduct = async () => {
  if (!hasRouteProductId.value) {
    resetForUrlMode()
    return
  }

  catalogLoading.value = true
  errorState.value = ''
  analysisPayload.value = null
  product.value = null
  selectedOption.value = null
  productLink.value = ''
  startLoadingStages()

  try {
    product.value = await getProduct(route.params.id, requestParams.value)
    selectInitialOption()
    syncProductLink()
  } catch (error) {
    product.value = null
    selectedOption.value = null
    productLink.value = ''
    errorState.value = error?.response?.status === 404 ? 'not-found' : 'api-error'
    if (errorState.value !== 'not-found') console.error('상품 컬러 매칭 정보를 불러오지 못했습니다.', error)
  } finally {
    catalogLoading.value = false
    stopLoadingStages()
  }
}

const analyzeUrl = async () => {
  if (!productLink.value.trim()) {
    errorState.value = 'invalid-url'
    return
  }

  analysisLoading.value = true
  errorState.value = ''
  product.value = null
  selectedOption.value = null
  analysisPayload.value = null
  startLoadingStages()

  try {
    const response = await analyzeProductColorUrl(productLink.value.trim())
    analysisPayload.value = response
    applyAnalysisResponse(response)
  } catch (error) {
    console.error('제품 링크 색상 분석에 실패했습니다.', error)
    product.value = null
    selectedOption.value = null
    errorState.value = errorStateFromAnalysisError(error)
  } finally {
    analysisLoading.value = false
    stopLoadingStages()
  }
}

const applyAnalysisResponse = (response) => {
  const sourceProduct = response?.product || {}
  const normalizedOptions = Array.isArray(response?.options) ? response.options.map(normalizeAnalysisOption) : []
  const bestOptionId = response?.best_option?.id
  product.value = {
    id: `analysis:${sourceProduct.url || productLink.value}`,
    brand: sourceProduct.brand_name || '',
    name: sourceProduct.product_name || '분석한 제품',
    category: sourceProduct.category || 'LIP',
    description: sourceProduct.description || '입력한 제품 링크에서 추출한 옵션 색상을 분석했습니다.',
    representative_image_url: sourceProduct.thumbnail_url || '',
    product_url: sourceProduct.url || productLink.value,
    options: normalizedOptions,
    best_option: normalizedOptions.find((option) => String(option.id) === String(bestOptionId)) || normalizedOptions[0] || null,
  }

  if (response?.user_tone) {
    userToneProfile.value = normalizeToneProfile(response.user_tone)
    hasPrimaryDiagnosis.value = true
  } else {
    hasPrimaryDiagnosis.value = false
  }
  selectInitialOption()
  syncProductLink()
}

const normalizeAnalysisOption = (option) => ({
  ...option,
  id: option.id || option.option_id || option.option_no || option.option_name,
  option_no: option.option_no || option.option_id || '',
  option_name: option.option_name || option.name || '',
  hex_code: option.hex_code || option.hex || '#c65367',
  image_url: option.image_url || product.value?.representative_image_url || '',
})

const normalizeToneProfile = (tone) => ({
  toneName: tone.tone_label || tone.tone_name || tone.tone_key || '메인 퍼스널컬러',
  toneTag: tone.tone_key,
  secondToneTag: tone.second_tone_key,
  axis_profile: tone.axis_profile || {},
  range_profile: tone.range_profile || {},
  recommended_color_families: tone.recommended_color_families || [],
  caution_color_families: tone.caution_color_families || [],
})

const resetForUrlMode = () => {
  product.value = null
  selectedOption.value = null
  errorState.value = ''
  analysisPayload.value = null
}

const selectInitialOption = () => {
  const optionId = String(route.query.option || '')
  const queriedOption = options.value.find((option) => String(option.id) === optionId)
  const bestOption = options.value.find((option) => String(option.id) === String(product.value?.best_option?.id))
  selectedOption.value = queriedOption || bestOption || product.value?.best_option || options.value[0] || null
}

const syncProductLink = () => {
  productLink.value = selectedOffer.value?.product_url || product.value?.product_url || productLink.value || ''
}

const optionLabel = (option) => {
  return [option?.option_no, option?.option_name].filter(Boolean).join(' ') || option?.option || '기본 옵션'
}

const optionGrade = (option) => {
  const grade = String(option?.grade || '').toUpperCase()
  if (grade === 'BEST' || grade === 'GOOD' || grade === 'CAUTION') return grade
  const score = Number(option?.match_score)
  if (!Number.isFinite(score)) return ''
  if (score >= 85) return 'BEST'
  if (score >= 55) return 'GOOD'
  return 'CAUTION'
}

const metricValue = (value) => {
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? Math.round(numberValue) : '-'
}

const openProductLink = () => {
  const url = productLink.value || selectedOffer.value?.product_url || product.value?.product_url
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer')
}

const errorStateFromAnalysisError = (error) => {
  const code = error?.response?.data?.code
  if (code === 'invalid_url') return 'invalid-url'
  if (code === 'fetch_failed' || code === 'response_too_large') return 'fetch-error'
  if (error?.response?.status === 400) return 'invalid-url'
  if (error?.response?.status === 502 || error?.response?.status === 504) return 'fetch-error'
  return 'analysis-error'
}

const startLoadingStages = () => {
  stopLoadingStages()
  loadingStageIndex.value = 0
  loadingTimer.value = window.setInterval(() => {
    loadingStageIndex.value = (loadingStageIndex.value + 1) % LOADING_STAGES.length
  }, 1800)
}

const stopLoadingStages = () => {
  if (loadingTimer.value) {
    window.clearInterval(loadingTimer.value)
    loadingTimer.value = null
  }
}

watch(
  () => selectedOption.value?.id,
  () => {
    if (product.value) syncProductLink()
  },
)

watch(
  () => route.query.option,
  () => {
    if (product.value) {
      selectInitialOption()
      syncProductLink()
    }
  },
)

watch(
  () => route.params.id,
  () => {
    loadProduct()
  },
)

onMounted(async () => {
  await syncPrimaryDiagnosisProfile()
  await loadProduct()
})

onBeforeUnmount(() => {
  stopLoadingStages()
})
</script>

<style scoped>
.matching-page {
  min-height: 100vh;
  padding: 32px 48px 64px;
  background: #fffaf7;
  color: #2d2524;
}

.back-btn {
  border: none;
  background: transparent;
  color: #6b625f;
  font-weight: 800;
  cursor: pointer;
  margin-bottom: 18px;
}

.state-panel,
.chart-section,
.detail-panel {
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
}

.state-panel {
  margin-top: 18px;
  padding: 56px 20px;
  text-align: center;
}

.loading-layout {
  margin-top: 18px;
}

.loading-panel {
  display: grid;
  gap: 10px;
  place-items: center;
}

.loading-panel p {
  margin: 0;
  color: #6b625f;
}

.spinner {
  width: 34px;
  height: 34px;
  border: 3px solid #f2d9dd;
  border-top-color: #c65367;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 18px;
  margin-top: 18px;
}

.skeleton-card {
  min-height: 330px;
  border-radius: 8px;
  background: linear-gradient(90deg, #fff1f3, #ffffff, #fff1f3);
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}

.skeleton-card.small {
  min-height: 260px;
}

.option-empty {
  margin-top: 18px;
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

.section-head strong,
.eyebrow {
  color: #c65367;
  font-weight: 900;
}

.legend-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 12px;
  color: #6b625f;
  font-size: 13px;
  font-weight: 800;
}

.legend-row span {
  display: inline-flex;
  gap: 6px;
  align-items: center;
}

.legend-row i {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-row .best {
  background: #c65367;
}

.legend-row .good {
  background: #7aa52e;
}

.legend-row .caution {
  background: #d6a400;
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

.swatch {
  display: block;
  width: 54px;
  height: 54px;
  border: 1px solid rgba(45, 37, 36, 0.1);
  border-radius: 50%;
}

.detail-panel p {
  color: #5f5754;
  line-height: 1.6;
}

.usage-tip {
  border-left: 3px solid #c65367;
  padding-left: 10px;
}

.detail-panel dl {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 22px 0;
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

.detail-panel button {
  width: 100%;
  height: 44px;
  border: none;
  border-radius: 8px;
  background: #c65367;
  color: white;
  font-weight: 900;
  cursor: pointer;
}

.disclaimer {
  margin: 18px 0 0;
  color: #8e7e79;
  font-size: 13px;
  line-height: 1.6;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

@media (max-width: 980px) {
  .matching-page {
    padding: 24px 16px 48px;
  }

  .result-grid,
  .skeleton-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .section-head {
    display: block;
  }
}
</style>
