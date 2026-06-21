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
      <button class="icon-button" type="button" aria-label="알림">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
          <path d="M10 21h4" />
        </svg>
      </button>

      <button class="icon-button hide-mobile" type="button" aria-label="사용자 메뉴">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M20 21a8 8 0 0 0-16 0" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      </button>

      <button v-if="!isLoggedIn" class="login-btn" type="button" @click="$router.push('/login')">
        로그인
      </button>

      <div v-else class="user-area">
        <UserAvatar :src="resolvedProfileImageUrl" :alt="`${userName} 프로필 이미지`" :name="userName" size="sm" />
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
import { computed, onMounted } from 'vue'

import UserAvatar from '@/components/user/UserAvatar.vue'
import { useCurrentUser } from '@/composables/useCurrentUser'
import { useResolvedProfileImage } from '@/composables/useResolvedProfileImage'

const { currentUser, loadCurrentUser, clearCurrentUser } = useCurrentUser()
const { resolvedProfileImageUrl, loadLatestDiagnosisForProfile, clearResolvedProfileImage } =
  useResolvedProfileImage(currentUser)

const isLoggedIn = computed(() => Boolean(localStorage.getItem('access_token')))
const userName = computed(() => currentUser.value?.nickname || currentUser.value?.username || '사용자')

onMounted(async () => {
  if (!isLoggedIn.value) return

  try {
    await loadCurrentUser({ force: true })
    await loadLatestDiagnosisForProfile()
  } catch (error) {
    console.error('사용자 정보를 가져오지 못했습니다.', error)
    logout()
  }
})

const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  clearCurrentUser()
  clearResolvedProfileImage()
  window.location.href = '/'
}
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

.icon-button,
.user-dropdown summary {
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

  .hide-mobile {
    display: none;
  }
}
</style>
