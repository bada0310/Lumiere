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

      <section v-if="loading" class="state-card">
        진단 결과를 불러오고 있어요.
      </section>

      <section v-else-if="errorMessage" class="state-card">
        <strong>{{ errorMessage }}</strong>
        <button type="button" @click="loadDiagnosis">다시 불러오기</button>
      </section>

      <section v-else-if="!diagnosisResult" class="state-card">
        표시할 진단 결과가 없어요.
      </section>

      <section v-else class="result-shell">
        <div class="result-topline">
          <span v-if="diagnosisResult.is_mock" class="demo-badge">개발용 mock 결과</span>
          <span v-else-if="diagnosisResult.is_demo" class="demo-badge">데모 진단 결과</span>

          <label v-if="isDev" class="mock-switcher">
            <span>Mock 타입</span>
            <select :value="selectedMockQuery" @change="changeMockType">
              <option value="">API 결과</option>
              <option v-for="mock in mockOptions" :key="mock.type || mock.toneKey" :value="mock.type || mock.toneKey">
                {{ mock.titleKo }}
              </option>
            </select>
          </label>
        </div>

        <section class="hero-grid">
          <article class="summary-panel">
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

            <div class="tags" aria-label="진단 키워드">
              <span v-for="tag in keywords" :key="tag">{{ tag }}</span>
            </div>
          </article>

          <article class="profile-panel">
            <div class="section-title-block">
              <span>Gen AI / 기본 프로필</span>
              <h2>결과 타입 대표 이미지</h2>
            </div>

            <div class="profile-image-frame">
              <img
                :src="safeProfileImageUrl"
                :alt="`${resultName} 타입의 기본 프로필 이미지`"
                @error="profileImageErrored = true"
              />
            </div>

            <p class="profile-caption">
              toneKey <strong>{{ diagnosisResult.personal_color_code || '-' }}</strong> 기준으로
              <code>images/tones</code> 이미지가 매핑됩니다.
            </p>

            <GeneratedMakeupImage
              :generated-url="diagnosisResult.generated_makeup_image_url"
              :uploaded-url="diagnosisResult.processed_image_url || diagnosisResult.uploaded_image_url"
              :generation-status="diagnosisResult.makeup_generation_status"
              @retry="loadDiagnosis"
            />

            <div v-if="diagnosisResult.uploaded_image_url" class="secondary-image">
              <img :src="diagnosisResult.uploaded_image_url" alt="진단에 사용한 원본 이미지" />
              <span>진단 원본 이미지</span>
            </div>
          </article>
        </section>

        <section class="feature-grid">
          <article class="section-card feature-panel">
            <div class="section-head">
              <div>
                <h2>전체 이미지 특징</h2>
                <p>AI가 읽은 인상과 톤의 방향입니다.</p>
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
                <h2>피부톤 정량 분석</h2>
                <p>mock 데이터 수치가 그대로 반영되는 영역입니다.</p>
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
                <p>평균값과 비교한 레이더 차트입니다.</p>
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
              <p>제품명이 아니라 색 계열과 사용 위치를 기준으로 정리했어요.</p>
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
              <h3>아이</h3>
              <p>{{ makeupGuide.eye.description }}</p>
              <div class="eye-guide-grid">
                <div v-for="group in eyeGuideGroups" :key="group.key" class="eye-guide-card">
                  <strong>{{ group.label }}</strong>
                  <small>{{ group.description }}</small>
                  <ColorChipList :colors="group.colors" :label="`아이 ${group.label} 컬러`" compact />
                </div>
              </div>
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
              <h2>AI 메이크오버 예시</h2>
              <p>제품 추천이 아니라 스타일 적용 분위기를 확인하는 영역입니다.</p>
            </div>

            <div v-if="makeoverStyles.length" class="tabs" role="tablist" aria-label="메이크오버 스타일">
              <button
                v-for="look in makeoverStyles"
                :key="look.key"
                type="button"
                :class="{ active: selectedLookKey === look.key }"
                @click="selectedLookKey = look.key"
              >
                {{ look.name }}
              </button>
            </div>
          </div>

          <div v-if="makeoverStyles.length" class="makeover-list">
            <article
              v-for="look in makeoverStyles"
              :key="look.key"
              class="look-card"
              :class="{ active: selectedLookKey === look.key }"
            >
              <img v-if="look.image_url" :src="look.image_url" :alt="`${look.name} 메이크업 스타일 이미지`" />
              <div v-else class="image-placeholder" aria-hidden="true">
                <span>{{ look.name }}</span>
              </div>
              <strong>{{ look.name }}</strong>
              <p>{{ look.description }}</p>
            </article>
          </div>
          <p v-else class="empty-text">메이크오버 이미지가 아직 없어요.</p>
        </section>

        <section class="lower-grid">
          <article class="section-card style-section">
            <div class="section-head">
              <div>
                <h2>추가 스타일 가이드</h2>
                <p>렌즈, 헤어, 액세서리, 의상 컬러 방향입니다.</p>
              </div>
            </div>

            <div class="style-grid">
              <div class="style-card">
                <h3>렌즈</h3>
                <ColorChipList :colors="styleGuide.lens" label="추천 렌즈 컬러" compact />
              </div>

              <div class="style-card">
                <h3>헤어</h3>
                <ColorChipList :colors="styleGuide.hair" label="추천 헤어 컬러" compact />
              </div>

              <div class="style-card">
                <h3>액세서리</h3>
                <ul class="plain-list">
                  <li v-for="item in styleGuide.accessory" :key="item">{{ item }}</li>
                </ul>
              </div>

              <div class="style-card">
                <h3>의상</h3>
                <ColorChipList :colors="styleGuide.fashion" label="추천 의상 컬러" compact />
              </div>
            </div>

            <div v-if="stylingKeywords.length || productToneRangeText" class="fixed-palette-meta">
              <div v-if="stylingKeywords.length">
                <h3>스타일링 키워드</h3>
                <div class="keyword-row">
                  <span v-for="keyword in stylingKeywords" :key="keyword">{{ keyword }}</span>
                </div>
              </div>

              <div v-if="productToneRangeText">
                <h3>추천 제품 색상 범위</h3>
                <p>{{ productToneRangeText }}</p>
              </div>
            </div>
          </article>

          <article class="section-card tip-section">
            <h2>컬러 선택 팁</h2>
            <p>{{ diagnosisResult.tip || defaultTip }}</p>
          </article>
        </section>

        <section class="cta-grid">
          <button type="button" class="cta-btn cta-btn--primary" @click="goToProducts">
            맞춤 화장품 추천 보기
            <span>제품 추천은 별도 페이지에서 확인해요.</span>
          </button>
          <button type="button" class="cta-btn" @click="scrollToMakeover">
            AI 메이크오버 더 보기
            <span>스타일 예시 영역으로 이동합니다.</span>
          </button>
          <button type="button" class="cta-btn" :class="{ saved: isSaved }" @click="saveResult">
            {{ isSaved ? '결과 저장 완료' : '결과 저장하기' }}
            <span>저장하면 마이페이지에서 다시 볼 수 있어요.</span>
          </button>
        </section>

        <p class="save-notice">
          개발 환경의 mock 결과는 localStorage에 저장되어 새로고침 후에도 마이페이지에서 확인할 수 있어요.
        </p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import GeneratedMakeupImage from '@/components/diagnosis/GeneratedMakeupImage.vue'
import SkinBalanceChart from '@/components/diagnosis/SkinBalanceChart.vue'
import { FALLBACK_TONE_IMAGE } from '@/data/toneImages'
import {
  DEFAULT_MOCK_TONE_KEY,
  getMockPersonalColorResult,
  isMockPersonalColorResultKey,
  MOCK_PERSONAL_COLOR_RESULTS,
} from '@/data/mockPersonalColorResults'
import { getDemoDiagnosis, getDiagnosisResult, getLatestDiagnosis } from '@/services/diagnosisApi'
import { useRequireLogin } from '@/composables/useRequireLogin'
import { getDiagnosisProfileImageUrl, normalizeDiagnosisResult } from '@/utils/diagnosisResultTransform'
import { getSavedMockDiagnosisResult, saveMockDiagnosisResult } from '@/utils/diagnosisMockStorage'

const ColorChipList = defineComponent({
  name: 'ColorChipList',
  props: {
    colors: {
      type: Array,
      default: () => [],
    },
    label: {
      type: String,
      default: '컬러칩',
    },
    compact: {
      type: Boolean,
      default: false,
    },
  },
  setup(props) {
    return () =>
      h(
        'div',
        {
          class: ['inline-color-list', { 'inline-color-list--compact': props.compact }],
          role: 'list',
          'aria-label': props.label,
        },
        props.colors.map((color) =>
          h(
            'div',
            {
              key: color.name,
              class: 'inline-color-chip',
              role: 'listitem',
              title: color.description || `${color.name} ${color.hex}`,
              'aria-label': `${color.name} ${color.hex}`,
            },
            [
              h('span', { style: { backgroundColor: color.hex } }),
              h('small', color.name),
            ],
          ),
        ),
      )
  },
})

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
              props.items.map((item) => h('li', { key: item }, item)),
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
const makeoverRef = ref(null)
const profileImageErrored = ref(false)
let makeupPollTimer = null

const isDev = import.meta.env.DEV
const mockOptions = MOCK_PERSONAL_COLOR_RESULTS
const defaultTip = '색상은 제품명보다 실제 발색과 채도, 명도, 온도감이 더 중요해요.'

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

const confidence = computed(() => clampPercent(diagnosisResult.value?.confidence ?? diagnosisResult.value?.confidence_score))

const resultName = computed(() => {
  return diagnosisResult.value?.korean_name || diagnosisResult.value?.personal_color?.korean_name || '퍼스널 컬러'
})

const resultEnglishName = computed(() => {
  return diagnosisResult.value?.english_name || diagnosisResult.value?.personal_color?.english_name || ''
})

const resultSummary = computed(() => {
  return diagnosisResult.value?.summary || '진단 결과에 맞춘 컬러와 스타일 가이드를 확인해보세요.'
})

const resultDate = computed(() => {
  return formatDate(diagnosisResult.value?.diagnosed_at || diagnosisResult.value?.created_at)
})

const keywords = computed(() => asArray(diagnosisResult.value?.keywords))
const imageFeatures = computed(() => asArray(diagnosisResult.value?.image_features))
const representativeColors = computed(() => asArray(diagnosisResult.value?.representative_colors))
const makeoverStyles = computed(() => asArray(diagnosisResult.value?.makeover_styles))
const makeupGuide = computed(() => diagnosisResult.value?.makeup_color_guide || normalizeDiagnosisResult({})?.makeup_color_guide)
const styleGuide = computed(() => diagnosisResult.value?.style_guide || { lens: [], hair: [], accessory: [], fashion: [] })
const paletteStatus = computed(() => diagnosisResult.value?.palette_status || '')
const stylingKeywords = computed(() => asArray(diagnosisResult.value?.styling_keywords))
const productToneRangeText = computed(() => {
  const range = diagnosisResult.value?.recommended_product_tone_range || {}
  const parts = []
  if (range.hue?.length) parts.push(`색상: ${range.hue.join(', ')}`)
  if (range.brightness?.length) parts.push(`명도: ${range.brightness.join(', ')}`)
  if (range.chroma?.length) parts.push(`채도: ${range.chroma.join(', ')}`)
  if (range.temperature) parts.push(`온도: ${range.temperature}`)
  return parts.join(' / ')
})
const isMakeupGenerating = computed(() =>
  ['queued', 'running', 'loading', 'pending'].includes(diagnosisResult.value?.makeup_generation_status),
)

const profileImageUrl = computed(() => getDiagnosisProfileImageUrl(diagnosisResult.value))
const safeProfileImageUrl = computed(() => (profileImageErrored.value ? FALLBACK_TONE_IMAGE : profileImageUrl.value))

const skinMetricLabels = [
  { key: 'brightness', name: '명도', desc: '피부 밝기 정도' },
  { key: 'saturation', name: '채도', desc: '색의 선명한 정도' },
  { key: 'clarity', name: '청탁', desc: '맑고 투명한 정도' },
  { key: 'contrast', name: '대비', desc: '이목구비 대비감' },
  { key: 'cool_warm', name: '쿨톤 ↔ 웜톤', desc: '피부 온도감 축' },
  { key: 'softness', name: '부드러움', desc: '전체 인상의 소프트함' },
]

const radarLabels = [
  { key: 'brightness', name: '명도', average: 62 },
  { key: 'saturation', name: '채도', average: 48 },
  { key: 'clarity', name: '청탁', average: 55 },
  { key: 'contrast', name: '대비', average: 50 },
  { key: 'softness', name: '부드러움', average: 57 },
  { key: 'coolness', name: '쿨감', average: 52 },
]

const paletteGroups = [
  { key: 'best', label: 'BEST', description: '가장 잘 어울리는 컬러' },
  { key: 'neutral', label: 'NEUTRAL', description: '자연스럽고 안정적인 컬러' },
  { key: 'accent', label: 'ACCENT', description: '포인트로 좋은 컬러' },
  { key: 'try', label: 'TRY', description: '부담 없이 시도해볼 컬러' },
  { key: 'worst', label: 'WORST', description: '피하면 좋은 컬러' },
]

const eyeGuideGroups = computed(() => [
  {
    key: 'highlighter',
    label: '하이라이터',
    description: '눈앞머리와 애교살 포인트',
    colors: makeupGuide.value.eye.highlighter,
  },
  {
    key: 'base',
    label: '베이스',
    description: '눈두덩 전체에 깔아주는 컬러',
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
    description: '눈꼬리와 언더 포인트 컬러',
    colors: makeupGuide.value.eye.point,
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

const paletteItems = (key) => {
  return asArray(diagnosisResult.value?.color_palettes?.[key])
}

const iconLabel = (icon) => ({
  sparkle: '✦',
  cloud: '☁',
  diamond: '◇',
  flower: '✿',
  sun: '☼',
  leaf: '◇',
}[icon] || '✦')

const applyDiagnosisResult = (raw) => {
  const normalized = normalizeDiagnosisResult(raw)
  diagnosisResult.value = normalized
  selectedLookKey.value =
    normalized?.makeover_styles?.find((look) => look.is_default)?.key ||
    normalized?.makeover_styles?.[0]?.key ||
    ''
  profileImageErrored.value = false
  isSaved.value = Boolean(normalized?.is_mock && getSavedMockDiagnosisResult()?.id === normalized.id)
  scheduleMakeupPolling()
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

const loadDiagnosis = async ({ silent = false } = {}) => {
  if (!silent) loading.value = true
  errorMessage.value = ''

  try {
    if (isDev && selectedMockQuery.value) {
      loadMockDiagnosis(selectedMockQuery.value)
      return
    }

    const id = route.params.diagnosisId || route.params.id
    const data = route.name === 'diagnosis-result-demo' || id === 'demo'
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
  } catch (error) {
    console.error('진단 결과 조회 실패:', error)

    if (silent) {
      stopMakeupPolling()
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

const stopMakeupPolling = () => {
  if (!makeupPollTimer) return
  window.clearInterval(makeupPollTimer)
  makeupPollTimer = null
}

const scheduleMakeupPolling = () => {
  stopMakeupPolling()
  if (!isMakeupGenerating.value || diagnosisResult.value?.is_mock) return

  makeupPollTimer = window.setInterval(() => {
    if (!isMakeupGenerating.value) {
      stopMakeupPolling()
      return
    }
    loadDiagnosis({ silent: true })
  }, 4000)
}

const changeMockType = (event) => {
  const nextMock = event.target.value
  router.replace({
    path: route.path,
    query: {
      ...route.query,
      mock: nextMock || undefined,
    },
  })
}

const goToProducts = () => {
  router.push('/products')
}

const scrollToMakeover = () => {
  makeoverRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const saveResult = () => {
  if (!requireLogin({
    message: '진단 결과 저장은 로그인 후 이용할 수 있어요.',
    redirect: route.fullPath,
  })) {
    return
  }

  if (diagnosisResult.value?.is_mock) {
    saveMockDiagnosisResult(diagnosisResult.value)
  }

  isSaved.value = true
  alert('진단 결과를 저장했어요. 마이페이지에서 다시 확인할 수 있어요.')
}

watch(() => route.fullPath, () => loadDiagnosis())
onMounted(loadDiagnosis)
onUnmounted(stopMakeupPolling)
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

.profile-caption code {
  padding: 1px 5px;
  border-radius: 4px;
  background: #f6eeee;
  color: #8b3a4a;
}

.profile-panel :deep(.generated-makeup) {
  height: 260px;
}

.secondary-image {
  display: grid;
  grid-template-columns: 52px 1fr;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fffaf7;
}

.secondary-image img {
  width: 52px;
  height: 52px;
  border-radius: 10px;
  object-fit: cover;
}

.secondary-image span {
  color: #6f625e;
  font-size: 13px;
  font-weight: 800;
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

.makeup-card h3,
.style-card h3 {
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

.inline-color-list {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.inline-color-chip {
  max-width: 150px;
  min-height: 38px;
  padding: 6px 9px 6px 7px;
  border: 1px solid #eee3df;
  border-radius: 999px;
  background: #fffaf7;
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.inline-color-chip span {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.08);
  flex: 0 0 auto;
}

.inline-color-chip small {
  min-width: 0;
  color: #534845;
  font-size: 12px;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.inline-color-list--compact .inline-color-chip {
  max-width: 132px;
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

.avoid-list ul,
.plain-list {
  margin: 8px 0 0;
  padding-left: 18px;
  color: #6d625f;
  font-size: 12px;
  line-height: 1.65;
}

.eye-guide-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
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

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tabs button {
  min-width: 88px;
  height: 34px;
  border: 0;
  border-radius: 7px;
  background: #f8eeee;
  color: #5e5653;
  font-weight: 800;
  cursor: pointer;
}

.tabs button.active,
.tabs button:focus-visible {
  background: #c65367;
  color: white;
  outline: 2px solid #efb8c2;
  outline-offset: 2px;
}

.makeover-list {
  margin-top: 24px;
  display: grid;
  grid-template-columns: repeat(3, minmax(160px, 1fr));
  gap: 16px;
}

.look-card {
  padding: 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  text-align: center;
}

.look-card.active {
  border-color: #c65367;
  background: #fffaf7;
}

.look-card img,
.image-placeholder {
  width: 100%;
  aspect-ratio: 1.5 / 1;
  border-radius: 8px;
  object-fit: cover;
  background: linear-gradient(135deg, #fff1eb, #f1d7e0);
  margin-bottom: 11px;
}

.image-placeholder {
  display: grid;
  place-items: center;
  color: #9e4655;
  font-weight: 900;
}

.look-card p {
  margin: 4px 0 0;
  color: #8e7e79;
  font-size: 12px;
}

.style-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.style-card {
  min-height: 132px;
  padding: 16px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fff;
}

.fixed-palette-meta {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fffaf7;
  display: grid;
  gap: 14px;
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

.keyword-row span {
  padding: 7px 10px;
  border-radius: 999px;
  background: #fff0f1;
  color: #8b3a4a;
  font-size: 12px;
  font-weight: 800;
}

.tip-section p {
  margin: 16px 0 0;
  color: #655a56;
  font-size: 15px;
  line-height: 1.7;
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

.cta-btn:focus-visible,
.state-card button:focus-visible,
.mock-switcher select:focus-visible {
  outline: 2px solid #c65367;
  outline-offset: 2px;
}

.save-notice,
.empty-text {
  margin: 16px 0 0;
  color: #8e7e79;
  font-size: 13px;
}

.save-notice {
  text-align: center;
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
  .feature-list,
  .palette-section,
  .makeup-grid,
  .eye-guide-grid,
  .makeover-list,
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

@media (prefers-reduced-motion: reduce) {
  * {
    scroll-behavior: auto !important;
  }
}
</style>
