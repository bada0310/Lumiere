<template>
  <div class="page">
    <main class="detail-page">
      <button class="back-btn" type="button" @click="router.back()">
        ← 추천 제품 목록으로 돌아가기
      </button>

      <section class="title-section">
        <h1>제품 상세 분석 ✨</h1>
        <p>내 피부톤과 제품 색상을 비교하여 상세 분석 결과를 보여드려요.</p>
      </section>

      <section v-if="isLoading" class="loading-box">
        제품 정보를 불러오는 중입니다...
      </section>

      <template v-else-if="product">
        <section class="top-card">
          <div class="product-visual">
            <div class="product-image" :class="product.imageClass"></div>
          </div>

          <div class="product-info">
            <p class="brand">{{ product.brand }}</p>
            <h2>{{ product.name }}</h2>
            <h3>{{ product.option }}</h3>
            <p class="meta">
              {{ product.categoryLabel }}
              <span></span>
              여름 쿨 라이트 추천
            </p>

            <div class="hex-box">
              <span :style="{ backgroundColor: product.hex }"></span>
              <p>
                색상 HEX<br />
                <strong>{{ product.hex }}</strong>
              </p>
            </div>
          </div>

          <div class="match-score">
            <p>전체 적합도 ⓘ</p>
            <strong>{{ product.score }}<span>%</span></strong>
            <h4>{{ matchMessage }}</h4>
            <p>{{ product.desc }}</p>
          </div>

          <div class="radar-box">
            <div class="legend">
              <span class="my"></span> 나의 피부톤
              <span class="product-line"></span> 제품 색상
            </div>

            <div class="radar">
              <div class="radar-shape"></div>
              <span class="label top">명도 {{ radarScores.brightness }}</span>
              <span class="label right">채도 {{ radarScores.chroma }}</span>
              <span class="label bottom-right">쿨톤 {{ radarScores.cool }}</span>
              <span class="label bottom-left">탁도 {{ radarScores.clear }}</span>
              <span class="label left">대비 {{ radarScores.contrast }}</span>
            </div>
          </div>
        </section>

        <section class="compare-card">
          <h2>상세 수치 비교</h2>

          <div class="compare-layout">
            <div class="compare-table">
              <div class="table-head">
                <span>항목</span>
                <span>나</span>
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
                ⓘ 차이 값이 작을수록 내 피부톤과 제품 색상이 자연스럽게 어울립니다.
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
            <p>{{ product.option }} 옵션과 비슷한 분위기의 제품들이에요.</p>
          </div>

          <div class="similar-grid">
            <article
              class="similar-card"
              v-for="item in similarProducts"
              :key="item.id"
              @click="goDetail(item.id)"
            >
              <div class="similar-img" :class="item.imageClass"></div>

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

            <button class="olive" type="button">
              OLIVE YOUNG <span>올리브영 바로가기 ↗</span>
            </button>

            <button class="brand-link" type="button">
              {{ product.brand }} <span>브랜드 공식몰 바로가기 ↗</span>
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

const categoryTabs = [
  { key: 'lip', label: '립', keywords: ['립', '립틴트', '틴트', '립스틱', 'lip'] },
  { key: 'eye', label: '아이', keywords: ['아이', '섀도우', '아이섀도우', '마스카라', '아이라이너', 'eye'] },
  { key: 'cheek', label: '치크', keywords: ['치크', '블러셔', '블러쉬', 'cheek', 'blush'] },
  { key: 'base', label: '베이스', keywords: ['베이스', '쿠션', '파운데이션', '컨실러', 'base', 'foundation', 'cushion'] },
  { key: 'lens', label: '렌즈', keywords: ['렌즈', '컬러렌즈', 'lens'] },
]

const mockProducts = [
  {
    id: 101,
    brand: 'rom&nd',
    name: '블러 퍼지 틴트',
    option_name: '23 베어 그레이프',
    category: '립틴트',
    match_score: 96,
    texture: '매트 MLBB 저채도 쿨톤',
    hex_code: '#B4818E',
    popularity_score: 96,
    match_reason: '맑고 부드러운 쿨 핑크 컬러로 여름 쿨 라이트의 분위기를 잘 살려줘요.',
  },
  {
    id: 102,
    brand: 'peripera',
    name: '잉크 무드 글로이 틴트',
    option_name: '07 쿨베리',
    category: '립틴트',
    match_score: 88,
    texture: '글로시 누디 쿨톤',
    hex_code: '#C45D73',
    popularity_score: 89,
    match_reason: '쿨톤에게 어울리는 맑은 베리 핑크로 생기 있는 입술을 연출해줘요.',
  },
  {
    id: 201,
    brand: 'dasique',
    name: '섀도우 팔레트',
    option_name: '쿨 블렌딩',
    category: '아이섀도우',
    match_score: 91,
    texture: '매트 저채도 쿨톤',
    hex_code: '#C5A3B8',
    popularity_score: 92,
    match_reason: '은은한 라벤더 모브 계열로 눈가를 차분하고 맑게 보여줘요.',
  },
  {
    id: 301,
    brand: 'rom&nd',
    name: '베러 댄 치크',
    option_name: '블루베리칩',
    category: '치크',
    match_score: 90,
    texture: '저채도 쿨톤',
    hex_code: '#F0A9B7',
    popularity_score: 90,
    match_reason: '과하지 않은 쿨 핑크 치크로 자연스러운 혈색을 만들어줘요.',
  },
  {
    id: 401,
    brand: 'espoir',
    name: '비 글로우 쿠션',
    option_name: 'A00 포슬린',
    category: '베이스',
    match_score: 93,
    texture: '글로시 고명도 쿨톤',
    hex_code: '#F1D4C6',
    popularity_score: 94,
    match_reason: '밝고 맑은 피부 표현에 잘 맞는 베이스 옵션이에요.',
  },
  {
    id: 501,
    brand: 'OLENS',
    name: '비비링',
    option_name: '애쉬 그레이',
    category: '렌즈',
    match_score: 89,
    texture: '저채도 쿨톤',
    hex_code: '#9A9AB0',
    popularity_score: 88,
    match_reason: '차분한 애쉬 그레이 컬러로 쿨톤 이미지와 자연스럽게 어울려요.',
  },
]

const normalizeText = (value) => {
  return String(value || '').toLowerCase().replace(/\s/g, '')
}

const findCategoryKey = (item) => {
  const text = normalizeText(`
    ${item.category || ''}
    ${item.category_name || ''}
    ${item.product_category || ''}
    ${item.name || ''}
    ${item.product_name || ''}
    ${item.option_name || ''}
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

const normalizeProduct = (item, index) => {
  const categoryKey = findCategoryKey(item)
  const colors = [
    item.hex_code,
    item.hex,
    item.rep_hex_code,
    item.color_hex,
  ].filter(Boolean)

  const defaultColors = getDefaultColors(categoryKey)

  return {
    id: item.id || item.product_option_id || item.option_id || index + 1,
    brand: item.brand || item.product_brand || 'Lumière',
    name: item.name || item.product_name || '추천 상품',
    option: item.option_name || item.option || item.color_name || item.category || '추천 옵션',
    categoryKey,
    categoryLabel: getCategoryLabel(categoryKey),
    score: Math.round(Number(item.match_score ?? item.similarity_score ?? item.score ?? 90)),
    popularityScore: Number(item.popularity_score || 0),
    hex: colors[0] || defaultColors[0],
    colors: colors.length ? colors : defaultColors,
    imageClass: `${categoryKey}${(index % 5) + 1}`,
    texture: item.texture || item.finish || '',
    desc: item.match_reason || item.desc || `${getCategoryLabel(categoryKey)} 카테고리의 추천 옵션입니다.`,
  }
}

const loadProducts = async () => {
  isLoading.value = true

  try {
    const response = await axios.get('http://127.0.0.1:8000/api/products/')

    const data = Array.isArray(response.data)
      ? response.data
      : response.data.results || response.data.products || []

    allProducts.value = data.length
      ? data.map((item, index) => normalizeProduct(item, index))
      : mockProducts.map((item, index) => normalizeProduct(item, index))
  } catch (error) {
    console.error('상세 상품 데이터 불러오기 실패:', error)

    allProducts.value = mockProducts.map((item, index) => normalizeProduct(item, index))
  }

  setCurrentProduct()
  isLoading.value = false
}

const getStoredCategoryLabel = (categoryKey) => {
  const labelMap = {
    lip: '립',
    eye: '아이',
    cheek: '치크',
    base: '베이스',
    lens: '렌즈',
  }

  return labelMap[categoryKey] || '립'
}

const normalizeStoredProduct = (item) => {
  return {
    id: item.id,
    brand: item.brand || 'Lumière',
    name: item.name || '추천 상품',
    option: item.option || item.option_name || '추천 옵션',
    categoryKey: item.categoryKey || 'lip',
    categoryLabel: item.categoryLabel || getStoredCategoryLabel(item.categoryKey),
    score: item.score || item.match_score || 90,
    popularityScore: item.popularityScore || item.popularity_score || 0,
    hex: item.hex || item.hex_code || item.colors?.[0] || '#C45B75',
    colors: item.colors || [item.hex || item.hex_code || '#C45B75'],
    imageClass: item.imageClass || `${item.categoryKey || 'lip'}1`,
    texture: item.texture || '',
    desc: item.desc || item.match_reason || '선택한 상품 옵션의 상세 분석 결과입니다.',
  }
}

const setCurrentProduct = () => {
  const currentId = String(route.params.id || '')

  const storedText = localStorage.getItem('selectedProductOption')

  if (storedText) {
    try {
      const storedProduct = JSON.parse(storedText)

      if (String(storedProduct.id) === currentId) {
        product.value = normalizeStoredProduct(storedProduct)
        isLiked.value = Boolean(storedProduct.liked)
        return
      }
    } catch (error) {
      console.error('저장된 상품 정보를 읽는 데 실패했습니다:', error)
    }
  }

  product.value =
    allProducts.value.find((item) => String(item.id) === currentId) ||
    allProducts.value[0] ||
    null

  isLiked.value = false
}


const matchMessage = computed(() => {
  if (!product.value) return ''

  if (product.value.score >= 95) return '매우 잘 어울려요!'
  if (product.value.score >= 90) return '잘 어울려요!'
  if (product.value.score >= 80) return '무난하게 어울려요!'
  return '참고용으로 추천드려요!'
})

const radarScores = computed(() => {
  const score = product.value?.score || 90

  return {
    brightness: Math.min(99, score - 2),
    chroma: Math.min(99, score - 1),
    cool: Math.min(99, score + 1),
    clear: Math.min(99, score - 4),
    contrast: Math.min(99, score - 3),
  }
})

const compareItems = computed(() => {
  const score = product.value?.score || 90

  return [
    {
      icon: '☀️',
      name: '명도',
      mine: 65,
      product: Math.min(100, 60 + Math.round(score / 10)),
      diff: '+3',
      analysis: '밝기 차이가 작아 자연스러워요.',
    },
    {
      icon: '💧',
      name: '채도',
      mine: 30,
      product: Math.min(100, 25 + Math.round(score / 12)),
      diff: '+2',
      analysis: '채도가 과하지 않아 잘 맞아요.',
    },
    {
      icon: '❄️',
      name: '쿨톤',
      mine: 85,
      product: Math.min(100, 78 + Math.round(score / 8)),
      diff: '+2',
      analysis: '쿨톤감이 잘 맞아요.',
    },
    {
      icon: '☁️',
      name: '탁도',
      mine: 18,
      product: 16,
      diff: '-2',
      analysis: '맑은 느낌이 잘 살아나요.',
    },
    {
      icon: '◐',
      name: '대비',
      mine: 35,
      product: 37,
      diff: '+2',
      analysis: '대비감이 부담스럽지 않아요.',
    },
  ]
})

const recommendReasons = computed(() => {
  if (!product.value) return []

  return [
    `${product.value.categoryLabel} 카테고리에서 여름 쿨 라이트 톤과 적합도가 높은 옵션이에요.`,
    '명도, 채도, 쿨톤 수치가 피부톤과 자연스럽게 어울려요.',
    product.value.desc,
  ]
})

const similarProducts = computed(() => {
  if (!product.value) return []

  return allProducts.value
    .filter((item) => item.id !== product.value.id)
    .filter((item) => item.categoryKey === product.value.categoryKey)
    .sort((a, b) => b.score - a.score)
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

const goDetail = (id) => {
  router.push({
    name: 'product-detail',
    params: { id },
  })
}

const toggleLike = () => {
  isLiked.value = !isLiked.value
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

.match-score > p:first-child {
  font-weight: 800;
}

.match-score strong {
  color: #c65367;
  font-size: 72px;
  font-family: Georgia, serif;
}

.match-score strong span {
  font-size: 34px;
}

.match-score h4 {
  color: #c65367;
  font-size: 18px;
}

.match-score p {
  color: #5f5754;
  line-height: 1.6;
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
  inset: 45px 52px;
  background: rgba(198, 83, 103, 0.22);
  clip-path: polygon(50% 0%, 88% 28%, 82% 75%, 50% 95%, 18% 75%, 12% 28%);
  border: 2px solid #c65367;
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

.bottom-left {
  left: 30px;
  bottom: 8px;
}

.left {
  left: 0;
  top: 43%;
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
</style>