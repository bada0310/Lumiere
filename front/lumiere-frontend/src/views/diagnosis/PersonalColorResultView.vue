<template>
  <div class="page">
    <main class="result-page">
      <section class="progress-steps" aria-label="진단 진행 단계">
        <div class="step-block">
          <span class="step-dot done" aria-hidden="true">✓</span>
          <span>사진 업로드</span>
        </div>
        <div class="step-line"></div>
        <div class="step-block">
          <span class="step-dot done" aria-hidden="true">✓</span>
          <span>AI 분석</span>
        </div>
        <div class="step-line"></div>
        <div class="step-block active">
          <span class="step-dot">3</span>
          <span>결과 확인</span>
        </div>
      </section>

      <section v-if="loading" class="state-card">진단 결과를 불러오고 있어요.</section>

      <section v-else-if="errorMessage" class="state-card">
        <strong>{{ errorMessage }}</strong>
        <button type="button" @click="loadDiagnosis">다시 불러오기</button>
      </section>

      <section v-else-if="!diagnosisResult" class="state-card">표시할 진단 결과가 없어요.</section>

      <section v-else class="result-shell">
        <div v-if="diagnosisResult.is_demo" class="result-topline">
          <span class="demo-badge">데모 진단 결과</span>
        </div>

        <section class="hero-grid">
          <article class="summary-panel">
            <div class="summary-panel-layout">
              <div class="source-profile-card">
                <img :src="primaryResultImageUrl" :alt="sourceImageUrl ? '진단에 사용한 원본 이미지' : `${resultName} 대표 이미지`" />
                <span>{{ sourceImageUrl ? '진단 원본 이미지' : '결과 대표 이미지' }}</span>
              </div>

              <div class="summary-copy">
                <p class="eyebrow">나의 퍼스널 컬러</p>
                <h1>{{ resultName }}</h1>
                <p class="eng">{{ resultEnglishName }}</p>
                <p class="summary">{{ resultSummary }}</p>

                <div class="meta-grid">
                  <div class="confidence-card">
                    <span>AI 신뢰도</span>
                    <strong>{{ confidence }}%</strong>
                  </div>
                  <div class="date-card">
                    <span>진단일</span>
                    <strong>{{ resultDate }}</strong>
                  </div>
                </div>

                <div class="tags" aria-label="스타일 키워드">
                  <span v-for="tag in keywords" :key="tag">{{ tag }}</span>
                </div>
              </div>
            </div>
          </article>

          <article class="profile-panel">
            <div class="section-title-block">
              <span>대표 이미지</span>
              <h2>결과 타입 대표 이미지</h2>
            </div>

            <div class="profile-image-frame">
              <img :src="safeProfileImageUrl" :alt="`${resultName} 대표 이미지`" @error="profileImageErrored = true" />
            </div>

            <p class="profile-caption">
              toneKey <strong>{{ diagnosisResult.personal_color_code || '-' }}</strong> 기준의 고정 대표 이미지입니다.
            </p>
          </article>
        </section>

        <section class="feature-grid">
          <article class="section-card feature-panel">
            <div class="section-head">
              <div>
                <h2>AI 분석 포인트</h2>
                <p>사진에서 읽은 톤 판단 근거입니다.</p>
              </div>
            </div>

            <div v-if="imageFeatures.length" class="feature-list">
              <div v-for="feature in imageFeatures" :key="feature.key || feature.title" class="feature-item">
                <span class="feature-icon" aria-hidden="true">{{ iconLabel(feature.icon) }}</span>
                <p>
                  <strong>{{ feature.title }}</strong>
                  <small>{{ feature.description }}</small>
                </p>
              </div>
            </div>
            <p v-else class="empty-text">이미지 특징 데이터가 아직 없어요.</p>
          </article>

          <article class="section-card color-keyword-panel">
            <div class="section-head">
              <div>
                <h2>대표 컬러 키워드</h2>
                <p>결과 타입을 설명하는 핵심 컬러입니다.</p>
              </div>
            </div>

            <div class="representative-colors">
              <div
                v-for="color in representativeColors"
                :key="color.name"
                class="color-chip color-chip--large"
                :title="`${color.name} ${color.hex}`"
                :aria-label="`${color.name} ${color.hex}`"
              >
                <span :style="{ backgroundColor: color.hex }"></span>
                <strong>{{ color.name }}</strong>
                <small>{{ color.hex }}</small>
              </div>
            </div>
          </article>
        </section>

        <section class="analysis-grid">
          <article class="section-card">
            <div class="section-head">
              <div>
                <h2>피부 톤 정량 분석</h2>
                <p>밝기, 채도, 대비를 시각화한 지표입니다.</p>
              </div>
            </div>

            <div class="metric-list">
              <div v-for="metric in skinMetricRows" :key="metric.key" class="metric-row">
                <div class="metric-copy">
                  <strong>{{ metric.name }}</strong>
                  <small>{{ metric.desc }}</small>
                </div>
                <div class="metric-track" :class="{ 'metric-track--temperature': metric.key === 'cool_warm' }">
                  <div class="metric-fill" :style="{ width: `${metric.value}%` }"></div>
                </div>
                <span class="metric-score">{{ metric.label }}</span>
              </div>
            </div>
          </article>

          <article class="section-card">
            <div class="section-head">
              <div>
                <h2>피부 특성 밸런스</h2>
                <p>주요 톤 지표를 한눈에 비교합니다.</p>
              </div>
            </div>
            <SkinBalanceChart :axes="radarRows" />
          </article>
        </section>

        <p v-if="paletteStatus === 'preparing'" class="palette-warning">
          선택된 toneKey의 상세 팔레트가 준비 중이라 기본 fallback palette를 표시합니다.
        </p>

        <section class="palette-section">
          <article v-for="group in paletteGroups" :key="group.key" class="palette-card">
            <div class="palette-card__head">
              <h2>{{ group.label }}</h2>
              <p>{{ group.description }}</p>
            </div>

            <div class="palette-swatches">
              <div
                v-for="color in paletteItems(group.key)"
                :key="`${group.key}-${color.name}`"
                class="color-chip"
                :title="color.description || `${color.name} ${color.hex}`"
                :aria-label="`${group.label} ${color.name} ${color.hex}`"
              >
                <span :style="{ backgroundColor: color.hex }"></span>
                <strong>{{ color.name }}</strong>
                <small>{{ color.hex }}</small>
              </div>
            </div>
          </article>
        </section>

        <section class="section-card makeup-section">
          <div class="section-head">
            <div>
              <h2>메이크업 컬러 가이드</h2>
              <p>제품명이 아니라 toneKey 기반 색상과 사용 위치를 정리했어요.</p>
            </div>
          </div>

          <div class="makeup-grid">
            <article class="makeup-card makeup-card--base">
              <h3>베이스</h3>
              <strong>{{ makeupGuide.base.title }}</strong>
              <p>{{ makeupGuide.base.description }}</p>

              <div v-if="makeupGuide.base.shadeRange.length" class="shade-row">
                <span v-for="shade in makeupGuide.base.shadeRange" :key="shade">{{ shade }}</span>
              </div>

              <ColorChipList :colors="makeupGuide.base.chips" label="베이스 추천 컬러" />
              <AvoidList :items="makeupGuide.base.avoid" />
            </article>

            <article class="makeup-card makeup-card--eye">
              <h3>아이 메이크업</h3>
              <p>{{ makeupGuide.eye.description }}</p>
              <div class="eye-guide-grid">
                <div v-for="group in eyeGuideGroups" :key="group.key" class="eye-guide-card">
                  <strong>{{ group.label }}</strong>
                  <small>{{ group.description }}</small>
                  <ColorChipList :colors="group.colors" :label="`아이 ${group.label} 컬러`" compact />
                </div>
              </div>
              <AvoidList :items="makeupGuide.eye.avoid" />
            </article>

            <article class="makeup-card">
              <h3>립</h3>
              <strong>{{ makeupGuide.lip.title }}</strong>
              <p>{{ makeupGuide.lip.description }}</p>
              <ColorChipList :colors="makeupGuide.lip.chips" label="립 추천 컬러" />
              <AvoidList :items="makeupGuide.lip.avoid" />
            </article>

            <article class="makeup-card">
              <h3>블러셔</h3>
              <strong>{{ makeupGuide.blush.title }}</strong>
              <p>{{ makeupGuide.blush.description }}</p>
              <ColorChipList :colors="makeupGuide.blush.chips" label="블러셔 추천 컬러" />
              <AvoidList :items="makeupGuide.blush.avoid" />
            </article>
          </div>
        </section>

        <section ref="makeoverRef" class="section-card makeover-section">
          <div class="section-head">
            <div>
              <h2>예상 메이크업 이미지</h2>
              <p>내 퍼스널 컬러에 어울리는 다양한 메이크업 스타일을 확인해보세요.</p>
            </div>
          </div>
          <div v-if="showMakeoverLoadingNotice" class="makeover-status-banner">
            <span class="makeover-status-spinner" aria-hidden="true"></span>

            <div>
              <strong>AI 예상 메이크업 이미지를 생성하고 있어요</strong>
              <p>
                이미지 생성은 시간이 조금 걸릴 수 있어요.
                완성된 스타일은 자동으로 표시됩니다.
                <b>{{ makeoverProgressText }}</b>
              </p>
            </div>
          </div>

          <AIMakeoverGallery
            :styles="makeoverStyles"
            :status="makeoverStatus"
            :selected-key="selectedLookKey"
            :makeup-guide="makeupGuide"
            :tone-key="diagnosisResult.personal_color_code"
            :loading="makeoverLoading"
            :error="makeoverError"
            @start="startMakeovers"
            @retry="retryMakeover"
            @select="selectedLookKey = $event"
          />
        </section>

        <section class="lower-grid">
          <article class="section-card style-section">
            <div class="section-head">
              <div>
                <h2>추가 스타일 가이드</h2>
                <p>렌즈, 헤어, 악세서리, 의상 컬러 방향입니다.</p>
              </div>
            </div>

            <div class="style-grid">
              <StyleGuideCard icon="◉" title="렌즈" :colors="styleGuide.lens" />
              <StyleGuideCard icon="⌁" title="헤어" :colors="styleGuide.hair" />
              <StyleGuideCard icon="✦" title="악세서리" :items="styleGuide.accessory" />
              <StyleGuideCard icon="▣" title="의상" :description="styleGuide.outfit.description" :colors="outfitColors" />
            </div>

            <div v-if="stylingKeywords.length || productToneRangeText" class="fixed-palette-meta">
              <div v-if="stylingKeywords.length">
                <h3>커뮤니티 스타일 키워드</h3>
                <div class="keyword-row">
                  <button
                    v-for="keyword in stylingKeywords"
                    :key="keyword"
                    type="button"
                    @click="openCommunityTag(keyword)"
                  >
                    #{{ normalizeHashKeyword(keyword) }}
                  </button>
                </div>
              </div>

              <div v-if="productToneRangeItems.length" class="tone-range-box">
                <h3>추천 제품 색상 범위</h3>
                <div class="tone-range-grid">
                  <div v-for="item in productToneRangeItems" :key="item.label">
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }}</strong>
                  </div>
                </div>
              </div>
            </div>
          </article>

          <article class="section-card tip-section">
            <h2>컬러 선택 팁</h2>
            <div class="tip-chip-row" aria-label="추천 컬러칩">
              <span
                v-for="color in colorTipChips"
                :key="`${color.name}-${color.hex}`"
                :style="{ backgroundColor: color.hex }"
                :title="`${color.name} ${color.hex}`"
              ></span>
            </div>
            <div class="tip-list">
              <div v-for="tip in colorTipItems" :key="tip.title" class="tip-item">
                <strong>{{ tip.title }}</strong>
                <p>{{ tip.description }}</p>
              </div>
            </div>
          </article>
        </section>

        <section class="cta-grid">
          <button type="button" class="cta-btn cta-btn--primary" @click="goToProducts">
            맞춤 화장품 추천 보기
            <span>제품 추천은 별도 페이지에서 확인해요.</span>
          </button>
          <button type="button" class="cta-btn" @click="scrollToMakeover">
            AI 메이크오버 보기
            <span>스타일 이미지 영역으로 이동합니다.</span>
          </button>
          <button type="button" class="cta-btn" :class="{ saved: isSaved }" :disabled="savingResult" @click="saveResult">
            {{ savingResult ? '저장 중...' : isSaved ? '결과 저장 완료' : '결과 저장하기' }}
            <span>저장하면 마이페이지에서 다시 볼 수 있어요.</span>
          </button>
        </section>

        <p v-if="saveFeedback" class="save-feedback">{{ saveFeedback }}</p>
        <p v-if="diagnosisResult.is_mock" class="save-notice">
          개발 환경의 mock 결과는 localStorage에 저장됩니다.
        </p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AIMakeoverGallery from '@/components/diagnosis/AIMakeoverGallery.vue'
import ColorChipList from '@/components/diagnosis/ColorChipList.vue'
import SkinBalanceChart from '@/components/diagnosis/SkinBalanceChart.vue'
import StyleGuideCard from '@/components/diagnosis/StyleGuideCard.vue'
import { FALLBACK_TONE_IMAGE } from '@/data/toneImages'
import {
  DEFAULT_MOCK_TONE_KEY,
  getMockPersonalColorResult,
  isMockPersonalColorResultKey,
} from '@/data/mockPersonalColorResults'
import {
  getDemoDiagnosis,
  getDiagnosisResult,
  getLatestDiagnosis,
  getMakeoverStatus,
  retryMakeoverStyle,
  setPrimaryDiagnosis,
  startMakeoverGeneration,
} from '@/services/diagnosisApi'
import { useRequireLogin } from '@/composables/useRequireLogin'
import { getDiagnosisProfileImageUrl, normalizeDiagnosisResult } from '@/utils/diagnosisResultTransform'
import { getSavedMockDiagnosisResult, saveMockDiagnosisResult } from '@/utils/diagnosisMockStorage'
import { saveDiagnosisColorProfile } from '@/utils/colorRecommendationHelpers'

const AvoidList = defineComponent({
  name: 'AvoidList',
  props: {
    items: {
      type: Array,
      default: () => [],
    },
  },
  setup(props) {
    return () =>
      props.items.length
        ? h('div', { class: 'avoid-list' }, [
            h('strong', '피하면 좋은 방향'),
            h(
              'ul',
              props.items.map((item) => h('li', { key: String(item) }, typeof item === 'string' ? item : item.name || item.description)),
            ),
          ])
        : null
  },
})

const route = useRoute()
const router = useRouter()
const { requireLogin } = useRequireLogin()

const diagnosisResult = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const selectedLookKey = ref('')
const isSaved = ref(false)
const savingResult = ref(false)
const saveFeedback = ref('')
const makeoverRef = ref(null)
const profileImageErrored = ref(false)
const makeoverState = ref({ status: 'none', styles: [], error: '' })
const makeoverLoading = ref(false)
let makeoverPollTimer = null

const isDev = import.meta.env.DEV
const defaultTip = '색상은 제품명보다 실제 발색, 채도, 명도, 온도감이 더 중요해요.'

const selectedMockQuery = computed(() => {
  const queryValue = route.query.mock
  return Array.isArray(queryValue) ? queryValue[0] || '' : queryValue || ''
})

const clampPercent = (value) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.min(100, Math.max(0, Math.round(number)))
}

const asArray = (value) => (Array.isArray(value) ? value : [])

const formatDate = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toISOString().slice(0, 10).replaceAll('-', '.')
}

const diagnosisId = computed(() => route.params.diagnosisId || route.params.id || diagnosisResult.value?.id || '')
const canUseMakeoverApi = computed(() => Boolean(diagnosisId.value && !diagnosisResult.value?.is_mock && !diagnosisResult.value?.is_demo))
const confidence = computed(() => clampPercent(diagnosisResult.value?.confidence ?? diagnosisResult.value?.confidence_score))
const resultName = computed(() => diagnosisResult.value?.korean_name || diagnosisResult.value?.personal_color?.korean_name || '퍼스널 컬러')
const resultEnglishName = computed(() => diagnosisResult.value?.english_name || diagnosisResult.value?.personal_color?.english_name || '')
const resultSummary = computed(() => diagnosisResult.value?.summary || '진단 결과에 맞춘 컬러와 스타일 가이드를 확인해보세요.')
const resultDate = computed(() => formatDate(diagnosisResult.value?.diagnosed_at || diagnosisResult.value?.created_at))
const keywords = computed(() => asArray(diagnosisResult.value?.keywords))
const imageFeatures = computed(() => asArray(diagnosisResult.value?.image_features))
const representativeColors = computed(() => asArray(diagnosisResult.value?.representative_colors))
const makeupGuide = computed(() => diagnosisResult.value?.makeup_color_guide || normalizeDiagnosisResult({})?.makeup_color_guide)
const styleGuide = computed(() => diagnosisResult.value?.style_guide || { lens: [], hair: [], accessory: [], outfit: { colors: [] } })
const outfitColors = computed(() => asArray(styleGuide.value?.outfit?.colors?.length ? styleGuide.value.outfit.colors : styleGuide.value?.fashion))
const paletteStatus = computed(() => diagnosisResult.value?.palette_status || '')
const stylingKeywords = computed(() => asArray(diagnosisResult.value?.styling_keywords || styleGuide.value?.styling_keywords))
const makeoverStyles = computed(() => asArray(makeoverState.value.styles?.length ? makeoverState.value.styles : diagnosisResult.value?.ai_makeover?.styles))
const makeoverStatus = computed(() => makeoverState.value.status || diagnosisResult.value?.ai_makeover?.status || 'none')
const makeoverError = computed(() => makeoverState.value.error || '')
const sourceImageUrl = computed(() => diagnosisResult.value?.processed_image_url || diagnosisResult.value?.uploaded_image_url || '')
const safeProfileImageUrl = computed(() =>
  profileImageErrored.value ? FALLBACK_TONE_IMAGE : getDiagnosisProfileImageUrl(diagnosisResult.value) || FALLBACK_TONE_IMAGE,
)
const primaryResultImageUrl = computed(() => sourceImageUrl.value || safeProfileImageUrl.value || FALLBACK_TONE_IMAGE)

const productToneRangeItems = computed(() => {
  const range = diagnosisResult.value?.recommended_product_tone_range || {}
  return [
    { label: '온도감', value: range.temperature },
    { label: '명도', value: asArray(range.brightness).join(', ') },
    { label: '채도', value: asArray(range.chroma).join(', ') },
    { label: '추천 색상', value: asArray(range.hue).join(', ') },
  ].filter((item) => item.value)
})
const productToneRangeText = computed(() => productToneRangeItems.value.map((item) => `${item.label} ${item.value}`).join(' / '))

const normalizeHashKeyword = (keyword) => String(keyword || '').replace(/^#/, '').replace(/\s+/g, '')
const colorTipChips = computed(() => {
  const chips = [
    ...representativeColors.value,
    ...paletteItems('best'),
    ...paletteItems('neutral'),
  ]
  const seen = new Set()
  return chips
    .filter((color) => color?.hex)
    .filter((color) => {
      const key = `${color.name}-${color.hex}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    .slice(0, 7)
})

const colorTipItems = computed(() => {
  const range = diagnosisResult.value?.recommended_product_tone_range || {}
  const chroma = asArray(range.chroma).join(', ') || '피부 톤과 비슷한 채도'
  const hue = asArray(range.hue).join(', ') || '추천 팔레트 안의 색상'
  const baseTip = diagnosisResult.value?.tip || defaultTip
  return [
    {
      title: '컬러 방향',
      description: `${hue} 계열을 얼굴 가까이에 두면 진단된 장점이 더 잘 보여요. 채도가 너무 높거나 노란기가 강한 컬러는 얼굴이 칙칙해보일 수 있어요.`,
    },
    {
      title: '채도와 명도',
      description: `${chroma} 범위처럼 너무 튀기보다 피부 밝기와 자연스럽게 이어지는 색을 고르면 안정적이에요.`,
    },
    {
      title: '텍스처',
      description: '립과 블러셔는 얇게 올라가는 쉬어/벨벳/새틴 질감이 좋아요. 과한 펄감이나 두껍게 덮이는 제형은 소량으로 테스트해보세요.',
    },
    {
      title: '한 줄 팁',
      description: baseTip,
    },
  ]
})

const getMakeoverImageUrl = (style) => style?.image_url || style?.imageUrl || style?.image || ''

const normalizeStatus = (status) => String(status || '').toLowerCase()

const hasMakeoverImage = (style) => Boolean(getMakeoverImageUrl(style))

const isMakeoverStyleComplete = (style) => {
  if (hasMakeoverImage(style)) return true
  return ['complete', 'completed', 'done', 'success'].includes(normalizeStatus(style?.status))
}

const isMakeoverStyleWaiting = (style) => {
  if (hasMakeoverImage(style)) return false
  return ['queued', 'running', 'pending', 'loading'].includes(normalizeStatus(style?.status))
}

const isMakeoverStyleFailed = (style) => {
  if (hasMakeoverImage(style)) return false
  return normalizeStatus(style?.status) === 'failed'
}

const normalizeMakeoverStyle = (style = {}, index = 0) => {
  const key = style.style_key || style.key || `style-${index}`
  const imageUrl = getMakeoverImageUrl(style)

  return {
    ...style,
    key,
    style_key: key,
    name: style.title || style.name || `스타일 ${index + 1}`,
    title: style.title || style.name || `스타일 ${index + 1}`,
    description: style.description || '',
    points: asArray(style.points),
    disclaimer: style.disclaimer || '',
    image_url: imageUrl,
    status: imageUrl ? 'complete' : style.status || 'none',
    error_message: style.error_message || style.error || '',
    order: style.order ?? index + 1,
    is_default: Boolean(style.is_default || index === 0),
  }
}

const deriveMakeoverStatus = (rawStatus, styles = []) => {
  if (!styles.length) return normalizeStatus(rawStatus) || 'none'
  if (styles.some(isMakeoverStyleWaiting)) return 'running'
  if (styles.every(isMakeoverStyleComplete)) return 'complete'
  if (styles.some(isMakeoverStyleComplete) && styles.some(isMakeoverStyleFailed)) return 'partial'
  if (styles.every(isMakeoverStyleFailed)) return 'failed'
  return normalizeStatus(rawStatus) || 'none'
}

const completedMakeoverCount = computed(() =>
  makeoverStyles.value.filter((style) => isMakeoverStyleComplete(style)).length
)

const totalMakeoverCount = computed(() => Math.max(makeoverStyles.value.length || 3, 3))

const isMakeoverActive = computed(() => {
  const styles = makeoverStyles.value || []

  if (styles.length > 0) {
    return styles.some((style) => isMakeoverStyleWaiting(style))
  }

  return ['queued', 'running', 'pending', 'loading'].includes(normalizeStatus(makeoverStatus.value))
})

const showMakeoverLoadingNotice = computed(() => {
  if (!canUseMakeoverApi.value) return false
  if (!isMakeoverActive.value && !makeoverLoading.value) return false
  return completedMakeoverCount.value < totalMakeoverCount.value
})

const makeoverProgressText = computed(() => {
  return `${completedMakeoverCount.value}/${totalMakeoverCount.value}개 완료`
})

const skinMetricLabels = [
  { key: 'brightness', name: '명도', desc: '피부가 밝게 보이는 정도' },
  { key: 'saturation', name: '채도', desc: '얼굴에 어울리는 색의 선명도' },
  { key: 'clarity', name: '맑기', desc: '탁기 없이 깨끗하게 보이는 정도' },
  { key: 'contrast', name: '대비', desc: '이목구비와 색의 또렷함' },
  { key: 'cool_warm', name: '온도감', desc: '쿨톤과 웜톤의 기울기' },
  { key: 'softness', name: '부드러움', desc: '부드러운 컬러가 어울리는 정도' },
]

const radarLabels = [
  { key: 'brightness', label: '명도' },
  { key: 'saturation', label: '채도' },
  { key: 'clarity', label: '맑기' },
  { key: 'contrast', label: '대비' },
  { key: 'softness', label: '부드러움' },
  { key: 'coolness', label: '쿨감' },
]

const paletteGroups = [
  { key: 'best', label: 'BEST', description: '가장 안정적으로 어울리는 컬러' },
  { key: 'neutral', label: 'NEUTRAL', description: '베이스와 데일리로 쓰기 좋은 컬러' },
  { key: 'accent', label: 'ACCENT', description: '포인트로 생기를 더하는 컬러' },
  { key: 'try', label: 'TRY', description: '조심스럽게 시도해볼 만한 컬러' },
  { key: 'worst', label: 'WORST', description: '얼굴색을 흐리게 만들 수 있는 컬러' },
]

const eyeGuideGroups = computed(() => [
  {
    key: 'highlighter',
    label: '하이라이터',
    description: '눈두덩과 눈 앞머리에 밝게 올리는 컬러',
    colors: makeupGuide.value.eye.highlighter,
  },
  {
    key: 'base',
    label: '베이스',
    description: '눈두덩 전체를 깔끔하게 정리하는 컬러',
    colors: makeupGuide.value.eye.base,
  },
  {
    key: 'shading',
    label: '음영',
    description: '깊고 선명한 눈매를 만드는 컬러',
    colors: makeupGuide.value.eye.shading,
  },
  {
    key: 'point',
    label: '포인트',
    description: '눈꼬리와 삼각존에 더하는 포인트 컬러',
    colors: makeupGuide.value.eye.point,
  },
  {
    key: 'aegyosal',
    label: '애굣살',
    description: '밝고 자연스럽게 볼륨을 주는 컬러',
    colors: makeupGuide.value.eye.aegyosal,
  },
  {
    key: 'eyeliner',
    label: '아이라이너',
    description: '점막과 라인을 또렷하게 잡는 컬러',
    colors: makeupGuide.value.eye.eyeliner,
  },
])

const formatMetricLabel = (metric) => {
  if (metric.key !== 'cool_warm') return String(metric.value)
  const intensity = Math.round(Math.abs(metric.value - 50) * 2)
  if (intensity === 0) return '중립'
  return metric.value < 50 ? `쿨 ${intensity}` : `웜 ${intensity}`
}

const skinMetricRows = computed(() => {
  const metrics = diagnosisResult.value?.skin_metrics || {}
  return skinMetricLabels.map((metric) => {
    const value = clampPercent(metrics[metric.key])
    return {
      ...metric,
      value,
      label: formatMetricLabel({ ...metric, value }),
    }
  })
})

const radarRows = computed(() => {
  const chart = diagnosisResult.value?.radar_chart || {}
  return radarLabels.map((axis) => ({
    ...axis,
    value: clampPercent(chart[axis.key]),
  }))
})

const paletteItems = (key) => asArray(diagnosisResult.value?.color_palettes?.[key])

const iconLabel = (icon) =>
  ({
    sparkle: '✦',
    cloud: '○',
    diamond: '◇',
    flower: '✽',
    sun: '☼',
    leaf: '⌁',
    circle: '◌',
  })[icon] || '✦'

const normalizeMakeoverPayload = (payload = {}) => {
  const styles = asArray(payload?.makeup_images || payload?.styles || payload?.makeover_styles).map(normalizeMakeoverStyle)
  const status = deriveMakeoverStatus(payload?.status || payload?.makeup_generation_status, styles)

  return {
    status,
    error: payload?.error || payload?.makeup_generation_error || payload?.detail || '',
    styles,
  }
}

const applyDiagnosisResult = (raw) => {
  const normalized = normalizeDiagnosisResult(raw)
  const initialMakeover = normalizeMakeoverPayload({
    status:
      raw?.makeup_generation_status ||
      raw?.makeover?.status ||
      raw?.ai_makeover?.status ||
      normalized?.ai_makeover?.status,
    error:
      raw?.makeup_generation_error ||
      raw?.makeover?.error ||
      raw?.ai_makeover?.error ||
      normalized?.ai_makeover?.error,
    makeup_images:
      raw?.makeup_images ||
      raw?.makeover_styles ||
      raw?.makeover?.makeup_images ||
      raw?.makeover?.styles ||
      raw?.ai_makeover?.makeup_images ||
      raw?.ai_makeover?.styles ||
      normalized?.makeup_images ||
      normalized?.makeover_styles ||
      normalized?.ai_makeover?.styles ||
      [],
  })

  diagnosisResult.value = normalized
  makeoverState.value = initialMakeover
  selectedLookKey.value =
    initialMakeover.styles.find((look) => look.is_default)?.key ||
    initialMakeover.styles[0]?.key ||
    ''
  profileImageErrored.value = false
  isSaved.value = Boolean(normalized?.is_primary || (normalized?.is_mock && getSavedMockDiagnosisResult()?.id === normalized.id))
  saveFeedback.value = ''
  saveDiagnosisColorProfile(normalized)
}

const loadMockDiagnosis = (toneKey = DEFAULT_MOCK_TONE_KEY) => {
  if (!isMockPersonalColorResultKey(toneKey)) {
    diagnosisResult.value = null
    selectedLookKey.value = ''
    errorMessage.value = `지원하지 않는 mock 타입입니다: ${toneKey}`
    return
  }
  applyDiagnosisResult({
    ...getMockPersonalColorResult(toneKey),
    is_mock: true,
  })
}

const loadMakeovers = async ({ silent = false } = {}) => {
  if (!canUseMakeoverApi.value) return
  if (!silent) makeoverLoading.value = true

  try {
    const data = await getMakeoverStatus(diagnosisId.value)
    makeoverState.value = normalizeMakeoverPayload(data)
    if (!selectedLookKey.value && makeoverState.value.styles.length) {
      selectedLookKey.value = makeoverState.value.styles[0].key
    }
    scheduleMakeoverPolling()
  } catch (error) {
    if (!silent) {
      makeoverState.value = {
        ...makeoverState.value,
        error: error?.response?.data?.detail || 'AI 메이크오버 상태를 불러오지 못했어요.',
      }
    }
    stopMakeoverPolling()
  } finally {
    if (!silent) makeoverLoading.value = false
  }
}

const startMakeovers = async () => {
  if (!canUseMakeoverApi.value || makeoverLoading.value) return
  makeoverLoading.value = true

  try {
    const data = await startMakeoverGeneration(diagnosisId.value)
    makeoverState.value = normalizeMakeoverPayload(data)
    if (!selectedLookKey.value && makeoverState.value.styles.length) {
      selectedLookKey.value = makeoverState.value.styles[0].key
    }
    scheduleMakeoverPolling()
  } catch (error) {
    makeoverState.value = {
      ...makeoverState.value,
      error: error?.response?.data?.detail || 'AI 메이크오버 생성을 시작하지 못했어요.',
    }
  } finally {
    makeoverLoading.value = false
  }
}

const startMakeoversIfNeeded = async () => {
  if (!canUseMakeoverApi.value) return
  if (!['none', 'skipped'].includes(makeoverStatus.value)) {
    scheduleMakeoverPolling()
    return
  }
  await startMakeovers()
}

const retryMakeover = async (styleKey) => {
  if (!canUseMakeoverApi.value || !styleKey) return
  makeoverLoading.value = true

  try {
    const data = await retryMakeoverStyle(diagnosisId.value, styleKey)
    makeoverState.value = normalizeMakeoverPayload(data)
    scheduleMakeoverPolling()
  } catch (error) {
    makeoverState.value = {
      ...makeoverState.value,
      error: error?.response?.data?.detail || 'AI 메이크오버 재생성을 시작하지 못했어요.',
    }
  } finally {
    makeoverLoading.value = false
  }
}

const loadDiagnosis = async ({ silent = false } = {}) => {
  if (!silent) loading.value = true
  errorMessage.value = ''

  try {
    if (isDev && selectedMockQuery.value) {
      loadMockDiagnosis(selectedMockQuery.value)
      return
    }

    const id = route.params.diagnosisId || route.params.id
    const data =
      route.name === 'diagnosis-result-demo' || id === 'demo'
        ? await getDemoDiagnosis()
        : id
          ? await getDiagnosisResult(id)
          : await getLatestDiagnosis()

    if (!data) {
      if (isDev) {
        const savedMock = getSavedMockDiagnosisResult()
        applyDiagnosisResult(savedMock || { ...getMockPersonalColorResult(), is_mock: true })
        return
      }
      diagnosisResult.value = null
      return
    }

    applyDiagnosisResult(data)
    await loadMakeovers({ silent: true })
  } catch (error) {
    console.error('진단 결과 조회 실패:', error)

    if (silent) {
      stopMakeoverPolling()
      return
    }

    if (isDev) {
      const savedMock = getSavedMockDiagnosisResult()
      applyDiagnosisResult(savedMock || { ...getMockPersonalColorResult(), is_mock: true })
      return
    }

    errorMessage.value = '진단 결과를 불러오지 못했어요.'
  } finally {
    if (!silent) loading.value = false
  }
}

const stopMakeoverPolling = () => {
  if (!makeoverPollTimer) return
  window.clearInterval(makeoverPollTimer)
  makeoverPollTimer = null
}
const scheduleMakeoverPolling = () => {
  stopMakeoverPolling()
  if (!isMakeoverActive.value || diagnosisResult.value?.is_mock || diagnosisResult.value?.is_demo) return

  makeoverPollTimer = window.setInterval(() => {
    if (!isMakeoverActive.value) {
      stopMakeoverPolling()
      return
    }
    loadMakeovers({ silent: true })
  }, 4000)
}

const goToProducts = () => {
  const profile = saveDiagnosisColorProfile(diagnosisResult.value)
  router.push({
    path: '/products',
    query: {
      source: 'diagnosis',
      tone_key: profile.toneTag,
      diagnosis_id: diagnosisResult.value?.id || undefined,
    },
  })
}

const openCommunityTag = (keyword) => {
  const tag = normalizeHashKeyword(keyword)
  if (!tag) return

  router.push({
    name: 'community',
    query: {
      category: 'popular-product-tags',
      tag,
    },
  })
}

const scrollToMakeover = () => {
  makeoverRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const saveResult = async () => {
  if (
    !requireLogin({
      message: '진단 결과 저장은 로그인 후 이용할 수 있어요.',
      redirect: route.fullPath,
    })
  ) {
    return
  }

  if (!diagnosisResult.value || savingResult.value) return

  savingResult.value = true
  saveFeedback.value = ''

  try {
    saveDiagnosisColorProfile(diagnosisResult.value)

    if (diagnosisResult.value?.is_mock) {
      saveMockDiagnosisResult(diagnosisResult.value)
    } else if (diagnosisId.value) {
      const updated = await setPrimaryDiagnosis(diagnosisId.value)
      if (updated) {
        applyDiagnosisResult(updated)
      } else {
        diagnosisResult.value = {
          ...diagnosisResult.value,
          is_primary: true,
        }
      }
    }

    isSaved.value = true
    saveFeedback.value = '현재 진단 결과가 이 페이지에서 바로 저장되었어요. 마이페이지와 추천 기준에 반영됩니다.'
  } catch (error) {
    console.error('진단 결과 저장 실패:', error)
    saveFeedback.value = '저장 중 문제가 발생했어요. 잠시 후 다시 시도해주세요.'
  } finally {
    savingResult.value = false
  }
}

watch(
  () => route.fullPath,
  () => loadDiagnosis(),
)
onMounted(loadDiagnosis)
onUnmounted(stopMakeoverPolling)
</script>

<style scoped>
.page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(246, 226, 219, 0.72), transparent 34rem),
    linear-gradient(180deg, #fffaf7 0%, #fdf8f6 100%);
  color: #2d2524;
}

.result-page {
  padding: 30px 56px 56px;
}

.progress-steps {
  max-width: 760px;
  margin: 0 auto 22px;
  display: grid;
  grid-template-columns: auto 1fr auto 1fr auto;
  align-items: center;
  gap: 12px;
  color: #c65367;
  font-size: 13px;
  font-weight: 800;
}

.step-block {
  display: grid;
  justify-items: center;
  gap: 7px;
}

.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #c65367;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 14px rgba(198, 83, 103, 0.22);
  font-size: 12px;
}

.step-line {
  height: 1px;
  background: #d98c99;
}

.state-card,
.result-shell {
  max-width: 1360px;
  margin: 0 auto;
}

.state-card {
  padding: 42px;
  border: 1px solid #eaded8;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.88);
  text-align: center;
}

.state-card button {
  margin-top: 14px;
  border: 1px solid #c65367;
  color: #c65367;
  background: white;
  border-radius: 8px;
  padding: 8px 16px;
  cursor: pointer;
}

.result-shell {
  padding: 28px 38px 26px;
  border: 1px solid #eaded8;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 22px 60px rgba(88, 55, 45, 0.06);
}

.result-topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.demo-badge,
.mock-switcher {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #fff0f1;
  color: #b64b5e;
  font-size: 12px;
  font-weight: 800;
}

.mock-switcher {
  background: #f4f0fa;
  color: #5f5379;
}

.mock-switcher select {
  border: 1px solid #ded3ea;
  border-radius: 999px;
  background: white;
  color: #4b425d;
  padding: 4px 10px;
  font: inherit;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(300px, 0.75fr);
  gap: 28px;
  align-items: stretch;
}

.summary-panel,
.profile-panel,
.section-card,
.palette-card {
  border: 1px solid #eaded8;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.88);
}

.summary-panel {
  padding: 34px;
}

.summary-panel-layout {
  display: grid;
  grid-template-columns: minmax(220px, 0.42fr) minmax(0, 1fr);
  gap: 30px;
  align-items: center;
}

.source-profile-card {
  min-width: 0;
  display: grid;
  gap: 12px;
  justify-items: center;
}

.source-profile-card img {
  width: min(100%, 280px);
  aspect-ratio: 4 / 5;
  border-radius: 24px;
  object-fit: cover;
  display: block;
  background: #f8eeee;
  box-shadow:
    0 20px 38px rgba(95, 58, 52, 0.16),
    0 0 0 8px #fffaf7;
}

.source-profile-card span {
  padding: 7px 12px;
  border-radius: 999px;
  background: #fff0f1;
  color: #9e4655;
  font-size: 12px;
  font-weight: 900;
}

.summary-copy {
  min-width: 0;
}

.eyebrow,
.section-title-block span {
  color: #7c6964;
  font-size: 14px;
  font-weight: 800;
}

.summary-panel h1 {
  margin: 16px 0 4px;
  font-size: clamp(38px, 4.2vw, 58px);
  line-height: 1.1;
  color: #211c1b;
  letter-spacing: 0;
}

.eng {
  margin: 0;
  color: #645856;
  font-size: 19px;
}

.summary {
  max-width: 760px;
  margin: 32px 0 0;
  color: #c65367;
  font-size: clamp(20px, 2.2vw, 29px);
  font-weight: 800;
  line-height: 1.65;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 180px));
  gap: 12px;
  margin-top: 28px;
}

.confidence-card,
.date-card {
  padding: 15px 16px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fffaf7;
  display: grid;
  gap: 5px;
}

.confidence-card span,
.date-card span {
  color: #8e7e79;
  font-size: 12px;
}

.confidence-card strong {
  color: #c65367;
  font-size: 30px;
}

.date-card strong {
  font-size: 17px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 30px;
}

.tags span {
  padding: 9px 15px;
  border-radius: 999px;
  background: #fff0f1;
  color: #9e4655;
  font-size: 13px;
  font-weight: 800;
}

.profile-panel {
  padding: 24px;
  display: grid;
  align-content: start;
  gap: 14px;
}

.section-title-block h2,
.section-card h2,
.palette-card h2 {
  margin: 4px 0 0;
  color: #2d2524;
  font-size: 20px;
}

.profile-image-frame {
  width: min(100%, 320px);
  aspect-ratio: 1 / 1;
  justify-self: center;
  border-radius: 50%;
  overflow: hidden;
  background: #f8eeee;
  box-shadow:
    inset 0 0 0 1px rgba(198, 83, 103, 0.1),
    0 18px 34px rgba(92, 55, 52, 0.1);
}

.profile-image-frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.profile-caption {
  margin: 0;
  color: #756965;
  font-size: 12px;
  line-height: 1.55;
  text-align: center;
}

.feature-grid,
.analysis-grid,
.lower-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 22px;
}

.section-card {
  padding: 24px 26px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
}

.section-head p {
  margin: 5px 0 0;
  color: #8b7d78;
  font-size: 13px;
}

.feature-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 20px;
}

.feature-item {
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: 13px;
  align-items: start;
  padding: 14px;
  border-radius: 10px;
  background: #fffaf7;
}

.feature-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f6e5ec;
  color: #9d4b61;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 900;
}

.feature-item p {
  margin: 0;
  display: grid;
  gap: 4px;
}

.feature-item small {
  color: #6d625f;
  line-height: 1.45;
}

.representative-colors,
.palette-swatches {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(128px, 1fr));
  gap: 12px;
  margin-top: 20px;
}

.color-chip {
  min-width: 0;
  padding: 12px;
  border: 1px solid #eee3df;
  border-radius: 10px;
  background: #fff;
  display: grid;
  gap: 7px;
}

.color-chip span {
  width: 100%;
  height: 42px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.color-chip strong,
.color-chip small {
  min-width: 0;
  overflow-wrap: anywhere;
}

.color-chip strong {
  font-size: 13px;
}

.color-chip small {
  color: #867874;
  font-size: 11px;
}

.color-chip--large span {
  height: 54px;
  border-radius: 999px;
}

.metric-list {
  display: grid;
  gap: 18px;
  margin-top: 24px;
}

.metric-row {
  display: grid;
  grid-template-columns: 128px 1fr 58px;
  align-items: center;
  gap: 16px;
}

.metric-copy {
  display: grid;
  gap: 2px;
}

.metric-copy strong {
  font-size: 14px;
}

.metric-copy small {
  color: #8e7e79;
  font-size: 11px;
}

.metric-track {
  height: 7px;
  border-radius: 999px;
  background: #eee2df;
  overflow: hidden;
}

.metric-track--temperature {
  background: linear-gradient(90deg, #d9e9f6 0%, #f2e8ec 50%, #f6ded7 100%);
}

.metric-fill {
  height: 100%;
  border-radius: 999px;
  background: #c65367;
}

.metric-track--temperature .metric-fill {
  background: linear-gradient(90deg, #6f9ec6 0%, #d7bacd 56%, #c65367 100%);
}

.metric-score {
  text-align: right;
  color: #4b403d;
  font-size: 13px;
  font-weight: 800;
}

.palette-section {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 16px;
}

.palette-warning {
  max-width: 1360px;
  margin: 22px 0 0;
  padding: 12px 14px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: #fffaf7;
  color: #8b3a4a;
  font-size: 13px;
  font-weight: 800;
}

.palette-card {
  padding: 20px;
}

.palette-card__head p {
  margin: 4px 0 0;
  color: #8e7e79;
  font-size: 12px;
}

.makeup-section,
.makeover-section {
  margin-top: 22px;
}

.makeup-grid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.makeup-card {
  min-width: 0;
  padding: 18px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fff;
}

.makeup-card h3 {
  margin: 0 0 10px;
  color: #9e4655;
  font-size: 15px;
}

.makeup-card > strong {
  display: block;
  margin-bottom: 7px;
}

.makeup-card p {
  margin: 0 0 14px;
  color: #6d625f;
  font-size: 13px;
  line-height: 1.55;
}

.makeup-card--eye {
  grid-column: span 2;
}

.shade-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.shade-row span {
  min-width: 42px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f7eeee;
  color: #8b3a4a;
  text-align: center;
  font-size: 12px;
  font-weight: 800;
}

.avoid-list {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #f0e5e1;
}

.avoid-list strong {
  color: #7d706c;
  font-size: 12px;
}

.avoid-list ul {
  margin: 8px 0 0;
  padding-left: 18px;
  color: #6d625f;
  font-size: 12px;
  line-height: 1.65;
}

.eye-guide-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.eye-guide-card {
  padding: 14px;
  border-radius: 10px;
  background: #fffaf7;
}

.eye-guide-card > strong,
.eye-guide-card > small {
  display: block;
}

.eye-guide-card > small {
  min-height: 34px;
  margin: 4px 0 12px;
  color: #7d706c;
  font-size: 12px;
  line-height: 1.45;
}

.style-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 12px;
}

.fixed-palette-meta {
  margin-top: 18px;
  padding: 18px;
  border: 1px solid #eaded8;
  border-radius: 12px;
  background:
    linear-gradient(135deg, rgba(255, 250, 247, 0.98), rgba(255, 240, 241, 0.72));
  display: grid;
  gap: 18px;
}

.fixed-palette-meta h3 {
  margin: 0 0 8px;
  color: #9e4655;
  font-size: 15px;
}

.fixed-palette-meta p {
  margin: 0;
  color: #655a56;
  font-size: 13px;
  line-height: 1.6;
}

.keyword-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-row button {
  border: 1px solid #e9c1c8;
  padding: 7px 10px;
  border-radius: 999px;
  background: #fff0f1;
  color: #8b3a4a;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

.keyword-row button:hover {
  background: #c65367;
  border-color: #c65367;
  color: #fff;
}

.tone-range-box {
  padding-top: 2px;
}

.tone-range-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.tone-range-grid div {
  min-width: 0;
  padding: 12px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.78);
}

.tone-range-grid span,
.tone-range-grid strong {
  display: block;
}

.tone-range-grid span {
  color: #9e4655;
  font-size: 11px;
  font-weight: 900;
}

.tone-range-grid strong {
  margin-top: 5px;
  color: #403633;
  font-size: 13px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.tip-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.tip-chip-row span {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 0 0 1px rgba(90, 58, 54, 0.08);
}

.tip-list {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.tip-item {
  padding: 14px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fffaf7;
}

.tip-item strong {
  color: #9e4655;
  font-size: 13px;
}

.tip-item p {
  margin: 6px 0 0;
  color: #655a56;
  font-size: 14px;
  line-height: 1.65;
}

.cta-grid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}

.cta-btn {
  min-height: 76px;
  border: 1px solid #d98c99;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.74);
  color: #c65367;
  cursor: pointer;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 5px;
  padding: 12px;
  font-size: 16px;
  font-weight: 900;
}

.cta-btn span {
  color: #b27b83;
  font-size: 12px;
  font-weight: 700;
}

.cta-btn--primary {
  border-color: transparent;
  background: linear-gradient(135deg, #c65367, #d9697b);
  color: #fff;
}

.cta-btn--primary span {
  color: rgba(255, 255, 255, 0.84);
}

.cta-btn.saved {
  background: #fff0f1;
}

.cta-btn:disabled {
  cursor: not-allowed;
  opacity: 0.64;
}

.cta-btn:focus-visible,
.state-card button:focus-visible,
.mock-switcher select:focus-visible {
  outline: 2px solid #c65367;
  outline-offset: 2px;
}

.save-notice,
.save-feedback,
.empty-text {
  margin: 16px 0 0;
  color: #8e7e79;
  font-size: 13px;
}

.save-notice,
.save-feedback {
  text-align: center;
}

.save-feedback {
  color: #8b3a4a;
  font-weight: 800;
}

@media (max-width: 1180px) {
  .hero-grid,
  .feature-grid,
  .analysis-grid,
  .lower-grid {
    grid-template-columns: 1fr;
  }

  .palette-section,
  .eye-guide-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 840px) {
  .result-page {
    padding: 22px 16px 42px;
  }

  .result-shell {
    padding: 20px 16px;
  }

  .progress-steps {
    grid-template-columns: auto 44px auto 44px auto;
    font-size: 11px;
  }

  .result-topline {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-panel,
  .profile-panel,
  .section-card,
  .palette-card {
    padding: 18px;
  }

  .meta-grid,
  .summary-panel-layout,
  .feature-list,
  .palette-section,
  .makeup-grid,
  .eye-guide-grid,
  .style-grid,
  .cta-grid {
    grid-template-columns: 1fr;
  }

  .makeup-card--eye {
    grid-column: auto;
  }

  .metric-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .metric-score {
    text-align: left;
  }

  .profile-image-frame {
    width: min(100%, 260px);
  }
}

.makeover-status-banner {
  margin: 18px 0 20px;
  padding: 18px 20px;
  border: 1px solid rgba(198, 83, 103, 0.14);
  border-radius: 18px;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.86), transparent 42%),
    linear-gradient(135deg, #fff8f5, #f8e7ee);
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 12px 28px rgba(120, 67, 78, 0.07);
}

.makeover-status-spinner {
  flex: 0 0 auto;
  width: 38px;
  height: 38px;
  border-radius: 999px;
  border: 4px solid rgba(198, 83, 103, 0.16);
  border-top-color: #c65367;
  animation: makeover-status-spin 0.9s linear infinite;
}

.makeover-status-banner strong {
  display: block;
  color: #3a2b2a;
  font-size: 15px;
  font-weight: 900;
}

.makeover-status-banner p {
  margin: 5px 0 0;
  color: #8b7672;
  font-size: 13px;
  line-height: 1.5;
}

.makeover-status-banner b {
  color: #c65367;
  font-weight: 900;
}

@keyframes makeover-status-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  * {
    scroll-behavior: auto !important;
  }
}
</style>
