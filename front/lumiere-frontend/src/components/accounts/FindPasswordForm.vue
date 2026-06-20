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
import axios from 'axios'

const emit = defineEmits(['goBack'])
const email = ref('')

// 비밀번호 찾기 처리 (백엔드 연결 전 임시 로직)
const handleFindPassword = async () => {
  if (!email.value) {
    alert("이메일을 입력해주세요.")
    return
  }

  try {
    // 장고로 이메일을 담아 POST 요청을 보냅니다.
    const response = await axios.post('http://127.0.0.1:8000/accounts/find-password/', {
      email: email.value
    })
    
    // 성공 시 장고가 보내준 메시지 띄우기
    alert(response.data.message)
    emit('goBack') // 성공했으니 다시 로그인 화면으로!

  } catch (error) {
    console.error("비밀번호 찾기 에러:", error.response?.data)
    // 에러 발생 시 (가입되지 않은 이메일 등) 장고가 보내준 에러 메시지 띄우기
    alert(error.response?.data?.error || "메일 발송에 실패했습니다.")
  }
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