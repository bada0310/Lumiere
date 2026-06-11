<template>
  <div class="page">
    <AppHeader />

    <main class="result-page">
      <section class="steps">
        <div class="step done">✓</div>
        <div class="line active"></div>
        <div class="step done">✓</div>
        <div class="line active"></div>
        <div class="step active">3</div>
      </section>

      <section class="step-labels">
        <span>사진 업로드</span>
        <span>AI 분석</span>
        <span class="active-text">결과 확인</span>
      </section>

      <section class="result-card">
        <div class="top-grid">
          <div class="main-result">
            <p class="eyebrow">나의 퍼스널컬러는</p>
            <h1>여름 쿨 라이트</h1>
            <p class="eng">Summer Cool Light</p>

            <p class="summary">
              맑고 부드러운 쿨톤 컬러가<br />
              당신의 매력을 가장 빛나게 해요.
            </p>

            <div class="tags">
              <span>맑은 톤</span>
              <span>부드러운 대비</span>
              <span>쿨 핑크 베이스</span>
              <span>저채도</span>
            </div>
          </div>

          <div class="confidence-area">
            <div class="circle">
              <div>
                <small>AI Confidence</small>
                <strong>93<span>%</span></strong>
                <p>높은 신뢰도</p>
              </div>
            </div>

            <div class="date-box">
              <span>진단 완료일</span>
              <strong>2024.05.20</strong>
            </div>
          </div>

          <div class="profile-box">
            <p>Gen AI로 완성한<br />나의 프로필 이미지</p>
            <div class="profile-img"></div>
            <div class="dots">
              <span class="active-dot"></span>
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>

          <aside class="feature-box">
            <h3>전체 이미지 특징</h3>

            <div class="feature-item">
              <span>☀️</span>
              <p><strong>맑음</strong><br />깨끗하고 투명한 인상</p>
            </div>

            <div class="feature-item">
              <span>☁️</span>
              <p><strong>부드러움</strong><br />은은하고 부드러운 톤</p>
            </div>

            <div class="feature-item">
              <span>💎</span>
              <p><strong>세련됨</strong><br />차분하고 도시적인 분위기</p>
            </div>

            <div class="feature-item">
              <span>🌿</span>
              <p><strong>우아함</strong><br />자연스럽고 우아한 무드</p>
            </div>

            <div class="keyword-colors">
              <p>대표 컬러 키워드</p>
              <div class="color-chips">
                <span v-for="color in keywordColors" :key="color" :style="{ backgroundColor: color }"></span>
              </div>
            </div>
          </aside>
        </div>

        <div class="analysis-grid">
          <section class="analysis-box">
            <div class="box-title">
              <h3>피부톤 상세 분석</h3>
              <div class="level">
                <span>낮음</span>
                <span>보통</span>
                <span>높음</span>
              </div>
            </div>

            <div class="metric" v-for="metric in metrics" :key="metric.name">
              <div class="metric-info">
                <strong>{{ metric.name }}</strong>
                <small>{{ metric.desc }}</small>
              </div>
              <div class="bar">
                <div class="fill" :style="{ width: metric.value + '%' }"></div>
              </div>
              <span class="score">{{ metric.value }}</span>
            </div>
          </section>

          <section class="analysis-box">
            <h3>피부 특성 밸런스</h3>

            <div class="radar">
              <div class="radar-shape"></div>
              <span class="radar-label top">명도</span>
              <span class="radar-label right">채도</span>
              <span class="radar-label bottom-right">탁도</span>
              <span class="radar-label bottom">광택</span>
              <span class="radar-label bottom-left">대비</span>
              <span class="radar-label left">쿨톤</span>
            </div>

            <div class="legend">
              <span class="mine"></span> 나의 특성
              <span class="avg"></span> 평균
            </div>
          </section>
        </div>

        <section class="makeover-section">
          <div class="section-head">
            <div>
              <h3>AI 메이크오버</h3>
              <p>당신의 퍼스널컬러에 어울리는 다양한 메이크업 룩을 확인해보세요.</p>
            </div>

            <div class="tabs">
              <button class="active">내추럴</button>
              <button>데일리</button>
              <button>청순</button>
              <button>로맨틱</button>
              <button>스모키</button>
            </div>

            <button class="more-btn">더 많은 스타일 보기 ›</button>
          </div>

          <div class="makeover-list">
            <div class="look-card active" v-for="look in looks" :key="look.name">
              <div class="look-img"></div>
              <strong>{{ look.name }}</strong>
              <p>{{ look.desc }}</p>
            </div>
          </div>
        </section>

        <section class="palette-section">
          <div class="palette-box">
            <h3>BEST 컬러</h3>
            <p>당신을 가장 빛나게 하는 컬러</p>
            <div class="palette">
              <span v-for="color in bestColors" :key="color" :style="{ backgroundColor: color }"></span>
            </div>
          </div>

          <div class="palette-box">
            <h3>NEUTRAL 컬러</h3>
            <p>자연스럽고 안정적인 컬러</p>
            <div class="palette">
              <span v-for="color in neutralColors" :key="color" :style="{ backgroundColor: color }"></span>
            </div>
          </div>

          <div class="palette-box">
            <h3>ACCENT 컬러</h3>
            <p>포인트로 좋은 컬러</p>
            <div class="palette">
              <span v-for="color in accentColors" :key="color" :style="{ backgroundColor: color }"></span>
            </div>
          </div>

          <div class="palette-box">
            <h3>WORST 컬러</h3>
            <p>피하는 것이 좋은 컬러</p>
            <div class="palette">
              <span v-for="color in worstColors" :key="color" :style="{ backgroundColor: color }"></span>
            </div>
          </div>
        </section>

        <section class="recommend-section">
          <h3>맞춤 메이크업 추천</h3>
          <p>당신의 퍼스널컬러와 조화로운 메이크업 제품을 추천드려요.</p>

          <div class="product-grid">
            <div class="product-card" v-for="product in products" :key="product.name">
              <div class="product-img"></div>
              <div class="product-info">
                <span class="category">{{ product.category }}</span>
                <p class="tone">{{ product.tone }}</p>
                <strong>{{ product.brand }}</strong>
                <p>{{ product.name }}</p>
                <small>{{ product.reason }}</small>
                <button>제품 보기 ›</button>
              </div>
            </div>
          </div>
        </section>

        <section class="bottom-buttons">
          <RouterLink to="/products" class="main-btn">맞춤 화장품 추천 보기 ›</RouterLink>
          <RouterLink to="/makeover" class="sub-btn">AI 메이크오버 더 보기 ›</RouterLink>
          <button class="sub-btn">♡ 결과 저장하기</button>
        </section>

        <p class="notice">🛡️ 진단 결과는 마이페이지에서 언제든 다시 확인할 수 있어요.</p>
      </section>
    </main>
  </div>
</template>

<script setup>
import AppHeader from '../components/AppHeader.vue'

const keywordColors = ['#ef9eb8', '#e3c0dd', '#c5a5cf', '#b28ab0', '#b9c4d2', '#a8b5c5']

const metrics = [
  { name: '명도', desc: '피부의 밝기 정도', value: 65 },
  { name: '채도', desc: '색의 선명한 정도', value: 30 },
  { name: '탁도', desc: '색의 탁한 정도', value: 18 },
  { name: '광택', desc: '피부의 윤기 정도', value: 40 },
  { name: '대비', desc: '명암 대비 정도', value: 35 },
  { name: '쿨톤', desc: '피부의 온도감', value: 85 },
]

const looks = [
  { name: '내추럴', desc: '자연스럽고 깨끗한 룩' },
  { name: '데일리', desc: '생기있는 데일리 룩' },
  { name: '청순', desc: '맑고 청순한 룩' },
  { name: '로맨틱', desc: '사랑스러운 핑크 룩' },
  { name: '스모키', desc: '우아한 음영 메이크업' },
]

const bestColors = ['#f19ab6', '#efb4cf', '#dca8cf', '#c6addd', '#a9a0d8']
const neutralColors = ['#d5d2cf', '#c8c7c7', '#b8bec7', '#a9b6c5']
const accentColors = ['#c65b76', '#b45d82', '#7c6094', '#586993']
const worstColors = ['#f0b24c', '#de8c58', '#e3c74c', '#929760']

const products = [
  { category: '베이스', tone: '라이트 베이지 계열', brand: '에스쁘아', name: '비 글로우 쿠션 A00', reason: '화사한 피부 표현에 적합해요.' },
  { category: '립', tone: '쿨 핑크 MLBB', brand: '롬앤', name: '쥬시 래스팅 틴트', reason: '맑은 입술 톤을 연출해요.' },
  { category: '치크', tone: '라벤더 핑크', brand: '릴리바이레드', name: '러브빔 치크', reason: '은은한 생기를 더해줘요.' },
  { category: '아이', tone: '쿨 라벤더', brand: '클리오', name: '프로 아이 팔레트', reason: '세련된 쿨톤 무드에 좋아요.' },
]
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

.result-page {
  padding: 28px 56px 56px;
  background:
    radial-gradient(circle at 20% 0%, rgba(255, 234, 226, 0.75), transparent 35%),
    linear-gradient(180deg, #fffaf7 0%, #fbf4f1 100%);
}

.steps {
  display: flex;
  justify-content: center;
  align-items: center;
}

.step {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: white;
  border: 1px solid #e2d5cf;
  color: #9a8b87;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}

.step.done,
.step.active {
  background: #c65367;
  color: white;
  border-color: #c65367;
  box-shadow: 0 6px 14px rgba(198, 83, 103, 0.22);
}

.line {
  width: 260px;
  height: 2px;
  background: #eaded8;
}

.line.active {
  background: linear-gradient(90deg, #c65367, #e8b8c0);
}

.step-labels {
  width: 610px;
  margin: 10px auto 28px;
  display: flex;
  justify-content: space-between;
  color: #9a8b87;
  font-size: 14px;
  font-weight: 700;
}

.step-labels span,
.active-text {
  color: #c65367;
}

.result-card {
  max-width: 1360px;
  margin: 0 auto;
  padding: 38px;
  border: 1px solid #eaded8;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 50px rgba(88, 55, 45, 0.06);
}

.top-grid {
  display: grid;
  grid-template-columns: 1.35fr 0.75fr 1.05fr 0.95fr;
  gap: 34px;
  align-items: start;
}

.eyebrow {
  font-size: 16px;
  font-weight: 800;
  margin-bottom: 22px;
}

.main-result h1 {
  font-size: 52px;
  letter-spacing: -1.5px;
  margin: 0 0 12px;
}

.eng {
  font-size: 20px;
  color: #5e5653;
}

.summary {
  margin-top: 34px;
  font-size: 26px;
  color: #c65367;
  font-weight: 800;
  line-height: 1.7;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 44px;
}

.tags span {
  padding: 11px 20px;
  border-radius: 8px;
  background: #fff0f1;
  color: #b64b5e;
  font-size: 14px;
  font-weight: 700;
}

.confidence-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 34px;
  min-height: 360px;
}

.circle {
  width: 168px;
  height: 168px;
  border-radius: 50%;
  background: conic-gradient(#c65367 0deg 335deg, #f1dddd 335deg 360deg);
  padding: 10px;
  box-shadow: 0 10px 24px rgba(198, 83, 103, 0.18);
}

.circle > div {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #fffaf7;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.circle small {
  color: #8e7e79;
  font-size: 12px;
}

.circle strong {
  color: #c65367;
  font-size: 46px;
  line-height: 1.1;
}

.circle span {
  font-size: 21px;
}

.circle p {
  font-size: 12px;
  margin: 0;
  font-weight: 700;
}

.date-box {
  width: 148px;
  height: 82px;
  border: 1px solid #eaded8;
  border-radius: 12px;
  background: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.date-box span {
  font-size: 12px;
  color: #8e7e79;
}

.date-box strong {
  margin-top: 6px;
  font-size: 17px;
}

.profile-box p {
  font-weight: 800;
  line-height: 1.6;
  margin-bottom: 18px;
}

.profile-img,
.look-img {
  background:
    radial-gradient(circle at 50% 25%, #f8d8d4 0 14%, transparent 15%),
    radial-gradient(ellipse at 50% 42%, #5a352b 0 23%, transparent 24%),
    radial-gradient(ellipse at 50% 45%, #ffe1d6 0 30%, transparent 31%),
    radial-gradient(circle at 43% 42%, #2b201d 0 2%, transparent 3%),
    radial-gradient(circle at 57% 42%, #2b201d 0 2%, transparent 3%),
    radial-gradient(ellipse at 50% 57%, #d85f69 0 5%, transparent 6%),
    linear-gradient(135deg, #f4d3ca, #fff1eb);
}

.profile-img {
  height: 300px;
  border-radius: 14px;
  box-shadow: inset 0 0 0 1px rgba(198, 83, 103, 0.08);
}

.dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 14px;
}

.dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ddd;
}

.active-dot {
  background: #c65367 !important;
}

.feature-box {
  border: 1px solid #eaded8;
  border-radius: 16px;
  padding: 30px;
  background: rgba(255, 255, 255, 0.88);
}

.feature-box h3 {
  font-size: 22px;
  margin-bottom: 28px;
}

.feature-item {
  display: flex;
  gap: 18px;
  margin-bottom: 28px;
}

.feature-item span {
  font-size: 28px;
}

.feature-item p {
  margin: 0;
  line-height: 1.65;
  color: #625956;
}

.feature-item strong {
  color: #2d2524;
  font-size: 17px;
}

.keyword-colors {
  border-top: 1px solid #eaded8;
  padding-top: 24px;
  margin-top: 10px;
}

.keyword-colors p {
  font-weight: 800;
}

.color-chips,
.palette {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.color-chips span,
.palette span {
  display: inline-block;
  width: 38px;
  height: 38px;
  border-radius: 9px;
}

.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px;
  margin-top: 30px;
}

.analysis-box,
.makeover-section,
.palette-section,
.recommend-section {
  border: 1px solid #eaded8;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  padding: 28px;
}

.box-title {
  display: flex;
  justify-content: space-between;
}

.level {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #8e7e79;
}

.metric {
  display: grid;
  grid-template-columns: 120px 1fr 40px;
  align-items: center;
  gap: 18px;
  margin-top: 20px;
}

.metric-info small {
  display: block;
  color: #8e7e79;
  font-size: 12px;
  margin-top: 4px;
}

.bar {
  height: 5px;
  background: #eee2df;
  border-radius: 999px;
}

.fill {
  height: 100%;
  background: linear-gradient(90deg, #e9a7b2, #c65367);
  border-radius: 999px;
}

.score {
  text-align: right;
  font-weight: 800;
}

.radar {
  width: 280px;
  height: 280px;
  margin: 18px auto;
  position: relative;
  background:
    radial-gradient(circle, transparent 20%, #eaded8 21%, transparent 22%),
    radial-gradient(circle, transparent 40%, #eaded8 41%, transparent 42%),
    radial-gradient(circle, transparent 60%, #eaded8 61%, transparent 62%),
    radial-gradient(circle, transparent 80%, #eaded8 81%, transparent 82%);
}

.radar-shape {
  position: absolute;
  inset: 58px;
  background: rgba(198, 83, 103, 0.22);
  clip-path: polygon(50% 0%, 85% 28%, 78% 72%, 50% 95%, 18% 72%, 15% 28%);
  border: 2px solid #c65367;
}

.radar-label {
  position: absolute;
  font-size: 12px;
  font-weight: 800;
}

.top { top: 0; left: 50%; transform: translateX(-50%); }
.right { right: 0; top: 35%; }
.bottom-right { right: 18px; bottom: 46px; }
.bottom { bottom: 0; left: 50%; transform: translateX(-50%); }
.bottom-left { left: 18px; bottom: 46px; }
.left { left: 0; top: 35%; }

.legend {
  text-align: center;
  color: #8e7e79;
  font-size: 13px;
}

.legend span {
  display: inline-block;
  width: 26px;
  height: 2px;
  margin: 0 6px;
  vertical-align: middle;
}

.mine {
  background: #c65367;
}

.avg {
  background: #aaa;
}

.makeover-section {
  margin-top: 24px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.section-head p {
  color: #8e7e79;
  margin-top: 6px;
}

.tabs {
  display: flex;
  gap: 8px;
}

.tabs button,
.more-btn {
  border: none;
  background: #f8eeee;
  color: #5e5653;
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 700;
}

.tabs .active {
  background: #c65367;
  color: white;
}

.more-btn {
  color: #c65367;
  background: white;
  border: 1px solid #eaded8;
}

.makeover-list {
  margin-top: 24px;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 18px;
}

.look-card {
  text-align: center;
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 12px;
}

.look-card.active {
  border-color: #c65367;
}

.look-img {
  height: 132px;
  border-radius: 10px;
  margin-bottom: 10px;
}

.look-card p {
  color: #8e7e79;
  font-size: 12px;
}

.palette-section {
  margin-top: 24px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.palette-box {
  border-right: 1px solid #eaded8;
}

.palette-box:last-child {
  border-right: none;
}

.palette-box p {
  color: #8e7e79;
  font-size: 13px;
}

.recommend-section {
  margin-top: 24px;
}

.recommend-section > p {
  color: #8e7e79;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin-top: 20px;
}

.product-card {
  border: 1px solid #eaded8;
  border-radius: 14px;
  padding: 18px;
  display: flex;
  gap: 16px;
  background: white;
}

.product-img {
  width: 82px;
  height: 104px;
  border-radius: 12px;
  background:
    radial-gradient(circle at 45% 20%, #fff 0 18%, transparent 19%),
    linear-gradient(135deg, #eaa0aa, #fff0e9);
  flex-shrink: 0;
}

.category {
  font-weight: 800;
}

.tone {
  color: #c65367;
  font-size: 13px;
  margin: 8px 0;
  font-weight: 700;
}

.product-info p,
.product-info small {
  color: #666;
  line-height: 1.5;
}

.product-info button {
  margin-top: 12px;
  border: 1px solid #d98c99;
  color: #c65367;
  background: white;
  border-radius: 8px;
  padding: 8px 16px;
}

.bottom-buttons {
  margin-top: 30px;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 28px;
}

.main-btn,
.sub-btn {
  height: 64px;
  border-radius: 10px;
  text-decoration: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}

.main-btn {
  background: linear-gradient(135deg, #c65367, #d96f82);
  color: white;
}

.sub-btn {
  background: white;
  border: 1px solid #d98c99;
  color: #c65367;
}

.notice {
  text-align: center;
  color: #8e7e79;
  margin-top: 22px;
}
</style>