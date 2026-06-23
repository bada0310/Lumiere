<template>
  <section class="recent-analysis-container">
    <div class="section-header">
      <div class="header-left">
        <span class="clock-icon" aria-hidden="true">R</span>
        <h3 class="section-title">최근 분석한 제품</h3>
      </div>
      <button class="view-all-btn" type="button" :disabled="!items.length" @click="scroll('right')">
        전체 보기
      </button>
    </div>

    <div v-if="loading" class="state-line">최근 분석 기록을 불러오는 중입니다.</div>
    <div v-else-if="!items.length" class="state-line">최근 분석한 제품이 없습니다.</div>

    <div v-else class="carousel-wrapper">
      <button class="nav-btn prev-btn" type="button" @click="scroll('left')">&lt;</button>

      <div ref="trackRef" class="carousel-track">
        <article
          v-for="item in items"
          :key="item.id"
          class="history-card"
          :class="{ active: String(selectedId) === String(item.id) }"
        >
          <button class="delete-btn" type="button" aria-label="최근 분석 삭제" @click.stop="$emit('delete-analysis', item)">
            ×
          </button>

          <button class="card-button" type="button" @click="$emit('select-analysis', item)">
            <div class="image-box">
              <img :src="item.thumbnailUrl || 'https://via.placeholder.com/80?text=Img'" :alt="item.productName" />
            </div>

            <div class="info-box">
              <p class="brand">{{ item.brandName || '브랜드 미상' }}</p>
              <p class="name">{{ item.productName || item.title || '분석한 제품' }}</p>
              <p class="date">분석일 {{ formatDate(item.analyzedAt) }}</p>

              <div class="bottom-action">
                <div class="color-swatches">
                  <span
                    v-for="color in item.colors"
                    :key="color"
                    class="swatch"
                    :style="{ backgroundColor: color }"
                  ></span>
                </div>
                <span class="result-btn">결과 보기 &gt;</span>
              </div>
            </div>
          </button>
        </article>
      </div>

      <button class="nav-btn next-btn" type="button" @click="scroll('right')">&gt;</button>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  selectedId: {
    type: [String, Number],
    default: '',
  },
})

defineEmits(['select-analysis', 'delete-analysis'])

const trackRef = ref(null)

const scroll = (direction) => {
  if (!trackRef.value) return
  const scrollAmount = 350
  trackRef.value.scrollBy({ left: direction === 'left' ? -scrollAmount : scrollAmount, behavior: 'smooth' })
}

const formatDate = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
.recent-analysis-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto 40px;
  background: #ffffff;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  font-family: 'Pretendard', sans-serif;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.clock-icon {
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

.view-all-btn {
  background: none;
  border: none;
  color: #b75a73;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}

.view-all-btn:disabled {
  color: #bbb;
  cursor: not-allowed;
}

.state-line {
  border: 1px dashed #eaded8;
  border-radius: 12px;
  color: #8e7e79;
  padding: 24px;
  text-align: center;
}

.carousel-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.nav-btn {
  position: absolute;
  z-index: 10;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ffffff;
  border: 1px solid #eaeaea;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  font-size: 1.2rem;
  color: #666;
}

.prev-btn {
  left: -20px;
}

.next-btn {
  right: -20px;
}

.carousel-track {
  display: flex;
  gap: 20px;
  overflow-x: auto;
  scroll-behavior: smooth;
  padding: 10px 5px;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.carousel-track::-webkit-scrollbar {
  display: none;
}

.history-card {
  position: relative;
  min-width: 320px;
  background: #ffffff;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.history-card:hover,
.history-card.active {
  border-color: #b75a73;
  box-shadow: 0 4px 15px rgba(183, 90, 115, 0.12);
}

.delete-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 2;
  background: white;
  border: none;
  border-radius: 50%;
  width: 26px;
  height: 26px;
  font-size: 1.1rem;
  color: #bbb;
  cursor: pointer;
}

.delete-btn:hover {
  color: #b75a73;
}

.card-button {
  width: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  display: flex;
  gap: 16px;
  padding: 20px;
}

.image-box {
  width: 70px;
  height: 90px;
  background: #f9f9f9;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  flex-shrink: 0;
}

.image-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.info-box {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.brand {
  font-size: 0.8rem;
  color: #666;
  font-weight: 600;
  margin: 0 0 4px;
}

.name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #333;
  margin: 0 0 6px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.date {
  font-size: 0.75rem;
  color: #aaa;
  margin: 0 0 12px;
}

.bottom-action {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.color-swatches {
  display: flex;
  gap: 4px;
  min-height: 14px;
}

.swatch {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.result-btn {
  color: #b75a73;
  font-size: 0.8rem;
  font-weight: 700;
  white-space: nowrap;
}
</style>
