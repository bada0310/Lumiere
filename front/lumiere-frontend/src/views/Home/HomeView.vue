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
          <div class="model-face">Beauty<br />Image</div>
        </div>

        <div class="summary-card">
          <p class="summary-title">내 퍼스널컬러 요약</p>
          <h3>여름 쿨 라이트</h3>
          <p class="eng">Summer Cool Light</p>

          <div class="chips">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
          </div>

          <p class="summary-desc">
            맑고 부드러운 파스텔 톤이 잘 어울려요.
            은은한 핑크, 라벤더, 라이트 블루 계열이 가장 잘 어울립니다.
          </p>

          <button @click="$router.push('/result')">
            상세 결과 보기
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
        <h2>오늘의 인기 제품 미리보기</h2>
        <RouterLink to="/products" class="section-link">
          전체 보기 →
        </RouterLink>
      </div>

      <div class="product-list">
        <RouterLink
          v-for="product in products"
          :key="product.id"
          :to="`/product-detail/${product.id}`"
          class="product-card"
        >
          <div class="product-img"></div>
          <p class="brand">{{ product.brand }}</p>
          <h4>{{ product.name }}</h4>
          <p class="option">{{ product.optionName }}</p>
          <p class="score">추천도 {{ product.score }}%</p>
        </RouterLink>
      </div>
    </section>
  </main>
</template>

<script setup>
const products = [
  {
    id: 1,
    brand: '롬앤',
    name: '쥬시 래스팅 틴트',
    optionName: '25호 베어 그레이프',
    score: 96,
  },
  {
    id: 2,
    brand: '클리오',
    name: '프로 아이 팔레트',
    optionName: '뮤트 라이브러리',
    score: 92,
  },
  {
    id: 3,
    brand: '에스쁘아',
    name: '비 글로우 쿠션',
    optionName: '21호 아이보리',
    score: 94,
  },
  {
    id: 4,
    brand: '휘',
    name: '블러셔 멜로우',
    optionName: '로지 핑크',
    score: 90,
  },
  {
    id: 5,
    brand: '데이지크',
    name: '섀도우 팔레트',
    optionName: '쿨 블렌딩',
    score: 89,
  },
]
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: #fffaf7;
  color: #2b2523;
}

.hero {
  min-height: 470px;
  padding: 60px 90px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(90deg, #fff7f2, #f7e5dd);
}

.hero-text h1 {
  font-size: 52px;
  line-height: 1.35;
  font-weight: 700;
}

.point-color {
  color: #c65367;
}

.hero-text p {
  margin-top: 24px;
  font-size: 18px;
  line-height: 1.8;
}

.hero-buttons {
  margin-top: 36px;
  display: flex;
  gap: 20px;
}

.hero-buttons button {
  width: 280px;
  height: 92px;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
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
  width: 330px;
  height: 380px;
  border-radius: 24px;
  background: linear-gradient(135deg, #f4cbbf, #fff3ec);
  display: flex;
  align-items: center;
  justify-content: center;
}

.model-face {
  font-size: 34px;
  color: #c65367;
  font-family: Georgia, serif;
  text-align: center;
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
  background: #efc7cf;
}

.chips span:nth-child(2) {
  background: #e7c9d8;
}

.chips span:nth-child(3) {
  background: #d6c5e3;
}

.chips span:nth-child(4) {
  background: #c7c5df;
}

.chips span:nth-child(5) {
  background: #d6e1e8;
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
  padding: 32px 76px;
}

.features h2 {
  text-align: center;
  font-family: Georgia, serif;
  font-size: 26px;
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
  padding: 24px;
  background: white;
  border: 1px solid #eaded8;
  border-radius: 16px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 22px;
}

.section-link {
  color: #c65367;
  text-decoration: none;
  font-weight: 700;
}

.product-list {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 18px;
}

.product-card {
  display: block;
  border: 1px solid #eaded8;
  border-radius: 12px;
  padding: 18px;
  text-decoration: none;
  color: inherit;
}

.product-card:hover {
  transform: translateY(-3px);
  transition: 0.2s;
  box-shadow: 0 8px 18px rgba(90, 50, 40, 0.08);
}

.product-img {
  height: 110px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f3c1c8, #fff1ec);
  margin-bottom: 14px;
}

.brand {
  color: #777;
  font-size: 14px;
}

.product-card h4 {
  margin: 6px 0 8px;
}

.option {
  color: #756a66;
  font-size: 13px;
  margin-bottom: 12px;
}

.score {
  color: #c65367;
  font-weight: 700;
  font-size: 18px;
}
</style>