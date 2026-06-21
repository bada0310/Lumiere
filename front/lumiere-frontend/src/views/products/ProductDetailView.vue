<template>
  <div class="page">
    <main class="detail-page">
      <button class="back-btn" type="button" @click="router.back()">
        ← 추천 제품 목록으로 돌아가기
      </button>

      <section class="title-section">
        <h1>제품 상세 분석 ✨</h1>
        <p>{{ pageSubtitle }}</p>
      </section>

      <section v-if="isLoading" class="loading-box">
        제품 정보를 불러오는 중입니다...
      </section>

      <template v-else-if="product">
        <section class="top-card">
          <div class="product-visual">
            <div class="product-image-box">
              <img
                v-if="product.imageUrl"
                :src="product.imageUrl"
                :alt="product.name"
                class="real-product-image"
              />

              <div
                v-else
                class="fallback-product-image product-image"
                :class="product.imageClass"
              ></div>
            </div>
          </div>

          <div class="product-info">
            <p class="brand">{{ product.brand }}</p>
            <h2>{{ product.name }}</h2>
            <h3>{{ product.option }}</h3>
            <p class="meta">
              {{ product.categoryLabel }}
              <span></span>
              {{ product.toneLabel || '여름 쿨 라이트' }} 추천
            </p>

            <div class="summary-chips">
              <span :style="{ '--chip-color': product.hex }">대표색 {{ product.hex }}</span>
              <span>{{ product.temperatureLabel }}</span>
              <span>{{ brightnessLabel }}</span>
              <span>{{ saturationLabel }}</span>
            </div>
          </div>

          <div class="match-score">
            <div class="score-head">
              <p>{{ scoreTitle }}</p>
              <span>{{ scoreBasisLabel }}</span>
            </div>

            <div class="score-ring" :style="{ '--score-degree': `${product.score * 3.6}deg` }">
              <strong>{{ product.score }}<span>%</span></strong>
            </div>

            <h4>{{ matchMessage }}</h4>

            <div class="score-meter">
              <div :style="{ width: product.score + '%' }"></div>
            </div>

            <p>{{ scoreDescription }}</p>
          </div>

          <div class="radar-box">
            <div class="legend">
              <span class="my"></span> {{ comparisonSubjectLabel }}
              <span class="product-line"></span> 제품 색상
            </div>

            <div class="radar">
              <div class="radar-shape reference-shape" :style="referenceRadarStyle"></div>
              <div class="radar-shape product-shape" :style="productRadarStyle"></div>
              <span class="label top">명도 {{ radarScores.brightness }}</span>
              <span class="label right">채도 {{ radarScores.chroma }}</span>
              <span class="label bottom-right">쿨 {{ radarScores.coolness }}</span>
              <span class="label bottom">웜 {{ radarScores.warmth }}</span>
              <span class="label bottom-left">탁도 {{ radarScores.softness }}</span>
              <span class="label left">대비 {{ radarScores.contrast }}</span>
            </div>

            <p class="profile-notice">
              {{ profileNotice }}
            </p>
          </div>
        </section>

        <section class="color-chart-card">
          <div class="section-head">
            <h2>색상 프로필</h2>
            <p>상품 이미지에서 추출한 대표 색상을 사용자가 이해하기 쉬운 기준으로 정리했어요.</p>
          </div>

          <div class="color-profile-layout">
            <div class="color-main-box">
              <div class="big-swatch" :style="{ backgroundColor: product.hex }"></div>

              <div>
                <p class="color-label">대표 색상</p>
                <strong>{{ product.hex }}</strong>
                <span>RGB {{ product.rgbR }}, {{ product.rgbG }}, {{ product.rgbB }}</span>
              </div>
            </div>

            <div class="color-bars">
              <div
                class="color-bar-row"
                v-for="item in colorProfileItems"
                :key="item.name"
              >
                <div class="color-bar-head">
                  <strong>{{ item.name }}</strong>
                  <span>{{ item.valueLabel }}</span>
                </div>

                <div class="color-track">
                  <div
                    class="color-fill"
                    :style="{ width: item.value + '%', backgroundColor: item.color }"
                  ></div>
                </div>

                <p>{{ item.description }}</p>
              </div>
            </div>

            <aside class="tone-guide-box">
              <h3>{{ guideTitle }}</h3>
              <p>{{ personalColorGuide }}</p>

              <div class="tone-chip-list">
                <span>{{ product.temperatureLabel }}</span>
                <span>{{ brightnessLabel }}</span>
                <span>{{ saturationLabel }}</span>
                <span>{{ softnessLabel }}</span>
              </div>
            </aside>
          </div>
        </section>

        <section class="compare-card">
          <div class="section-head compact">
            <h2>상세 수치 비교</h2>
            <p>{{ compareSubtitle }}</p>
          </div>

          <div class="compare-layout">
            <div class="compare-table">
              <div class="table-head">
                <span>항목</span>
                <span>{{ comparisonColumnLabel }}</span>
                <span>제품 색상</span>
                <span>차이</span>
                <span>분석</span>
              </div>

              <div class="table-row" v-for="item in compareItems" :key="item.name">
                <div class="item-name">
                  <span>{{ item.icon }}</span>
                  <strong>{{ item.name }}</strong>
                </div>

                <div class="bar-cell">
                  <div class="bar">
                    <div class="fill mine" :style="{ width: item.mine + '%' }"></div>
                  </div>
                  <span>{{ item.mine }}</span>
                </div>

                <div class="bar-cell">
                  <div class="bar">
                    <div class="fill product-fill" :style="{ width: item.product + '%' }"></div>
                  </div>
                  <span>{{ item.product }}</span>
                </div>

                <div class="diff">{{ item.diff }}</div>
                <div class="analysis">{{ item.analysis }} <span></span></div>
              </div>

              <p class="compare-note">
                ⓘ {{ compareNote }}
              </p>
            </div>

            <aside class="reason-box">
              <h3>추천 이유</h3>

              <div class="reason-item" v-for="reason in recommendReasons" :key="reason">
                <span>✓</span>
                <p>{{ reason }}</p>
              </div>
            </aside>
          </div>
        </section>

        <section class="similar-section">
          <div class="section-head">
            <h2>유사 제품 추천</h2>
            <p>{{ product.option || product.texture }} 옵션과 비슷한 분위기의 제품들이에요.</p>
          </div>

          <div class="similar-grid">
            <article
              class="similar-card"
              v-for="item in similarProducts"
              :key="item.id"
              @click="goDetail(item)"
            >
              <div class="similar-image-box">
                <img
                  v-if="item.imageUrl"
                  :src="item.imageUrl"
                  :alt="item.name"
                  class="similar-real-img"
                />

                <div
                  v-else
                  class="similar-img"
                  :class="item.imageClass"
                ></div>
              </div>

              <div>
                <p class="brand">{{ item.brand }}</p>
                <h3>{{ item.name }}</h3>
                <p>{{ item.option }}</p>

                <div class="dots">
                  <span
                    v-for="color in item.colors"
                    :key="color"
                    :style="{ backgroundColor: color }"
                  ></span>
                </div>

                <strong>적합도 {{ item.score }}%</strong>
              </div>
            </article>
          </div>
        </section>

        <section class="bottom-grid">
          <div class="purchase-box">
            <h2>구매하기</h2>
            <p>아래 링크를 통해 제품을 구매할 수 있어요.</p>

            <button class="olive" type="button" @click="openProductUrl">
              상품 구매 링크 <span>네이버 쇼핑/스토어 바로가기 ↗</span>
            </button>

            <button class="brand-link" type="button" @click="openProductUrl">
              {{ product.brand }} <span>상품 페이지 바로가기 ↗</span>
            </button>
          </div>

          <div class="review-box">
            <h2>커뮤니티 후기</h2>
            <p>실제 사용자들의 후기를 확인해보세요.</p>

            <div class="review" v-for="review in reviews" :key="review.name">
              <div class="avatar"></div>

              <div>
                <strong>{{ review.name }}</strong>
                <span>★★★★★</span>
                <p>{{ review.text }}</p>
              </div>

              <small>{{ review.date }}</small>
            </div>

            <button class="more-review" type="button">
              후기 더 보기 ›
            </button>
          </div>

          <aside class="action-box">
            <button
              class="main-btn"
              type="button"
              :class="{ liked: isLiked }"
              @click="toggleLike"
            >
              {{ isLiked ? '♥ 찜 완료' : '♡ 찜하기' }}
            </button>

            <button class="outline-btn" type="button" @click="router.push('/mypage')">
              ▱ 마이페이지에서 보기
            </button>

            <button class="outline-btn" type="button" @click="router.push('/product-analysis')">
              ✨ 다른 제품 분석하기 →
            </button>

            <div class="tip-box">
              <h3>💡 Lumière TIP</h3>
              <p>
                유사도가 높을수록 자연스럽고<br />
                조화로운 메이크업 연출이 가능해요!
              </p>
              <div class="palette-icon"></div>
            </div>
          </aside>
        </section>

        <p class="notice">
          🛡️ 분석 결과는 참고용이며, 개인의 피부 톤과 조명 환경에 따라 다를 수 있습니다.
        </p>
      </template>

      <section v-else class="loading-box">
        제품 정보를 찾을 수 없어요.
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const isLoading = ref(true)
const product = ref(null)
const allProducts = ref([])
const isLiked = ref(false)

const DEFAULT_REFERENCE_METRICS = {
  brightness: 65,
  saturation: 30,
  coolness: 85,
  warmth: 15,
  softness: 18,
  contrast: 35,
}

const getStoredSkinMetrics = () => {
  const candidates = ['skinColorMetrics', 'userColorMetrics', 'personalColorMetrics']

  for (const key of candidates) {
    const storedText = localStorage.getItem(key)

    if (!storedText) continue

    try {
      const parsed = JSON.parse(storedText)

      return {
        brightness: clampScore(parsed.brightness, DEFAULT_REFERENCE_METRICS.brightness),
        saturation: clampScore(parsed.saturation, DEFAULT_REFERENCE_METRICS.saturation),
        coolness: clampScore(parsed.coolness, DEFAULT_REFERENCE_METRICS.coolness),
        warmth: clampScore(parsed.warmth, DEFAULT_REFERENCE_METRICS.warmth),
        softness: clampScore(parsed.softness, DEFAULT_REFERENCE_METRICS.softness),
        contrast: clampScore(parsed.contrast, DEFAULT_REFERENCE_METRICS.contrast),
      }
    } catch (error) {
      console.error('피부 분석 데이터를 읽는 데 실패했습니다:', error)
    }
  }

  return null
}

const userSkinMetrics = ref(null)

const categoryTabs = [
  {
    key: 'lip',
    serverKey: 'LIP',
    label: '립',
    keywords: ['립', '립틴트', '틴트', '립스틱', 'lip'],
  },
  {
    key: 'eye',
    serverKey: 'EYE',
    label: '아이',
    keywords: ['아이', '섀도우', '쉐도우', '아이섀도우', '아이팔레트', '마스카라', '아이라이너', 'eye'],
  },
  {
    key: 'cheek',
    serverKey: 'CHEEK',
    label: '치크',
    keywords: ['치크', '블러셔', '블러쉬', '볼터치', 'cheek', 'blush'],
  },
  {
    key: 'base',
    serverKey: 'BASE',
    label: '베이스',
    keywords: ['베이스', '쿠션', '파운데이션', '컨실러', 'base', 'foundation', 'cushion'],
  },
  {
    key: 'lens',
    serverKey: 'LENS',
    label: '렌즈',
    keywords: ['렌즈', '컬러렌즈', 'lens'],
  },
]

const normalizeText = (value) => {
  return String(value || '').toLowerCase().replace(/\s/g, '')
}

const toNumber = (value, fallback = 0) => {
  const numberValue = Number(value)
  return Number.isNaN(numberValue) ? fallback : numberValue
}

const clampScore = (value, fallback = 90) => {
  const numberValue = Number(value)

  if (Number.isNaN(numberValue)) {
    return fallback
  }

  return Math.max(0, Math.min(100, Math.round(numberValue)))
}

const findCategoryKey = (item) => {
  const serverCategory = String(item.category || '').toUpperCase()

  const matchedByServerKey = categoryTabs.find((category) => {
    return category.serverKey === serverCategory
  })

  if (matchedByServerKey) {
    return matchedByServerKey.key
  }

  const text = normalizeText(`
    ${item.category || ''}
    ${item.category_name || ''}
    ${item.product_category || ''}
    ${item.name || ''}
    ${item.product_name || ''}
    ${item.option_name || ''}
    ${item.texture || ''}
  `)

  const matchedCategory = categoryTabs.find((category) => {
    return category.keywords.some((keyword) => text.includes(normalizeText(keyword)))
  })

  return matchedCategory?.key || 'lip'
}

const getCategoryLabel = (categoryKey) => {
  return categoryTabs.find((category) => category.key === categoryKey)?.label || '립'
}

const getDefaultColors = (categoryKey) => {
  const colorMap = {
    lip: ['#c45b75', '#de91a2', '#e8b4c0', '#c9b0c9'],
    eye: ['#c5a3b8', '#d8bfd8', '#b8a2c8', '#e8d7e8'],
    cheek: ['#f0a9b7', '#f4c2c9', '#e7a2b0', '#d9b7c8'],
    base: ['#f1d4c6', '#f5dfd2', '#ead0c3', '#f7e7dc'],
    lens: ['#8f8fa8', '#a8a6bd', '#c1bfcc', '#d8d6df'],
  }

  return colorMap[categoryKey] || colorMap.lip
}

const getToneLabel = (toneTag) => {
  const labels = {
    SPRING_LIGHT: '봄 웜 라이트',
    SPRING_BRIGHT: '봄 웜 브라이트',
    SUMMER_LIGHT: '여름 쿨 라이트',
    SUMMER_MUTE: '여름 쿨 뮤트',
    AUTUMN_MUTE: '가을 웜 뮤트',
    AUTUMN_DEEP: '가을 웜 딥',
    WINTER_BRIGHT: '겨울 쿨 브라이트',
    WINTER_DEEP: '겨울 쿨 딥',
  }

  return labels[toneTag] || ''
}

const getFinishLabel = (finish) => {
  const labels = {
    MATTE: '매트',
    GLOSSY: '글로시',
    VELVET: '벨벳',
    SHIMMER: '쉬머',
    NATURAL: '내추럴',
    UNKNOWN: '',
  }

  return labels[finish] || ''
}

const getTemperatureAxis = (coolness, warmth) => {
  return clampScore((coolness - warmth + 100) / 2, 50)
}

const getTemperatureLabel = (coolness, warmth) => {
  const diff = coolness - warmth
  const mainScore = Math.max(coolness, warmth)

  if (diff >= 20) return `쿨 ${mainScore}`
  if (diff <= -20) return `웜 ${mainScore}`
  return '뉴트럴'
}

const getMetric = (item, key, fallback) => {
  return toNumber(item[key], fallback)
}

const getMetricAnalysis = (metricName, diff, productValue) => {
  const absDiff = Math.abs(diff)
  const reference = comparisonMetricsWithAxis.value

  if (metricName === '명도') {
    if (absDiff <= 10) return '밝기 차이가 작아 자연스러워요.'
    if (diff > 0) return '제품이 내 기준보다 더 밝은 편이에요.'
    return '제품이 내 기준보다 조금 딥한 편이에요.'
  }

  if (metricName === '채도') {
    if (absDiff <= 10) return '채도 차이가 크지 않아 무난해요.'
    if (productValue > reference.saturation) return '제품 색상이 더 선명한 편이에요.'
    return '제품 색상이 더 차분한 편이에요.'
  }

  if (metricName === '쿨 방향') {
    if (absDiff <= 12) return '쿨 방향성이 비슷해요.'
    if (productValue > reference.coolness) return '제품이 더 쿨하게 분류됐어요.'
    return '제품의 쿨 방향성이 더 낮아요.'
  }

  if (metricName === '웜 방향') {
    if (absDiff <= 12) return '웜 방향성이 비슷해요.'
    if (productValue > reference.warmth) return '제품이 더 웜하게 분류됐어요.'
    return '제품의 웜 방향성이 더 낮아요.'
  }

  if (metricName === '탁도') {
    if (absDiff <= 15) return '부드러움/탁도 차이가 적당해요.'
    if (diff > 0) return '제품이 더 부드럽고 뮤트한 편이에요.'
    return '제품이 더 맑고 선명한 편이에요.'
  }

  if (metricName === '대비') {
    if (absDiff <= 15) return '대비감이 부담스럽지 않아요.'
    if (diff > 0) return '제품 대비감이 더 강한 편이에요.'
    return '제품 대비감이 더 낮은 편이에요.'
  }

  return '수치 차이를 기준으로 비교했어요.'
}

const formatDiff = (diff) => {
  return diff > 0 ? `+${diff}` : String(diff)
}

const normalizeProduct = (item, index = 0) => {
  const categoryKey = findCategoryKey(item)
  const defaultColors = getDefaultColors(categoryKey)
  const hex = item.hexCode || item.hex_code || item.hex || item.rep_hex_code || item.color_hex || item.colors?.[0] || defaultColors[0]

  const imageUrl =
    item.imageUrl ||
    item.image_url ||
    item.image ||
    item.thumbnail ||
    item.thumbnail_url ||
    item.originalImageUrl ||
    ''

  const score = clampScore(item.score ?? item.match_score ?? item.similarity_score ?? 90, 90)

  const brightness = getMetric(item, 'brightness', 65)
  const saturation = getMetric(item, 'saturation', 30)
  const coolness = getMetric(item, 'coolness', 85)
  const warmth = getMetric(item, 'warmth', 15)
  const depth = getMetric(item, 'depth', 20)
  const softness = getMetric(item, 'softness', 18)
  const contrast = getMetric(item, 'contrast', 35)
  const temperatureAxis = getTemperatureAxis(coolness, warmth)
  const temperatureLabel = getTemperatureLabel(coolness, warmth)

  return {
    id: item.id || item.product_option_id || item.option_id || index + 1,
    brand: item.brand || item.product_brand || '브랜드 미상',
    name: item.name || item.product_name || '추천 상품',
    option: item.option || item.option_name || item.color_name || item.texture || '',
    categoryKey,
    categoryLabel: item.categoryLabel || getCategoryLabel(categoryKey),
    score,
    popularityScore: Number(item.popularityScore || item.popularity_score || item.review_count || 0),

    hex,
    hexCode: hex,
    hex_code: hex,
    colors: Array.isArray(item.colors) && item.colors.length
      ? item.colors
      : [hex, ...defaultColors.slice(1)],

    imageUrl,
    originalImageUrl: imageUrl,
    productUrl: item.productUrl || item.product_url || item.link || '',

    imageClass: item.imageClass || `${categoryKey}${(index % 5) + 1}`,
    texture: item.texture || '',
    finish: item.finish || '',
    finishLabel: item.finishLabel || getFinishLabel(item.finish),
    toneTag: item.toneTag || item.tone_tag || '',
    toneLabel: item.toneLabel || getToneLabel(item.toneTag || item.tone_tag),
    colorFamily: item.colorFamily || item.color_family || '',

    rgbR: toNumber(item.rgbR ?? item.rgb_r),
    rgbG: toNumber(item.rgbG ?? item.rgb_g),
    rgbB: toNumber(item.rgbB ?? item.rgb_b),

    brightness,
    saturation,
    coolness,
    warmth,
    temperatureAxis,
    temperatureLabel,
    depth,
    softness,
    contrast,

    desc:
      item.desc ||
      item.match_reason ||
      item.reason ||
      item.description ||
      `${getCategoryLabel(categoryKey)} 카테고리의 추천 옵션입니다.`,

    liked: Boolean(item.liked),
    raw: item.raw || item,
  }
}

const loadProducts = async () => {
  isLoading.value = true

  try {
    const response = await axios.get('http://127.0.0.1:8000/api/products/')

    const data = Array.isArray(response.data)
      ? response.data
      : response.data.results || response.data.products || []

    allProducts.value = data.map((item, index) => normalizeProduct(item, index))
  } catch (error) {
    console.error('상세 상품 데이터 불러오기 실패:', error)
    allProducts.value = []
  } finally {
    setCurrentProduct()
    isLoading.value = false
  }
}

const setCurrentProduct = () => {
  const currentId = String(route.params.id || '')
  const storedText = localStorage.getItem('selectedProductOption')

  const fetchedProduct =
    allProducts.value.find((item) => String(item.id) === currentId) ||
    allProducts.value[0] ||
    null

  if (fetchedProduct) {
    product.value = fetchedProduct
    isLiked.value = Boolean(fetchedProduct.liked)
    localStorage.setItem('selectedProductOption', JSON.stringify(fetchedProduct))
    return
  }

  if (storedText) {
    try {
      const storedProduct = normalizeProduct(JSON.parse(storedText))

      if (!currentId || String(storedProduct.id) === currentId) {
        product.value = storedProduct
        isLiked.value = Boolean(storedProduct.liked)
        return
      }
    } catch (error) {
      console.error('저장된 상품 정보를 읽는 데 실패했습니다:', error)
    }
  }

  product.value = null
  isLiked.value = Boolean(product.value?.liked)
}

const matchMessage = computed(() => {
  if (!product.value) return ''

  if (product.value.score >= 90) return '무난하게 어울려요!'
  if (product.value.score >= 80) return '추천 후보로 좋아요!'
  if (product.value.score >= 70) return '부분적으로 어울려요!'
  return '참고용으로 추천드려요!'
})

const hasSkinProfile = computed(() => {
  return Boolean(userSkinMetrics.value)
})

const comparisonMetrics = computed(() => {
  return userSkinMetrics.value || DEFAULT_REFERENCE_METRICS
})

const comparisonMetricsWithAxis = computed(() => {
  return {
    ...comparisonMetrics.value,
    temperatureAxis: getTemperatureAxis(
      comparisonMetrics.value.coolness,
      comparisonMetrics.value.warmth,
    ),
  }
})

const comparisonSubjectLabel = computed(() => {
  return hasSkinProfile.value ? '나의 피부 데이터' : '여름 쿨 라이트 기준'
})

const comparisonColumnLabel = computed(() => {
  return hasSkinProfile.value ? '내 피부' : '추천 기준'
})

const pageSubtitle = computed(() => {
  return hasSkinProfile.value
    ? '내 피부 데이터와 제품 색상을 비교하여 상세 분석 결과를 보여드려요.'
    : '아직 피부 분석 전이라 여름 쿨 라이트 기준으로 제품 색상을 먼저 보여드려요.'
})

const scoreTitle = computed(() => {
  return hasSkinProfile.value ? '내 피부 적합도' : '추천 기준 적합도'
})

const scoreBasisLabel = computed(() => {
  return hasSkinProfile.value ? '피부 분석 기반' : '기준 톤 기반'
})

const scoreDescription = computed(() => {
  if (!product.value) return ''

  if (hasSkinProfile.value) {
    return `${comparisonSubjectLabel.value}와 제품 대표색 ${product.value.hex}의 명도, 채도, 쿨/웜 방향성을 비교했어요.`
  }

  return `피부 분석 전에는 ${comparisonSubjectLabel.value}과 제품 대표색 ${product.value.hex}를 기준으로 적합도를 보여줘요.`
})

const profileNotice = computed(() => {
  return hasSkinProfile.value
    ? '내 피부 분석값과 제품 색상값을 같은 축으로 비교하고 있어요.'
    : '피부 사진을 분석하면 이 그래프가 내 피부 데이터 기준으로 바뀌어요.'
})

const guideTitle = computed(() => {
  return hasSkinProfile.value ? '나에게 어울리는 이유' : '추천 기준에서 보는 포인트'
})

const compareSubtitle = computed(() => {
  return hasSkinProfile.value
    ? '내 피부 데이터와 제품 대표색의 차이를 항목별로 비교했어요.'
    : '피부 분석 전에는 여름 쿨 라이트 기준값과 제품 대표색을 비교해요.'
})

const compareNote = computed(() => {
  return hasSkinProfile.value
    ? '차이 값이 작을수록 내 피부톤과 제품 색상이 자연스럽게 어울립니다.'
    : '피부 분석을 완료하면 추천 기준 대신 내 피부 데이터와 비교됩니다.'
})

const radarScores = computed(() => {
  if (!product.value) {
    return {
      brightness: 0,
      chroma: 0,
      coolness: 0,
      warmth: 0,
      softness: 0,
      contrast: 0,
    }
  }

  return {
    brightness: product.value.brightness,
    chroma: product.value.saturation,
    coolness: product.value.coolness,
    warmth: product.value.warmth,
    softness: product.value.softness,
    contrast: product.value.contrast,
  }
})

const radarPolygon = (metrics) => {
  const values = [
    metrics.brightness,
    metrics.saturation,
    metrics.coolness,
    metrics.warmth,
    metrics.softness,
    metrics.contrast,
  ]
  const angles = [-90, -30, 30, 90, 150, 210]

  return values
    .map((value, index) => {
      const radius = clampScore(value, 0) * 0.42
      const angle = (angles[index] * Math.PI) / 180
      const x = 50 + Math.cos(angle) * radius
      const y = 50 + Math.sin(angle) * radius

      return `${x.toFixed(1)}% ${y.toFixed(1)}%`
    })
    .join(', ')
}

const referenceRadarStyle = computed(() => {
  return {
    clipPath: `polygon(${radarPolygon(comparisonMetrics.value)})`,
  }
})

const productRadarStyle = computed(() => {
  if (!product.value) {
    return {
      clipPath: 'polygon(50% 50%, 50% 50%, 50% 50%)',
    }
  }

  return {
    clipPath: `polygon(${radarPolygon(product.value)})`,
  }
})

const brightnessLabel = computed(() => {
  if (!product.value) return ''
  if (product.value.brightness >= 72) return '고명도'
  if (product.value.brightness <= 42) return '저명도'
  return '중명도'
})

const saturationLabel = computed(() => {
  if (!product.value) return ''
  if (product.value.saturation >= 60) return '고채도'
  if (product.value.saturation <= 40) return '저채도'
  return '중채도'
})

const softnessLabel = computed(() => {
  if (!product.value) return ''
  if (product.value.softness >= 55) return '뮤트한 색감'
  if (product.value.softness <= 25) return '맑은 색감'
  return '부드러운 색감'
})

const colorProfileItems = computed(() => {
  if (!product.value) return []

  return [
    {
      name: '명도',
      value: product.value.brightness,
      valueLabel: `${product.value.brightness} / 100`,
      color: '#d35f72',
      description: '값이 높을수록 밝고 화사한 색상이에요.',
    },
    {
      name: '채도',
      value: product.value.saturation,
      valueLabel: `${product.value.saturation} / 100`,
      color: '#c65367',
      description: '값이 높을수록 선명하고 생기 있는 색상이에요.',
    },
    {
      name: '쿨 방향',
      value: product.value.coolness,
      valueLabel: `${product.value.coolness} / 100`,
      color: '#8e8fd6',
      description: '값이 높을수록 핑크, 로즈, 모브 계열에 가까워요.',
    },
    {
      name: '웜 방향',
      value: product.value.warmth,
      valueLabel: `${product.value.warmth} / 100`,
      color: '#dd8a54',
      description: '값이 높을수록 코랄, 피치, 베이지 계열에 가까워요.',
    },
    {
      name: '탁도',
      value: product.value.softness,
      valueLabel: `${product.value.softness} / 100`,
      color: '#a98b98',
      description: '값이 높을수록 회색기와 차분함이 있는 색상이에요.',
    },
  ]
})

const personalColorGuide = computed(() => {
  if (!product.value) return ''

  const brightnessText = product.value.brightness >= 72
    ? '밝은 색감'
    : product.value.brightness <= 42
      ? '딥한 색감'
      : '중간 밝기의 색감'

  const chromaText = product.value.saturation <= 40
    ? '채도가 낮아 부드럽고'
    : product.value.saturation >= 60
      ? '채도가 높아 생기 있고'
      : '채도가 적당해 무난하고'

  const temperatureText = product.value.coolness >= product.value.warmth
    ? '쿨 방향성이 더 강한 편이에요.'
    : '웜 방향성이 더 강한 편이에요.'

  if (hasSkinProfile.value) {
    return `${brightnessText}이고 ${chromaText}, ${temperatureText} 내 피부 데이터와의 차이를 아래 표에서 확인할 수 있어요.`
  }

  return `${brightnessText}이고 ${chromaText}, ${temperatureText} 피부 분석 전에는 여름 쿨 라이트 기준과 먼저 비교해볼 수 있어요.`
})

const compareItems = computed(() => {
  if (!product.value) return []
  const reference = comparisonMetricsWithAxis.value

  const rows = [
    {
      icon: '☀️',
      name: '명도',
      mine: reference.brightness,
      product: product.value.brightness,
    },
    {
      icon: '💧',
      name: '채도',
      mine: reference.saturation,
      product: product.value.saturation,
    },
    {
      icon: '❄️',
      name: '쿨 방향',
      mine: reference.coolness,
      product: product.value.coolness,
    },
    {
      icon: '🔥',
      name: '웜 방향',
      mine: reference.warmth,
      product: product.value.warmth,
    },
    {
      icon: '☁️',
      name: '탁도',
      mine: reference.softness,
      product: product.value.softness,
    },
    {
      icon: '◐',
      name: '대비',
      mine: reference.contrast,
      product: product.value.contrast,
    },
  ]

  return rows.map((row) => {
    const diff = Math.round(row.product - row.mine)

    return {
      ...row,
      diff: formatDiff(diff),
      analysis: getMetricAnalysis(row.name, diff, row.product),
    }
  })
})

const recommendReasons = computed(() => {
  if (!product.value) return []

  const reasons = [
    `${product.value.categoryLabel} 카테고리에서 ${product.value.toneLabel || '여름 쿨 라이트'} 기준에 가까운 옵션이에요.`,
    `대표 색상은 ${product.value.hex}이고, 명도 ${product.value.brightness}, 채도 ${product.value.saturation}, 쿨 ${product.value.coolness}/웜 ${product.value.warmth}로 분석됐어요.`,
    product.value.desc,
  ]

  return reasons.filter(Boolean)
})

const getColorDistance = (a, b) => {
  return (
    Math.abs(a.brightness - b.brightness) * 0.22 +
    Math.abs(a.saturation - b.saturation) * 0.18 +
    Math.abs(a.temperatureAxis - b.temperatureAxis) * 0.30 +
    Math.abs(a.softness - b.softness) * 0.12 +
    Math.abs(a.contrast - b.contrast) * 0.10
  )
}

const similarProducts = computed(() => {
  if (!product.value) return []

  return allProducts.value
    .filter((item) => item.id !== product.value.id)
    .filter((item) => item.categoryKey === product.value.categoryKey)
    .sort((a, b) => getColorDistance(a, product.value) - getColorDistance(b, product.value))
    .slice(0, 4)
})

const reviews = [
  {
    name: '라이트여쿨',
    text: '여쿨라에게 찰떡인 컬러예요! 자연스럽고 데일리로 좋아요.',
    date: '2026.06.18',
  },
  {
    name: '쿨톤수집가',
    text: '색이 과하지 않아서 얼굴이 맑아 보여요.',
    date: '2026.06.16',
  },
  {
    name: 'sujin_beauty',
    text: '추천 적합도가 높게 나온 이유가 납득되는 색감이에요.',
    date: '2026.06.14',
  },
]

const goDetail = (item) => {
  localStorage.setItem('selectedProductOption', JSON.stringify(item))

  router.push({
    name: 'product-detail',
    params: { id: item.id },
  })
}

const toggleLike = () => {
  isLiked.value = !isLiked.value

  if (product.value) {
    product.value.liked = isLiked.value
    localStorage.setItem('selectedProductOption', JSON.stringify(product.value))
  }
}

const openProductUrl = () => {
  if (product.value?.productUrl) {
    window.open(product.value.productUrl, '_blank', 'noopener,noreferrer')
    return
  }

  alert('상품 구매 링크가 아직 등록되지 않았어요.')
}

watch(
  () => route.params.id,
  () => {
    if (allProducts.value.length > 0) {
      setCurrentProduct()
    }
  }
)

onMounted(() => {
  userSkinMetrics.value = getStoredSkinMetrics()
  loadProducts()
})
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.page {
  min-height: 100vh;
  background: #fffaf7;
  color: #2d2524;
}

.detail-page {
  padding: 28px 64px 52px;
  background:
    radial-gradient(circle at 50% 0%, rgba(255, 233, 225, 0.9), transparent 38%),
    linear-gradient(180deg, #fffaf7 0%, #fbf4f1 100%);
}

.back-btn {
  border: none;
  background: transparent;
  color: #5f5754;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  margin-bottom: 10px;
}

.title-section {
  text-align: center;
  margin-bottom: 28px;
}

.title-section h1 {
  font-family: Georgia, serif;
  font-size: 32px;
  margin-bottom: 12px;
}

.title-section p {
  color: #5f5754;
}

.loading-box {
  max-width: 1240px;
  margin: 0 auto;
  padding: 80px;
  text-align: center;
  border: 1px solid #eaded8;
  border-radius: 16px;
  background: white;
  color: #5f5754;
}

.top-card,
.color-chart-card,
.compare-card,
.similar-section,
.purchase-box,
.review-box,
.action-box {
  max-width: 1240px;
  margin: 0 auto;
  border: 1px solid #eaded8;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 14px 40px rgba(88, 55, 45, 0.05);
}

.top-card {
  padding: 42px 36px;
  display: grid;
  grid-template-columns: 270px 250px 220px 1fr;
  gap: 34px;
  align-items: center;
}

.product-image {
  height: 260px;
  border-radius: 14px;
}

.lip1,
.lip2,
.lip3,
.lip4,
.lip5 {
  background:
    radial-gradient(ellipse at 35% 58%, rgba(180, 80, 100, 0.42) 0 30%, transparent 31%),
    linear-gradient(90deg, transparent 42%, #a75a70 43% 56%, transparent 57%),
    linear-gradient(135deg, transparent 0 58%, rgba(190, 74, 94, 0.5) 59% 68%, transparent 69%),
    linear-gradient(135deg, #fff3ef, #f4d8d1);
}

.eye1,
.eye2,
.eye3,
.eye4,
.eye5 {
  background:
    radial-gradient(circle at 30% 45%, #c5a3b8 0 16%, transparent 17%),
    radial-gradient(circle at 55% 45%, #d8bfd8 0 16%, transparent 17%),
    radial-gradient(circle at 40% 70%, #b8a2c8 0 16%, transparent 17%),
    linear-gradient(135deg, #fff1eb, #f3e5f2);
}

.cheek1,
.cheek2,
.cheek3,
.cheek4,
.cheek5 {
  background:
    radial-gradient(circle at 50% 55%, rgba(240, 145, 165, 0.6) 0 30%, transparent 31%),
    radial-gradient(circle at 50% 55%, rgba(255, 255, 255, 0.5) 0 12%, transparent 13%),
    linear-gradient(135deg, #fff1eb, #f8dce2);
}

.base1,
.base2,
.base3,
.base4,
.base5 {
  background:
    radial-gradient(circle at 50% 48%, #f2d2c4 0 26%, transparent 27%),
    linear-gradient(90deg, transparent 35%, #e8c3b0 36% 63%, transparent 64%),
    linear-gradient(135deg, #fff7f1, #f3ded3);
}

.lens1,
.lens2,
.lens3,
.lens4,
.lens5 {
  background:
    radial-gradient(circle at 38% 50%, #9a9ab0 0 24%, #f6f3f6 25% 34%, transparent 35%),
    radial-gradient(circle at 62% 50%, #aaa7bd 0 24%, #f6f3f6 25% 34%, transparent 35%),
    linear-gradient(135deg, #fff1eb, #ebeaf2);
}

.brand {
  color: #5f5754;
  margin-bottom: 12px;
}

.product-info h2 {
  font-size: 30px;
  margin-bottom: 10px;
}

.product-info h3 {
  font-size: 24px;
  margin-bottom: 22px;
}

.meta {
  color: #7b706c;
}

.meta span {
  display: inline-block;
  width: 1px;
  height: 12px;
  background: #d8c8c2;
  margin: 0 12px;
}

.summary-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 26px;
}

.summary-chips span {
  min-height: 34px;
  padding: 8px 12px 8px 30px;
  border: 1px solid #eaded8;
  border-radius: 999px;
  background: #fff8f6;
  color: #5f5754;
  font-size: 12px;
  font-weight: 800;
  position: relative;
}

.summary-chips span::before {
  content: "";
  position: absolute;
  left: 11px;
  top: 50%;
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: var(--chip-color, #d35f72);
  transform: translateY(-50%);
}

.hex-box {
  margin-top: 32px;
  width: 190px;
  padding: 16px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fff4f3;
  display: flex;
  gap: 14px;
  align-items: center;
}

.hex-box span {
  width: 36px;
  height: 36px;
  border-radius: 50%;
}

.hex-box p {
  margin: 0;
  color: #6b625f;
}

.match-score {
  border-left: 1px solid #eaded8;
  padding-left: 34px;
}

.score-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.score-head p {
  margin: 0;
  font-weight: 900;
}

.score-head span {
  padding: 6px 10px;
  border-radius: 999px;
  background: #fff0f1;
  color: #c65367;
  font-size: 12px;
  font-weight: 900;
}

.score-ring {
  width: 132px;
  height: 132px;
  border-radius: 50%;
  background:
    radial-gradient(circle, white 0 57%, transparent 58%),
    conic-gradient(#c65367 var(--score-degree), #efe4e0 0);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.match-score strong {
  color: #c65367;
  font-size: 48px;
  font-family: Georgia, serif;
}

.match-score strong span {
  font-size: 24px;
}

.match-score h4 {
  color: #c65367;
  font-size: 18px;
}

.match-score p {
  color: #5f5754;
  line-height: 1.6;
}

.score-meter {
  height: 8px;
  border-radius: 999px;
  background: #efe4e0;
  overflow: hidden;
  margin: 12px 0;
}

.score-meter div {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #c65367, #df8b9a);
}

.legend {
  text-align: right;
  color: #5f5754;
  font-size: 13px;
  margin-bottom: 10px;
}

.legend span {
  display: inline-block;
  width: 34px;
  height: 2px;
  margin: 0 8px;
  vertical-align: middle;
}

.legend .my {
  background: #c65367;
}

.legend .product-line {
  background: repeating-linear-gradient(90deg, #777 0 6px, transparent 6px 10px);
}

.radar {
  width: 280px;
  height: 240px;
  margin: 0 auto;
  position: relative;
  background:
    radial-gradient(circle, transparent 20%, #eaded8 21%, transparent 22%),
    radial-gradient(circle, transparent 40%, #eaded8 41%, transparent 42%),
    radial-gradient(circle, transparent 60%, #eaded8 61%, transparent 62%),
    radial-gradient(circle, transparent 80%, #eaded8 81%, transparent 82%);
}

.radar-shape {
  position: absolute;
  inset: 18px 26px;
  transition: clip-path 0.25s ease;
}

.reference-shape {
  background: rgba(198, 83, 103, 0.18);
  border: 2px solid rgba(198, 83, 103, 0.55);
}

.product-shape {
  background: rgba(95, 87, 84, 0.12);
  border: 2px dashed rgba(95, 87, 84, 0.75);
}

.label {
  position: absolute;
  font-size: 13px;
  font-weight: 800;
  color: #5f5754;
}

.top {
  top: 0;
  left: 50%;
  transform: translateX(-50%);
}

.right {
  right: 0;
  top: 43%;
}

.bottom-right {
  right: 30px;
  bottom: 8px;
}

.bottom {
  left: 50%;
  bottom: 0;
  transform: translateX(-50%);
}

.bottom-left {
  left: 30px;
  bottom: 8px;
}

.left {
  left: 0;
  top: 43%;
}

.profile-notice {
  margin: 14px 0 0;
  padding: 12px 14px;
  border-radius: 10px;
  background: #fff8f6;
  color: #6b625f;
  font-size: 13px;
  line-height: 1.5;
}

.color-chart-card {
  margin-top: 18px;
  padding: 34px;
}

.color-profile-layout {
  display: grid;
  grid-template-columns: 260px 1fr 300px;
  gap: 28px;
  align-items: stretch;
}

.color-main-box {
  border: 1px solid #eaded8;
  border-radius: 12px;
  padding: 22px;
  background: #fff8f6;
  display: flex;
  gap: 18px;
  align-items: center;
}

.big-swatch {
  width: 86px;
  height: 86px;
  border-radius: 50%;
  border: 1px solid rgba(45, 37, 36, 0.1);
  box-shadow: inset 0 0 0 8px rgba(255, 255, 255, 0.32);
  flex: 0 0 auto;
}

.color-label {
  margin: 0 0 8px;
  color: #7b706c;
  font-size: 13px;
  font-weight: 800;
}

.color-main-box strong {
  display: block;
  font-size: 24px;
  margin-bottom: 8px;
}

.color-main-box span {
  color: #6b625f;
  font-size: 13px;
}

.color-bars {
  border: 1px solid #eaded8;
  border-radius: 12px;
  padding: 20px 22px;
  background: white;
}

.color-bar-row + .color-bar-row {
  margin-top: 18px;
}

.color-bar-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 8px;
}

.color-bar-head strong {
  font-size: 14px;
}

.color-bar-head span {
  color: #6b625f;
  font-size: 13px;
  font-weight: 800;
}

.color-track {
  height: 9px;
  border-radius: 999px;
  background: #efe4e0;
  overflow: hidden;
}

.color-fill {
  height: 100%;
  border-radius: inherit;
}

.color-bar-row p {
  margin: 7px 0 0;
  color: #6b625f;
  font-size: 13px;
  line-height: 1.45;
}

.tone-guide-box {
  border: 1px solid #eaded8;
  border-radius: 12px;
  padding: 22px;
  background: #fff8f6;
}

.tone-guide-box h3 {
  margin: 0 0 14px;
}

.tone-guide-box p {
  margin: 0;
  color: #5f5754;
  line-height: 1.7;
}

.tone-chip-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 18px;
}

.tone-chip-list span {
  padding: 8px 12px;
  border-radius: 999px;
  background: white;
  border: 1px solid #eaded8;
  color: #6b4b52;
  font-size: 12px;
  font-weight: 800;
}

.compare-card {
  margin-top: 18px;
  padding: 34px;
}

.compare-card h2 {
  margin-bottom: 24px;
}

.compare-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 28px;
}

.compare-table {
  border: 1px solid #eaded8;
  border-radius: 12px;
  overflow: hidden;
}

.table-head,
.table-row {
  display: grid;
  grid-template-columns: 1.1fr 1.35fr 1.35fr 0.5fr 1.2fr;
  align-items: center;
}

.table-head {
  background: #fff8f6;
  font-weight: 800;
  padding: 16px 18px;
  border-bottom: 1px solid #eaded8;
  font-size: 13px;
}

.table-row {
  padding: 16px 18px;
  border-bottom: 1px solid #eaded8;
}

.item-name {
  display: flex;
  gap: 12px;
  align-items: center;
}

.item-name span {
  font-size: 22px;
}

.bar-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar {
  width: 120px;
  height: 5px;
  background: #eee2df;
  border-radius: 999px;
}

.fill {
  height: 100%;
  border-radius: 999px;
}

.fill.mine {
  background: #c65367;
}

.fill.product-fill {
  background: #c8939e;
}

.diff {
  font-weight: 800;
}

.analysis {
  color: #5f5754;
  font-size: 13px;
}

.analysis span {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #d78d9a;
  margin-left: 8px;
}

.compare-note {
  text-align: center;
  color: #8e7e79;
  padding: 14px;
  margin: 0;
}

.reason-box {
  border: 1px solid #eaded8;
  border-radius: 12px;
  padding: 28px;
  background: #fffaf7;
}

.reason-box h3 {
  margin-bottom: 28px;
}

.reason-item {
  display: flex;
  gap: 16px;
  margin-bottom: 28px;
  line-height: 1.7;
}

.reason-item span {
  color: #2d2524;
  font-weight: 900;
}

.reason-item p {
  margin: 0;
  color: #5f5754;
}

.similar-section {
  margin-top: 18px;
  padding: 34px;
}

.section-head {
  display: flex;
  gap: 28px;
  align-items: center;
  margin-bottom: 24px;
}

.section-head p {
  color: #7b706c;
}

.section-head.compact {
  justify-content: space-between;
  align-items: flex-end;
}

.section-head.compact h2 {
  margin: 0;
}

.section-head.compact p {
  max-width: 560px;
  margin: 0;
  text-align: right;
  line-height: 1.55;
}

.similar-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 22px;
}

.similar-card {
  border: 1px solid #eaded8;
  border-radius: 12px;
  padding: 18px;
  display: flex;
  gap: 18px;
  background: white;
  cursor: pointer;
  transition: 0.2s;
}

.similar-card:hover {
  transform: translateY(-3px);
}

.similar-img {
  width: 80px;
  height: 100px;
  border-radius: 10px;
  flex-shrink: 0;
}

.similar-card h3 {
  font-size: 15px;
}

.similar-card p {
  color: #5f5754;
  margin: 4px 0;
}

.similar-card strong {
  color: #c65367;
  font-size: 18px;
}

.dots {
  display: flex;
  gap: 6px;
  margin: 12px 0;
}

.dots span {
  width: 14px;
  height: 14px;
  border-radius: 50%;
}

.bottom-grid {
  max-width: 1240px;
  margin: 18px auto 0;
  display: grid;
  grid-template-columns: 1fr 1.15fr 1fr;
  gap: 18px;
}

.purchase-box,
.review-box,
.action-box {
  margin: 0;
  padding: 30px;
}

.purchase-box p,
.review-box > p {
  color: #7b706c;
  margin-bottom: 28px;
}

.purchase-box button {
  width: 100%;
  height: 64px;
  border-radius: 9px;
  background: white;
  margin-bottom: 18px;
  font-size: 18px;
  font-weight: 900;
  cursor: pointer;
}

.purchase-box button span {
  float: right;
  color: #5f5754;
  font-size: 14px;
  font-weight: 400;
}

.olive {
  border: 1px solid #96c83d;
  color: #7cbd00;
}

.brand-link {
  border: 1px solid #d98c99;
  color: #c65367;
}

.review {
  display: grid;
  grid-template-columns: 42px 1fr 82px;
  gap: 12px;
  margin-bottom: 18px;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 50% 30%, #f6d6d1 0 25%, transparent 26%),
    radial-gradient(ellipse at 50% 48%, #5a352b 0 32%, transparent 33%),
    #f5dfd8;
}

.review span {
  color: #c65367;
  font-size: 12px;
  margin-left: 6px;
}

.review p {
  color: #5f5754;
  margin: 4px 0 0;
  line-height: 1.45;
}

.review small {
  color: #7b706c;
}

.more-review,
.main-btn,
.outline-btn {
  width: 100%;
  height: 58px;
  border-radius: 9px;
  font-weight: 800;
  font-size: 16px;
  cursor: pointer;
}

.more-review,
.outline-btn {
  background: white;
  border: 1px solid #d98c99;
  color: #c65367;
}

.action-box {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.main-btn {
  background: linear-gradient(135deg, #c65367, #d96f82);
  color: white;
  border: none;
}

.main-btn.liked {
  background: #a94155;
}

.tip-box {
  margin-top: 10px;
  padding: 22px;
  border: 1px solid #eaded8;
  border-radius: 12px;
  background: #fff8f6;
  position: relative;
}

.tip-box h3 {
  color: #c65367;
}

.tip-box p {
  color: #5f5754;
  line-height: 1.6;
}

.palette-icon {
  position: absolute;
  right: 18px;
  bottom: 18px;
  width: 62px;
  height: 78px;
  border-radius: 8px;
  background:
    linear-gradient(90deg, transparent 48%, rgba(255, 255, 255, 0.6) 50%),
    linear-gradient(0deg, transparent 48%, rgba(255, 255, 255, 0.6) 50%),
    linear-gradient(135deg, #f5b6c6, #d58298);
  background-size: 20px 20px, 20px 20px, 100% 100%;
  transform: rotate(12deg);
  opacity: 0.8;
}

.notice {
  text-align: center;
  color: #8e7e79;
  margin-top: 26px;
}

.product-image-box {
  width: 100%;
  height: 260px;
  border-radius: 14px;
  overflow: hidden;
  background: #fff1f3;
  display: flex;
  align-items: center;
  justify-content: center;
}

.real-product-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: white;
}

.fallback-product-image {
  width: 100%;
  height: 100%;
}

.similar-image-box {
  width: 80px;
  height: 100px;
  border-radius: 10px;
  overflow: hidden;
  background: #fff1f3;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.similar-real-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: white;
}

</style>
