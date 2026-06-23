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
          <div class="tone-prism" :aria-label="`${summaryToneName} 퍼스널컬러 팔레트`">
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

          <div class="model-overlay">
            <span>{{ hasDiagnosis ? 'My Tone' : 'Lumière' }}</span>
            <strong>{{ summaryToneName }}</strong>
          </div>
        </div>

        <div class="summary-card">
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
          <p>올리브영 URL을 입력하면 가장 잘 어울리는 호수를 찾아드려요.</p>
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

      <div class="carousel-container">
        <div class="product-list">
          
          <div class="flip-card" v-for="product in products" :key="product.name">
            <div class="flip-card-inner">
              
              <div class="flip-card-front">
                <div class="product-img" :class="product.imageClass">
                  <img
                    v-if="product.imageUrl"
                    :src="product.imageUrl"
                    :alt="product.name"
                    loading="lazy"
                  />
                  <div v-else class="product-art"></div>
                </div>
                <p class="brand">{{ product.brand }}</p>
                <h4>{{ product.name }}</h4>
              </div>

              <div class="flip-card-back">
                <div class="ai-badge">✨ AI's Pick</div>
                <h4>{{ product.name }}</h4>
                <p class="reason">{{ product.reason }}</p>
                <button class="detail-btn" @click="goToProductDetail(product)">상세보기</button>
              </div>

            </div>
          </div>

        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

import { getLatestDiagnosis } from '@/services/diagnosisApi'
import { normalizeDiagnosisResult } from '@/utils/diagnosisResultTransform'
import { getSavedMockDiagnosisResult } from '@/utils/diagnosisMockStorage'

const router = useRouter()

const fallbackProducts = [
  { brand: '롬앤', name: '쥬시 래스팅 틴트', category: 'LIP', score: 96, reason: '입술에 맑게 차오르는 쿨톤 광택이 예술이에요!' },
  { brand: '클리오', name: '프로 아이 팔레트', category: 'EYE', score: 92, reason: '버릴 색상 하나 없는 데일리 음영의 정석입니다.' },
  { brand: '에스쁘아', name: '비 글로우 쿠션', category: 'BASE', score: 94, reason: 'AI 분석 결과, 고객님의 피부결에 완벽 밀착됩니다.' },
  { brand: '퓌', name: '블러셔 멜로우', category: 'CHEEK', score: 90, reason: '수채화처럼 맑게 발색되어 생기를 더해줘요.' },
  { brand: '데이지크', name: '섀도우 팔레트', category: 'EYE', score: 89, reason: '은은한 펄감이 눈매를 한층 깊게 만들어줍니다.' },
]

const products = ref(fallbackProducts.map((product, index) => normalizeHomeProduct(product, index)))
const latestDiagnosis = ref(null)

const hasDiagnosis = computed(() => Boolean(latestDiagnosis.value))

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
function normalizeHomeProduct(item, index) {
  const category = String(item.category || item.category_key || '').toUpperCase()
  const imageClass = category.includes('EYE')
    ? 'eye'
    : category.includes('CHEEK')
      ? 'cheek'
      : category.includes('BASE')
        ? 'base'
        : 'lip'

  return {
    id: item.id || item.product_option_id || index + 1,
    brand: item.brand || item.product_brand || '브랜드 미상',
    name: item.name || item.product_name || '추천 상품',
    score: Math.min(99, Math.max(70, Math.round(Number(item.match_score || item.score || 90 - index) || 90))),
    reason: item.reason || item.match_reason || item.description || '내 톤과 가까운 색감으로 추천된 제품이에요.',
    imageUrl: item.image_url || item.image || item.thumbnail || item.thumbnail_url || '',
    imageClass,
    raw: item,
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
  try {
    let response

    try {
      response = await axios.get('http://127.0.0.1:8000/api/products/')
    } catch (apiError) {
      console.warn('홈 인기 제품은 로컬 products_raw.json을 사용합니다:', apiError)
      response = await axios.get('/products_raw.json')
    }

    const data = Array.isArray(response.data)
      ? response.data
      : response.data.results || response.data.products || []

    const normalized = data
      .filter((item) => !String(item.category || '').toUpperCase().includes('LENS'))
      .sort((a, b) => Number(b.review_count || b.popularity_score || 0) - Number(a.review_count || a.popularity_score || 0))
      .slice(0, 8)
      .map(normalizeHomeProduct)

    if (normalized.length) products.value = normalized
  } catch (error) {
    console.warn('홈 인기 추천 제품을 불러오지 못했어요:', error)
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
  router.push(`/product-detail/${product.id}`)
}

onMounted(() => {
  loadLatestDiagnosis()
  loadPopularProducts()
})
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
  width: 330px;
  padding: 28px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 10px 30px rgba(90, 50, 40, 0.08);
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

/* --- 제품 추천 섹션 레이아웃 --- */
.products {
  margin: 20px 76px 50px;
  padding: 30px 0 30px 30px; /* 오른쪽 패딩을 없애서 카드 끝이 잘린 느낌(스크롤 암시)을 줍니다 */
  background: white;
  border: 1px solid #eaded8;
  border-radius: 16px;
  overflow: hidden; /* 영역 밖으로 나가는 건 일단 숨김 */
}

.section-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 22px;
  padding-right: 30px; /* 머리부분은 오른쪽 여백 유지 */
}

.view-all {
  color: #c65367;
  font-weight: 600;
  cursor: pointer;
}

/* --- 가로 스크롤 (캐러셀) --- */
.carousel-container {
  overflow-x: auto; /* 가로 스크롤 허용 */
  padding-bottom: 20px; /* 스크롤바와 카드 사이의 여유 공간 */
  /* 스크롤바 숨기기 (선택사항, 깔끔하게 보이려면 유지) */
  scrollbar-width: none; 
}
.carousel-container::-webkit-scrollbar {
  display: none; 
}

.product-list {
  display: flex;
  gap: 18px;
  width: max-content; /* 내부 아이템 개수만큼 가로 길이 무한 확장 */
  padding-right: 30px;
}

/* --- 3D 플립 카드 애니메이션 --- */
.flip-card {
  width: 200px;
  height: 270px;
  perspective: 1000px; /* 3D 공간의 원근감 부여 */
  flex-shrink: 0; /* 카드가 찌그러지지 않고 원래 크기 유지 */
  cursor: pointer;
}

.flip-card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1); /* 쫀득한 뒤집기 속도 */
  transform-style: preserve-3d; /* 3D 효과 유지 */
}

/* 마우스를 올렸을 때 Y축으로 180도 회전 */
.flip-card:hover .flip-card-inner {
  transform: rotateY(180deg);
}

/* 앞면과 뒷면의 공통 설정 */
.flip-card-front, .flip-card-back {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden; /* 뒷통수는 안 보이게 처리 */
  border-radius: 12px;
  border: 1px solid #eaded8;
  padding: 18px;
}

/* --- 앞면 디자인 --- */
.flip-card-front {
  background: white;
  display: flex;
  flex-direction: column;
}

.product-img {
  position: relative;
  height: 120px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f8e1df, #fff6f1);
  margin-bottom: 14px;
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

.brand { color: #777; font-size: 13px; }
.flip-card-front h4 {
  margin: 6px 0 0;
  font-size: 15px;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* --- 뒷면 디자인 --- */
.flip-card-back {
  background: linear-gradient(135deg, #fffaf7, #fdf1ed);
  transform: rotateY(180deg); /* 기본적으로 뒤집혀 있도록 설정 */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.ai-badge {
  background: #c65367;
  color: white;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 20px;
  margin-bottom: 12px;
}

.flip-card-back h4 { font-size: 15px; margin-bottom: 10px; color: #2b2523; }

.reason {
  font-size: 13px;
  color: #6b5f5b;
  line-height: 1.5;
  margin-bottom: auto; /* 버튼을 아래로 밀어냄 */
}

.detail-btn {
  margin-top: 15px;
  padding: 8px 16px;
  border: 1px solid #d98c99;
  background: white;
  color: #c65367;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: 0.2s;
}

.detail-btn:hover {
  background: #fdf1ed;
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
    padding-left: 18px;
  }
}
</style>
