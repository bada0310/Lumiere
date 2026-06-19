<template>
  <div class="mypage-container">
    <section class="profile-section">
      <div class="profile-card">
        <div class="profile-image-wrapper">
          <img
            :src="userInfo.profileImage || 'https://via.placeholder.com/100'"
            alt="프로필 이미지"
            class="profile-img"
          />
        </div>

        <div class="profile-info">
          <div class="profile-header">
            <h2>
              {{ userInfo.nickname }}
              <span class="email">({{ userInfo.email }})</span>
            </h2>

            <button @click="editProfile" class="edit-btn">
              정보 수정
            </button>
          </div>

          <div
            class="personal-color-summary"
            :style="{ backgroundColor: latestDiagnosis?.colorThemeBg || '#f8f8f8' }"
          >
            <div>
              <p>
                나의 최근 퍼스널 컬러는
                <span class="color-highlight">
                  {{ latestDiagnosis?.personalColor || '미진단' }}
                </span>
                입니다.
              </p>

              <small v-if="latestDiagnosis">
                최근 진단일: {{ latestDiagnosis.date }} /
                신뢰도 {{ latestDiagnosis.confidenceScore }}%
              </small>
            </div>

            <button @click="goToDiagnosis" class="rediagnosis-btn">
              재진단하기
            </button>
          </div>
        </div>
      </div>
    </section>

    <div class="dashboard-grid">
      <!-- Diagnosis 목록 -->
      <section class="dashboard-card diagnosis-log">
        <h3>🎨 진단 기록 리스트</h3>

        <div v-if="diagnosisList.length === 0" class="empty-msg">
          진단 기록이 없습니다.
        </div>

        <ul v-else class="log-list">
          <li v-for="item in diagnosisList" :key="item.id" class="log-item">
            <div class="item-info">
              <span class="date">{{ item.date }}</span>
              <span class="result-tag" :class="item.resultClass">
                {{ item.result }}
              </span>
              <span class="confidence">신뢰도 {{ item.confidenceScore }}%</span>
            </div>

            <button @click="viewDiagnosisResult(item.id)" class="action-btn">
              결과 다시보기
            </button>
          </li>
        </ul>
      </section>

      <!-- Wishlist 목록 -->
      <section class="dashboard-card wishlist-log">
        <h3>❤️ 찜한 제품 옵션 목록</h3>

        <div v-if="wishlist.length === 0" class="empty-msg">
          찜한 제품이 없습니다.
        </div>

        <div v-else class="product-grid">
          <div
            v-for="product in wishlist"
            :key="product.id"
            class="product-card"
            @click="goToProductDetail(product.productOptionId)"
          >
            <img :src="product.image" alt="제품 이미지" class="product-img" />

            <div class="product-desc">
              <span class="brand">{{ product.brand }}</span>
              <p class="name">{{ product.name }}</p>
              <span class="option">{{ product.option }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ExternalAnalysis 목록 -->
      <section class="dashboard-card analysis-log">
        <h3>🔗 최근 URL 분석 기록</h3>

        <div v-if="analysisList.length === 0" class="empty-msg">
          분석 기록이 없습니다.
        </div>

        <ul v-else class="log-list">
          <li
            v-for="analysis in analysisList"
            :key="analysis.id"
            class="log-item"
            @click="goToAnalysisResult(analysis.id)"
          >
            <div class="item-info">
              <span class="platform-tag">올리브영</span>
              <p class="url-title">{{ analysis.title }}</p>
            </div>

            <span class="analysis-date">{{ analysis.date }}</span>
          </li>
        </ul>
      </section>

      <!-- Community 목록 -->
      <section class="dashboard-card community-log">
        <h3>📝 내가 쓴 커뮤니티 글</h3>

        <div v-if="communityList.length === 0" class="empty-msg">
          작성한 글이 없습니다.
        </div>

        <ul v-else class="log-list">
          <li v-for="post in communityList" :key="post.id" class="log-item">
            <span class="post-title">{{ post.title }}</span>
            <span class="post-comments">[{{ post.commentCount }}]</span>
          </li>
        </ul>
      </section>
    </div> <ProfileEditModal 
      :isOpen="isEditModalOpen"
      :username="userInfo.username"
      :initialEmail="userInfo.email"
      :initialNickname="userInfo.nickname"
      :initialImage="userInfo.profileImage"
      @close="closeEditModal"
      @save="handleSaveProfile"
      @delete="handleDeleteAccount"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import ProfileEditModal from '@/components/accounts/ProfileEditModal.vue'
const router = useRouter()

// User 데이터
const userInfo = ref({
  id: 1,
  username: 'subina123', // 고유 아이디 추가
  nickname: 'Subina',
  email: 'subina@example.com',
  profileImage: '',
})


// Diagnosis 1:N 데이터
const diagnosisList = ref([
  {
    id: 101,
    date: '2026-06-01',
    result: '여름 쿨 라이트',
    resultClass: 'summer-cool',
    confidenceScore: 93,
    colorThemeBg: '#f3f8fc',
  },
  {
    id: 102,
    date: '2026-03-15',
    result: '봄 웜 라이트',
    resultClass: 'spring-warm',
    confidenceScore: 88,
    colorThemeBg: '#fff5e8',
  },
])

// 최근 Diagnosis 요약
const latestDiagnosis = computed(() => {
  return diagnosisList.value.length > 0 ? diagnosisList.value[0] : null
})

// Wishlist 1:N 데이터
// id = Wishlist id
// productOptionId = 실제 상세 페이지로 이동할 ProductOption id
const wishlist = ref([
  {
    id: 1,
    productOptionId: 101,
    brand: '롬앤',
    name: '쥬시 래스팅 틴트',
    option: '25호 베어 그레이프',
    image: 'https://via.placeholder.com/60',
  },
  {
    id: 2,
    productOptionId: 102,
    brand: '클리오',
    name: '프로 아이 팔레트 에어',
    option: '04 핑크 페어링',
    image: 'https://via.placeholder.com/60',
  },
])

// ExternalAnalysis 1:N 데이터
const analysisList = ref([
  {
    id: 501,
    title: '데이지크 블러 벨벳 틴트 분석 결과',
    date: '2026-06-10',
  },
  {
    id: 502,
    title: '페리페라 올테이크 무드 팔레트 분석 결과',
    date: '2026-05-28',
  },
])

// 커뮤니티 데이터
const communityList = ref([
  {
    id: 1,
    title: '여름 쿨톤 인생 립 추천해주세요!',
    commentCount: 5,
  },
  {
    id: 2,
    title: '오늘 올리브영 세일 꿀템 공유합니다',
    commentCount: 2,
  },
])

//profileEditModal.vue

//모달창 On/Off 스위치 만들기
const isEditModalOpen = ref(false) 

// 알람 대신 스위치
const editProfile = () => {
  isEditModalOpen.value = true
}
//모달창 닫기, 저장, 탈퇴 처리를 위한 함수 추가
const closeEditModal = () => {
  isEditModalOpen.value = false
}

const handleSaveProfile = (formData) => {
  console.log("모달에서 넘어온 수정 데이터:", formData)
  
  // 1. 화면에 변경된 정보 즉시 반영하기 (프론트 단독 테스트용)
  userInfo.value.nickname = formData.nickname
  userInfo.value.email = formData.email
  if (formData.profileImage) {
    // 선택한 이미지 파일을 브라우저 임시 주소로 만들어서 바로 보여줍니다.
    userInfo.value.profileImage = URL.createObjectURL(formData.profileImage)
  }
  
  // 2. 성공 알림
  alert('정보가 성공적으로 수정되었습니다!')
  
  // ★ 3. 여기서 반드시 모달 스위치를 꺼주어야 창이 닫힙니다! ★
  isEditModalOpen.value = false 
}

// 마이페이지 → 재진단
const goToDiagnosis = () => {
  router.push('/upload')
}

// 마이페이지 → 과거 진단 결과
const viewDiagnosisResult = (id) => {
  router.push(`/result/${id}`)
}

// 마이페이지 → 찜한 제품 옵션 상세
const goToProductDetail = (productOptionId) => {
  router.push(`/product-detail/${productOptionId}`)
}

// 마이페이지 → 최근 URL 분석 결과
const goToAnalysisResult = (id) => {
  router.push(`/analysis/result/${id}`)
}

</script>

<style scoped>
.mypage-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: 'Pretendard', sans-serif;
  color: #333;
}

.profile-section {
  background: white;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  margin-bottom: 40px;
}

.profile-card {
  display: flex;
  gap: 30px;
  align-items: center;
}

.profile-img {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #eee;
}

.profile-info {
  flex: 1;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.profile-header h2 {
  font-size: 1.5rem;
  margin: 0;
}

.profile-header .email {
  font-size: 0.95rem;
  color: #888;
  font-weight: normal;
}

.edit-btn {
  background: none;
  border: 1px solid #ccc;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
}

.personal-color-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 25px;
  border-radius: 12px;
}

.personal-color-summary p {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 500;
}

.personal-color-summary small {
  display: block;
  margin-top: 6px;
  color: #777;
}

.color-highlight {
  color: #8b3a4a;
  font-weight: bold;
}

.rediagnosis-btn {
  background-color: #8b3a4a;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

.dashboard-card {
  background: white;
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  min-height: 250px;
}

.dashboard-card h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.2rem;
  border-bottom: 2px solid #f9f9f9;
  padding-bottom: 10px;
}

.empty-msg {
  color: #aaa;
  text-align: center;
  padding: 40px 0;
  font-size: 0.95rem;
}

.log-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.log-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
}

.log-item:last-child {
  border-bottom: none;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.date {
  color: #888;
  font-size: 0.9rem;
}

.confidence {
  color: #999;
  font-size: 0.8rem;
}

.result-tag {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
}

.summer-cool {
  background-color: #e3f2fd;
  color: #1e88e5;
}

.spring-warm {
  background-color: #fff3e0;
  color: #fb8c00;
}

.action-btn {
  background: #f5f5f5;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.product-card {
  display: flex;
  gap: 12px;
  padding: 10px;
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  align-items: center;
  cursor: pointer;
}

.product-card:hover {
  background: #fff7f5;
}

.product-img {
  width: 50px;
  height: 50px;
  border-radius: 6px;
  object-fit: cover;
}

.product-desc {
  display: flex;
  flex-direction: column;
}

.product-desc .brand {
  font-size: 0.75rem;
  color: #999;
}

.product-desc .name {
  font-size: 0.85rem;
  margin: 2px 0;
  font-weight: bold;
}

.product-desc .option {
  font-size: 0.75rem;
  color: #666;
}

.platform-tag {
  background-color: #efebe9;
  color: #4e342e;
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 4px;
}

.url-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 500;
}

.analysis-date {
  font-size: 0.85rem;
  color: #bbb;
}

.post-title {
  font-size: 0.9rem;
}

.post-comments {
  color: #8b3a4a;
  font-size: 0.85rem;
  font-weight: bold;
  margin-left: 5px;
}
</style>