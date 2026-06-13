<template>
  <div class="login-container">
    <div class="left-banner">
      <h1 class="logo">Lumière</h1>
      <div class="banner-text">
        <h2>나에게 가장<br>잘 어울리는 컬러를,<br><span class="highlight">Lumière</span>가 찾아드려요</h2>
        <p>AI 퍼스널컬러 진단부터 맞춤 화장품 추천까지,<br>당신만을 위한 뷰티 큐레이션 서비스</p>
      </div>
    </div>

    <div class="right-form-area">
      <div class="tab-header">
        <button :class="{ active: currentTab === 'login' }" @click="currentTab = 'login'">로그인</button>
        <button :class="{ active: currentTab === 'signup' }" @click="currentTab = 'signup'">회원가입</button>
      </div>
      
      <div class="tab-content">
        <LoginForm v-if="currentTab === 'login'" />
        <SignupForm v-else />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import LoginForm from '@/components/accounts/LoginForm.vue'
import SignupForm from '@/components/accounts/SignupForm.vue'

const currentTab = ref('login') // 'login' 또는 'signup'
</script>

<style scoped>
/* 전체 레이아웃 */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #fdf8f5; /* 부드러운 배경색 */
  padding: 40px;
  gap: 60px;
}

/* 좌측 배너 */
.left-banner {
  flex: 1;
  max-width: 500px;
}
.logo {
  color: #8b3a4a;
  font-family: 'Georgia', serif;
  margin-bottom: 40px;
}
.banner-text h2 {
  font-size: 2.2rem;
  line-height: 1.4;
  margin-bottom: 20px;
}
.highlight {
  color: #8b3a4a;
}
.banner-text p {
  color: #666;
  line-height: 1.6;
}

/* 우측 카드 */
.right-form-area {
  flex: 1;
  max-width: 450px;
  background: white;
  border-radius: 24px;
  padding: 40px;
  box-shadow: 0 10px 40px rgba(139, 58, 74, 0.05);
}

/* 탭 스타일 */
.tab-header {
  display: flex;
  border-bottom: 2px solid #f0f0f0;
  margin-bottom: 30px;
}
.tab-header button {
  flex: 1;
  padding: 15px;
  background: none;
  border: none;
  font-size: 1.1rem;
  font-weight: bold;
  color: #999;
  cursor: pointer;
  transition: all 0.3s;
}
.tab-header button.active {
  color: #8b3a4a;
  border-bottom: 2px solid #8b3a4a;
  margin-bottom: -2px; /* 보더 겹치기 정렬 */
}
</style>