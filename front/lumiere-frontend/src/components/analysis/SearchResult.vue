<template>
  <div class="search-result-container">
    
    <section class="result-section">
      <div class="section-header">
        <span class="search-icon">🔍</span>
        <h3 class="section-title">검색 결과 미리보기</h3>
      </div>

      <div class="product-grid">
        <div v-for="product in products" :key="product.id" class="product-card">
          <div class="image-wrapper">
            <img :src="product.image || 'https://via.placeholder.com/150?text=Product'" :alt="product.name" class="product-img" />
          </div>
          
          <div class="product-info">
            <span class="category-tag">{{ product.category }}</span>
            <p class="brand">{{ product.brand }}</p>
            <p class="name">{{ product.name }}</p>
            <p class="price">{{ product.price }}</p>
            
            <div class="color-swatches">
              <span 
                v-for="(color, index) in product.colors" 
                :key="index" 
                class="swatch" 
                :style="{ backgroundColor: color }"
              ></span>
            </div>
          </div>
        </div>
      </div>

      <button class="load-more-btn">
        더 많은 검색 결과 보기 &gt;
      </button>
    </section>

    <aside class="info-banner">
      <h3 class="banner-title">Lumiere만의 특별한 분석</h3>
      
      <ul class="feature-list">
        <li>
          <span class="feature-icon">☼</span>
          <div class="feature-text">
            <strong>색상 옵션 추출</strong>
            <p>제품 페이지에서 모든 색상 옵션을 자동으로 추출해요.</p>
          </div>
        </li>
        <li>
          <span class="feature-icon">⚖️</span>
          <div class="feature-text">
            <strong>피부톤과 비교</strong>
            <p>당신의 퍼스널컬러와 가장 잘 어울리는 색상을 분석해요.</p>
          </div>
        </li>
        <li>
          <span class="feature-icon">🌿</span>
          <div class="feature-text">
            <strong>맞춤 추천</strong>
            <p>적합도 점수와 함께 추천 이유를 자세히 알려드려요.</p>
          </div>
        </li>
      </ul>
    </aside>

  </div>
</template>

<script setup>
import { ref } from 'vue';

// 💡 목업 이미지를 기반으로 한 더미(임시) 데이터입니다.
// 실제 개발 시에는 부모 컴포넌트(AnalysisView.vue)에서 props로 데이터를 받아오도록 수정하면 됩니다.
const products = ref([
  {
    id: 1,
    category: '틴트',
    brand: 'rom&nd',
    name: '블러 퍼지 틴트 23 베어 그레이프',
    price: '13,000원',
    colors: ['#D98894', '#C76A78', '#A94858', '#8E3845', '#EAC1C8'],
    image: '' // 비워두면 placeholder 이미지가 나옵니다.
  },
  {
    id: 2,
    category: '립스틱',
    brand: '3CE',
    name: '벨벳 립 컬러 DAFFODIL',
    price: '17,900원',
    colors: ['#C85A5A', '#A03C3C', '#E68282', '#641E1E', '#F0A0A0'],
    image: ''
  },
  {
    id: 3,
    category: '블러셔',
    brand: 'fwee',
    name: '퓨어 블러셔 ND02 오디 모브',
    price: '12,000원',
    colors: ['#DCA0B4', '#C87896', '#E6C8D2', '#B45A78', '#F0DCE6'],
    image: ''
  },
  {
    id: 4,
    category: '아이섀도우',
    brand: 'CLIO',
    name: '프로 아이 팔레트 13 피치 크러쉬',
    price: '32,000원',
    colors: ['#F5D2C8', '#E6A08C', '#C86450', '#AA3C28', '#821E0A'],
    image: ''
  }
]);
</script>

<style scoped>
/* 전체 컨테이너: 좌우 분할 레이아웃 */
.search-result-container {
  display: flex;
  gap: 30px;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px 40px;
  font-family: 'Pretendard', sans-serif;
}

@media (max-width: 992px) {
  .search-result-container {
    flex-direction: column; /* 화면이 작아지면 위아래로 배치 */
  }
}

/* =========================================
   1. 왼쪽: 검색 결과 리스트 영역
   ========================================= */
.result-section {
  flex: 7; /* 좌측이 약 70% 비율 차지 */
  background: #ffffff;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}
.search-icon {
  font-size: 1.2rem;
  color: #888;
}
.section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
  margin: 0;
}

/* 제품 그리드 (4열 배치) */
.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 25px;
}
@media (max-width: 768px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 개별 제품 카드 */
.product-card {
  display: flex;
  flex-direction: column;
}
.image-wrapper {
  background: #f8f8f8;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 12px;
  aspect-ratio: 1 / 1;
}
.product-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.product-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.category-tag {
  background: #f3f3f3;
  color: #888;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 10px;
  margin-bottom: 6px;
}
.brand {
  font-size: 0.8rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 2px 0;
}
.name {
  font-size: 0.85rem;
  color: #555;
  margin: 0 0 6px 0;
  line-height: 1.3;
  /* 말줄임표 처리 (2줄 이상 시) */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.price {
  font-size: 0.95rem;
  font-weight: 700;
  color: #333;
  margin: 0 0 10px 0;
}

/* 색상 동그라미 스와치 */
.color-swatches {
  display: flex;
  gap: 4px;
}
.swatch {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.05);
}

/* 더보기 버튼 */
.load-more-btn {
  width: 100%;
  background: #f9f9f9;
  border: 1px solid #eee;
  color: #666;
  padding: 12px 0;
  border-radius: 10px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}
.load-more-btn:hover {
  background: #f0f0f0;
  color: #333;
}

/* =========================================
   2. 오른쪽: Lumiere만의 특별한 분석 안내 배너
   ========================================= */
.info-banner {
  flex: 3; /* 우측이 약 30% 비율 차지 */
  background: #fff8fa; /* 연한 핑크 배경 */
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
  border: 1px solid #fce8ed;
}

.banner-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
  margin: 0 0 24px 0;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.feature-list li {
  display: flex;
  gap: 12px;
}
.feature-icon {
  font-size: 1.2rem;
  margin-top: 2px;
}
.feature-text strong {
  display: block;
  font-size: 0.9rem;
  color: #333;
  margin-bottom: 4px;
}
.feature-text p {
  font-size: 0.8rem;
  color: #777;
  margin: 0;
  line-height: 1.4;
}
</style>