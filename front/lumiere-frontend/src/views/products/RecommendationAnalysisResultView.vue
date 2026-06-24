<template>
  <main class="recommend-result-page">
    <button type="button" class="back-btn" @click="router.back()">추천 목록으로 돌아가기</button>

    <section v-if="isLoading" class="state-panel" role="status" aria-live="polite">
      <div class="spinner"></div>
      <strong>추천 제품 색상 정보를 불러오는 중입니다.</strong>
    </section>

    <section v-else-if="errorMessage" class="state-panel error">
      {{ errorMessage }}
    </section>

    <template v-else-if="product">
      <article class="summary-panel">
        <div class="image-box">
          <img v-if="productImage" :src="productImage" :alt="product.name" />
          <div v-else class="image-fallback">{{ brandInitial }}</div>
        </div>

        <div class="summary-copy">
          <p class="eyebrow">{{ product.brand || '브랜드 미확인' }}</p>
          <h1>{{ product.name }}</h1>
          <p>{{ summaryReason }}</p>
          <div class="summary-tags">
            <span>{{ categoryLabel(product.category) }}</span>
            <span>{{ toneLabel }}</span>
            <span>{{ analysisBasis }}</span>
          </div>
        </div>

        <aside v-if="selectedOption" class="score-panel">
          <span class="status-chip" :class="statusClass(selectedStatus)">{{ selectedStatus || 'COLOR' }}</span>
          <strong>{{ scoreLabel(selectedOption) }}</strong>
          <p>{{ optionLabel(selectedOption) }}</p>
          <span class="swatch" :style="{ backgroundColor: optionColor(selectedOption) }"></span>
        </aside>
      </article>

      <div v-if="!payload?.personalized" class="notice-panel">
        퍼스널 컬러 진단을 하면 나에게 맞는 추천 제품을 더 정확하게 볼 수 있어요.
      </div>

      <section v-if="!options.length" class="state-panel">
        아직 비교 가능한 색상 옵션 정보가 없어요.
      </section>

      <template v-else>
        <section class="chart-section">
          <div class="section-head">
            <div>
              <h2>색상 옵션 비교</h2>
              <p>옵션별 색상을 Warm-Cool, Light-Deep 축에 배치해 내 퍼스널 컬러 위치와 비교합니다.</p>
            </div>
            <strong>{{ options.length }}개 옵션</strong>
          </div>

          <ProductOptionColorChart
            v-model="selectedOption"
            :product="product"
            :options="options"
            :user-tone-profile="userToneProfile"
          />

          <p v-if="selectedOption && !selectedOption.is_precise_color" class="fallback-note">
            이 옵션은 일부 색상 수치가 부족해 추정값 또는 대표 색상 기준으로 배치했습니다.
          </p>

          <div class="legend-row" aria-label="추천 등급 범례">
            <span><i class="best"></i>BEST</span>
            <span><i class="good"></i>GOOD</span>
            <span><i class="mix"></i>MIX</span>
            <span><i class="caution"></i>CAUTION</span>
            <span><i class="avoid"></i>AVOID</span>
          </div>
        </section>

        <section class="analysis-grid">
          <RecommendationAccordion
            :options="options"
            :selected-option="selectedOption"
            @select="selectedOption = $event"
          />

          <aside v-if="selectedOption" class="detail-panel">
            <span class="status-chip" :class="statusClass(selectedStatus)">{{ selectedStatus || 'COLOR' }}</span>
            <h2>{{ optionLabel(selectedOption) }}</h2>
            <p>{{ selectedOption.detail_reason || selectedOption.reason || summaryReason }}</p>
            <p v-if="selectedOption.usage_tip" class="usage-tip">{{ selectedOption.usage_tip }}</p>
            <button type="button" class="link-btn" :disabled="!productLink" @click="openProductLink">
              제품 링크 열기
            </button>
          </aside>
        </section>

        <section class="metrics-section">
          <div class="section-head">
            <div>
              <h2>피부톤과 제품 색상 비교</h2>
              <p>명도, 채도, 온도감, 선명도 등 주요 값을 같은 기준으로 비교합니다.</p>
            </div>
          </div>

          <div class="metric-bars">
            <article v-for="metric in metricRows" :key="metric.key">
              <div class="metric-top">
                <strong>{{ metric.label }}</strong>
                <span>차이 {{ metric.diff }}</span>
              </div>
              <div class="bar-pair">
                <span class="user-bar" :style="{ width: `${metric.user_value}%` }"></span>
                <span class="product-bar" :style="{ width: `${metric.product_value}%` }"></span>
              </div>
            </article>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>항목</th>
                  <th>내 퍼스널 컬러</th>
                  <th>제품 옵션</th>
                  <th>차이</th>
                  <th>해석</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="metric in metricRows" :key="`${metric.key}-row`">
                  <td>{{ metric.label }}</td>
                  <td>{{ metric.user_value }}</td>
                  <td>{{ metric.product_value }}</td>
                  <td>{{ metric.diff }}</td>
                  <td>{{ metric.explanation }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <p class="disclaimer">{{ disclaimer }}</p>
      </template>
    </template>
  </main>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ProductOptionColorChart from '@/components/products/ProductOptionColorChart.vue'
import RecommendationAccordion from '@/components/products/RecommendationAccordion.vue'
import { getRecommendationColorMatching } from '@/services/productApi'
import { readUserColorProfile } from '@/utils/colorRecommendationHelpers'

const route = useRoute()
const router = useRouter()

const payload = ref(null)
const selectedOption = ref(null)
const isLoading = ref(false)
const errorMessage = ref('')

const product = computed(() => normalizeProduct(payload.value?.product))
const options = computed(() => (Array.isArray(payload.value?.options) ? payload.value.options.map(normalizeOption) : []))
const userToneProfile = computed(() => normalizeToneProfile(payload.value?.user_tone))
const selectedStatus = computed(() => matchStatus(selectedOption.value))
const summaryReason = computed(() => payload.value?.summary_reason || selectedOption.value?.short_reason || selectedOption.value?.reason || '제품 옵션 색상과 퍼스널 컬러 기준을 비교했습니다.')
const toneLabel = computed(() => payload.value?.user_tone?.tone_label || payload.value?.user_tone?.tone_name || userToneProfile.value.toneName || '퍼스널 컬러 미설정')
const analysisBasis = computed(() => (payload.value?.personalized ? '퍼스널 컬러 / 제품 옵션 색상' : '제품 옵션 색상'))
const brandInitial = computed(() => (product.value?.brand || product.value?.name || 'L').slice(0, 1).toUpperCase())
const productImage = computed(() => selectedOption.value?.image_url || product.value?.image_url || product.value?.thumbnail_url || '')
const productLink = computed(() => selectedOption.value?.representative_offer?.product_url || product.value?.product_url || '')
const disclaimer = computed(() => payload.value?.disclaimer || '화면의 색상은 실제와 다를 수 있으며, AI 분석 결과는 참고용입니다.')
const metricRows = computed(() => {
  const apiRows = Array.isArray(payload.value?.comparison_metrics) ? payload.value.comparison_metrics : []
  if (apiRows.length) return apiRows.map(normalizeMetricRow)
  return buildMetricRows(userToneProfile.value, selectedOption.value)
})

const loadResult = async () => {
  if (!route.params.id) return
  isLoading.value = true
  errorMessage.value = ''
  payload.value = null
  selectedOption.value = null
  try {
    const result = await getRecommendationColorMatching(route.params.id, requestParams.value)
    payload.value = result
    selectedOption.value = selectInitialOption(result)
  } catch (error) {
    console.error('recommendation color matching load failed:', error)
    errorMessage.value = error?.response?.status === 404
      ? '추천 제품 색상 정보를 찾을 수 없습니다.'
      : '추천 제품 색상 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.'
  } finally {
    isLoading.value = false
  }
}

const selectInitialOption = (result) => {
  const normalizedOptions = Array.isArray(result?.options) ? result.options.map(normalizeOption) : []
  if (!normalizedOptions.length) return null
  const queryOptionId = String(route.query.option || '')
  const bestId = result?.best_option?.id
  return (
    normalizedOptions.find((option) => String(option.id) === queryOptionId) ||
    normalizedOptions.find((option) => String(option.id) === String(bestId)) ||
    normalizedOptions[0]
  )
}

const requestParams = computed(() => ({
  tone_key: route.query.tone_key || undefined,
  second_tone_key: route.query.second_tone_key || undefined,
}))

const normalizeProduct = (raw = {}) => ({
  id: raw.id,
  brand: raw.brand || raw.brand_name || '',
  name: raw.name || raw.product_name || '추천 제품',
  category: raw.category || 'ETC',
  image_url: raw.image_url || raw.thumbnail_url || '',
  product_url: raw.product_url || raw.url || '',
})

const normalizeOption = (option = {}) => ({
  ...option,
  id: option.id || option.option_id || option.option_key,
  option_no: option.option_no || '',
  option_name: option.option_name || option.display_name || '',
  hex_code: option.hex_code || option.hex || '#d9d3cf',
  match_status: matchStatus(option),
  chart_x: option.chart_x ?? option.coolness,
  chart_y: option.chart_y ?? metricInvert(option.brightness),
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

const normalizeMetricRow = (row) => ({
  key: row.key,
  label: row.label,
  user_value: metricValue(row.user_value),
  product_value: metricValue(row.product_value),
  diff: metricValue(row.diff),
  explanation: row.explanation || metricExplanation(row.label, row.diff),
})

const buildMetricRows = (toneProfile, option) => {
  if (!option) return []
  const axis = toneProfile?.axis_profile || toneProfile || {}
  return [
    ['brightness', '명도'],
    ['saturation', '채도'],
    ['coolness', '쿨 경향'],
    ['warmth', '웜 경향'],
    ['softness', '부드러움'],
    ['contrast', '대비'],
  ].map(([key, label]) => {
    const userValue = metricValue(axis[key])
    const productValue = metricValue(option[key])
    const diff = Math.abs(userValue - productValue)
    return {
      key,
      label,
      user_value: userValue,
      product_value: productValue,
      diff,
      explanation: metricExplanation(label, diff),
    }
  })
}

const metricExplanation = (label, diffValue) => {
  const diff = metricValue(diffValue)
  if (diff <= 8) return `${label} 차이가 작아 자연스럽게 이어지는 편이에요.`
  if (diff <= 20) return `${label} 차이가 있어 발색 강도를 조절하면 좋아요.`
  return `${label} 차이가 커서 포인트 사용을 권장해요.`
}

const matchStatus = (option) => {
  const explicit = String(option?.match_status || option?.grade || '').toUpperCase()
  if (['BEST', 'GOOD', 'MIX', 'CAUTION', 'AVOID', 'PENDING'].includes(explicit)) return explicit
  const score = Number(option?.match_score)
  if (!Number.isFinite(score)) return ''
  if (score >= 85) return 'BEST'
  if (score >= 70) return 'GOOD'
  if (score >= 55) return 'MIX'
  if (score >= 40) return 'CAUTION'
  return 'AVOID'
}

const optionLabel = (option) => {
  return [option?.option_no, option?.option_name || option?.display_name].filter(Boolean).join(' ') || '기본 옵션'
}

const optionColor = (option) => option?.hex_code || option?.hex || '#d9d3cf'

const scoreLabel = (option) => {
  const score = Number(option?.match_score)
  return Number.isFinite(score) ? `${Math.round(score)}점` : '점수 없음'
}

const statusClass = (status) => String(status || 'color').toLowerCase()

const categoryLabel = (value) => {
  const map = { LIP: '립', EYE: '아이', CHEEK: '치크', BASE: '베이스', LENS: '렌즈', ETC: '기타' }
  return map[value] || '기타'
}

const metricValue = (value) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.min(100, Math.max(0, Math.round(number)))
}

const metricInvert = (value) => 100 - metricValue(value)

const openProductLink = () => {
  if (!productLink.value) return
  window.open(productLink.value, '_blank', 'noopener,noreferrer')
}

watch(
  () => route.params.id,
  () => loadResult(),
)

watch(
  () => route.query.option,
  () => {
    if (payload.value) selectedOption.value = selectInitialOption(payload.value)
  },
)

watch(
  () => [route.query.tone_key, route.query.second_tone_key],
  () => loadResult(),
)

onMounted(loadResult)
</script>

<style scoped>
.recommend-result-page {
  min-height: 100vh;
  padding: 32px clamp(16px, 5vw, 48px) 72px;
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
.notice-panel,
.summary-panel,
.chart-section,
.detail-panel,
.metrics-section {
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.94);
}

.state-panel {
  min-height: 240px;
  display: grid;
  place-items: center;
  gap: 12px;
  padding: 32px;
  text-align: center;
  color: #6b625f;
}

.state-panel.error {
  color: #b14a5e;
}

.spinner {
  width: 34px;
  height: 34px;
  border: 3px solid #f2d9dd;
  border-top-color: #c65367;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.summary-panel {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) 220px;
  gap: 22px;
  padding: 22px;
}

.image-box {
  min-height: 220px;
  border-radius: 8px;
  overflow: hidden;
  background: #f7f3f1;
  display: grid;
  place-items: center;
}

.image-box img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #fff;
}

.image-fallback {
  color: #c65367;
  font-size: 44px;
  font-weight: 900;
}

.summary-copy {
  display: grid;
  align-content: center;
  gap: 12px;
}

.eyebrow {
  margin: 0;
  color: #8b7b76;
  font-size: 13px;
  font-weight: 900;
  text-transform: uppercase;
}

.summary-copy h1,
.detail-panel h2,
.metrics-section h2,
.chart-section h2 {
  margin: 0;
  color: #241d1c;
}

.summary-copy p,
.detail-panel p,
.section-head p,
.fallback-note,
.disclaimer {
  margin: 0;
  color: #5f5653;
  line-height: 1.65;
}

.summary-tags,
.legend-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.summary-tags span,
.status-chip {
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  font-weight: 900;
}

.summary-tags span {
  background: #f5ece8;
  color: #6c4d45;
}

.score-panel {
  border-left: 1px solid #efe4df;
  padding-left: 22px;
  display: grid;
  align-content: center;
  gap: 10px;
}

.score-panel strong {
  font-size: 32px;
}

.score-panel p {
  margin: 0;
  color: #6b625f;
  font-weight: 800;
}

.swatch {
  width: 44px;
  height: 44px;
  border: 1px solid rgba(45, 37, 36, 0.12);
  border-radius: 50%;
}

.status-chip.best {
  background: #fff0f1;
  color: #c65367;
}

.status-chip.good {
  background: #f0f7e8;
  color: #668e24;
}

.status-chip.mix {
  background: #fff5e6;
  color: #9b6124;
}

.status-chip.caution,
.status-chip.avoid {
  background: #fff3df;
  color: #9c5b15;
}

.notice-panel,
.fallback-note {
  margin-top: 18px;
  padding: 14px 18px;
  color: #8b3a4a;
  font-weight: 800;
}

.chart-section,
.metrics-section {
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

.section-head strong {
  color: #c65367;
  white-space: nowrap;
}

.legend-row {
  margin-top: 14px;
  color: #6b625f;
  font-size: 13px;
  font-weight: 900;
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

.legend-row .best { background: #c65367; }
.legend-row .good { background: #7aa52e; }
.legend-row .mix { background: #c98734; }
.legend-row .caution { background: #d6a400; }
.legend-row .avoid { background: #8f4d44; }

.analysis-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 18px;
  margin-top: 18px;
}

.detail-panel {
  align-self: start;
  display: grid;
  gap: 14px;
  padding: 24px;
}

.usage-tip {
  border-left: 3px solid #c65367;
  padding-left: 10px;
}

.link-btn {
  width: 100%;
  height: 44px;
  border: none;
  border-radius: 8px;
  background: #c65367;
  color: white;
  font-weight: 900;
  cursor: pointer;
}

.link-btn:disabled {
  background: #d9c2c6;
  cursor: not-allowed;
}

.metric-bars {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.metric-bars article {
  border: 1px solid #f0e5df;
  border-radius: 8px;
  padding: 14px;
}

.metric-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #6b625f;
  font-size: 13px;
  margin-bottom: 10px;
}

.bar-pair {
  display: grid;
  gap: 6px;
}

.bar-pair span {
  display: block;
  max-width: 100%;
  height: 8px;
  border-radius: 999px;
}

.user-bar {
  background: #6f8eb8;
}

.product-bar {
  background: #c65367;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 720px;
}

th,
td {
  border-top: 1px solid #efe4df;
  padding: 12px 10px;
  text-align: left;
  font-size: 13px;
}

th {
  color: #8b7b76;
  font-weight: 900;
}

td {
  color: #4a403e;
}

.disclaimer {
  margin-top: 16px;
  font-size: 13px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 980px) {
  .summary-panel,
  .analysis-grid {
    grid-template-columns: 1fr;
  }

  .score-panel {
    border-left: none;
    border-top: 1px solid #efe4df;
    padding: 18px 0 0;
  }

  .metric-bars {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .section-head {
    display: block;
  }
}
</style>
