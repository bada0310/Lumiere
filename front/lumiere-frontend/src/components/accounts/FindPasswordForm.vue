<template>
  <form @submit.prevent="handleFindPassword" class="find-form">
    <div class="input-group">
      <label>가입한 이메일</label>
      <input type="email" v-model.trim="email" placeholder="이메일을 입력해주세요" required />
    </div>

    <button type="submit" class="submit-btn">임시 비밀번호 발송</button>

    <div class="options">
      <span class="go-back-text" @click="goBack">로그인 화면으로 돌아가기</span>
    </div>
  </form>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['goBack'])
const email = ref('')

// 비밀번호 찾기 처리 (백엔드 연결 전 임시 로직)
const handleFindPassword = () => {
  if (!email.value) return
  alert(`${email.value}로 임시 비밀번호를 발송했습니다! (현재는 UI 테스트 중입니다)`)
  emit('goBack') // 발송 후 깔끔하게 로그인 화면으로 돌려보내기
}

// 돌아가기 버튼 클릭 시 부모에게 신호 보내기
const goBack = () => {
  emit('goBack')
}
</script>

<style scoped>
.find-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 10px;
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

.submit-btn {
  padding: 15px;
  background-color: #8b3a4a;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 10px;
}

.options {
  text-align: center;
  margin-top: -5px;
}

.go-back-text {
  font-size: 0.85rem;
  color: #888;
  text-decoration: underline;
  cursor: pointer;
  transition: color 0.2s ease-in-out;
}

.go-back-text:hover {
  color: #8b3a4a;
}
</style>