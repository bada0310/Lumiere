<template>
  <form @submit.prevent="handleLogin" class="login-form">
    <div class="input-group">
      <label>이메일</label>
      <input type="email" v-model="email" placeholder="이메일을 입력해주세요" required />
    </div>

    <div class="input-group">
      <label>비밀번호</label>
      <input type="password" v-model="password" placeholder="비밀번호를 입력해주세요" required />
    </div>

    <button type="submit" class="login-btn">로그인</button>

    </form>
</template>

<script setup>
import { ref } from 'vue'

const email = ref('')
const password = ref('')

const handleLogin = () => {
  // 여기에 백엔드 API(예: FastAPI 또는 Django)로 로그인 요청을 보내는 로직을 작성합니다.
  console.log('로그인 시도:', email.value, password.value)
}
</script>

<style scoped>
.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px; /* 입력창과 버튼 사이 간격 */
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
  border-color: #8b3a4a; /* 포커스 시 이미지의 포인트 컬러 */
}

.login-btn {
  padding: 15px;
  background-color: #8b3a4a; /* 이미지의 로그인 버튼 색상 */
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 10px;
}
</style>