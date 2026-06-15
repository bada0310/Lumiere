<template>
  <div class="page">
    <AppHeader />

    <main class="detail-page">
      <div class="back">← URL 분석 결과로 돌아가기</div>

      <section class="title-section">
        <h1>제품 상세 분석 ✨</h1>
        <p>내 피부톤과 제품 색상을 비교하여 상세 분석 결과를 보여드려요.</p>
      </section>

      <section class="top-card">
        <div class="product-visual">
          <div class="product-image"></div>
        </div>

        <div class="product-info">
          <p class="brand">rom&nd</p>
          <h2>블러 퍼지 틴트</h2>
          <h3>23 베어 그레이프</h3>
          <p class="meta">립틴트 <span></span> 쿨톤 추천</p>

          <div class="hex-box">
            <span></span>
            <p>색상 HEX<br /><strong>#B4818E</strong></p>
          </div>
        </div>

        <div class="match-score">
          <p>전체 적합도 ⓘ</p>
          <strong>96<span>%</span></strong>
          <h4>매우 잘 어울려요!</h4>
          <p>여름 쿨 라이트 타입에게 가장 잘 어울리는 색상이에요.</p>
        </div>

        <div class="radar-box">
          <div class="legend">
            <span class="my"></span> 나의 피부톤
            <span class="product"></span> 제품 색상
          </div>

          <div class="radar">
            <div class="radar-shape"></div>
            <span class="label top">명도 92</span>
            <span class="label right">채도 95</span>
            <span class="label bottom-right">쿨톤 97</span>
            <span class="label bottom-left">탁도 90</span>
            <span class="label left">대비 94</span>
          </div>
        </div>
      </section>

      <section class="compare-card">
        <h2>상세 수치 비교</h2>

        <div class="compare-layout">
          <div class="compare-table">
            <div class="table-head">
              <span>항목</span>
              <span>나 (여름 쿨 라이트)</span>
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
                  <div class="fill product" :style="{ width: item.product + '%' }"></div>
                </div>
                <span>{{ item.product }}</span>
              </div>

              <div class="diff"> {{ item.diff }} </div>
              <div class="analysis">{{ item.analysis }} <span></span></div>
            </div>

            <p class="compare-note">ⓘ 차이 값이 ±5 이내일 때 가장 자연스럽게 어울립니다.</p>
          </div>

          <aside class="reason-box">
            <h3>추천 이유</h3>

            <div class="reason-item">
              <span>✓</span>
              <p>명도, 채도, 쿨톤 수치가<br />당신의 피부톤과 매우 유사해요.</p>
            </div>

            <div class="reason-item">
              <span>✓</span>
              <p>여름 쿨 라이트의 맑고 부드러운<br />분위기를 잘 살려주는 색상이에요.</p>
            </div>

            <div class="reason-item">
              <span>✓</span>
              <p>자연스럽고 화사한 혈색을 연출해<br />데일리 립으로 추천드려요.</p>
            </div>
          </aside>
        </div>
      </section>

      <section class="similar-section">
        <div class="section-head">
          <h2>유사 제품 추천</h2>
          <p>23 베어 그레이프와 유사한 색상의 제품들이에요.</p>
        </div>

        <div class="similar-grid">
          <article class="similar-card" v-for="item in similarProducts" :key="item.name">
            <div class="similar-img" :class="item.imageClass"></div>

            <div>
              <p class="brand">{{ item.brand }}</p>
              <h3>{{ item.name }}</h3>
              <p>{{ item.option }}</p>
              <div class="dots">
                <span v-for="color in item.colors" :key="color" :style="{ backgroundColor: color }"></span>
              </div>
              <strong>유사도 {{ item.score }}%</strong>
            </div>
          </article>
        </div>
      </section>

      <section class="bottom-grid">
        <div class="purchase-box">
          <h2>구매하기</h2>
          <p>아래 링크를 통해 제품을 구매할 수 있어요.</p>

          <button class="olive">OLIVE YOUNG <span>올리브영 바로가기 ↗</span></button>
          <button class="brand-link">rom&nd <span>브랜드 공식몰 바로가기 ↗</span></button>
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

          <button class="more-review">후기 더 보기 ›</button>
        </div>

        <aside class="action-box">
          <button class="main-btn">♡ 찜하기</button>
          <button class="outline-btn">▱ 마이페이지에서 보기</button>
          <button class="outline-btn">✨ 다른 제품 분석하기 →</button>

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

      <p class="notice">🛡️ 분석 결과는 참고용이며, 개인의 피부 톤과 환경에 따라 다를 수 있습니다.</p>
    </main>
  </div>
</template>

<script setup>
import AppHeader from '@/components/AppHeader.vue'

const compareItems = [
  { icon: '☀️', name: '명도 (밝기)', mine: 65, product: 68, diff: '+3', analysis: '제품이 조금 더 밝아요.' },
  { icon: '💧', name: '채도 (선명도)', mine: 30, product: 32, diff: '+2', analysis: '아주 약간 더 선명해요.' },
  { icon: '❄️', name: '쿨톤 (온도감)', mine: 85, product: 87, diff: '+2', analysis: '쿨톤감이 잘 맞아요.' },
  { icon: '☁️', name: '탁도 (탁한 정도)', mine: 18, product: 16, diff: '-2', analysis: '제품이 조금 더 맑아요.' },
  { icon: '◐', name: '대비 (명암 대비)', mine: 35, product: 37, diff: '+2', analysis: '대비감이 잘 맞아요.' },
]

const similarProducts = [
  {
    brand: 'rom&nd',
    name: '쥬시 래스팅 틴트',
    option: '25 베어 그레이프',
    score: 93,
    imageClass: 'lip2',
    colors: ['#c86175', '#e29aac', '#e9bec5', '#cdb2c8', '#c3bec6', '#c7c2c2'],
  },
  {
    brand: 'peripera',
    name: '잉크 무드 글로이 틴트',
    option: '07 쿨베리',
    score: 91,
    imageClass: 'lip4',
    colors: ['#c45d73', '#dc8798', '#e6aeb9', '#cab5c6', '#c6bebd'],
  },
  {
    brand: 'dasique',
    name: '크림 드 로즈 틴트',
    option: '12 모브 베리',
    score: 89,
    imageClass: 'lip5',
    colors: ['#c35d72', '#d9909d', '#e8b8c0', '#c8b4c4', '#c7c2c5'],
  },
  {
    brand: '3CE',
    name: '벨벳 립 틴트',
    option: 'DAFFODIL',
    score: 87,
    imageClass: 'lip3',
    colors: ['#bd6074', '#d78090', '#e5abb4', '#c7b2c3', '#c8c2c5'],
  },
]

const reviews = [
  { name: '봄날의핑크', text: '여쿨라에게 찰떡인 MLBB 컬러예요! 자연스럽고 데일리로 최고 💕', date: '2024.05.18' },
  { name: '라이트여쿨', text: '23호 진짜 인생템이에요ㅠㅠ 베어한 느낌이 너무 예뻐요!', date: '2024.05.16' },
  { name: 'subina_beauty', text: '차분한 포도빛이라 쿨톤 피부에 착붙입니다! 발색도 예쁘고 지속력도 좋아요.', date: '2024.05.14' },
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

.detail-page {
  padding: 28px 64px 52px;
  background:
    radial-gradient(circle at 50% 0%, rgba(255, 233, 225, 0.9), transparent 38%),
    linear-gradient(180deg, #fffaf7 0%, #fbf4f1 100%);
}

.back {
  font-size: 14px;
  margin-bottom: 4px;
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
  background:
    radial-gradient(ellipse at 35% 58%, rgba(180, 80, 100, 0.42) 0 30%, transparent 31%),
    linear-gradient(90deg, transparent 42%, #a75a70 43% 56%, transparent 57%),
    linear-gradient(135deg, transparent 0 58%, rgba(190, 74, 94, 0.5) 59% 68%, transparent 69%),
    linear-gradient(135deg, #fff3ef, #f4d8d1);
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
  background: #b4818e;
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

.legend .product {
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

.top { top: 0; left: 50%; transform: translateX(-50%); }
.right { right: 0; top: 43%; }
.bottom-right { right: 30px; bottom: 8px; }
.bottom-left { left: 30px; bottom: 8px; }
.left { left: 0; top: 43%; }

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

.table-row:last-of-type {
  border-bottom: none;
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

.fill.product {
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
  margin-bottom: 32px;
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
}

.similar-img {
  width: 80px;
  height: 100px;
  border-radius: 10px;
  flex-shrink: 0;
}

.lip2 {
  background:
    linear-gradient(90deg, transparent 40%, #f0b6c0 41% 52%, transparent 53%),
    linear-gradient(90deg, transparent 60%, #edc4cb 61% 72%, transparent 73%),
    linear-gradient(135deg, #fff1eb, #f7d5d5);
}

.lip3 {
  background:
    radial-gradient(ellipse at 36% 55%, rgba(150, 68, 84, 0.5) 0 30%, transparent 31%),
    linear-gradient(90deg, transparent 55%, #a85b70 56% 68%, transparent 69%),
    linear-gradient(135deg, #fff1eb, #f7d5d5);
}

.lip4 {
  background:
    linear-gradient(90deg, transparent 38%, #d45b6c 39% 52%, transparent 53%),
    linear-gradient(90deg, transparent 58%, #b73e4e 59% 75%, transparent 76%),
    linear-gradient(135deg, #fff1eb, #f7d5d5);
}

.lip5 {
  background:
    linear-gradient(90deg, transparent 40%, #d78994 41% 55%, transparent 56%),
    linear-gradient(90deg, transparent 64%, #f0c2c6 65% 78%, transparent 79%),
    linear-gradient(135deg, #fff1eb, #f7d5d5);
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
    linear-gradient(90deg, transparent 48%, rgba(255,255,255,0.6) 50%),
    linear-gradient(0deg, transparent 48%, rgba(255,255,255,0.6) 50%),
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