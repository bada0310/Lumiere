<template>
  <div class="search-result-container">
    <section class="result-section">
      <div class="section-header">
        <span class="search-icon" aria-hidden="true">P</span>
        <h3 class="section-title">검색 결과 미리 보기</h3>
      </div>

      <div v-if="loading" class="state-line">제품을 검색하는 중입니다.</div>
      <div v-else-if="searched && !products.length" class="state-line">검색 결과가 없습니다.</div>

      <div v-else class="product-grid">
        <button
          v-for="product in products"
          :key="product.id"
          type="button"
          class="product-card"
          :class="{ active: String(selectedProductId) === String(product.id) }"
          @click="$emit('select-product', product)"
        >
          <div class="image-wrapper">
            <img :src="product.thumbnailUrl || 'https://via.placeholder.com/150?text=Product'" :alt="product.productName" class="product-img" />
          </div>

          <div class="product-info">
            <span class="category-tag">{{ product.category || 'PRODUCT' }}</span>
            <p class="brand">{{ product.brandName || '브랜드 미상' }}</p>
            <p class="name">{{ product.productName || '제품명 없음' }}</p>
            <p class="price">옵션 {{ product.optionCount || 0 }}개</p>

            <div class="color-swatches">
              <span
                v-for="color in product.colors"
                :key="color"
                class="swatch"
                :style="{ backgroundColor: color }"
              ></span>
            </div>
            <span class="analysis-link">분석 보기 &gt;</span>
          </div>
        </button>
      </div>

      <button
        v-if="keyword && products.length"
        type="button"
        class="load-more-btn"
        @click="$emit('show-more')"
      >
        더 많은 검색 결과 보기 &gt;
      </button>
    </section>

    <aside class="info-banner">
      <h3 class="banner-title">Lumiere의 컬러 분석</h3>

      <ul class="feature-list">
        <li>
          <span class="feature-icon">1</span>
          <div class="feature-text">
            <strong>색상 옵션 추출</strong>
            <p>제품에 등록된 색상 옵션과 컬러 데이터를 한 화면에서 확인합니다.</p>
          </div>
        </li>
        <li>
          <span class="feature-icon">2</span>
          <div class="feature-text">
            <strong>퍼스널컬러 비교</strong>
            <p>메인 퍼스널컬러 기준으로 BEST / GOOD / CAUTION을 분류합니다.</p>
          </div>
        </li>
        <li>
          <span class="feature-icon">3</span>
          <div class="feature-text">
            <strong>추천 이유 확인</strong>
            <p>추천 점수와 옵션별 사용 팁을 아코디언으로 확인할 수 있습니다.</p>
          </div>
        </li>
      </ul>
    </aside>
  </div>
</template>

<script setup>
defineProps({
  products: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  searched: {
    type: Boolean,
    default: false,
  },
  keyword: {
    type: String,
    default: '',
  },
  selectedProductId: {
    type: [String, Number],
    default: '',
  },
})

defineEmits(['select-product', 'show-more'])
</script>

<style scoped>
.search-result-container {
  display: flex;
  gap: 30px;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px 40px;
  font-family: 'Pretendard', sans-serif;
}

.result-section {
  flex: 7;
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
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #fff0f4;
  color: #b75a73;
  display: grid;
  place-items: center;
  font-size: 0.75rem;
  font-weight: 900;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.state-line {
  border: 1px dashed #eaded8;
  border-radius: 12px;
  color: #8e7e79;
  padding: 24px;
  text-align: center;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 25px;
}

.product-card {
  border: 1px solid transparent;
  border-radius: 14px;
  background: white;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  text-align: left;
  padding: 0;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}

.product-card:hover,
.product-card.active {
  border-color: #b75a73;
  box-shadow: 0 8px 18px rgba(183, 90, 115, 0.12);
  transform: translateY(-1px);
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
  padding: 0 4px 4px;
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
  margin: 0 0 2px;
}

.name {
  font-size: 0.85rem;
  color: #555;
  margin: 0 0 6px;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.price {
  font-size: 0.9rem;
  font-weight: 700;
  color: #333;
  margin: 0 0 10px;
}

.color-swatches {
  display: flex;
  gap: 4px;
  min-height: 12px;
}

.swatch {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.analysis-link {
  margin-top: 10px;
  color: #b75a73;
  font-size: 0.8rem;
  font-weight: 800;
}

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

.info-banner {
  flex: 3;
  background: #fff8fa;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
  border: 1px solid #fce8ed;
}

.banner-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #333;
  margin: 0 0 24px;
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
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #fff0f4;
  color: #b75a73;
  display: grid;
  place-items: center;
  font-size: 0.75rem;
  font-weight: 900;
  margin-top: 2px;
  flex: 0 0 auto;
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

@media (max-width: 992px) {
  .search-result-container {
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 520px) {
  .product-grid {
    grid-template-columns: 1fr;
  }
}
</style>
