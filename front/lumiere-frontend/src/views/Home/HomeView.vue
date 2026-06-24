<template>
  <main class="home">
    <section class="hero">
      <div class="hero-text">
        <h1>
          나만의 <span class="point-color">분위기</span>를 찾는 가장<br />
          똑똑한 방법
        </h1>


    <p>
      AI 퍼스널컬러 진단과 제품 색상 분석으로<br />
      당신에게 딱 맞는 뷰티를 추천해드려요.
    </p>

    <div class="hero-buttons">
      <button class="primary-btn" @click="$router.push('/upload')">
        AI 퍼스널컬러 진단하기
        <small>내 퍼스널컬러 찾기 →</small>
      </button>

      <button class="outline-btn" @click="$router.push('/product-analysis')">
        제품 색상 분석하기
        <small>제품 색상/호수 분석 →</small>
      </button>
    </div>
  </div>

  <div class="hero-image">
    <div class="model-card">
      <transition name="makeover-fade" mode="out-in">
        <div
          v-if="activeHeroMakeover"
          :key="activeHeroMakeover.key"
          class="hero-makeover"
        >
          <img
            class="hero-makeover__image"
            :src="activeHeroMakeover.imageUrl"
            :alt="`${summaryToneName} ${activeHeroMakeover.title}`"
          />

          <div class="hero-makeover__label">
            {{ activeHeroMakeover.title }}
          </div>
        </div>

        <div
          v-else
          class="tone-prism"
          :aria-label="`${summaryToneName} 퍼스널컬러 팔레트`"
        >
          <div class="tone-prism__mark">
            <span class="tone-prism__letter">L</span>
            <div class="tone-prism__spectrum">
              <span
                v-for="(color, index) in summaryColors"
                :key="`${color}-${index}`"
                :style="{ background: color }"
              ></span>
            </div>
          </div>

          <div class="tone-prism__copy">
            <span>Personal Color Palette</span>
            <strong>{{ hasDiagnosis ? summaryToneName : 'Lumière' }}</strong>
          </div>
        </div>
      </transition>

      <div class="model-overlay">
        <span>{{ hasDiagnosis ? 'My Tone' : 'Lumière' }}</span>
        <strong>{{ summaryToneName }}</strong>
      </div>
    </div>

    <div class="summary-card">
      <img
        v-if="summaryToneBackgroundUrl && !summaryToneImageErrored"
        class="tone-bg-image"
        :src="summaryToneBackgroundUrl"
        :alt="`${summaryToneName} 대표 이미지`"
        @error="summaryToneImageErrored = true"
      />
      <div class="tone-bg-overlay"></div>

      <div class="personal-summary-content">
        <p class="summary-title">내 퍼스널컬러 요약</p>
        <h3>{{ summaryToneName }}</h3>
        <p class="eng">{{ summaryToneEnglish }}</p>

        <div class="chips">
          <span
            v-for="color in summaryColors"
            :key="color"
            :style="{ background: color }"
          ></span>
        </div>

        <p class="summary-desc">
          {{ summaryDescription }}
        </p>

        <button @click="goToSummaryResult">
          {{ hasDiagnosis ? '상세 결과 보기' : '진단하고 요약 받기' }}
        </button>
      </div>
    </div>
  </div>
</section>

<section class="features">
  <h2>Lumière의 핵심 기능</h2>

  <div class="feature-grid">
    <div class="feature-card">
      <div class="icon">☺</div>
      <h3>AI 퍼스널컬러 진단</h3>
      <p>AI가 분석한 당신의 피부톤과 이미지로 퍼스널컬러를 찾아드려요.</p>
      <RouterLink to="/upload" class="feature-link">
        바로 진단하기 →
      </RouterLink>
    </div>

    <div class="feature-card">
      <div class="icon">💄</div>
      <h3>맞춤 화장품 추천</h3>
      <p>당신의 퍼스널컬러에 맞는 화장품을 카테고리별로 추천해드려요.</p>
      <RouterLink to="/products" class="feature-link">
        추천 제품 보기 →
      </RouterLink>
    </div>

    <div class="feature-card">
      <div class="icon">🔍</div>
      <h3>제품 색상/호수 분석</h3>
      <p>제품 이미지와 옵션 색상을 분석해 내 퍼스널컬러와 비교해드려요.</p>
      <RouterLink to="/product-analysis" class="feature-link">
        제품 분석하기 →
      </RouterLink>
    </div>

    <div class="feature-card">
      <div class="icon">📋</div>
      <h3>진단 기록 관리</h3>
      <p>이전 진단 결과를 확인하고 변화를 비교해보세요.</p>
      <RouterLink to="/mypage" class="feature-link">
        마이페이지 가기 →
      </RouterLink>
    </div>
  </div>
</section>

<section class="products">
  <div class="section-head">
    <h2>오늘의 인기 추천 제품</h2>
    <RouterLink to="/products" class="view-all">전체 보기 →</RouterLink>
  </div>

  <div v-if="!hasDiagnosis" class="recommend-state">
    퍼스널 컬러 진단을 하면 나에게 맞는 추천 제품을 볼 수 있어요.
  </div>

  <div v-else-if="isRecommendationsLoading" class="recommend-state">
    추천 제품을 불러오는 중입니다.
  </div>

  <div v-else-if="recommendationError" class="recommend-state error">
    {{ recommendationError }}
  </div>

  <div v-else-if="products.length === 0" class="recommend-state">
    아직 추천할 만한 제품이 충분하지 않아요. 제품 데이터가 더 쌓이면 더 정확한 추천을 보여드릴게요.
  </div>

  <div v-else class="carousel-shell">
    <button
      type="button"
      class="carousel-arrow left"
      aria-label="이전 추천 제품"
      @click="scrollCarousel(-1)"
    >
      ‹
    </button>

    <div ref="carouselRef" class="recommendation-carousel">
      <article
        v-for="product in products"
        :key="`${product.id}-${product.optionId || 'best'}`"
        class="recommend-card"
        tabindex="0"
        @click="goToProductDetail(product)"
        @keydown.enter.prevent="goToProductDetail(product)"
      >
        <div class="flip-card-inner">
          <div class="flip-card-face flip-card-front">
            <button
              type="button"
              class="heart"
              :class="{ active: isHomeProductLiked(product) }"
              :disabled="isHomeProductLiking(product)"
              :aria-label="isHomeProductLiked(product) ? '찜 해제' : '찜하기'"
              @click.stop="toggleHomeProductLike(product)"
            >
              {{ isHomeProductLiked(product) ? '♥' : '♡' }}
            </button>

            <div class="product-img" :class="product.imageClass">
              <img
                v-if="product.imageUrl"
                :src="product.imageUrl"
                :alt="product.name"
                loading="lazy"
              />
              <div v-else class="product-art"></div>
            </div>

            <div class="card-copy">
              <div class="card-topline">
                <span>{{ product.categoryLabel }}</span>
                <strong :class="statusClass(product.matchStatus)">
                  {{ product.matchStatus || 'COLOR' }}
                </strong>
              </div>

              <p class="brand">{{ product.brand }}</p>
              <h4>{{ product.name }}</h4>
              <p v-if="product.optionName" class="option-name">
                {{ product.optionName }}
              </p>
              <p class="reason">{{ product.reason }}</p>
            </div>
          </div>

          <div class="flip-card-face flip-card-back">
            <span class="back-label">AI Recommendation</span>
            <h4>{{ product.name }}</h4>
            <p>{{ product.detailReason || product.reason }}</p>
            <p v-if="product.usageTip" class="usage-tip">
              {{ product.usageTip }}
            </p>

            <div class="back-meta">
              <span :class="statusClass(product.matchStatus)">
                {{ product.matchStatus || 'COLOR' }}
              </span>
              <span>{{ product.score }}% match</span>
            </div>

            <button
              type="button"
              tabindex="-1"
              @click.stop="goToProductDetail(product)"
            >
              제품 자세히 보기
            </button>
          </div>
        </div>
      </article>
    </div>

    <button
      type="button"
      class="carousel-arrow right"
      aria-label="다음 추천 제품"
      @click="scrollCarousel(1)"
    >
      ›
    </button>
  </div>
</section>
```

  </main>
</template>


<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { getLatestDiagnosis } from '@/services/diagnosisApi'
import { getPersonalizedRecommendedProducts } from '@/services/productApi'
import { getLatestDiagnosisToneImageUrl } from '@/data/toneImages'
import { useEngagementStore } from '@/stores/engagement'
import { normalizeDiagnosisResult } from '@/utils/diagnosisResultTransform'
import { getSavedMockDiagnosisResult } from '@/utils/diagnosisMockStorage'

const router = useRouter()
const engagementStore = useEngagementStore()

const products = ref([])
const latestDiagnosis = ref(null)
const isRecommendationsLoading = ref(false)
const recommendationError = ref('')
const carouselRef = ref(null)
const summaryToneImageErrored = ref(false)

const activeMakeoverIndex = ref(0)
let makeoverTimer = null

const hasDiagnosis = computed(() => Boolean(latestDiagnosis.value))
const summaryToneBackgroundUrl = computed(() => {
  if (!hasDiagnosis.value) return ''
  return getLatestDiagnosisToneImageUrl(latestDiagnosis.value)
})

const summaryToneName = computed(() => latestDiagnosis.value?.korean_name || '아직 진단 전')
const summaryToneEnglish = computed(() => latestDiagnosis.value?.english_name || 'Find Your Personal Color')
const summaryDescription = computed(() => {
  if (latestDiagnosis.value?.summary) return latestDiagnosis.value.summary
  if (!latestDiagnosis.value) {
    return 'AI 진단을 완료하면 내 퍼스널컬러와 어울리는 컬러 팔레트가 이곳에 바로 표시돼요.'
  }
  return '진단 결과를 바탕으로 어울리는 색감과 메이크업 방향을 요약해드려요.'
})

const summaryColors = computed(() => {
  const colors = latestDiagnosis.value?.representative_colors
    ?.map((color) => color.hex)
    .filter(Boolean)
    .slice(0, 5)

  return colors?.length
    ? colors
    : ['#efc7cf', '#e7c9d8', '#d6c5e3', '#c7c5df', '#d6e1e8']
})

const rawMakeoverImages = computed(() => {
  const diagnosis = latestDiagnosis.value || {}

  return (
    diagnosis.makeup_images ||
    diagnosis.makeover?.makeup_images ||
    diagnosis.makeover?.styles ||
    diagnosis.makeover_styles ||
    diagnosis.styles ||
    []
  )
})

const heroMakeoverImages = computed(() => {
  return rawMakeoverImages.value
    .filter((item) => {
      const status = String(item.status || '').toLowerCase()
      const imageUrl = item.image_url || item.imageUrl || item.image || ''
      return imageUrl && ['complete', 'completed', 'done', 'success'].includes(status)
    })
    .map((item) => ({
      key: item.style_key || item.key || item.name,
      title: item.title || item.name || '메이크업 프리뷰',
      imageUrl: resolveMediaUrl(item.image_url || item.imageUrl || item.image || ''),
    }))
})

const activeHeroMakeover = computed(() => {
  if (!heroMakeoverImages.value.length) return null
  return heroMakeoverImages.value[activeMakeoverIndex.value % heroMakeoverImages.value.length]
})

watch(summaryToneBackgroundUrl, () => {
  summaryToneImageErrored.value = false
})

const stopMakeoverTimer = () => {
  if (makeoverTimer) {
    clearInterval(makeoverTimer)
    makeoverTimer = null
  }
}

const startMakeoverTimer = () => {
  stopMakeoverTimer()

  if (heroMakeoverImages.value.length <= 1) return

  makeoverTimer = setInterval(() => {
    activeMakeoverIndex.value =
      (activeMakeoverIndex.value + 1) % heroMakeoverImages.value.length
  }, 3500)
}

watch(
  heroMakeoverImages,
  () => {
    activeMakeoverIndex.value = 0
    startMakeoverTimer()
  },
  { immediate: true }
)

function normalizeHomeProduct(item, index) {
  const category = String(item.category || item.category_key || '').toUpperCase()
  const bestOption = item.best_option || {}
  const imageClass = category.includes('EYE')
    ? 'eye'
    : category.includes('CHEEK')
      ? 'cheek'
      : category.includes('BASE')
        ? 'base'
        : 'lip'

  return {
    id: item.id || bestOption.product_id || index + 1,
    productId: item.id || bestOption.product_id || index + 1,
    optionId: bestOption.id || item.option_id || '',
    groupKey: item.group_key || `${item.id || bestOption.product_id || index + 1}-${bestOption.id || item.option_id || 'product'}`,
    brand: item.brand || item.product_brand || '브랜드 미상',
    name: item.name || item.product_name || '추천 상품',
    category,
    categoryLabel: categoryLabel(category),
    optionName: [bestOption.option_no, bestOption.option_name].filter(Boolean).join(' '),
    matchStatus: item.match_status || bestOption.match_status || bestOption.grade || '',
    score: Math.min(99, Math.max(0, Math.round(Number(item.match_score || bestOption.match_score || 0) || 0))),
    reason: item.short_reason || item.summary_reason || item.reason || item.match_reason || bestOption.short_reason || '내 톤과 가까운 색감으로 추천된 제품이에요.',
    detailReason: item.detail_reason || bestOption.detail_reason || item.short_reason || item.summary_reason || '',
    usageTip: item.usage_tip || bestOption.usage_tip || '',
    imageUrl: item.image_url || bestOption.image_url || item.image || item.thumbnail || item.thumbnail_url || '',
    productUrl: item.product_url || bestOption.product_url || bestOption.representative_offer?.product_url || '',
    imageClass,
    raw: item,
  }
}

const categoryLabel = (value) => {
  const map = { LIP: 'Lip', EYE: 'Eye', BASE: 'Base', CHEEK: 'Cheek', LENS: 'Lens', ETC: 'Etc' }
  return map[value] || 'Etc'
}

const statusClass = (status) => String(status || 'color').toLowerCase()

const buildHomeLikedPayload = (product) => {
  const productId = Number(product.productId || product.id)
  const optionId = Number(product.optionId)
  const optionName = product.optionName || ''

  const payload = {
    product_id: productId,
    option_id: String(optionId || optionName || product.groupKey || ''),
    group_key: product.groupKey,
    brand: product.brand,
    name: product.name,
    option: optionName,
    image_url: product.imageUrl,
    product_url: product.productUrl,
    snapshot: {
      ...product.raw,
      productId,
      optionId: optionId || '',
      groupKey: product.groupKey,
      optionName,
      recommendedReason: product.reason,
      usageTip: product.usageTip,
    },
  }

  if (Number.isFinite(optionId) && optionId > 0) {
    payload.product_option_id = optionId
  }

  return payload
}

const isHomeProductLiked = (product) => engagementStore.isLiked(buildHomeLikedPayload(product))

const isHomeProductLiking = (product) => engagementStore.isLiking(buildHomeLikedPayload(product))

const toggleHomeProductLike = async (product) => {
  if (!localStorage.getItem('access_token')) {
    alert('로그인 후 찜할 수 있어요.')
    router.push({ name: 'login', query: { redirect: '/' } })
    return
  }

  try {
    await engagementStore.toggleLikedProduct(buildHomeLikedPayload(product))
  } catch (error) {
    console.error('추천 제품 찜 상태를 저장하지 못했습니다.', error)
    alert('찜 상태를 저장하지 못했습니다.')
  }
}

const loadLatestDiagnosis = async () => {
  const savedMock = normalizeDiagnosisResult(getSavedMockDiagnosisResult())
  if (savedMock) latestDiagnosis.value = savedMock

  if (!localStorage.getItem('access_token')) return

  try {
    const result = normalizeDiagnosisResult(await getLatestDiagnosis())
    if (result) latestDiagnosis.value = result
  } catch (error) {
    console.warn('홈 퍼스널컬러 요약을 불러오지 못했어요:', error)
  }
}

const loadPopularProducts = async () => {
  products.value = []
  recommendationError.value = ''
  if (!latestDiagnosis.value) return

  isRecommendationsLoading.value = true
  try {
    const toneKey = latestDiagnosis.value.personal_color_code || latestDiagnosis.value.tone_key || latestDiagnosis.value.type || ''
    const response = await getPersonalizedRecommendedProducts({
      limit: 12,
      per_category: 2,
      tone_key: toneKey ? String(toneKey).replace(/-/g, '_') : undefined,
    })
    const data = Array.isArray(response) ? response : response.results || []
    const normalized = data.map(normalizeHomeProduct).filter((item) => item.id)
    if (normalized.length) products.value = normalized
    if (localStorage.getItem('access_token')) {
      await engagementStore.loadLikedOptions({ force: true })
    }
  } catch (error) {
    console.warn('홈 개인화 추천 제품을 불러오지 못했어요:', error)
    recommendationError.value = '추천 제품을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.'
  } finally {
    isRecommendationsLoading.value = false
  }
}

const goToSummaryResult = () => {
  if (!latestDiagnosis.value) {
    router.push('/upload')
    return
  }

  if (latestDiagnosis.value.is_mock) {
    router.push({
      path: '/diagnosis/result',
      query: {
        mock: String(latestDiagnosis.value.personal_color_code || latestDiagnosis.value.type || '').replace(/-/g, '_'),
      },
    })
    return
  }

  router.push(`/diagnosis/results/${latestDiagnosis.value.id}`)
}

const goToProductDetail = (product) => {
  if (product.raw) {
    localStorage.setItem('selectedProductOption', JSON.stringify(product.raw))
  }
  const toneKey = latestDiagnosis.value?.personal_color_code || latestDiagnosis.value?.tone_key || latestDiagnosis.value?.type || ''
  router.push({
    name: 'recommendAnalysisResult',
    params: { id: product.id },
    query: {
      ...(product.optionId ? { option: product.optionId } : {}),
      ...(toneKey ? { tone_key: String(toneKey).replace(/-/g, '_') } : {}),
    },
  })
}

const scrollCarousel = (direction) => {
  const el = carouselRef.value
  if (!el) return
  el.scrollBy({
    left: direction * Math.min(el.clientWidth * 0.85, 760),
    behavior: 'smooth',
  })
}

onMounted(async () => {
  await loadLatestDiagnosis()
  if (localStorage.getItem('access_token')) {
    await engagementStore.loadLikedOptions({ force: true })
  }
  await loadPopularProducts()
})

onBeforeUnmount(() => {
  stopMakeoverTimer()
})

const API_ORIGIN =
  import.meta.env.VITE_API_ORIGIN ||
  String(import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/api\/?$/, '')

const resolveMediaUrl = (url) => {
  if (!url) return ''
  if (
    url.startsWith('http://') ||
    url.startsWith('https://') ||
    url.startsWith('blob:') ||
    url.startsWith('data:')
  ) {
    return url
  }
  if (url.startsWith('/')) return `${API_ORIGIN}${url}`
  return `${API_ORIGIN}/${url}`
}


</script>


<style scoped>
.home {
  min-height: 100vh;
  background: #fffaf7;
  color: #2b2523;
}

.hero {
  min-height: 470px;
  padding: clamp(36px, 5vw, 60px) clamp(24px, 7vw, 90px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(90deg, #fff7f2, #f7e5dd);
  gap: clamp(24px, 4vw, 48px);
}

.hero-text h1 {
  font-family: var(--font-title-serif) !important;
  font-size: clamp(32px, 5vw, 52px);
  line-height: 1.35;
  font-weight: 700;
}

.point-color {
  color: #c65367;
}

.hero-text h1 .point-color {
  font-family: var(--font-title-serif) !important;
  font-weight: inherit;
  letter-spacing: inherit;
}

.hero-text p {
  margin-top: 24px;
  font-size: clamp(15px, 1.8vw, 18px);
  line-height: 1.8;
}

.hero-buttons {
  margin-top: 36px;
  display: flex;
  gap: 20px;
}

.hero-buttons button {
  width: clamp(210px, 22vw, 280px);
  min-height: clamp(76px, 8vw, 92px);
  border-radius: 12px;
  font-size: clamp(15px, 1.6vw, 18px);
  font-weight: 700;
  cursor: pointer;
  padding: 14px 18px;
}

.hero-buttons small {
  display: block;
  margin-top: 8px;
  font-size: 14px;
  font-weight: 400;
}

.primary-btn {
  background: #c65367;
  color: white;
  border: none;
}

.outline-btn {
  background: white;
  color: #c65367;
  border: 1px solid #d98c99;
}

.hero-image {
  position: relative;
  display: flex;
  align-items: center;
  gap: 30px;
}

.model-card {
  position: relative;
  width: 330px;
  height: 380px;
  border-radius: 24px;
  background:
    radial-gradient(circle at 28% 18%, rgba(255, 255, 255, 0.94), transparent 28%),
    linear-gradient(135deg, #f7dfd9, #fff7f2 54%, #eadce7);
  overflow: hidden;
  box-shadow: 0 18px 44px rgba(90, 50, 40, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.tone-prism {
  width: 238px;
  padding: 24px;
  border: 1px solid rgba(222, 204, 198, 0.76);
  border-radius: 18px;
  background: rgba(255, 252, 250, 0.82);
  box-shadow: 0 22px 44px rgba(90, 50, 40, 0.1);
  display: grid;
  gap: 18px;
  backdrop-filter: blur(8px);
}

.tone-prism__mark {
  display: grid;
  grid-template-columns: 78px 1fr;
  gap: 14px;
  align-items: stretch;
  min-height: 118px;
}

.tone-prism__letter {
  border: 1px solid rgba(200, 176, 169, 0.66);
  border-radius: 14px;
  background: #fffaf7;
  color: #b64f61;
  font-family: var(--font-title-serif) !important;
  font-size: 58px;
  line-height: 1;
  display: grid;
  place-items: center;
  box-shadow: inset 0 -10px 22px rgba(198, 83, 103, 0.08);
}

.tone-prism__spectrum {
  display: grid;
  grid-template-columns: repeat(5, minmax(14px, 1fr));
  gap: 6px;
}

.tone-prism__spectrum span {
  min-width: 0;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  box-shadow:
    inset 0 -14px 20px rgba(69, 43, 45, 0.08),
    0 10px 18px rgba(90, 50, 40, 0.08);
}

.tone-prism__copy span {
  display: block;
  color: #9c5f65;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.tone-prism__copy strong {
  display: block;
  color: #2b2523;
  font-size: 22px;
  line-height: 1.32;
}

.model-overlay {
  position: absolute;
  left: 22px;
  right: 22px;
  bottom: 22px;
  padding: 16px 18px;
  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 14px;
  background: rgba(255, 250, 247, 0.76);
  backdrop-filter: blur(10px);
  box-shadow: 0 12px 26px rgba(90, 50, 40, 0.1);
}

.model-overlay span {
  display: block;
  color: #c65367;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.model-overlay strong {
  display: block;
  color: #2b2523;
  font-size: 20px;
}

.summary-card {
  position: relative;
  width: 330px;
  min-height: 360px;
  padding: 28px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 10px 30px rgba(90, 50, 40, 0.08);
  overflow: hidden;
  isolation: isolate;
}

.tone-bg-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.3;
  pointer-events: none;
  z-index: 0;
}

.tone-bg-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.94) 0%, rgba(255, 255, 255, 0.76) 62%, rgba(255, 250, 247, 0.52) 100%),
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.72), transparent 42%);
  pointer-events: none;
  z-index: 0;
}

.personal-summary-content {
  position: relative;
  z-index: 1;
}

.summary-title {
  font-weight: 700;
  margin-bottom: 28px;
}

.summary-card h3 {
  font-size: 24px;
}

.eng {
  color: #777;
  margin-top: 6px;
}

.chips {
  display: flex;
  gap: 12px;
  margin: 20px 0;
}

.chips span {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(92, 62, 58, 0.08);
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.42);
}

.summary-desc {
  color: #6b5f5b;
  line-height: 1.7;
  font-size: 14px;
}

.summary-card button {
  margin-top: 20px;
  padding: 12px 22px;
  border: 1px solid #d98c99;
  background: white;
  color: #c65367;
  border-radius: 8px;
  cursor: pointer;
}

.features {
  padding: 32px clamp(24px, 6vw, 76px);
}

.features h2 {
  text-align: center;
  font-family: var(--font-title-serif) !important;
  font-size: clamp(24px, 2.7vw, 30px);
  margin-bottom: 24px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 22px;
}

.feature-card {
  background: white;
  border: 1px solid #eaded8;
  border-radius: 14px;
  padding: 28px;
}

.icon {
  width: 56px;
  height: 56px;
  background: #f8e9e6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c65367;
  font-size: 24px;
  margin-bottom: 18px;
}

.feature-card h3 {
  margin-bottom: 12px;
}

.feature-card p {
  color: #756a66;
  line-height: 1.6;
  font-size: 14px;
}

.feature-link {
  display: inline-block;
  margin-top: 18px;
  color: #c65367;
  font-weight: 700;
  text-decoration: none;
}

.products {
  margin: 20px 76px 50px;
  padding: 30px;
  background: white;
  border: 1px solid #eaded8;
  border-radius: 16px;
  overflow: hidden;
}

.section-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 22px;
}

.view-all {
  color: #c65367;
  font-weight: 600;
  cursor: pointer;
}

.recommend-state {
  border: 1px dashed #eaded8;
  border-radius: 8px;
  background: #fffaf7;
  color: #7b6d68;
  font-weight: 800;
  padding: 42px 18px;
  text-align: center;
}

.recommend-state.error {
  color: #b14a5e;
}

.carousel-shell {
  position: relative;
}

.recommendation-carousel {
  display: flex;
  gap: 18px;
  overflow-x: auto;
  scroll-behavior: smooth;
  scroll-snap-type: x mandatory;
  padding: 4px 42px 18px;
  scrollbar-width: none;
}

.recommendation-carousel::-webkit-scrollbar {
  display: none;
}

.carousel-arrow {
  position: absolute;
  top: 50%;
  z-index: 2;
  display: grid;
  place-items: center;
  width: 36px;
  height: 52px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.94);
  color: #8b3a4a;
  font-size: 30px;
  font-weight: 700;
  transform: translateY(-50%);
  cursor: pointer;
}

.carousel-arrow.left {
  left: 0;
}

.carousel-arrow.right {
  right: 0;
}

.recommend-card {
  position: relative;
  flex: 0 0 clamp(220px, 24vw, 270px);
  min-height: 344px;
  border: 0;
  border-radius: 14px;
  background: transparent;
  cursor: pointer;
  scroll-snap-align: start;
  perspective: 1100px;
  outline: none;
}

.recommend-card:focus-visible .flip-card-inner {
  box-shadow: 0 0 0 3px rgba(198, 83, 103, 0.24), 0 18px 32px rgba(88, 55, 45, 0.11);
}

.flip-card-inner {
  position: relative;
  width: 100%;
  min-height: 344px;
  border-radius: 14px;
  transform-style: preserve-3d;
  transition: transform 0.55s cubic-bezier(0.2, 0.72, 0.24, 1);
}

.recommend-card:hover .flip-card-inner {
  transform: rotateY(180deg);
}

.flip-card-face {
  position: absolute;
  inset: 0;
  display: grid;
  grid-template-rows: 132px minmax(0, 1fr);
  min-height: 344px;
  border: 1px solid #eaded8;
  border-radius: 14px;
  background: #fff;
  overflow: hidden;
  backface-visibility: hidden;
  box-shadow: 0 10px 24px rgba(88, 55, 45, 0.04);
}

.flip-card-front {
  z-index: 2;
}

.flip-card-back {
  grid-template-rows: auto;
  align-content: start;
  gap: 12px;
  padding: 22px;
  background:
    radial-gradient(circle at 18% 12%, rgba(255, 240, 241, 0.95), transparent 34%),
    linear-gradient(135deg, #fffaf7, #fff0f1);
  transform: rotateY(180deg);
}

.back-label {
  width: fit-content;
  padding: 5px 9px;
  border-radius: 999px;
  background: rgba(198, 83, 103, 0.1);
  color: #9b4658;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.flip-card-back h4 {
  margin: 0;
  color: #332b28;
  font-size: 17px;
  line-height: 1.4;
}

.flip-card-back p {
  margin: 0;
  color: #5f5754;
  font-size: 13px;
  line-height: 1.65;
}

.usage-tip {
  padding: 10px 11px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.68);
}

.back-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.back-meta span {
  padding: 6px 9px;
  border-radius: 999px;
  background: #fff;
  color: #8b3a4a;
  font-size: 11px;
  font-weight: 900;
}

.flip-card-back button {
  margin-top: auto;
  min-height: 40px;
  border: 0;
  border-radius: 9px;
  background: #c65367;
  color: #fff;
  font-weight: 900;
  cursor: pointer;
}

.heart {
  position: absolute;
  right: 12px;
  top: 12px;
  z-index: 3;
  width: 36px;
  height: 36px;
  border: 1px solid rgba(234, 222, 216, 0.88);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: #9c908b;
  font-size: 23px;
  font-weight: 900;
  line-height: 1;
  display: grid;
  place-items: center;
  cursor: pointer;
  box-shadow: 0 8px 16px rgba(88, 55, 45, 0.08);
}

.heart.active {
  color: #c65367;
}

.heart:disabled {
  cursor: wait;
  opacity: 0.58;
}

.product-img {
  position: relative;
  min-height: 132px;
  background: linear-gradient(135deg, #f8e1df, #fff6f1);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-img img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 8px;
  background: #fff;
}

.product-art {
  width: 100%;
  height: 100%;
}

.product-img.lip .product-art {
  background:
    radial-gradient(ellipse at 42% 62%, rgba(190, 74, 94, 0.45) 0 26%, transparent 27%),
    linear-gradient(90deg, transparent 42%, #b6576b 43% 55%, transparent 56%),
    linear-gradient(135deg, #fff1eb, #f8d4d9);
}

.product-img.eye .product-art {
  background:
    radial-gradient(circle at 30% 45%, #c5a3b8 0 15%, transparent 16%),
    radial-gradient(circle at 55% 45%, #d8bfd8 0 15%, transparent 16%),
    radial-gradient(circle at 42% 70%, #b8a2c8 0 15%, transparent 16%),
    linear-gradient(135deg, #fff1eb, #f3e5f2);
}

.product-img.cheek .product-art {
  background:
    radial-gradient(circle at 50% 55%, rgba(240, 145, 165, 0.62) 0 30%, transparent 31%),
    radial-gradient(circle at 50% 55%, rgba(255, 255, 255, 0.54) 0 12%, transparent 13%),
    linear-gradient(135deg, #fff1eb, #f8dce2);
}

.product-img.base .product-art {
  background:
    radial-gradient(circle at 50% 48%, #f2d2c4 0 26%, transparent 27%),
    linear-gradient(90deg, transparent 35%, #e8c3b0 36% 63%, transparent 64%),
    linear-gradient(135deg, #fff7f1, #f3ded3);
}

.card-copy {
  display: grid;
  align-content: start;
  gap: 8px;
  min-width: 0;
  padding: 16px;
}

.card-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #8b7b76;
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
}

.card-topline strong {
  border-radius: 999px;
  background: #f5ece8;
  color: #6c4d45;
  padding: 4px 8px;
  font-size: 11px;
}

.card-topline .best {
  background: #fff0f1;
  color: #c65367;
}

.card-topline .good {
  background: #f0f7e8;
  color: #668e24;
}

.card-topline .mix {
  background: #fff5e6;
  color: #9b6124;
}

.card-topline .caution,
.card-topline .avoid {
  background: #fff3df;
  color: #9c5b15;
}

.back-meta .best {
  background: #fff0f1;
  color: #c65367;
}

.back-meta .good {
  background: #f0f7e8;
  color: #668e24;
}

.back-meta .mix,
.back-meta .caution {
  background: #fff5e6;
  color: #9b6124;
}

.brand {
  color: #777;
  font-size: 13px;
  margin: 0;
}

.recommend-card h4 {
  margin: 6px 0 0;
  font-size: 15px;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.option-name {
  margin: 0;
  color: #8b3a4a;
  font-size: 12px;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reason {
  font-size: 13px;
  color: #6b5f5b;
  line-height: 1.55;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (hover: none), (max-width: 720px) {
  .recommend-card,
  .flip-card-inner {
    min-height: 0;
  }

  .recommend-card:hover .flip-card-inner {
    transform: none;
  }

  .flip-card-inner {
    display: grid;
    gap: 10px;
    transform-style: flat;
  }

  .flip-card-face {
    position: relative;
    min-height: 0;
    backface-visibility: visible;
  }

  .flip-card-back {
    transform: none;
    padding: 16px;
  }
}

@media (max-width: 900px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-buttons {
    flex-wrap: wrap;
  }

  .hero-buttons button {
    width: min(100%, 280px);
  }

  .hero-image {
    width: 100%;
    flex-wrap: wrap;
  }

  .model-card,
  .summary-card {
    width: min(100%, 330px);
  }

  .feature-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .products {
    margin-inline: clamp(16px, 5vw, 40px);
  }

  .recommend-card {
    flex-basis: min(78vw, 270px);
  }
}

@media (max-width: 560px) {
  .hero-text h1 {
    font-size: clamp(28px, 9vw, 34px);
  }

  .hero-buttons,
  .hero-buttons button,
  .hero-image {
    width: 100%;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }

  .products {
    margin: 16px;
    padding: 18px;
  }

  .recommendation-carousel {
    padding-inline: 38px;
  }
}

.hero-makeover {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.hero-makeover::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(255, 250, 247, 0.02) 0%, rgba(255, 244, 241, 0.52) 100%),
    radial-gradient(circle at 50% 20%, rgba(255, 255, 255, 0.18), transparent 44%);
  pointer-events: none;
}

.hero-makeover__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
  display: block;
}

.hero-makeover__label {
  position: absolute;
  top: 22px;
  left: 22px;
  z-index: 2;
  padding: 8px 13px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: #c65367;
  font-size: 12px;
  font-weight: 900;
  box-shadow: 0 10px 22px rgba(90, 50, 40, 0.1);
  backdrop-filter: blur(8px);
}

.makeover-fade-enter-active,
.makeover-fade-leave-active {
  transition: opacity 0.45s ease, transform 0.45s ease;
}

.makeover-fade-enter-from,
.makeover-fade-leave-to {
  opacity: 0;
  transform: scale(1.02);
}
</style>
