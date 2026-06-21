<template>
  <div class="page">
    <main class="recommend-page">
      <section class="hero">
        <div>
          <h1>당신에게 딱 맞는 화장품 옵션을 추천해드려요</h1>
          <p>{{ selectedCategoryLabel }} 카테고리에서 여름 쿨 라이트 톤에 어울리는 옵션만 선별했어요.</p>
        </div>

        <div class="my-tone-card">
          <div>
            <p>나의 퍼스널컬러</p>
            <strong>여름 쿨 라이트</strong>
            <RouterLink to="/result">진단 결과 보기 ›</RouterLink>
          </div>
          <div class="profile"></div>
        </div>
      </section>

      <section class="category-tabs">
        <button
          v-for="category in categoryTabs"
          :key="category.key"
          type="button"
          :class="{ active: selectedCategory === category.key }"
          @click="selectCategory(category.key)"
        >
          {{ category.icon }} {{ category.label }}
        </button>
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
        <p>총 {{ filteredProducts.length }}개의 추천 옵션</p>
        <p>ⓘ 적합도는 나의 퍼스널컬러와의 유사도를 기반으로 계산됩니다.</p>
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
            :class="{ active: product.liked }"
            @click.stop="toggleLike(product)"
          >
            {{ product.liked ? '♥' : '♡' }}
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
          <p v-if="product.option" class="option">{{ product.option }}</p>

          <div class="color-dots">
            <span
              v-for="color in product.colors"
              :key="color"
              :style="{ backgroundColor: color }"
            ></span>
          </div>

          <p class="score">
            {{ product.score }}<span>% 적합</span>
          </p>

          <p class="desc">{{ product.desc }}</p>

          <div class="tags">
            <span v-for="tag in product.tags" :key="tag">{{ tag }}</span>
          </div>
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
          <span>여름 쿨 라이트</span>
          <span>명도: 밝음</span>
          <span>채도: 낮음</span>
          <span>쿨톤</span>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const products = ref([])
const selectedCategory = ref('lip')
const selectedFilters = ref([])
const sortOption = ref('scoreDesc')
const likedOnly = ref(false)
const isFilterModalOpen = ref(false)
const draftCategory = ref('lip')
const draftFilters = ref([])
const draftSortOption = ref('scoreDesc')
const isLoading = ref(false)

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
    keywords: ['치크', '블러셔', '블러쉬', 'cheek', 'blush'],
  },
  {
    key: 'base',
    serverKey: 'BASE',
    label: '베이스',
    icon: '🧴',
    keywords: ['베이스', '쿠션', '파운데이션', '컨실러', 'base', 'foundation', 'cushion'],
  },
  {
    key: 'lens',
    serverKey: 'LENS',
    label: '렌즈',
    icon: '👀',
    keywords: ['렌즈', '컬러렌즈', 'lens'],
  },
]

const filterOptions = [
  { key: 'mlbb', label: 'MLBB', keywords: ['mlbb', '엠엘비비'] },
  { key: 'nude', label: '누디', keywords: ['누디', 'nude', '베이지'] },
  { key: 'matte', label: '매트', keywords: ['매트', 'matte', '벨벳', '블러'] },
  { key: 'glossy', label: '글로시', keywords: ['글로시', 'glossy', '글로우', '촉촉', '워터'] },
  { key: 'cool', label: '쿨톤', keywords: ['쿨톤', '여름쿨', '쿨', 'cool', '라벤더', '모브', '핑크', '로즈'] },
  { key: 'lowChroma', label: '저채도', keywords: ['저채도', '차분', '뮤트', 'soft', 'mauve'] },
  { key: 'highBrightness', label: '고명도', keywords: ['고명도', '라이트', '밝음', '맑은', 'light'] },
]

const toneFilters = computed(() => {
  return filterOptions.filter((filter) => {
    return ['mlbb', 'nude', 'cool', 'lowChroma', 'highBrightness'].includes(filter.key)
  })
})

const textureFilters = computed(() => {
  return filterOptions.filter((filter) => {
    return ['matte', 'glossy'].includes(filter.key)
  })
})

const selectedCategoryLabel = computed(() => {
  return categoryTabs.find((item) => item.key === selectedCategory.value)?.label || '립'
})

const filteredProducts = computed(() => {
  let result = [...products.value]

  result = result.filter((product) => product.categoryKey === selectedCategory.value)

  if (likedOnly.value) {
    result = result.filter((product) => product.liked)
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

const makeFallbackTags = (categoryKey, index) => {
  const tags = ['추천', '쿨톤']

  if (index % 2 === 0) {
    tags.push('저채도')
  } else {
    tags.push('고명도')
  }

  if (categoryKey === 'lip') {
    tags.push(index % 2 === 0 ? 'MLBB' : '누디')
    tags.push(index % 3 === 0 ? '매트' : '글로시')
  }

  if (categoryKey === 'eye') {
    tags.push(index % 2 === 0 ? '매트' : '글로시')
  }

  if (categoryKey === 'base') {
    tags.push('베이스')
  }

  return tags
}

const getFilterKeys = (text) => {
  const searchText = normalizeText(text)

  return filterOptions
    .filter((filter) => {
      return filter.keywords.some((keyword) => searchText.includes(normalizeText(keyword)))
    })
    .map((filter) => filter.key)
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

const clampScore = (value) => {
  const numberValue = Number(value)

  if (Number.isNaN(numberValue)) {
    return 90
  }

  return Math.max(0, Math.min(100, Math.round(numberValue)))
}

const normalizeProduct = (item, index) => {
  const categoryKey = findCategoryKey(item)

  const brand = item.brand || item.product_brand || '브랜드 미상'
  const name = item.name || item.product_name || '추천 상품'
  const option = item.option_name || item.option || item.color_name || ''
  const score = clampScore(item.match_score ?? item.similarity_score ?? item.score ?? 90 - index)
  const popularityScore = Number(item.popularity_score || item.popularityScore || item.review_count || 0)

  const imageUrl = item.image_url || item.image || item.thumbnail || item.thumbnail_url || ''

  const fallbackTags = makeFallbackTags(categoryKey, index)
  const rawTags = Array.isArray(item.tags) ? item.tags : []

  const tags = [
    item.category,
    item.texture,
    ...rawTags,
    ...fallbackTags,
  ]
    .filter(Boolean)
    .filter((tag, tagIndex, arr) => arr.indexOf(tag) === tagIndex)
    .slice(0, 5)

  const desc = item.match_reason || item.reason || item.description || `${selectedCategoryLabel.value} 카테고리의 추천 상품입니다.`

  const filterText = `
    ${brand}
    ${name}
    ${option}
    ${item.category || ''}
    ${item.texture || ''}
    ${item.description || ''}
    ${desc}
    ${tags.join(' ')}
  `

  const colors = [
    item.hex_code,
    item.hex,
    item.rep_hex_code,
    item.color_hex,
  ].filter(Boolean)

  return {
    id: item.id || item.product_option_id || item.option_id || index + 1,
    brand,
    name,
    option,
    categoryKey,
    score,
    popularityScore,
    liked: false,
    imageUrl,
    originalImageUrl: item.image_url || '',
    productUrl: item.product_url || item.link || '',
    imageClass: `${categoryKey}${(index % 5) + 1}`,
    colors: colors.length ? colors : getDefaultColors(categoryKey),
    desc,
    tags,
    filterKeys: getFilterKeys(filterText),
    raw: item,
  }
}

const fetchProducts = async () => {
  isLoading.value = true

  try {
    const response = await axios.get('http://127.0.0.1:8000/api/products/')

    const data = Array.isArray(response.data)
      ? response.data
      : response.data.results || response.data.products || []

    products.value = data.map((item, index) => normalizeProduct(item, index))

    console.log('백엔드 상품 데이터:', products.value)
  } catch (error) {
    console.error('상품 데이터 불러오기 실패:', error)
    products.value = []
  } finally {
    isLoading.value = false
  }
}

const selectCategory = (categoryKey) => {
  selectedCategory.value = categoryKey
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
  selectedCategory.value = 'lip'
  selectedFilters.value = []
  sortOption.value = 'scoreDesc'
  likedOnly.value = false
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
  let result = [...products.value]

  result = result.filter((product) => product.categoryKey === draftCategory.value)

  if (draftFilters.value.length > 0) {
    result = result.filter((product) => {
      return draftFilters.value.every((filterKey) => product.filterKeys.includes(filterKey))
    })
  }

  return result.length
})

const toggleLike = (product) => {
  product.liked = !product.liked
}

const toggleLikedMode = () => {
  likedOnly.value = !likedOnly.value
  selectedFilters.value = []
}

const compareItems = () => {
  alert('비교 기능은 다음 단계에서 연결하면 됩니다!')
}

const goDetail = (product) => {
  localStorage.setItem('selectedProductOption', JSON.stringify(product))

  router.push({
    name: 'product-detail',
    params: {
      id: product.id,
    },
  })
}

onMounted(() => {
  fetchProducts()
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
  font-size: 30px;
  margin-bottom: 16px;
  letter-spacing: -0.5px;
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
  grid-template-columns: repeat(5, 1fr);
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
  min-height: 430px;
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
  margin: 0 0 14px;
  color: #3c3431;
}

.color-dots {
  display: flex;
  gap: 7px;
  margin-bottom: 16px;
}

.color-dots span {
  width: 17px;
  height: 17px;
  border-radius: 50%;
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
</style>