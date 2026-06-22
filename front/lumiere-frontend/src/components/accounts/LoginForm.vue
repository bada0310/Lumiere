<template>
  <form @submit.prevent="handleLogin" class="login-form">
    <div class="input-group">
      <label>아이디</label>
      <input type="text" v-model.trim="username" placeholder="아이디를 입력해주세요" required />
    </div>

    <div class="input-group">
      <label>비밀번호</label>
      <input type="password" v-model.trim="password" placeholder="비밀번호를 입력해주세요" required />
    </div>

    <button type="submit" class="login-btn">로그인</button>

    <div class="login-options">
      <span class="find-password-text" @click="goToFindPassword">비밀번호를 잊으셨나요?</span>
    </div>
  </form>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const emit = defineEmits(['goToFindPassword'])

// email 대신 username 사용
const username = ref('')
const password = ref('')
const route = useRoute()

const handleLogin = async () => { 
  const loginData = {
    username: username.value, // 입력받은 진짜 아이디를 보냄
    password: password.value
  }

  try {
    const response = await axios.post('http://127.0.0.1:8000/accounts/jwt-login/', loginData)
    
    localStorage.setItem('access_token', response.data.access)
    localStorage.setItem('refresh_token', response.data.refresh)
    
    alert('로그인에 성공했습니다!')

    const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/')
      ? route.query.redirect
      : '/'
    window.location.href = redirect

  } catch (error) {
    console.error("로그인 실패:", error.response?.data)
    alert('아이디 또는 비밀번호가 올바르지 않습니다.')
  }
}

const goToFindPassword = () => {
  emit('goToFindPassword')
}
</script>

<style scoped>
.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  font-weight: bold;
  font-size: 0.9rem;
  color: #333;
}

.input-group input {
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  outline: none;
}

.input-group input:focus {
  border-color: #8b3a4a;
}

.login-btn {
  padding: 15px;
  background-color: #8b3a4a;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 10px;
}

/* ★ 비밀번호 찾기 텍스트 스타일 */
.login-options {
  text-align: center;
  margin-top: -5px;
}

.find-password-text {
  font-size: 0.85rem;
  color: #888;
  text-decoration: underline;
  cursor: pointer;
  transition: color 0.2s ease-in-out;
}

.find-password-text:hover {
  color: #8b3a4a;
}
</style>
