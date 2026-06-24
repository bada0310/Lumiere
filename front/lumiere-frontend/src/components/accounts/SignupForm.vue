<template>
  <form @submit.prevent="handleSignup" class="signup-form">
    <div class="input-group">
      <label>이메일</label>
      <input type="email" v-model="email" placeholder="이메일을 입력해주세요" required />
    </div>

    <div class="input-group">
      <label>아이디</label>
      <div class="username-wrapper">
        <input type="text" v-model.trim="username" placeholder="사용하실 아이디를 입력해주세요" required @input="resetCheck" />
        <button type="button" class="check-btn" @click="checkUsername">중복 확인</button>
      </div>
      <span v-if="usernameMessage" :class="{'success-text': isAvailable, 'error-text': !isAvailable}">
        {{ usernameMessage }}
      </span>
      </div>

    <div class="input-group">
      <label>비밀번호</label>
      <input type="password" v-model="password" placeholder="비밀번호를 입력해주세요" required />
    </div>

    <div class="input-group">
      <label>비밀번호 확인</label>
      <input type="password" v-model="passwordConfirm" placeholder="비밀번호를 한번 더 입력해주세요" required />
    </div>

    <button type="submit" class="signup-btn">회원가입</button>
  </form>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '@/config/api'

const username = ref('') 
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')

const isAvailable = ref(false)
const usernameMessage = ref('')

// 1. 중복 확인 로직
const checkUsername = async () => {
  if (!username.value) {
    usernameMessage.value = '아이디를 먼저 입력해주세요.'
    isAvailable.value = false
    return
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/accounts/check-username/`, {
      username: username.value
    })
    
    isAvailable.value = response.data.is_available
    usernameMessage.value = response.data.message
  } catch (error) {
    console.error("중복 확인 에러:", error)
    usernameMessage.value = '확인 중 오류가 발생했습니다.'
    isAvailable.value = false
  }
}

// 2. 아이디 수정 시 검사 초기화
const resetCheck = () => {
  isAvailable.value = false
  usernameMessage.value = ''
}

// 3. 회원가입 로직 (중복된 함수 하나로 병합 완료)
const handleSignup = async () => {
  // 방어막 1: 중복 확인 통과 여부
  if (!isAvailable.value) {
    alert('아이디 중복 확인을 먼저 완료해주세요.')
    return
  }

  // 방어막 2: 비밀번호 일치 여부
  if (password.value !== passwordConfirm.value) {
    alert('비밀번호가 일치하지 않습니다.')
    return
  }

  const userData = {
    username: username.value,
    email: email.value,
    password: password.value
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/accounts/signup/`, userData)
    console.log("서버 응답:", response.data)
    alert('회원가입이 완료되었습니다! 로그인해주세요.')
    
    // 폼 초기화
    username.value = ''
    email.value = ''
    password.value = ''
    passwordConfirm.value = ''
    isAvailable.value = false
    usernameMessage.value = ''
    
  } catch (error) {
    console.error("회원가입 실패:", error.response?.data)
    alert('회원가입에 실패했습니다.')
  }
}
</script>

<style scoped>
/* 기존 스타일은 그대로 유지하시면 됩니다! */
.signup-form {
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
.signup-btn {
  padding: 15px;
  background-color: #8b3a4a;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 10px;
}
/* 아이디와 버튼을 한 줄에 나란히 배치 */
.username-wrapper {
  display: flex;
  gap: 10px;
  width: 100%;
}

.username-wrapper input {
  flex: 1; /* 인풋 창이 남은 가로 공간을 꽉 채우도록 설정해서 찌그러짐 방지 */
}

/* 중복 확인 버튼 디자인 맞춤 */
.check-btn {
  padding: 0 18px; /* 좌우 여백 */
  background-color: white; /* 배경은 깔끔하게 하얀색 */
  color: #8b3a4a; /* 글씨는 메인 컬러 */
  border: 1px solid #8b3a4a; /* 테두리도 메인 컬러 */
  border-radius: 8px; /* 둥근 모서리 맞춤 */
  font-weight: bold;
  font-size: 0.9rem;
  cursor: pointer;
  white-space: nowrap; /* 글씨가 세로로 두 줄이 되지 않게 방지 */
  transition: all 0.2s ease-in-out; /* 색상이 부드럽게 변하는 애니메이션 */
}

/* 마우스를 올렸을 때(Hover) 디자인 */
.check-btn:hover {
  background-color: #8b3a4a;
  color: white;
}

/* 안내 메시지 디자인 (초록색/빨간색) */
.success-text {
  color: #2e7d32; 
  font-size: 0.8rem;
  margin-top: -2px;
  padding-left: 4px;
}
.error-text {
  color: #d32f2f; 
  font-size: 0.8rem;
  margin-top: -2px;
  padding-left: 4px;
}
</style>
