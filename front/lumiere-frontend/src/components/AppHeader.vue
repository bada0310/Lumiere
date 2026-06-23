<template>
  <header class="app-header">
    <RouterLink to="/" class="brand-logo">Lumière</RouterLink>

    <nav class="nav-menu" aria-label="주요 메뉴">
      <RouterLink to="/upload" class="nav-item">진단하기</RouterLink>
      <RouterLink to="/product-analysis" class="nav-item">제품 분석</RouterLink>
      <RouterLink to="/products" class="nav-item">추천 제품</RouterLink>
      <RouterLink to="/community" class="nav-item">커뮤니티</RouterLink>
      <RouterLink to="/mypage" class="nav-item">마이페이지</RouterLink>
    </nav>

    <div class="header-actions">
      <div class="search-wrap" :class="{ open: isSearchOpen }">
        <button class="search-toggle" type="button" @click="toggleSearch">
          {{ isSearchOpen ? '닫기' : '검색' }}
        </button>

        <form v-if="isSearchOpen" class="search-form" @submit.prevent="submitSearch">
          <input
            ref="searchInput"
            v-model.trim="searchKeyword"
            placeholder="제품명, 브랜드, 색상"
            @keydown.esc="closeSearch"
          />

          <div class="search-actions">
            <button class="search-submit" type="submit" :disabled="!searchKeyword">
              검색하기
            </button>
            <button class="search-close" type="button" @click="closeSearch">
              닫기
            </button>
          </div>

          <button v-if="searchKeyword" class="search-preview" type="submit">
            <strong>{{ searchKeyword }}</strong>
            <span>추천 제품에서 검색</span>
          </button>
        </form>
      </div>

      <div class="notification-wrap">
        <button
          class="icon-button"
          type="button"
          aria-label="알림"
          :aria-expanded="isNotificationOpen"
          @click="toggleNotifications"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
            <path d="M10 21h4" />
          </svg>
          <span v-if="notificationCount" class="action-badge">{{ notificationCount }}</span>
        </button>

        <div v-if="isNotificationOpen" class="notification-panel">
          <strong>알림</strong>
          <button
            v-for="notice in notificationItems"
            :key="notice.key"
            type="button"
            class="notification-item"
            @click="goNotice(notice)"
          >
            <span>{{ notice.title }}</span>
            <small>{{ notice.description }}</small>
          </button>
        </div>
      </div>

      <RouterLink class="icon-button hide-mobile" :to="{ name: 'mypage-liked-options' }" aria-label="찜한 제품">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M19.5 12.6 12 20l-7.5-7.4a5 5 0 0 1 7.1-7.1l.4.4.4-.4a5 5 0 0 1 7.1 7.1Z" />
        </svg>
        <span v-if="likedCount" class="action-badge">{{ likedCount }}</span>
      </RouterLink>

      <button v-if="!isLoggedIn" class="login-btn" type="button" @click="router.push('/login')">
        로그인
      </button>

      <div v-else class="user-area">
        <UserAvatar
          :src="resolvedProfileImageUrl"
          :alt="`${userName} 프로필 이미지`"
          :name="userName"
          size="sm"
        />
        <span class="greeting">안녕하세요, {{ userName }}님</span>

        <details class="user-dropdown">
          <summary aria-label="사용자 메뉴 열기">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m6 9 6 6 6-6" />
            </svg>
          </summary>
          <div class="dropdown-menu">
            <RouterLink to="/mypage">마이페이지</RouterLink>
            <button type="button" @click="logout">로그아웃</button>
          </div>
        </details>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import UserAvatar from '@/components/user/UserAvatar.vue'
import { useCurrentUser } from '@/composables/useCurrentUser'
import { useResolvedProfileImage } from '@/composables/useResolvedProfileImage'
import { getLatestDiagnosis } from '@/services/diagnosisApi'
import { getLikedProductOptions } from '@/services/engagementApi'

const router = useRouter()
const { currentUser, loadCurrentUser, clearCurrentUser } = useCurrentUser()
const { resolvedProfileImageUrl, loadLatestDiagnosisForProfile, clearResolvedProfileImage } =
  useResolvedProfileImage(currentUser)

const isSearchOpen = ref(false)
const isNotificationOpen = ref(false)
const searchKeyword = ref('')
const searchInput = ref(null)
const latestDiagnosis = ref(null)
const likedCount = ref(0)

const isLoggedIn = computed(() => Boolean(localStorage.getItem('access_token')))
const userName = computed(() => currentUser.value?.nickname || currentUser.value?.username || '사용자')
const notificationItems = computed(() => {
  if (!isLoggedIn.value) {
    return [
      {
        key: 'login',
        title: '로그인이 필요해요',
        description: '진단 결과와 찜 목록 알림은 로그인 후 확인할 수 있어요.',
        route: { name: 'login' },
      },
    ]
  }

  const items = []
  if (latestDiagnosis.value) {
    items.push({
      key: 'diagnosis',
      title: '퍼스널컬러 요약 준비 완료',
      description: `${latestDiagnosis.value.korean_name || latestDiagnosis.value.tone_label || '진단 결과'} 기준 추천을 확인할 수 있어요.`,
      route: latestDiagnosis.value.id
        ? { name: 'diagnosis-result-detail', params: { diagnosisId: latestDiagnosis.value.id } }
        : { name: 'mypage-diagnoses' },
    })
  } else {
    items.push({
      key: 'diagnosis-empty',
      title: '아직 진단 결과가 없어요',
      description: '사진을 업로드하면 홈과 추천제품에 내 톤이 반영돼요.',
      route: { name: 'upload' },
    })
  }

  items.push({
    key: 'likes',
    title: likedCount.value ? `찜한 제품 ${likedCount.value}개` : '찜한 제품이 없어요',
    description: likedCount.value ? '마이페이지에서 저장한 제품 옵션을 다시 볼 수 있어요.' : '추천제품에서 하트를 눌러 제품을 저장해보세요.',
    route: { name: 'mypage-liked-options' },
  })

  return items
})
const notificationCount = computed(() => notificationItems.value.length)

const toggleSearch = async () => {
  isSearchOpen.value = !isSearchOpen.value

  if (isSearchOpen.value) {
    await nextTick()
    searchInput.value?.focus()
  }
}

const closeSearch = () => {
  isSearchOpen.value = false
  searchKeyword.value = ''
}

const toggleNotifications = () => {
  isNotificationOpen.value = !isNotificationOpen.value
}

const goNotice = (notice) => {
  isNotificationOpen.value = false
  if (notice.route) router.push(notice.route)
}

const submitSearch = () => {
  if (!searchKeyword.value) return

  router.push({
    path: '/products',
    query: {
      keyword: searchKeyword.value,
    },
  })

  closeSearch()
}

const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  clearCurrentUser()
  clearResolvedProfileImage()
  window.location.href = '/'
}

onMounted(async () => {
  if (!isLoggedIn.value) return

  try {
    await loadCurrentUser({ force: true })
    await loadLatestDiagnosisForProfile()
  } catch (error) {
    console.error('사용자 정보를 가져오지 못했습니다.', error)
    logout()
  }

  try {
    const [diagnosis, likedOptions] = await Promise.all([
      getLatestDiagnosis(),
      getLikedProductOptions({ page: 1, page_size: 1 }),
    ])
    latestDiagnosis.value = diagnosis
    likedCount.value = Array.isArray(likedOptions) ? likedOptions.length : Number(likedOptions?.count || 0)
  } catch (error) {
    console.warn('헤더 알림 정보를 가져오지 못했습니다.', error)
  }
})
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 20;
  height: 76px;
  padding: 0 42px;
  border-bottom: 1px solid rgba(226, 210, 204, 0.78);
  background: rgba(255, 250, 247, 0.94);
  backdrop-filter: blur(14px);
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 32px;
}

.brand-logo {
  color: #bf4f63;
  font-size: 30px;
  line-height: 1;
  text-decoration: none;
}

.nav-menu {
  display: flex;
  justify-content: center;
  gap: clamp(22px, 4vw, 58px);
  font-size: 15px;
  font-weight: 700;
}

.nav-item {
  color: #211c1b;
  text-decoration: none;
  transition: color 0.2s ease;
}

.nav-item:hover,
.nav-item.router-link-active {
  color: #bf4f63;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.search-wrap {
  position: relative;
}

.search-toggle,
.login-btn,
.search-submit,
.search-close,
.search-preview {
  cursor: pointer;
  font-weight: 800;
}

.search-toggle {
  height: 38px;
  padding: 0 16px;
  border: 1px solid #eaded8;
  border-radius: 999px;
  background: white;
  color: #5f5754;
}

.search-wrap.open .search-toggle {
  color: #c65367;
  border-color: #d98c99;
}

.search-form {
  position: absolute;
  right: 0;
  top: 48px;
  z-index: 30;
  width: 340px;
  padding: 12px;
  border: 1px solid #eaded8;
  border-radius: 16px;
  background: white;
  box-shadow: 0 14px 34px rgba(88, 55, 45, 0.12);
}

.search-form input {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: 1px solid #eaded8;
  border-radius: 11px;
  background: #fffaf7;
  outline: none;
}

.search-form input:focus {
  border-color: #d98c99;
}

.search-actions {
  display: grid;
  grid-template-columns: 1fr 78px;
  gap: 8px;
  margin-top: 10px;
}

.search-submit,
.search-close {
  height: 38px;
  border-radius: 10px;
}

.search-submit {
  border: 0;
  background: #c65367;
  color: white;
}

.search-submit:disabled {
  opacity: 0.45;
  cursor: default;
}

.search-close {
  border: 1px solid #eaded8;
  background: white;
  color: #6b625f;
}

.search-preview {
  width: 100%;
  margin-top: 10px;
  padding: 12px;
  border: 0;
  border-radius: 12px;
  background: #fff0f1;
  color: #5f5754;
  text-align: left;
}

.search-preview strong {
  display: block;
  color: #c65367;
  margin-bottom: 4px;
}

.search-preview span {
  font-size: 12px;
}

.icon-button,
.user-dropdown summary {
  position: relative;
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: #211c1b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  text-decoration: none;
}

.icon-button:hover,
.user-dropdown summary:hover {
  background: #fff0f1;
  color: #bf4f63;
}

.icon-button svg,
.user-dropdown svg {
  width: 21px;
  height: 21px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.action-badge {
  position: absolute;
  right: -3px;
  top: -4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border: 2px solid #fffaf7;
  border-radius: 999px;
  background: #c65367;
  color: #fff;
  font-size: 9px;
  font-weight: 900;
  line-height: 12px;
  display: grid;
  place-items: center;
}

.notification-wrap {
  position: relative;
}

.notification-panel {
  position: absolute;
  right: -8px;
  top: 44px;
  z-index: 35;
  width: 286px;
  padding: 12px;
  border: 1px solid #eaded8;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 16px 38px rgba(75, 45, 38, 0.12);
  display: grid;
  gap: 8px;
}

.notification-panel > strong {
  color: #2b2523;
  font-size: 14px;
}

.notification-item {
  width: 100%;
  padding: 10px;
  border: 1px solid #f1e4de;
  border-radius: 10px;
  background: #fffaf7;
  color: #443b39;
  text-align: left;
  cursor: pointer;
}

.notification-item:hover {
  border-color: #e3bac0;
  background: #fff0f1;
}

.notification-item span {
  display: block;
  font-size: 13px;
  font-weight: 900;
}

.notification-item small {
  display: block;
  margin-top: 4px;
  color: #7b6d68;
  font-size: 11px;
  line-height: 1.45;
}

.login-btn {
  height: 38px;
  padding: 0 18px;
  border: 1px solid #c65367;
  border-radius: 8px;
  background: #c65367;
  color: #fff;
  font-weight: 800;
  cursor: pointer;
  white-space: nowrap;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  white-space: nowrap;
}

.greeting {
  color: #443b39;
}

.user-dropdown {
  position: relative;
}

.user-dropdown summary {
  list-style: none;
}

.user-dropdown summary::-webkit-details-marker {
  display: none;
}

.dropdown-menu {
  position: absolute;
  right: 0;
  top: 42px;
  min-width: 132px;
  padding: 8px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 14px 34px rgba(75, 45, 38, 0.1);
  display: grid;
  gap: 4px;
}

.dropdown-menu a,
.dropdown-menu button {
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #443b39;
  cursor: pointer;
  font-size: 13px;
  padding: 8px 10px;
  text-align: left;
}

.dropdown-menu a:hover,
.dropdown-menu button:hover {
  background: #fff4f2;
  color: #bf4f63;
}

@media (max-width: 980px) {
  .app-header {
    padding: 0 20px;
    gap: 18px;
  }

  .nav-menu {
    gap: 18px;
    font-size: 14px;
  }

  .greeting {
    display: none;
  }
}

@media (max-width: 720px) {
  .app-header {
    height: auto;
    min-height: 70px;
    grid-template-columns: 1fr auto;
    padding: 14px 16px;
  }

  .nav-menu {
    grid-column: 1 / -1;
    order: 3;
    justify-content: flex-start;
    gap: 16px;
    overflow-x: auto;
    padding-bottom: 4px;
  }

  .header-actions {
    gap: 8px;
  }

  .search-form {
    width: min(340px, calc(100vw - 32px));
  }

  .hide-mobile {
    display: none;
  }
}
</style>
