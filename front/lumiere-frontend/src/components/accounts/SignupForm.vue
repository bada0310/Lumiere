<template>
  <form @submit.prevent="handleSignup" class="signup-form">
    <div class="input-group">
      <label>이메일</label>
      <input type="email" v-model="email" placeholder="이메일을 입력해주세요" required />
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

const email = ref('')
const password = ref('')
const passwordConfirm = ref('')

const handleSignup = () => {
  if (password.value !== passwordConfirm.value) {
    alert('비밀번호가 일치하지 않습니다.')
    return
  }
  console.log('회원가입 시도:', email.value)
}
</script>

<style scoped>
/* LoginForm.vue와 스타일을 동일하게 맞춰 통일감을 줍니다 */
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
</style>