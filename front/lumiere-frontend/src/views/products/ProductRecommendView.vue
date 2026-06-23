<template>
  <div class="page">
    <main class="recommend-page">
      <section class="hero">
        <div>
          <h1>색상 기준으로 추천 제품을 골라보세요</h1>
          <p>{{ heroDescription }}</p>
        </div>

        <div class="my-tone-card">
          <div>
            <p>{{ hasDiagnosisProfile ? 'AI 진단 기준' : '추천 기준' }}</p>
            <strong>{{ recommendationBasis.toneName }}</strong>
            <RouterLink to="/upload">
              {{ hasDiagnosisProfile ? '다시 진단하기 ›' : '피부 분석 후 맞춤 추천 보기 ›' }}
            </RouterLink>
          </div>
          <div class="profile"></div>
        </div>
      </section>

      <section v-if="!hasDiagnosisProfile" class="primary-missing-box">
        메인 퍼스널컬러가 설정되어 있지 않습니다. 진단 결과 목록에서 메인 결과를 선택해주세요.
      </section>

      <section class="category-tabs">
        <button
          v-for="category in visibleCategoryTabs"
          :key="category.key"
          type="button"
          :class="{ active: selectedCategory === category.key }"
          @click="selectCategory(category.key)"
        >
          {{ category.icon }} {{ category.label }}
        </button>
      </section>

      <section class="color-chart-section">
        <div class="chart-copy">
          <span>{{ hasDiagnosisProfile ? 'AI 추천 알고리즘' : '기준 톤 추천' }}</span>
          <h2>내 톤과 가까운 색상 분포</h2>
          <p>
            {{
              hasDiagnosisProfile
                ? '진단 결과의 명도와 채도, 쿨/웜 방향을 기준으로 선택한 브랜드의 색상 옵션을 모두 비교했어요.'
                : '아직 피부 분석 전이라 기본 기준 톤과 선택한 브랜드의 색상 옵션을 먼저 비교해요.'
            }}
          </p>

          <div class="chart-meta">
            <span>{{ chartProducts.length }}개 색상 옵션</span>
            <span>점 크기 = 채도</span>
          </div>
        </div>

        <div class="tone-chart" aria-label="추천 색상 분포 차트">
          <div class="axis axis-x"></div>
          <div class="axis axis-y"></div>
          <span class="axis-label axis-label--warm">Warm</span>
          <span class="axis-label axis-label--cool">Cool</span>
          <span class="axis-label axis-label--light">Light</span>
          <span class="axis-label axis-label--deep">Deep</span>

          <button
            v-for="point in chartProducts"
            :key="point.id"
            type="button"
            class="chart-dot"
            :title="`${point.brand} ${point.name} ${point.option} - 채도 ${point.saturation}`"
            :style="{
              left: `${point.chart.x}%`,
              bottom: `${point.chart.y}%`,
              width: `${point.chart.size}px`,
              height: `${point.chart.size}px`,
              backgroundColor: point.chart.color,
            }"
            @click="goDetail(point, point)"
          ></button>

          <div
            class="user-zone"
            :style="{
              left: `${recommendationBasisChart.x}%`,
              bottom: `${recommendationBasisChart.y}%`,
            }"
          >
            내 기준
          </div>
        </div>
      </section>

      <section class="brand-board" v-if="brandStats.length">
        <div class="brand-board-head">
          <div>
            <h2>브랜드</h2>
            <p>Total {{ brandTotalCount }}</p>
          </div>

          <button type="button" @click="clearBrands" :disabled="selectedBrands.length === 0">
            선택 초기화
          </button>
        </div>

        <div class="brand-check-grid">
          <label
            v-for="brand in visibleBrandStats"
            :key="brand.name"
            :class="{ active: selectedBrands.includes(brand.name) }"
          >
            <input
              type="checkbox"
              :checked="selectedBrands.includes(brand.name)"
              @change="toggleBrand(brand.name)"
            />
            <span>{{ brand.name }}</span>
            <small>{{ brand.count }}</small>
          </label>
        </div>

        <div class="brand-board-foot" v-if="brandStats.length > brandPanelLimit">
          <button type="button" @click="toggleBrandPanel">
            {{ isBrandPanelExpanded ? '접기' : `더보기 ${brandStats.length - brandPanelLimit}` }}
          </button>
        </div>
      </section>

      <section class="filter-row">
        <div class="filters">
          <button type="button" class="filter-title">필터</button>

          <button
            v-for="filter in filterOptions"
            :key="filter.key"
            type="button"
            :class="{ active: selectedFilters.includes(filter.key) }"
            @click="toggleFilter(filter.key)"
          >
            {{ filter.label }}
          </button>

          <button type="button" class="all-filter-btn" @click="openAllFilter">
            전체 필터 ⚙
          </button>
        </div>

        <div class="sort">
          <span>정렬</span>
          <select v-model="sortOption">
            <option value="scoreDesc">적합도 높은 순</option>
            <option value="scoreAsc">적합도 낮은 순</option>
            <option value="popularDesc">인기순</option>
          </select>
        </div>
      </section>

      <section class="info-row">
        <p>
          <span v-if="keyword">"{{ keyword }}" {{ selectedCategoryLabel }} 검색 결과 </span>
          총 {{ filteredProducts.length }}개의 제품 그룹
        </p>
        <p>ⓘ 브랜드를 선택하면 위 차트가 해당 브랜드의 전체 색상 옵션 분포로 바뀝니다.</p>
      </section>

      <section v-if="isLoading" class="empty-box">
        <h3>상품을 불러오는 중이에요.</h3>
        <p>백엔드에서 추천 상품 데이터를 가져오고 있어요.</p>
      </section>

      <section v-else-if="filteredProducts.length" class="product-grid">
        <article
          class="product-card"
          v-for="(product, index) in filteredProducts"
          :key="product.id"
          @click="goDetail(product)"
        >
          <div class="rank" :class="{ top: index + 1 <= 3 }">
            {{ index + 1 }}
          </div>

          <button
            type="button"
            class="heart"
            :class="{ active: isProductLiked(product) }"
            @click.stop="toggleLike(product)"
          >
            {{ isProductLiked(product) ? '♥' : '♡' }}
          </button>

          <div class="product-img">
            <img
              v-if="product.imageUrl"
              :src="product.imageUrl"
              :alt="product.name"
              class="real-product-img"
            />

            <div
              v-else
              class="fallback-product-visual"
              :class="product.imageClass"
            ></div>
          </div>

          <p class="brand">{{ product.brand }}</p>
          <h3>{{ product.name }}</h3>
          <p class="option">
            색상 옵션 {{ product.options.length }}개
            <span v-if="product.option"> · 대표 {{ product.option }}</span>
          </p>

          <div class="color-dots">
            <span
              v-for="color in product.colors"
              :key="color"
              :style="{ backgroundColor: color }"
            ></span>
          </div>

          <div class="metric-summary">
            <span>{{ product.brightnessLabel }}</span>
            <span>{{ product.saturationLabel }}</span>
            <span>{{ product.temperatureLabel }}</span>
          </div>

          <p class="score">
            {{ product.bestScore || product.score }}<span>% 대표 옵션</span>
          </p>
        </article>
      </section>

      <section v-else class="empty-box">
        <h3>조건에 맞는 추천 옵션이 없어요.</h3>
        <p>필터를 줄이거나 다른 카테고리를 눌러보세요.</p>
        <button type="button" @click="resetAllFilters">필터 전체 초기화</button>
      </section>

      <section class="bottom-bar">
        <div class="standard">
          <strong>맞춤 추천 기준</strong>
          <span>{{ recommendationBasis.toneName }}</span>
          <span>{{ recommendationBasisLabels.brightness }}</span>
          <span>{{ recommendationBasisLabels.saturation }}</span>
          <span>{{ recommendationBasisLabels.direction }}</span>
        </div>

        <button class="outline-btn" type="button" @click="resetAllFilters">
          필터 초기화 ↻
        </button>

        <button class="main-btn" type="button" @click="toggleLikedMode">
          {{ likedOnly ? '전체 제품 보기' : '♡ 찜한 제품 보기' }}
        </button>

        <button class="outline-btn" type="button" @click="compareItems">
          추천된 아이템 비교하기
        </button>
      </section>

      <section
        v-if="isFilterModalOpen"
        class="filter-modal-backdrop"
        @click.self="closeAllFilter"
      >
        <aside class="filter-modal">
          <div class="filter-modal-header">
            <div>
              <h2>전체 필터</h2>
              <p>원하는 조건을 선택해서 추천 옵션을 좁혀보세요.</p>
            </div>

            <button type="button" class="modal-close" @click="closeAllFilter">
              ×
            </button>
          </div>

          <div class="filter-modal-body">
            <div class="filter-group">
              <h3>카테고리</h3>

              <div class="filter-chip-grid">
                <button
                  v-for="category in categoryTabs"
                  :key="category.key"
                  type="button"
                  :class="{ active: draftCategory === category.key }"
                  @click="draftCategory = category.key"
                >
                  {{ category.icon }} {{ category.label }}
                </button>
              </div>
            </div>

            <div class="filter-group">
              <h3>색감 / 톤</h3>

              <div class="filter-chip-grid">
                <button
                  v-for="filter in toneFilters"
                  :key="filter.key"
                  type="button"
                  :class="{ active: draftFilters.includes(filter.key) }"
                  @click="toggleDraftFilter(filter.key)"
                >
                  {{ filter.label }}
                </button>
              </div>
            </div>

            <div class="filter-group">
              <h3>제형</h3>

              <div class="filter-chip-grid">
                <button
                  v-for="filter in textureFilters"
                  :key="filter.key"
                  type="button"
                  :class="{ active: draftFilters.includes(filter.key) }"
                  @click="toggleDraftFilter(filter.key)"
                >
                  {{ filter.label }}
                </button>
              </div>
            </div>

            <div class="filter-group">
              <h3>정렬</h3>

              <div class="filter-chip-grid">
                <button
                  type="button"
                  :class="{ active: draftSortOption === 'scoreDesc' }"
                  @click="draftSortOption = 'scoreDesc'"
                >
                  적합도 높은 순
                </button>

                <button
                  type="button"
                  :class="{ active: draftSortOption === 'scoreAsc' }"
                  @click="draftSortOption = 'scoreAsc'"
                >
                  적합도 낮은 순
                </button>

                <button
                  type="button"
                  :class="{ active: draftSortOption === 'popularDesc' }"
                  @click="draftSortOption = 'popularDesc'"
                >
                  인기순
                </button>
              </div>
            </div>
          </div>

          <div class="filter-modal-footer">
            <button type="button" class="modal-reset-btn" @click="resetDraftFilters">
              초기화
            </button>

            <button type="button" class="modal-apply-btn" @click="applyAllFilter">
              {{ previewCount }}개 상품 보기
            </button>
          </div>
        </aside>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getLatestDiagnosis } from '@/services/diagnosisApi'
import { getLikedProductOptions, toggleLikedProductOption } from '@/services/engagementApi'
import { getProducts } from '@/services/productApi'
import {
  getChartPoint,
  getMetricLabels,
  clearDiagnosisColorProfile,
  hasSavedUserColorProfile,
  readUserColorProfile,
  saveDiagnosisColorProfile,
} from '@/utils/colorRecommendationHelpers'

const router = useRouter()
const route = useRoute()

const products = ref([])
const productGroups = computed(() => products.value)
const selectedCategory = ref('lip')
const selectedBrands = ref([])
const selectedFilters = ref([])
const sortOption = ref('scoreDesc')
const likedOnly = ref(false)
const likedOptionKeys = ref(new Set())
const isFilterModalOpen = ref(false)
const draftCategory = ref('lip')
const draftFilters = ref([])
const draftSortOption = ref('scoreDesc')
const isLoading = ref(false)
const keyword = computed(() => String(route.query.keyword || '').trim())
const userColorProfile = ref(readUserColorProfile())
const hasDiagnosisProfile = ref(hasSavedUserColorProfile())
const brandPanelLimit = 15
const isBrandPanelExpanded = ref(false)

const allCategoryTab = {
  key: 'all',
  serverKey: '',
  label: '전체',
  icon: '✨',
  keywords: [],
}

const categoryTabs = [
  {
    key: 'lip',
    serverKey: 'LIP',
    label: '립',
    icon: '💄',
    keywords: ['립', '립틴트', '틴트', '립스틱', 'lip'],
  },
  {
    key: 'eye',
    serverKey: 'EYE',
    label: '아이',
    icon: '👁️',
    keywords: ['아이', '섀도우', '쉐도우', '아이섀도우', '아이팔레트', '마스카라', '아이라이너', 'eye'],
  },
  {
    key: 'cheek',
    serverKey: 'CHEEK',
    label: '치크',
    icon: '😊',
    keywords: ['치크', '블러셔', '블러쉬', '볼터치', 'cheek', 'blush'],
  },
  {
    key: 'base',
    serverKey: 'BASE',
    label: '베이스',
    icon: '🧴',
    keywords: ['베이스', '쿠션', '파운데이션', '컨실러', 'base', 'foundation', 'cushion'],
  },
]

const filterOptions = [
  { key: 'mlbb', label: 'MLBB', keywords: ['mlbb', '엠엘비비', '모브', '로즈', '누드'] },
  { key: 'nude', label: '누디', keywords: ['누디', 'nude', '베이지', 'beige'] },
  { key: 'matte', label: '매트', keywords: ['매트', 'matte', '벨벳', '블러', 'VELVET', 'MATTE'] },
  { key: 'glossy', label: '글로시', keywords: ['글로시', 'glossy', '글로우', '촉촉', '워터', 'GLOSSY'] },
  { key: 'cool', label: '쿨 계열', keywords: ['쿨톤', '여름쿨', '겨울쿨', '쿨', 'cool', '라벤더', '모브', '핑크', '로즈', 'SUMMER', 'WINTER'] },
  { key: 'warm', label: '웜 계열', keywords: ['웜톤', '봄웜', '가을웜', '웜', 'warm', '코랄', '피치', '브라운', '베이지', 'SPRING', 'AUTUMN'] },
  { key: 'lowChroma', label: '저채도', keywords: ['저채도', '차분', '뮤트', 'soft', 'mauve', 'MUTE'] },
  { key: 'highBrightness', label: '고명도', keywords: ['고명도', '라이트', '밝음', '맑은', 'light', 'LIGHT'] },
]

const toneFilters = computed(() => {
  return filterOptions.filter((filter) => {
    return ['mlbb', 'nude', 'cool', 'warm', 'lowChroma', 'highBrightness'].includes(filter.key)
  })
})

const textureFilters = computed(() => {
  return filterOptions.filter((filter) => {
    return ['matte', 'glossy'].includes(filter.key)
  })
})

const selectedCategoryLabel = computed(() => {
  if (selectedCategory.value === 'all') {
    return '전체'
  }

  return categoryTabs.find((item) => item.key === selectedCategory.value)?.label || '립'
})

const visibleCategoryTabs = computed(() => {
  return keyword.value ? [allCategoryTab, ...categoryTabs] : categoryTabs
})

const heroDescription = computed(() => {
  if (keyword.value) {
    return selectedCategory.value === 'all'
      ? `"${keyword.value}"와 관련된 전체 추천 옵션을 보여드려요.`
      : `"${keyword.value}" 검색 결과 중 ${selectedCategoryLabel.value} 카테고리 옵션을 보여드려요.`
  }

  return `${selectedCategoryLabel.value} 카테고리에서 ${recommendationBasis.value.toneName} 기준에 가까운 옵션을 먼저 보여드려요.`
})

const recommendationBasis = computed(() => userColorProfile.value)
const recommendationBasisLabels = computed(() => getMetricLabels(recommendationBasis.value))
const recommendationBasisChart = computed(() => getChartPoint(recommendationBasis.value))

const chartProducts = computed(() => {
  const options = filteredProducts.value.flatMap((product) => {
    return product.options.map((option) => ({
      ...option,
      productId: product.id,
      product_id: product.id,
      parentId: product.id,
      productName: product.name,
      chart: getChartPoint(option),
    }))
  })

  const uniqueOptions = new Map()
  options.forEach((option) => {
    uniqueOptions.set(String(option.id), option)
  })

  const clusterIndexes = new Map()

  return [...uniqueOptions.values()].map((option) => {
    const basePoint = getChartPoint(option)
    const clusterKey = `${Math.round(basePoint.x / 3) * 3}-${Math.round(basePoint.y / 3) * 3}`
    const clusterIndex = clusterIndexes.get(clusterKey) || 0
    clusterIndexes.set(clusterKey, clusterIndex + 1)

    const angle = clusterIndex * 2.399963
    const radius = clusterIndex === 0 ? 0 : 2.4 + Math.floor(clusterIndex / 6) * 1.2
    const chart = {
      ...basePoint,
      x: Math.min(98, Math.max(2, basePoint.x + Math.cos(angle) * radius)),
      y: Math.min(98, Math.max(2, basePoint.y + Math.sin(angle) * radius)),
    }

    return {
      ...option,
      chart,
    }
  })
})

const brandStats = computed(() => {
  const counts = new Map()

  productGroups.value
    .filter((product) => {
      return selectedCategory.value === 'all' || product.categoryKey === selectedCategory.value
    })
    .forEach((product) => {
      if (!product.brand) return
      counts.set(product.brand, (counts.get(product.brand) || 0) + 1)
    })

  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => {
      if (b.count !== a.count) return b.count - a.count
      return a.name.localeCompare(b.name, 'ko')
    })
})

const visibleBrandStats = computed(() => {
  return isBrandPanelExpanded.value
    ? brandStats.value
    : brandStats.value.slice(0, brandPanelLimit)
})

const brandTotalCount = computed(() => {
  return brandStats.value.reduce((sum, brand) => sum + brand.count, 0)
})

const filteredProducts = computed(() => {
  let result = [...productGroups.value]

  if (!keyword.value || selectedCategory.value !== 'all') {
    result = result.filter((product) => product.categoryKey === selectedCategory.value)
  }

  if (likedOnly.value) {
    result = result.filter((product) => isProductLiked(product))
  }

  if (selectedBrands.value.length > 0) {
    result = result.filter((product) => selectedBrands.value.includes(product.brand))
  }

  if (keyword.value) {
    const searchText = normalizeText(keyword.value)

    result = result.filter((product) => {
      return normalizeText(`
        ${product.brand}
        ${product.name}
        ${product.option}
        ${product.categoryLabel}
        ${product.colorFamily}
        ${product.tags.join(' ')}
      `).includes(searchText)
    })
  }

  if (selectedFilters.value.length > 0) {
    result = result.filter((product) => {
      return selectedFilters.value.every((filterKey) => product.filterKeys.includes(filterKey))
    })
  }

  if (sortOption.value === 'scoreDesc') {
    result.sort((a, b) => b.score - a.score)
  }

  if (sortOption.value === 'scoreAsc') {
    result.sort((a, b) => a.score - b.score)
  }

  if (sortOption.value === 'popularDesc') {
    result.sort((a, b) => b.popularityScore - a.popularityScore)
  }

  return result
})

const normalizeText = (value) => {
  return String(value || '').toLowerCase().replace(/\s/g, '')
}

const isLensProduct = (item) => {
  const category = String(item.category || item.product_category || '').toUpperCase()
  if (category === 'LENS') return true

  const text = normalizeText(`
    ${item.category || ''}
    ${item.category_name || ''}
    ${item.product_category || ''}
    ${item.name || ''}
    ${item.product_name || ''}
    ${item.option_name || ''}
    ${item.description || ''}
  `)

  return ['렌즈', '컬러렌즈', '원데이', 'lens'].some((keyword) => text.includes(normalizeText(keyword)))
}

const toNumber = (value, fallback = 0) => {
  const numberValue = Number(value)
  return Number.isNaN(numberValue) ? fallback : numberValue
}

const clampScore = (value) => {
  const numberValue = Number(value)

  if (Number.isNaN(numberValue)) {
    return 90
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
    ${item.description || ''}
  `)

  const matchedCategory = categoryTabs.find((category) => {
    return category.keywords.some((keyword) => text.includes(normalizeText(keyword)))
  })

  return matchedCategory?.key || 'lip'
}

const getDefaultColors = (categoryKey) => {
  const colorMap = {
    lip: ['#c45b75', '#de91a2', '#e8b4c0', '#c9b0c9'],
    eye: ['#c5a3b8', '#d8bfd8', '#b8a2c8', '#e8d7e8'],
    cheek: ['#f0a9b7', '#f4c2c9', '#e7a2b0', '#d9b7c8'],
    base: ['#f1d4c6', '#f5dfd2', '#ead0c3', '#f7e7dc'],
  }

  return colorMap[categoryKey] || colorMap.lip
}

const getFinishLabel = (finish) => {
  const labels = {
    MATTE: '매트',
    GLOSSY: '글로시',
    VELVET: '벨벳',
    SHIMMER: '쉬머',
    NATURAL: '내추럴',
  }

  return labels[finish] || ''
}

const getToneLabel = (toneTag) => {
  const labels = {
    SPRING_LIGHT: '봄웜 라이트',
    SPRING_BRIGHT: '봄웜 브라이트',
    SUMMER_LIGHT: '여름쿨 라이트',
    SUMMER_MUTE: '여름쿨 뮤트',
    AUTUMN_MUTE: '가을웜 뮤트',
    AUTUMN_DEEP: '가을웜 딥',
    WINTER_BRIGHT: '겨울쿨 브라이트',
    WINTER_DEEP: '겨울쿨 딥',
  }

  return labels[toneTag] || ''
}

const makeMetricTags = (metrics, item) => {
  const tags = ['추천']

  if (metrics.coolness >= metrics.warmth) {
    tags.push('쿨 계열')
  } else {
    tags.push('웜 계열')
  }

  if (metrics.brightness >= 70) {
    tags.push('고명도')
  }

  if (metrics.saturation <= 40) {
    tags.push('저채도')
  }

  if (metrics.saturation >= 60) {
    tags.push('고채도')
  }

  const finishLabel = getFinishLabel(item.finish)
  if (finishLabel) {
    tags.push(finishLabel)
  }

  const toneLabel = getToneLabel(item.tone_tag)
  if (toneLabel) {
    tags.push(toneLabel)
  }

  if (item.texture) {
    tags.push(item.texture)
  }

  return tags
}

const getBrightnessLabel = (brightness) => {
  if (brightness >= 72) return '고명도'
  if (brightness <= 42) return '저명도'
  return '중명도'
}

const getSaturationLabel = (saturation) => {
  if (saturation >= 60) return '고채도'
  if (saturation <= 40) return '저채도'
  return '중채도'
}

const getTemperatureLabel = (coolness, warmth) => {
  const diff = coolness - warmth
  const mainScore = Math.max(coolness, warmth)

  if (diff >= 20) return `쿨 ${mainScore}`
  if (diff <= -20) return `웜 ${mainScore}`
  return '뉴트럴'
}

const getFilterKeys = (text) => {
  const searchText = normalizeText(text)

  return filterOptions
    .filter((filter) => {
      return filter.keywords.some((keyword) => searchText.includes(normalizeText(keyword)))
    })
    .map((filter) => filter.key)
}

const getMetricFilterKeys = (metrics) => {
  const keys = []

  if (metrics.coolness >= metrics.warmth) {
    keys.push('cool')
  } else {
    keys.push('warm')
  }

  if (metrics.brightness >= 70) {
    keys.push('highBrightness')
  }

  if (metrics.saturation <= 40) {
    keys.push('lowChroma')
  }

  return keys
}

const normalizeProduct = (item, index) => {
  const categoryKey = findCategoryKey(item)
  const categoryLabel = categoryTabs.find((category) => category.key === categoryKey)?.label || '립'
  const brand = item.brand || '브랜드 미상'
  const name = item.name || item.product_name || '추천 상품'
  const apiOptions = Array.isArray(item.options) ? item.options : []
  const normalizedOptions = apiOptions.map((option, optionIndex) => {
    return normalizeProductOption(item, option, optionIndex, categoryKey, categoryLabel)
  })
  const bestOption = item.best_option || apiOptions[0] || {}
  const representative =
    normalizedOptions.find((option) => String(option.id) === String(bestOption.id)) ||
    normalizedOptions[0] ||
    null
  const representativeMetrics = representative || {
    brightness: 65,
    saturation: 30,
    coolness: 50,
    warmth: 50,
    depth: 35,
    softness: 50,
    contrast: 30,
  }
  const colors = [...new Set(normalizedOptions.map((option) => option.hex).filter(Boolean))].slice(0, 8)
  const tags = [
    item.category,
    item.texture,
    item.finish,
    representative?.toneTag,
    representative?.colorFamily,
    ...makeMetricTags(representativeMetrics, item),
  ]
    .filter(Boolean)
    .filter((tag, tagIndex, arr) => arr.indexOf(tag) === tagIndex)
    .slice(0, 6)
  const desc = item.description || `${categoryLabel} 카테고리의 추천 상품입니다.`
  const filterText = `
    ${brand}
    ${name}
    ${representative?.option || ''}
    ${categoryLabel}
    ${item.texture || ''}
    ${item.finish || ''}
    ${representative?.colorFamily || ''}
    ${desc}
    ${tags.join(' ')}
  `

  return {
    id: item.id,
    productId: item.id,
    product_id: item.id,
    parentId: item.id,
    brand,
    name,
    option: representative?.option || '',
    categoryKey,
    categoryLabel,
    score: representative?.score || 0,
    bestScore: representative?.score || 0,
    popularityScore: Number(item.review_count || item.popularity_score || 0),
    liked: false,
    imageUrl:
      representative?.imageUrl ||
      item.representative_image_url ||
      item.image ||
      item.image_url ||
      '',
    originalImageUrl: item.representative_image_url || item.image || item.image_url || '',
    productUrl: representative?.productUrl || item.product_url || '',
    hexCode: representative?.hexCode || colors[0] || getDefaultColors(categoryKey)[0],
    hex_code: representative?.hex_code || colors[0] || getDefaultColors(categoryKey)[0],
    hex: representative?.hex || colors[0] || getDefaultColors(categoryKey)[0],
    colors: colors.length ? colors : getDefaultColors(categoryKey),
    ...representativeMetrics,
    toneTag: representative?.toneTag || '',
    toneLabel: getToneLabel(representative?.toneTag),
    texture: item.texture || '',
    finish: item.finish || '',
    finishLabel: getFinishLabel(item.finish),
    colorFamily: representative?.colorFamily || '',
    brightnessLabel: getBrightnessLabel(representativeMetrics.brightness),
    saturationLabel: getSaturationLabel(representativeMetrics.saturation),
    temperatureLabel: getTemperatureLabel(representativeMetrics.coolness, representativeMetrics.warmth),
    imageClass: `${categoryKey}${(index % 5) + 1}`,
    desc,
    tags,
    filterKeys: [...new Set([...getFilterKeys(filterText), ...getMetricFilterKeys(representativeMetrics)])],
    minPrice: item.min_price,
    maxPrice: item.max_price,
    representative,
    options: normalizedOptions,
    raw: item,
  }
}

const normalizeProductOption = (product, option, optionIndex, categoryKey, categoryLabel) => {
  const offer = option.representative_offer || option.offers?.[0] || {}
  const label = [option.option_no, option.option_name].filter(Boolean).join(' ') || '기본 옵션'
  const metrics = {
    rgbR: toNumber(option.rgb_r),
    rgbG: toNumber(option.rgb_g),
    rgbB: toNumber(option.rgb_b),
    brightness: toNumber(option.brightness, 65),
    saturation: toNumber(option.saturation, 30),
    coolness: toNumber(option.coolness, 50),
    warmth: toNumber(option.warmth, 50),
    depth: toNumber(option.depth, 35),
    softness: toNumber(option.softness, 50),
    contrast: toNumber(option.contrast, 30),
  }
  const hexCode = option.hex_code || option.hex || getDefaultColors(categoryKey)[optionIndex % getDefaultColors(categoryKey).length]
  const score = clampScore(option.match_score ?? 0)

  return {
    id: option.id,
    optionId: option.id,
    productId: product.id,
    product_id: product.id,
    parentId: product.id,
    brand: product.brand,
    name: product.name,
    option: label,
    option_no: option.option_no,
    option_name: option.option_name,
    categoryKey,
    categoryLabel,
    score,
    match_score: score,
    grade: option.grade,
    reason: option.reason,
    imageUrl: option.image_url || product.representative_image_url || product.image || product.image_url || '',
    productUrl: offer.product_url || product.product_url || '',
    hexCode,
    hex_code: hexCode,
    hex: hexCode,
    colors: [hexCode],
    ...metrics,
    toneTag: option.analyzed_tone_tag || '',
    toneLabel: getToneLabel(option.analyzed_tone_tag),
    texture: product.texture || '',
    finish: product.finish || '',
    finishLabel: getFinishLabel(product.finish),
    colorFamily: option.color_family || '',
    brightnessLabel: getBrightnessLabel(metrics.brightness),
    saturationLabel: getSaturationLabel(metrics.saturation),
    temperatureLabel: getTemperatureLabel(metrics.coolness, metrics.warmth),
    tags: makeMetricTags(metrics, option),
    raw: option,
  }
}

const fetchProducts = async () => {
  isLoading.value = true

  try {
    const response = await getProducts({
      tone_key: userColorProfile.value.toneTag,
      second_tone_key: userColorProfile.value.secondToneTag || undefined,
      q: keyword.value || undefined,
    })
    const data = Array.isArray(response)
      ? response
      : response.results || response.products || []

    products.value = data
      .filter((item) => !isLensProduct(item))
      .map((item, index) => normalizeProduct(item, index))

    console.log('백엔드 상품 데이터:', products.value)
  } catch (error) {
    console.error('상품 데이터 불러오기 실패:', error)
    products.value = []
  } finally {
    isLoading.value = false
  }
}

const syncLatestDiagnosisProfile = async () => {
  if (!localStorage.getItem('access_token')) {
    clearDiagnosisColorProfile()
    userColorProfile.value = readUserColorProfile()
    hasDiagnosisProfile.value = false
    return
  }

  try {
    const latestDiagnosis = await getLatestDiagnosis()
    if (!latestDiagnosis) {
      clearDiagnosisColorProfile()
      userColorProfile.value = readUserColorProfile()
      hasDiagnosisProfile.value = false
      return
    }

    userColorProfile.value = saveDiagnosisColorProfile(latestDiagnosis)
    hasDiagnosisProfile.value = true
  } catch (error) {
    console.warn('최신 진단 피부 데이터를 불러오지 못했어요:', error)
  }
}

const selectCategory = (categoryKey) => {
  selectedCategory.value = categoryKey
  selectedBrands.value = []
  isBrandPanelExpanded.value = false
  likedOnly.value = false
}

const toggleFilter = (filterKey) => {
  likedOnly.value = false

  if (selectedFilters.value.includes(filterKey)) {
    selectedFilters.value = selectedFilters.value.filter((key) => key !== filterKey)
  } else {
    selectedFilters.value.push(filterKey)
  }
}

const resetAllFilters = () => {
  selectedCategory.value = keyword.value ? 'all' : 'lip'
  selectedBrands.value = []
  selectedFilters.value = []
  sortOption.value = 'scoreDesc'
  likedOnly.value = false
  isBrandPanelExpanded.value = false
}

const toggleBrand = (brand) => {
  likedOnly.value = false

  if (selectedBrands.value.includes(brand)) {
    selectedBrands.value = selectedBrands.value.filter((item) => item !== brand)
  } else {
    selectedBrands.value = [...selectedBrands.value, brand]
  }
}

const clearBrands = () => {
  selectedBrands.value = []
}

const toggleBrandPanel = () => {
  isBrandPanelExpanded.value = !isBrandPanelExpanded.value
}

const openAllFilter = () => {
  draftCategory.value = selectedCategory.value
  draftFilters.value = [...selectedFilters.value]
  draftSortOption.value = sortOption.value
  isFilterModalOpen.value = true
}

const closeAllFilter = () => {
  isFilterModalOpen.value = false
}

const toggleDraftFilter = (filterKey) => {
  if (draftFilters.value.includes(filterKey)) {
    draftFilters.value = draftFilters.value.filter((key) => key !== filterKey)
  } else {
    draftFilters.value.push(filterKey)
  }
}

const resetDraftFilters = () => {
  draftCategory.value = 'lip'
  draftFilters.value = []
  draftSortOption.value = 'scoreDesc'
}

const applyAllFilter = () => {
  selectedCategory.value = draftCategory.value
  selectedFilters.value = [...draftFilters.value]
  sortOption.value = draftSortOption.value
  likedOnly.value = false
  isFilterModalOpen.value = false
}

const previewCount = computed(() => {
  let result = [...productGroups.value]

  if (draftCategory.value !== 'all') {
    result = result.filter((product) => product.categoryKey === draftCategory.value)
  }

  if (draftFilters.value.length > 0) {
    result = result.filter((product) => {
      return draftFilters.value.every((filterKey) => product.filterKeys.includes(filterKey))
    })
  }

  return result.length
})

const likedKey = (productId, optionId = '') => `${productId || ''}:${optionId || ''}`

const likedKeyForProduct = (product) => {
  const option = product.representative || product.options?.[0] || null
  return likedKey(product.id, option?.id || '')
}

const isProductLiked = (product) => {
  return likedOptionKeys.value.has(likedKeyForProduct(product))
}

const buildDetailPayload = (product, option = product?.representative) => {
  if (!product) return null
  return {
    ...(option || {}),
    productId: product.id,
    product_id: product.id,
    parentId: product.id,
    productName: product.name,
    options: product.options || [],
  }
}

const buildLikedOptionPayload = (product) => {
  const detailPayload = buildDetailPayload(product, product.representative || product.options?.[0])
  const productId = product.id
  const optionId = detailPayload?.id || ''
  return {
    product_id: Number(productId),
    product_option_id: Number(optionId),
    option_id: String(optionId || ''),
    group_key: '',
    brand: detailPayload.brand || '',
    name: detailPayload.name || '',
    option: detailPayload.option || '',
    image_url: detailPayload.imageUrl || detailPayload.image || '',
    product_url: detailPayload.productUrl || '',
    snapshot: detailPayload,
  }
}

const loadLikedGroups = async () => {
  if (!localStorage.getItem('access_token')) return

  try {
    const data = await getLikedProductOptions({ limit: 50 })
    const rows = Array.isArray(data) ? data : data.results || []
    likedOptionKeys.value = new Set(
      rows.map((item) => {
        const productId = item.product?.id || item.product_id
        const optionId = item.product_option?.id || item.option_id || ''
        return likedKey(productId, optionId)
      }).filter((key) => key !== ':'),
    )
  } catch (error) {
    console.warn('찜한 제품 목록을 불러오지 못했습니다.', error)
  }
}

const toggleLike = async (product) => {
  if (!localStorage.getItem('access_token')) {
    alert('로그인 후 찜할 수 있어요.')
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }

  const key = likedKeyForProduct(product)
  const nextKeys = new Set(likedOptionKeys.value)
  const wasLiked = nextKeys.has(key)

  if (wasLiked) {
    nextKeys.delete(key)
  } else {
    nextKeys.add(key)
  }

  likedOptionKeys.value = nextKeys

  try {
    await toggleLikedProductOption(buildLikedOptionPayload(product))
  } catch (error) {
    const rollbackKeys = new Set(likedOptionKeys.value)
    if (wasLiked) {
      rollbackKeys.add(key)
    } else {
      rollbackKeys.delete(key)
    }
    likedOptionKeys.value = rollbackKeys
    console.error('찜 상태를 저장하지 못했습니다.', error)
    alert('찜 상태를 저장하지 못했습니다.')
  }
}

const toggleLikedMode = () => {
  likedOnly.value = !likedOnly.value
  selectedFilters.value = []
  selectedBrands.value = []
}

const compareItems = () => {
  alert('비교 기능은 다음 단계에서 연결하면 됩니다!')
}

const goDetail = (product, option = product.representative) => {
  const detailPayload = buildDetailPayload(product, option)
  console.log('clicked product:', product)
  console.log('product id:', product?.id)

  const productId =
    product?.id ||
    product?.product_id ||
    detailPayload?.productId ||
    detailPayload?.product_id

  if (!productId) {
    alert('상세 조회에 필요한 상품 ID가 없습니다.')
    return
  }

  localStorage.setItem('selectedProductOption', JSON.stringify(detailPayload))
  localStorage.setItem('selectedProductGroup', JSON.stringify(product))

  router.push({
    name: 'product-color-matching',
    params: {
      id: productId,
    },
    query: detailPayload?.id ? { option: detailPayload.id } : {},
  })
}

onMounted(async () => {
  userColorProfile.value = readUserColorProfile()
  hasDiagnosisProfile.value = hasSavedUserColorProfile()
  await syncLatestDiagnosisProfile()

  if (keyword.value) {
    selectedCategory.value = 'all'
  }

  await loadLikedGroups()
  fetchProducts()
})

watch(
  () => route.query.keyword,
  (value) => {
    if (value) {
      selectedCategory.value = 'all'
      likedOnly.value = false
    }
  },
)
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

.recommend-page {
  padding: 42px 86px 110px;
  background:
    radial-gradient(circle at 20% 0%, rgba(255, 233, 225, 0.8), transparent 38%),
    linear-gradient(180deg, #fffaf7 0%, #fbf4f1 100%);
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.hero h1 {
  font-family: var(--font-title-serif) !important;
  font-size: 30px;
  margin-bottom: 16px;
  letter-spacing: 0;
}

.hero p {
  color: #5f5754;
}

.my-tone-card {
  width: 330px;
  height: 112px;
  border: 1px solid #eaded8;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.86);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 28px;
}

.my-tone-card p {
  color: #8e7e79;
  font-size: 13px;
  margin: 0 0 8px;
}

.my-tone-card strong {
  display: block;
  font-size: 17px;
  margin-bottom: 8px;
}

.my-tone-card a {
  color: #c65367;
  text-decoration: none;
  font-weight: 700;
  font-size: 13px;
}

.primary-missing-box {
  margin: 0 0 20px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fff8f6;
  color: #8b3a4a;
  font-weight: 800;
  line-height: 1.6;
  padding: 14px 18px;
}

.profile {
  width: 66px;
  height: 66px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 50% 28%, #f8d8d4 0 18%, transparent 19%),
    radial-gradient(ellipse at 50% 45%, #5a352b 0 30%, transparent 31%),
    linear-gradient(135deg, #f2d2c8, #fff1eb);
}

.category-tabs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  border: 1px solid #eaded8;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 28px;
  background: white;
}

.category-tabs button {
  height: 54px;
  border: none;
  border-right: 1px solid #eaded8;
  background: rgba(255, 255, 255, 0.84);
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
}

.category-tabs button:last-child {
  border-right: none;
}

.category-tabs .active {
  background: linear-gradient(135deg, #c65367, #d96f82);
  color: white;
}

.color-chart-section {
  display: grid;
  grid-template-columns: minmax(260px, 0.8fr) minmax(420px, 1.2fr);
  gap: 22px;
  align-items: stretch;
  margin: 0 0 28px;
  padding: 24px;
  border: 1px solid #eaded8;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 10px 24px rgba(88, 55, 45, 0.04);
}

.chart-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.chart-copy span {
  color: #c65367;
  font-size: 13px;
  font-weight: 800;
}

.chart-copy h2 {
  margin: 8px 0 10px;
  font-size: 24px;
  letter-spacing: 0;
}

.chart-copy p {
  margin: 0;
  color: #6b625f;
  line-height: 1.7;
}

.chart-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 18px;
}

.chart-meta span {
  padding: 8px 12px;
  border: 1px solid #eaded8;
  border-radius: 999px;
  background: #fff8f6;
  color: #6b4b52;
  font-size: 12px;
  font-weight: 900;
}

.tone-chart {
  position: relative;
  min-height: 320px;
  border: 1px solid #eaded8;
  border-radius: 12px;
  background:
    linear-gradient(90deg, rgba(246, 211, 177, 0.18), rgba(218, 222, 255, 0.22)),
    #fffaf7;
  overflow: hidden;
}

.axis {
  position: absolute;
  background: rgba(198, 83, 103, 0.2);
}

.axis-x {
  left: 8%;
  right: 8%;
  bottom: 50%;
  height: 1px;
}

.axis-y {
  top: 8%;
  bottom: 8%;
  left: 50%;
  width: 1px;
}

.axis-label {
  position: absolute;
  color: #8e7e79;
  font-size: 12px;
  font-weight: 800;
}

.axis-label--warm {
  left: 18px;
  bottom: 48%;
}

.axis-label--cool {
  right: 18px;
  bottom: 48%;
}

.axis-label--light {
  top: 14px;
  left: 51%;
}

.axis-label--deep {
  bottom: 14px;
  left: 51%;
}

.chart-dot {
  position: absolute;
  transform: translate(-50%, 50%);
  border: 2px solid rgba(255, 255, 255, 0.9);
  border-radius: 999px;
  box-shadow: 0 5px 14px rgba(80, 45, 50, 0.18);
  cursor: pointer;
  transition: 0.18s;
}

.chart-dot:hover {
  z-index: 4;
  transform: translate(-50%, 50%) scale(1.22);
}

.user-zone {
  position: absolute;
  transform: translate(-50%, 50%);
  z-index: 3;
  padding: 6px 10px;
  border: 1px solid #c65367;
  border-radius: 999px;
  background: #fff;
  color: #c65367;
  font-size: 12px;
  font-weight: 900;
  box-shadow: 0 8px 20px rgba(198, 83, 103, 0.16);
  white-space: nowrap;
}

.brand-board {
  margin: 0 0 24px;
  border: 1px solid #a7c957;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.92);
  overflow: hidden;
}

.brand-board-head {
  display: grid;
  grid-template-columns: 200px 1fr;
  align-items: stretch;
  border-bottom: 1px solid #eaded8;
}

.brand-board-head > div {
  padding: 20px 24px;
  border-right: 1px solid #eaded8;
}

.brand-board h2 {
  margin: 0 0 8px;
  font-size: 19px;
}

.brand-board p {
  margin: 0;
  color: #91be3f;
  font-weight: 900;
}

.brand-board-head button {
  justify-self: end;
  align-self: end;
  margin: 0 18px 16px 0;
  height: 36px;
  padding: 0 14px;
  border: none;
  background: transparent;
  color: #8e7e79;
  font-weight: 800;
  cursor: pointer;
}

.brand-board-head button:disabled {
  cursor: default;
  opacity: 0.45;
}

.brand-check-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.brand-check-grid label {
  min-height: 52px;
  padding: 0 18px;
  border-right: 1px solid #eaded8;
  border-bottom: 1px solid #eaded8;
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  color: #4d4441;
  font-weight: 800;
  cursor: pointer;
}

.brand-check-grid label:nth-child(5n) {
  border-right: none;
}

.brand-check-grid label.active {
  background: #f6fbef;
  color: #5f8f16;
}

.brand-check-grid input {
  width: 15px;
  height: 15px;
  accent-color: #91be3f;
}

.brand-check-grid span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.brand-check-grid small {
  color: #9b8d88;
  font-size: 12px;
}

.brand-board-foot {
  height: 46px;
  display: flex;
  align-items: center;
  border-top: 1px solid #eaded8;
  background: #f7f7f7;
}

.brand-board-foot button {
  height: 100%;
  padding: 0 24px;
  border: none;
  border-right: 1px solid #eaded8;
  background: white;
  color: #6b625f;
  font-weight: 900;
  cursor: pointer;
}

.filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 26px;
}

.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filters button {
  height: 42px;
  padding: 0 20px;
  border: 1px solid #eaded8;
  border-radius: 9px;
  background: white;
  color: #4d4441;
  font-weight: 700;
  cursor: pointer;
}

.filters .filter-title {
  cursor: default;
}

.filters .active {
  background: #c65367;
  color: white;
  border-color: #c65367;
}

.sort {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 800;
  margin-left: auto;
}

.sort select {
  width: 200px;
  height: 44px;
  padding: 0 16px;
  border: 1px solid #eaded8;
  border-radius: 9px;
  background: white;
  color: #4d4441;
}

.info-row {
  display: flex;
  justify-content: space-between;
  border-top: 1px solid #eaded8;
  padding-top: 22px;
  margin-bottom: 20px;
  color: #6b625f;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 18px;
}

.product-card {
  position: relative;
  min-height: 338px;
  border: 1px solid #eaded8;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.9);
  padding: 22px;
  box-shadow: 0 10px 24px rgba(88, 55, 45, 0.04);
  cursor: pointer;
  transition: 0.2s;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 14px 28px rgba(88, 55, 45, 0.08);
}

.rank {
  position: absolute;
  left: 18px;
  top: 18px;
  width: 31px;
  height: 31px;
  border-radius: 50%;
  background: #ded9d7;
  color: #555;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  z-index: 2;
}

.rank.top {
  background: #c65367;
  color: white;
}

.heart {
  position: absolute;
  right: 18px;
  top: 16px;
  border: none;
  background: none;
  font-size: 28px;
  color: #aaa;
  cursor: pointer;
  z-index: 2;
}

.heart.active {
  color: #c65367;
}

.product-img {
  height: 150px;
  margin: 8px 18px 20px;
  border-radius: 12px;
  overflow: hidden;
  background: #fff1f3;
  display: flex;
  align-items: center;
  justify-content: center;
}

.real-product-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: white;
}

.fallback-product-visual {
  width: 100%;
  height: 100%;
}

.lip1,
.lip2,
.lip3,
.lip4,
.lip5 {
  background:
    radial-gradient(ellipse at 40% 60%, rgba(190, 74, 94, 0.45) 0 28%, transparent 29%),
    linear-gradient(90deg, transparent 42%, #aa5068 43% 55%, transparent 56%),
    linear-gradient(135deg, #fff1eb, #f7d5d5);
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
  margin: 0 0 8px;
}

.product-card h3 {
  margin: 0 0 10px;
  font-size: 17px;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.option {
  margin: 0 0 12px;
  color: #3c3431;
}

.option span {
  color: #8a7772;
  font-size: 13px;
}

.color-dots {
  display: flex;
  gap: 7px;
  margin-bottom: 14px;
}

.color-dots span {
  width: 17px;
  height: 17px;
  border-radius: 50%;
}

.metric-summary {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.metric-summary span {
  padding: 6px 9px;
  border-radius: 999px;
  background: #fff0f1;
  color: #6b4b52;
  font-size: 11px;
  font-weight: 900;
}

.score {
  color: #c65367;
  font-size: 22px;
  font-weight: 900;
  margin: 0 0 10px;
}

.score span {
  font-size: 14px;
  margin-left: 3px;
}

.desc {
  color: #5f5754;
  line-height: 1.55;
  font-size: 14px;
  min-height: 42px;
}

.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.tags span {
  padding: 7px 12px;
  border-radius: 999px;
  background: #fff0f1;
  color: #6b4b52;
  font-size: 12px;
}

.empty-box {
  border: 1px solid #eaded8;
  border-radius: 14px;
  background: white;
  padding: 52px;
  text-align: center;
  color: #5f5754;
}

.empty-box h3 {
  color: #2d2524;
  margin-bottom: 10px;
}

.empty-box button {
  margin-top: 18px;
  height: 42px;
  padding: 0 20px;
  border: 1px solid #d98c99;
  border-radius: 9px;
  background: white;
  color: #c65367;
  font-weight: 800;
  cursor: pointer;
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: 92px;
  padding: 16px 86px;
  background: rgba(255, 250, 247, 0.92);
  border-top: 1px solid #eaded8;
  backdrop-filter: blur(10px);
  display: grid;
  grid-template-columns: 1.4fr 0.8fr 0.8fr 0.9fr;
  gap: 28px;
  align-items: center;
}

.standard {
  height: 56px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: white;
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 0 22px;
  color: #5f5754;
}

.standard strong {
  color: #2d2524;
}

.outline-btn,
.main-btn {
  height: 52px;
  border-radius: 9px;
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
}

.outline-btn {
  background: white;
  color: #c65367;
  border: 1px solid #d98c99;
}

.main-btn {
  background: linear-gradient(135deg, #c65367, #d96f82);
  color: white;
  border: none;
}

.all-filter-btn {
  border-color: #d98c99 !important;
  color: #c65367 !important;
}

.filter-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(45, 37, 36, 0.36);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.filter-modal {
  width: 430px;
  height: 100vh;
  background: #fffaf7;
  border-left: 1px solid #eaded8;
  box-shadow: -12px 0 30px rgba(88, 55, 45, 0.18);
  display: flex;
  flex-direction: column;
}

.filter-modal-header {
  padding: 28px 28px 22px;
  border-bottom: 1px solid #eaded8;
  display: flex;
  justify-content: space-between;
  gap: 18px;
}

.filter-modal-header h2 {
  margin: 0 0 8px;
  font-size: 24px;
}

.filter-modal-header p {
  margin: 0;
  color: #6b625f;
  font-size: 14px;
  line-height: 1.5;
}

.modal-close {
  width: 36px;
  height: 36px;
  border: none;
  background: white;
  border-radius: 50%;
  font-size: 28px;
  color: #5f5754;
  cursor: pointer;
}

.filter-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 26px 28px;
}

.filter-group {
  margin-bottom: 34px;
}

.filter-group h3 {
  margin: 0 0 14px;
  font-size: 17px;
}

.filter-chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-chip-grid button {
  min-width: 88px;
  height: 42px;
  padding: 0 16px;
  border: 1px solid #eaded8;
  border-radius: 999px;
  background: white;
  color: #4d4441;
  font-weight: 800;
  cursor: pointer;
}

.filter-chip-grid button.active {
  background: #c65367;
  color: white;
  border-color: #c65367;
}

.filter-modal-footer {
  padding: 18px 28px;
  border-top: 1px solid #eaded8;
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 12px;
  background: rgba(255, 250, 247, 0.96);
}

.modal-reset-btn,
.modal-apply-btn {
  height: 52px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 900;
  cursor: pointer;
}

.modal-reset-btn {
  background: white;
  color: #c65367;
  border: 1px solid #d98c99;
}

.modal-apply-btn {
  background: linear-gradient(135deg, #c65367, #d96f82);
  color: white;
  border: none;
}

@media (max-width: 1100px) {
  .recommend-page {
    padding: 32px 24px 110px;
  }

  .hero,
  .filter-row,
  .info-row {
    align-items: stretch;
    flex-direction: column;
    gap: 18px;
  }

  .my-tone-card {
    width: 100%;
  }

  .color-chart-section {
    grid-template-columns: 1fr;
  }

  .brand-board-head {
    grid-template-columns: 1fr;
  }

  .brand-board-head > div {
    border-right: none;
  }

  .brand-check-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .brand-check-grid label:nth-child(5n) {
    border-right: 1px solid #eaded8;
  }

  .brand-check-grid label:nth-child(2n) {
    border-right: none;
  }

  .sort {
    margin-left: 0;
  }

  .product-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .product-grid {
    grid-template-columns: 1fr;
  }

  .bottom-bar {
    grid-template-columns: 1fr;
  }
}
</style>
