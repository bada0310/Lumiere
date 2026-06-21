<template>
  <header class="app-header">
    <div class="logo">
      <RouterLink to="/">Lumière</RouterLink>
    </div>

    <nav class="nav-menu">
      <RouterLink to="/upload" class="nav-item">진단하기</RouterLink>
      <RouterLink to="/product-analysis" class="nav-item">제품 분석</RouterLink>
      <RouterLink to="/products" class="nav-item">추천 제품</RouterLink>
      <RouterLink to="/community" class="nav-item">커뮤니티</RouterLink>
      <RouterLink to="/mypage" class="nav-item">마이페이지</RouterLink>
    </nav>

    <div class="header-right">
      <div class="search-wrap" :class="{ open: isSearchOpen }">
        <button class="search-toggle" type="button" @click="toggleSearch">
          {{ isSearchOpen ? '닫기' : '검색' }}
        </button>

        <form v-if="isSearchOpen" class="search-form" @submit.prevent="submitSearch">
          <input
            v-model.trim="searchKeyword"
            ref="searchInput"
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

      <button v-if="!isLoggedIn" class="login-btn" type="button" @click="$router.push('/login')">
        로그인
      </button>

      <div v-else class="user-area">
        <button class="icon-btn" type="button" aria-label="알림">🔔</button>
        <button class="icon-btn" type="button" aria-label="찜한 제품">♡</button>
        <div class="profile"></div>
        <span class="hello">안녕하세요, {{ userName }}님</span>
        <button class="logout-text" type="button" @click="logout">로그아웃</button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const isLoggedIn = ref(false)
const userName = ref('')
const isSearchOpen = ref(false)
const searchKeyword = ref('')
const searchInput = ref(null)

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

const submitSearch = () => {
  if (!searchKeyword.value) return

  router.push({
    path: '/products',
    query: {
      keyword: searchKeyword.value,
    },
  })

  isSearchOpen.value = false
}

const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  isLoggedIn.value = false
  alert('로그아웃 되었습니다.')
  window.location.href = '/'
}

onMounted(async () => {
  const token = localStorage.getItem('access_token')

  if (!token) return

  isLoggedIn.value = true

  try {
    const response = await axios.get('http://127.0.0.1:8000/accounts/user/', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    userName.value = response.data.nickname
  } catch (error) {
    console.error('유저 정보를 가져오는데 실패했습니다.', error)
    logout()
  }
})
</script>

<style scoped>
.app-header {
  height: 72px;
  padding: 0 42px;
  border-bottom: 1px solid #eaded8;
  background: rgba(255, 250, 247, 0.96);
  display: grid;
  grid-template-columns: 220px 1fr 360px;
  align-items: center;
  gap: 24px;
}

.logo {
  font-family: Georgia, serif;
  font-size: 30px;
  font-weight: 700;
  color: #bf4f63;
}

.logo a {
  color: inherit;
  text-decoration: none;
}

.nav-menu {
  display: flex;
  justify-content: center;
  gap: 48px;
  font-size: 15px;
  font-weight: 700;
}

.nav-item {
  color: #2d2524;
  text-decoration: none;
}

.nav-item.router-link-active {
  color: #c65367;
}

.header-right {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
}

.search-wrap {
  position: relative;
}

.search-toggle,
.login-btn,
.icon-btn,
.logout-text,
.search-submit,
.search-close,
.search-preview {
  border: none;
  cursor: pointer;
  font-weight: 800;
}

.search-toggle {
  height: 42px;
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
  top: 52px;
  width: 340px;
  padding: 12px;
  border: 1px solid #eaded8;
  border-radius: 16px;
  background: white;
  box-shadow: 0 14px 34px rgba(88, 55, 45, 0.12);
  z-index: 20;
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

.login-btn {
  height: 42px;
  padding: 0 22px;
  border-radius: 10px;
  background: #c65367;
  color: white;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: white;
  border: 1px solid #eaded8;
}

.profile {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f5d6c8, #fff1ea);
}

.hello {
  max-width: 130px;
  color: #4d4441;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-text {
  padding: 0;
  background: transparent;
  color: #8a7b76;
  font-size: 12px;
  text-decoration: underline;
}

@media (max-width: 1180px) {
  .app-header {
    grid-template-columns: 180px 1fr auto;
    padding: 0 24px;
  }

  .nav-menu {
    gap: 24px;
  }

  .hello {
    display: none;
  }
}
</style>
