<template>
  <div class="mypage-container">
    <section class="profile-section">
      <div class="profile-card">
        <UserAvatar
          :src="resolvedProfileImageUrl"
          :alt="`${userInfo.nickname} 프로필 이미지`"
          :name="userInfo.nickname"
          size="xl"
          class-name="profile-img"
        />

        <div class="profile-info">
          <div class="profile-header">
            <h2>
              {{ userInfo.nickname }}
              <span class="email">({{ userInfo.email || 'email 없음' }})</span>
            </h2>

            <button type="button" @click="editProfile" class="edit-btn">
              정보 수정
            </button>
          </div>

          <div class="personal-color-summary">
            <div>
              <p>
                나의 최근 퍼스널 컬러는
                <span class="color-highlight">
                  {{ latestDiagnosis?.result || '미진단' }}
                </span>
                입니다.
              </p>

              <small v-if="latestDiagnosis">
                최근 진단일 {{ latestDiagnosis.date }} /
                신뢰도 {{ latestDiagnosis.confidenceScore }}%
              </small>
              <small v-else>진단을 완료하면 결과 타입별 기본 프로필 이미지가 적용돼요.</small>
            </div>

            <button type="button" @click="goToDiagnosis" class="rediagnosis-btn">
              다시 진단하기
            </button>
          </div>
        </div>
      </div>
    </section>

    <div class="dashboard-grid">
      <section class="dashboard-card diagnosis-log">
        <h3>진단 기록 리스트</h3>

        <div v-if="diagnosisList.length === 0" class="empty-msg">
          진단 기록이 없습니다.
        </div>

        <ul v-else class="log-list">
          <li v-for="item in diagnosisList" :key="item.id" class="log-item">
            <div class="item-info">
              <span class="date">{{ item.date }}</span>
              <span class="result-tag">
                {{ item.result }}
              </span>
              <span class="confidence">신뢰도 {{ item.confidenceScore }}%</span>
              <span v-if="item.isMock" class="mock-tag">mock</span>
            </div>

            <button type="button" @click="viewDiagnosisResult(item)" class="action-btn">
              결과 다시보기
            </button>
          </li>
        </ul>
      </section>

      <section class="dashboard-card wishlist-log">
        <h3>찜한 제품 옵션 목록</h3>

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

      <section class="dashboard-card analysis-log">
        <h3>최근 URL 분석 기록</h3>

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

      <section class="dashboard-card community-log">
        <h3>내가 쓴 커뮤니티 글</h3>

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
    </div>

    <ProfileEditModal
      :isOpen="isEditModalOpen"
      :username="userInfo.username"
      :initialEmail="userInfo.email"
      :initialNickname="userInfo.nickname"
      :initialImage="currentUser?.profileImageUrl"
      :isSaving="isSavingProfile"
      @close="closeEditModal"
      @save="handleSaveProfile"
      @delete="handleDeleteAccount"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import ProfileEditModal from '@/components/accounts/ProfileEditModal.vue'
import UserAvatar from '@/components/user/UserAvatar.vue'
import { useCurrentUser } from '@/composables/useCurrentUser'
import { useRequireLogin } from '@/composables/useRequireLogin'
import { DEFAULT_PROFILE_IMAGE } from '@/constants/images'
import { getLatestDiagnosis } from '@/services/diagnosisApi'
import { getSavedMockDiagnosisResult } from '@/utils/diagnosisMockStorage'
import { getDiagnosisProfileImageUrl, normalizeDiagnosisResult } from '@/utils/diagnosisResultTransform'

const router = useRouter()
const { currentUser, loadCurrentUser, saveCurrentUser } = useCurrentUser()
const { handleAuthFailure } = useRequireLogin()

const isEditModalOpen = ref(false)
const isSavingProfile = ref(false)
const latestDiagnosisFromApi = ref(null)
const savedMockDiagnosis = ref(null)

const userInfo = computed(() => ({
  id: currentUser.value?.id || null,
  username: currentUser.value?.username || '',
  nickname: currentUser.value?.nickname || currentUser.value?.username || '사용자',
  email: currentUser.value?.email || '',
}))

const normalizedLatestDiagnosis = computed(() => {
  const source = latestDiagnosisFromApi.value || savedMockDiagnosis.value
  return source ? normalizeDiagnosisResult(source) : null
})

const resolvedProfileImageUrl = computed(() => {
  return currentUser.value?.profileImageUrl || getDiagnosisProfileImageUrl(normalizedLatestDiagnosis.value) || DEFAULT_PROFILE_IMAGE
})

const diagnosisList = computed(() => {
  if (!normalizedLatestDiagnosis.value) return []

  const result = normalizedLatestDiagnosis.value
  return [
    {
      id: result.id,
      date: new Date(result.diagnosed_at || result.created_at).toLocaleDateString('ko-KR'),
      result: result.korean_name || '진단 결과',
      toneKey: result.personal_color_code,
      mockQuery: result.type || result.personal_color_code,
      confidenceScore: result.confidence_score || result.confidence,
      isMock: Boolean(result.is_mock),
    },
  ]
})

const latestDiagnosis = computed(() => diagnosisList.value[0] || null)

const wishlist = ref([
  {
    id: 1,
    productOptionId: 101,
    brand: 'rom&nd',
    name: '쥬시 래스팅 틴트',
    option: '25 베어 그레이프',
    image: 'https://via.placeholder.com/60',
  },
])

const analysisList = ref([])
const communityList = ref([])

const editProfile = () => {
  isEditModalOpen.value = true
}

const closeEditModal = () => {
  isEditModalOpen.value = false
}

const handleSaveProfile = async (formData) => {
  isSavingProfile.value = true

  try {
    await saveCurrentUser({
      email: formData.email,
      nickname: formData.nickname,
      profileImage: formData.profileImage,
    })
    isEditModalOpen.value = false
  } catch (error) {
    console.error('프로필 저장 실패:', error)
    if (handleAuthFailure(error)) return
    alert('프로필을 저장하지 못했어요.')
  } finally {
    isSavingProfile.value = false
  }
}

const handleDeleteAccount = () => {
  alert('회원 탈퇴 기능은 아직 연결되지 않았어요.')
}

const goToDiagnosis = () => {
  router.push('/upload')
}

const viewDiagnosisResult = (item) => {
  if (item.isMock) {
    router.push({
      path: '/diagnosis/result',
      query: {
        mock: String(item.mockQuery || item.toneKey || '').replace(/-/g, '_'),
      },
    })
    return
  }

  router.push(`/result/${item.id}`)
}

const goToProductDetail = (productOptionId) => {
  router.push(`/product-detail/${productOptionId}`)
}

const goToAnalysisResult = (id) => {
  router.push(`/analysis/result/${id}`)
}

onMounted(async () => {
  savedMockDiagnosis.value = getSavedMockDiagnosisResult()

  if (!localStorage.getItem('access_token')) return

  try {
    await loadCurrentUser({ force: true })
    latestDiagnosisFromApi.value = await getLatestDiagnosis()
  } catch (error) {
    if (handleAuthFailure(error)) return
    console.error('마이페이지 데이터를 가져오지 못했어요.', error)
  }
})
</script>

<style scoped>
.mypage-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: 'Pretendard', sans-serif;
  color: #333;
  background: #fdf8f6;
  min-height: 100vh;
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

:deep(.profile-img) {
  border: 2px solid #eee;
}

.profile-info {
  flex: 1;
  min-width: 0;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 15px;
}

.profile-header h2 {
  min-width: 0;
  margin: 0;
  font-size: 1.5rem;
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
  gap: 18px;
  background: #fff0f1;
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
  white-space: nowrap;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
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
  gap: 12px;
  flex-wrap: wrap;
}

.date {
  color: #888;
  font-size: 0.9rem;
}

.confidence,
.mock-tag {
  color: #999;
  font-size: 0.8rem;
}

.mock-tag {
  padding: 2px 7px;
  border-radius: 999px;
  background: #f4f0fa;
  color: #5f5379;
  font-weight: 800;
}

.result-tag {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
  background-color: #fff0f1;
  color: #8b3a4a;
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
  min-width: 0;
}

.product-desc .brand {
  font-size: 0.75rem;
  color: #999;
}

.product-desc .name {
  margin: 2px 0;
  font-size: 0.85rem;
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

@media (max-width: 768px) {
  .profile-card,
  .personal-color-summary,
  .profile-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .dashboard-grid,
  .product-grid {
    grid-template-columns: 1fr;
  }
}
</style>
