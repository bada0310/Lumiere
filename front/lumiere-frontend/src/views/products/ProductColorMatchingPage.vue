<template>
  <main class="matching-page">
    <button class="back-btn" type="button" @click="router.back()">추천 목록으로 돌아가기</button>

    <section v-if="isLoading" class="state-panel">상품 정보를 불러오는 중입니다.</section>
    <section v-else-if="errorMessage" class="state-panel">{{ errorMessage }}</section>

    <template v-else-if="product">
      <section class="summary">
        <div class="image-box">
          <img v-if="productImage" :src="productImage" :alt="product.name" />
          <div v-else class="image-fallback"></div>
        </div>

        <div class="summary-body">
          <p class="brand">{{ product.brand }}</p>
          <h1>{{ product.name }}</h1>
          <p>
            {{
              product.description ||
              `${product.category || '제품'}의 색상 옵션을 퍼스널 컬러 기준으로 비교합니다.`
            }}
          </p>
          <div class="link-row">
            <input v-model="productLink" type="url" placeholder="제품 링크" />
            <button type="button" @click="openProductLink">링크 열기</button>
          </div>
        </div>

        <aside v-if="selectedOption" class="best-summary">
          <span :style="{ backgroundColor: selectedOption.hex_code || '#c65367' }"></span>
          <p>선택 옵션</p>
          <strong>{{ optionLabel(selectedOption) }}</strong>
          <em>{{ scoreLabel(selectedOption) }}점 · {{ optionGrade(selectedOption) }}</em>
        </aside>
      </section>

      <section v-if="hasNoOptions" class="state-panel option-empty">색상 옵션 정보가 없습니다.</section>

      <template v-else>
        <section v-if="!hasPrimaryDiagnosis" class="primary-missing-box">
          메인 퍼스널컬러가 설정되어 있지 않습니다. 진단 결과 목록에서 메인 결과를 선택해주세요.
        </section>

        <section class="chart-section">
          <div class="section-head">
            <div>
              <h2>옵션 색상 차트</h2>
              <p>Warm-Cool 축은 coolness, Light-Deep 축은 brightness 기준으로 배치합니다.</p>
            </div>
            <strong>{{ userToneProfile.toneName }}</strong>
          </div>
          <ProductColorChart
            v-model="selectedOption"
            :product="product"
            :options="options"
            :user-tone-profile="userToneProfile"
          />
        </section>

        <section class="result-grid">
          <article class="result-list">
            <h2>내 추천 결과</h2>
            <div class="grade-columns">
              <div v-for="group in gradeGroups" :key="group.grade" class="grade-column">
                <h3>{{ group.grade }}</h3>
                <button
                  v-for="option in group.options"
                  :key="option.id"
                  type="button"
                  :class="{ active: selectedOption?.id === option.id }"
                  @click="selectedOption = option"
                >
                  <span :style="{ backgroundColor: option.hex_code || '#c65367' }"></span>
                  <strong>{{ optionLabel(option) }}</strong>
                  <em>{{ scoreLabel(option) }}</em>
                </button>
                <p v-if="!group.options.length">해당 옵션 없음</p>
              </div>
            </div>
          </article>

          <aside class="detail-panel" v-if="selectedOption">
            <div class="swatch" :style="{ backgroundColor: selectedOption.hex_code || '#c65367' }"></div>
            <p class="eyebrow">{{ optionGrade(selectedOption) }}</p>
            <h2>{{ optionLabel(selectedOption) }}</h2>
            <p>
              {{
                selectedOption.reason ||
                '선택한 옵션의 색상 분석값을 기준으로 추천 점수를 계산했습니다.'
              }}
            </p>
            <dl>
              <div v-for="metric in selectedMetrics" :key="metric.label">
                <dt>{{ metric.label }}</dt>
                <dd>{{ metric.value }}</dd>
              </div>
            </dl>
            <button type="button" @click="openProductLink">구매 링크 열기</button>
          </aside>
        </section>
      </template>
    </template>
  </main>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ProductColorChart from '@/components/products/ProductColorChart.vue'
import { getLatestDiagnosis } from '@/services/diagnosisApi'
import { getProduct } from '@/services/productApi'
import { clearDiagnosisColorProfile, readUserColorProfile, saveDiagnosisColorProfile } from '@/utils/colorRecommendationHelpers'

const route = useRoute()
const router = useRouter()

const isLoading = ref(false)
const errorState = ref('')
const product = ref(null)
const selectedOption = ref(null)
const productLink = ref('')
const userToneProfile = ref(readUserColorProfile())
const hasPrimaryDiagnosis = ref(false)

const options = computed(() => (Array.isArray(product.value?.options) ? product.value.options : []))
const hasNoOptions = computed(() => Boolean(product.value) && options.value.length === 0)
const errorMessage = computed(() => {
  if (errorState.value === 'not-found') return '상품 정보를 찾을 수 없습니다.'
  if (errorState.value === 'api-error') return '상품 정보를 불러오지 못했습니다.'
  return ''
})

const selectedOffer = computed(() => {
  return selectedOption.value?.representative_offer || selectedOption.value?.offers?.[0] || null
})
const productImage = computed(() => {
  return (
    selectedOption.value?.image_url ||
    product.value?.representative_image_url ||
    product.value?.image ||
    product.value?.image_url ||
    ''
  )
})

const gradeGroups = computed(() => {
  const order = ['BEST', 'GOOD', 'OK', 'CAUTION']
  return order.map((grade) => ({
    grade,
    options: options.value.filter((option) => optionGrade(option) === grade),
  }))
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
    tone_key: userToneProfile.value.toneTag || undefined,
    second_tone_key: userToneProfile.value.secondToneTag || undefined,
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
    hasPrimaryDiagnosis.value = false
  }
}

const loadProduct = async () => {
  const productId = route.params.id
  isLoading.value = true
  errorState.value = ''
  product.value = null
  selectedOption.value = null
  productLink.value = ''

  if (!productId) {
    errorState.value = 'not-found'
    isLoading.value = false
    return
  }

  try {
    product.value = await getProduct(productId, requestParams.value)
    selectInitialOption()
    syncProductLink()
  } catch (error) {
    product.value = null
    selectedOption.value = null
    productLink.value = ''
    errorState.value = error?.response?.status === 404 ? 'not-found' : 'api-error'

    if (errorState.value !== 'not-found') {
      console.error('상품 컬러 매칭 정보를 불러오지 못했습니다.', error)
    }
  } finally {
    isLoading.value = false
  }
}

const selectInitialOption = () => {
  const optionId = String(route.query.option || '')
  const queriedOption = options.value.find((option) => String(option.id) === optionId)
  const bestOption = options.value.find((option) => {
    return String(option.id) === String(product.value?.best_option?.id)
  })

  selectedOption.value =
    queriedOption ||
    bestOption ||
    product.value?.best_option ||
    options.value[0] ||
    null
}

const syncProductLink = () => {
  productLink.value = selectedOffer.value?.product_url || product.value?.product_url || ''
}

const optionLabel = (option) => {
  return [option?.option_no, option?.option_name].filter(Boolean).join(' ') || option?.option || '기본 옵션'
}

const optionGrade = (option) => {
  if (option?.grade) return String(option.grade).toUpperCase()
  const score = Number(option?.match_score || 0)
  if (score >= 85) return 'BEST'
  if (score >= 70) return 'GOOD'
  if (score >= 55) return 'OK'
  return 'CAUTION'
}

const scoreLabel = (option) => {
  const score = Number(option?.match_score)
  return Number.isFinite(score) ? Math.round(score) : '-'
}

const metricValue = (value) => {
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? Math.round(numberValue) : '-'
}

const openProductLink = () => {
  const url = productLink.value || selectedOffer.value?.product_url
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer')
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
.summary,
.chart-section,
.result-list,
.detail-panel {
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
}

.state-panel {
  padding: 64px 20px;
  text-align: center;
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

.summary {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) 260px;
  gap: 24px;
  padding: 24px;
  align-items: stretch;
}

.image-box {
  display: grid;
  place-items: center;
  height: 220px;
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
  width: 80px;
  height: 120px;
  border-radius: 12px;
  background: linear-gradient(160deg, #f5b7c3, #c65367);
}

.brand,
.eyebrow {
  color: #c65367;
  font-size: 13px;
  font-weight: 900;
}

.summary h1 {
  margin: 6px 0 12px;
  font-size: 30px;
  letter-spacing: 0;
}

.summary p {
  color: #5f5754;
  line-height: 1.6;
}

.link-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 110px;
  gap: 10px;
  margin-top: 24px;
}

.link-row input {
  min-width: 0;
  height: 44px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  padding: 0 14px;
}

.link-row button,
.detail-panel button {
  height: 44px;
  border: none;
  border-radius: 8px;
  background: #c65367;
  color: white;
  font-weight: 900;
  cursor: pointer;
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
.result-list h2,
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

.result-list,
.detail-panel {
  padding: 24px;
}

.grade-columns {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.grade-column h3 {
  margin: 0 0 12px;
  font-size: 15px;
}

.grade-column button {
  width: 100%;
  min-height: 54px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: white;
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  padding: 9px 10px;
  cursor: pointer;
  text-align: left;
}

.grade-column button + button {
  margin-top: 8px;
}

.grade-column button.active {
  border-color: #c65367;
  background: #fff0f1;
}

.grade-column span {
  width: 16px;
  height: 16px;
  border-radius: 50%;
}

.grade-column strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.grade-column em {
  color: #c65367;
  font-style: normal;
  font-weight: 900;
}

.grade-column p {
  margin: 0;
  color: #8e7e79;
  font-size: 13px;
}

.detail-panel {
  align-self: start;
}

.detail-panel p {
  color: #5f5754;
  line-height: 1.6;
}

.detail-panel dl {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 22px 0;
}

.detail-panel div {
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

@media (max-width: 980px) {
  .matching-page {
    padding: 24px 16px 48px;
  }

  .summary,
  .result-grid {
    grid-template-columns: 1fr;
  }

  .grade-columns {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 620px) {
  .grade-columns {
    grid-template-columns: 1fr;
  }

  .section-head {
    display: block;
  }
}
</style>
