<template>
  <div class="recent-analysis-container">
    
    <div class="section-header">
      <div class="header-left">
        <span class="clock-icon">🕒</span>
        <h3 class="section-title">최근 분석한 제품</h3>
      </div>
      <button class="view-all-btn">전체 보기 &gt;</button>
    </div>

    <div class="carousel-wrapper">
      
      <button class="nav-btn prev-btn" @click="scroll('left')">&lt;</button>

      <div class="carousel-track" ref="trackRef">
        
        <div class="history-card" v-for="item in recentItems" :key="item.id">
          <button class="delete-btn" @click="removeItem(item.id)">✕</button>

          <div class="card-content">
            <div class="image-box">
              <img :src="item.image || 'https://via.placeholder.com/80?text=Img'" :alt="item.name" />
            </div>

            <div class="info-box">
              <p class="brand">{{ item.brand }}</p>
              <p class="name">{{ item.name }}</p>
              <p class="date">분석일 {{ item.date }}</p>

              <div class="bottom-action">
                <div class="color-swatches">
                  <span 
                    v-for="(color, idx) in item.colors" 
                    :key="idx" 
                    class="swatch" 
                    :style="{ backgroundColor: color }"
                  ></span>
                </div>
                <button class="result-btn" @click="viewResult(item.id)">
                  결과 보기 &gt;
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>

      <button class="nav-btn next-btn" @click="scroll('right')">&gt;</button>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const trackRef = ref(null);

// 💡 목업 이미지에 기반한 최근 분석 기록 더미 데이터
const recentItems = ref([
  {
    id: 101,
    brand: 'rom&nd',
    name: '블러 퍼지 틴트\n23 베어 그레이프',
    date: '2024.05.20',
    colors: ['#D98894', '#C76A78', '#A94858', '#8E3845', '#EAC1C8'],
    image: ''
  },
  {
    id: 102,
    brand: 'espoir',
    name: '프로 테일러 비 글로우\n파운데이션 21호 아이보리',
    date: '2024.05.19',
    colors: ['#F5E6D3', '#EED8C0', '#E5CAA8', '#D8B894', '#CBA37E'],
    image: ''
  },
  {
    id: 103,
    brand: 'dasique',
    name: '섀도우 팔레트\n07 밀크 라떼',
    date: '2024.05.18',
    colors: ['#E8DCC8', '#D6BFA4', '#C4A180', '#A87D5D', '#8C5A3E'],
    image: ''
  },
  {
    id: 104,
    brand: 'peripera',
    name: '맑게 물든 선샤인 치크\n05 봄바람 핑크',
    date: '2024.05.17',
    colors: ['#F4A3B4', '#EE8297', '#E55F7A', '#D83C5A', '#C41E40'],
    image: ''
  }
]);

// 좌우 화살표 클릭 시 스크롤 이동 로직
const scroll = (direction) => {
  if (!trackRef.value) return;
  
  // 한 번 클릭할 때 이동할 픽셀량 (카드 한 장 너비 정도)
  const scrollAmount = 350; 
  
  if (direction === 'left') {
    trackRef.value.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
  } else {
    trackRef.value.scrollBy({ left: scrollAmount, behavior: 'smooth' });
  }
};

// 개별 삭제 버튼 로직
const removeItem = (id) => {
  recentItems.value = recentItems.value.filter(item => item.id !== id);
};

// 결과 보기 버튼 클릭 시 라우터 이동
const viewResult = (id) => {
  // 이전 대화에서 세팅한 과거 분석 결과 라우터 주소로 이동합니다.
  router.push(`/analysis/result/${id}`);
};
</script>

<style scoped>
/* 전체 컨테이너 */
.recent-analysis-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  margin-bottom: 40px;
  background: #ffffff;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  font-family: 'Pretendard', sans-serif;
}

/* 헤더 영역 */
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
  font-size: 1.2rem;
  color: #888;
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
  color: #b75a73; /* 브랜드 컬러 */
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}

/* 캐러셀 래퍼 */
.carousel-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

/* 좌우 네비게이션 버튼 */
.nav-btn {
  position: absolute;
  z-index: 10;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ffffff;
  border: 1px solid #eaeaea;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  font-size: 1.2rem;
  color: #666;
  transition: all 0.2s;
}
.nav-btn:hover {
  background: #f8f8f8;
  color: #333;
}
.prev-btn {
  left: -20px; /* 박스 바깥쪽으로 살짝 걸치게 배치 */
}
.next-btn {
  right: -20px;
}

/* 리스트 트랙 (가로 스크롤 영역) */
.carousel-track {
  display: flex;
  gap: 20px;
  overflow-x: auto; /* 내용이 넘치면 스크롤 생성 */
  scroll-behavior: smooth;
  padding: 10px 5px; /* 그림자가 잘리지 않도록 여백 부여 */
  
  /* 스크롤바 숨기기 (디자인 깔끔하게) */
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}
.carousel-track::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
}

/* 개별 히스토리 카드 */
.history-card {
  position: relative;
  min-width: 320px; /* 카드 최소 너비 고정 */
  background: #ffffff;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s;
}
.history-card:hover {
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}

/* X 삭제 버튼 */
.delete-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  font-size: 1.1rem;
  color: #ccc;
  cursor: pointer;
}
.delete-btn:hover {
  color: #ff6b6b;
}

/* 카드 내부 콘텐츠 (이미지 + 텍스트 가로 배치) */
.card-content {
  display: flex;
  gap: 16px;
}

/* 제품 이미지 영역 */
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

/* 제품 정보 영역 */
.info-box {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.brand {
  font-size: 0.8rem;
  color: #666;
  font-weight: 600;
  margin: 0 0 4px 0;
}
.name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #333;
  margin: 0 0 6px 0;
  line-height: 1.4;
  white-space: pre-line; /* \n 을 인식해서 줄바꿈 처리 */
}
.date {
  font-size: 0.75rem;
  color: #aaa;
  margin: 0 0 12px 0;
}

/* 하단 액션 영역 (스와치 + 버튼) */
.bottom-action {
  margin-top: auto; /* 하단으로 밀어내기 */
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 색상 팔레트 */
.color-swatches {
  display: flex;
  gap: 4px;
}
.swatch {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.05);
}

/* 결과 보기 버튼 */
.result-btn {
  background: none;
  border: none;
  color: #b75a73;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}
.result-btn:hover {
  text-decoration: underline;
}
</style>