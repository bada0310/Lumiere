<template>
  <div class="modal-overlay" v-if="isOpen" @click.self="handleClose">
    <div class="modal-content">
      <button class="close-btn" @click="handleClose">✕</button>
      <h2 class="modal-title">회원정보 수정</h2>

      <form @submit.prevent="submitForm">
        <div class="profile-section">
          <img :src="previewImage || defaultImage" alt="Profile" class="profile-preview" />
          <input type="file" ref="fileInput" @change="handleImageChange" accept="image/*" hidden />
          <button type="button" class="img-edit-btn" @click="$refs.fileInput.click()">사진 변경</button>
        </div>

        <div class="input-group">
          <label>아이디 (고유 식별값)</label>
          <input type="text" :value="username" disabled class="read-only" />
        </div>

        <div class="input-group">
          <label>이메일 (로그인 계정)</label>
          <input type="email" v-model.trim="form.email" required />
        </div>

        <div class="input-group">
          <label>닉네임</label>
          <div class="nickname-wrapper">
            <input 
              type="text" 
              v-model.trim="form.nickname" 
              @input="resetNicknameCheck" 
              required 
            />
            <button type="button" class="check-btn" @click="checkNickname">중복 확인</button>
          </div>
          <span v-if="nicknameMessage" :class="{'success-text': isNicknameAvailable, 'error-text': !isNicknameAvailable}">
            {{ nicknameMessage }}
          </span>
        </div>

        <div class="password-section">
          <label class="section-label">비밀번호 변경 (선택)</label>
          <div class="input-group">
            <input type="password" v-model.trim="form.currentPassword" placeholder="현재 비밀번호" />
          </div>
          <div class="input-group">
            <input type="password" v-model.trim="form.newPassword" placeholder="새 비밀번호" />
          </div>
          <div class="input-group">
            <input type="password" v-model.trim="form.confirmPassword" placeholder="새 비밀번호 확인" />
          </div>
        </div>

        <button type="submit" class="save-btn">수정 완료</button>
      </form>

      <div class="delete-account-wrapper">
        <span class="delete-text" @click="handleDelete">회원 탈퇴</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import axios from 'axios' // 서버 통신을 위해 axios 추가!

const props = defineProps({
  isOpen: Boolean,
  username: String,
  initialEmail: String,
  initialNickname: String,
  initialImage: String
})

const emit = defineEmits(['close', 'save', 'delete'])
const fileInput = ref(null)

const defaultImage = 'https://via.placeholder.com/100'
const previewImage = ref(props.initialImage)
const selectedFile = ref(null)

const form = reactive({
  email: props.initialEmail || '',
  nickname: props.initialNickname || '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// ★ 닉네임 중복 확인용 상태 변수
const isNicknameAvailable = ref(true) // 처음엔 원래 자기 닉네임이므로 true
const nicknameMessage = ref('')

// 모달 초기화
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    form.email = props.initialEmail
    form.nickname = props.initialNickname
    form.currentPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
    previewImage.value = props.initialImage
    selectedFile.value = null
    
    // 상태 초기화
    isNicknameAvailable.value = true 
    nicknameMessage.value = ''
  }
})

const handleClose = () => {
  const isChanged = 
    form.email !== props.initialEmail ||
    form.nickname !== props.initialNickname ||
    form.currentPassword !== '' ||
    form.newPassword !== '' ||
    selectedFile.value !== null

  if (isChanged) {
    if (confirm('작성 중인 내용이 저장되지 않았습니다. 정말 창을 닫으시겠습니까?')) {
      emit('close')
    }
  } else {
    emit('close')
  }
}

const handleImageChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    previewImage.value = URL.createObjectURL(file)
  }
}

// ★ 닉네임 입력 시 상태 초기화 로직
const resetNicknameCheck = () => {
  if (form.nickname === props.initialNickname) {
    // 원래 쓰던 닉네임으로 다시 돌려놓으면 통과!
    isNicknameAvailable.value = true
    nicknameMessage.value = ''
  } else {
    // 한 글자라도 바뀌면 다시 검사받게 만듦
    isNicknameAvailable.value = false
    nicknameMessage.value = ''
  }
}

// ★ 닉네임 중복 확인 로직
const checkNickname = async () => {
  if (!form.nickname) {
    nicknameMessage.value = '닉네임을 입력해주세요.'
    isNicknameAvailable.value = false
    return
  }

  // 자기 원래 닉네임으로 검사 누른 경우
  if (form.nickname === props.initialNickname) {
    nicknameMessage.value = '현재 사용 중인 닉네임입니다.'
    isNicknameAvailable.value = true
    return
  }

  try {
    const response = await axios.post('http://127.0.0.1:8000/accounts/check-nickname/', {
      nickname: form.nickname
    })
    
    isNicknameAvailable.value = response.data.is_available
    nicknameMessage.value = response.data.message
  } catch (error) {
    console.error("닉네임 중복 확인 에러:", error)
    nicknameMessage.value = '확인 중 오류가 발생했습니다.'
    isNicknameAvailable.value = false
  }
}

const submitForm = () => {
  // ★ 방어막: 닉네임 중복 확인 통과 못하면 컷!
  if (!isNicknameAvailable.value) {
    alert('닉네임 중복 확인을 완료해주세요.')
    return
  }

  if (form.newPassword || form.confirmPassword) {
    if (form.newPassword !== form.confirmPassword) {
      alert('새 비밀번호가 일치하지 않습니다.')
      return
    }
  }

  emit('save', {
    email: form.email,
    nickname: form.nickname,
    currentPassword: form.currentPassword,
    newPassword: form.newPassword,
    profileImage: selectedFile.value
  })
}

const handleDelete = () => {
  if (confirm('정말로 탈퇴하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
    emit('delete')
  }
}
</script>

<style scoped>
/* 기존 스타일 그대로 유지 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: white; width: 400px; padding: 30px; border-radius: 12px; position: relative; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
.close-btn { position: absolute; top: 15px; right: 15px; background: none; border: none; font-size: 1.2rem; cursor: pointer; color: #666; }
.modal-title { text-align: center; margin-bottom: 20px; color: #333; }
.profile-section { display: flex; flex-direction: column; align-items: center; gap: 10px; margin-bottom: 20px; }
.profile-preview { width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 2px solid #eaded8; }
.img-edit-btn { background: white; border: 1px solid #c65367; color: #c65367; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; cursor: pointer; }
.img-edit-btn:hover { background: #fffafa; }
form { display: flex; flex-direction: column; gap: 15px; }
.input-group { display: flex; flex-direction: column; gap: 5px; }
.input-group label { font-size: 0.85rem; font-weight: bold; color: #555; }
.input-group input { padding: 10px; border: 1px solid #ddd; border-radius: 6px; outline: none; }
.input-group input:focus { border-color: #c65367; }
.read-only { background-color: #f5f5f5; color: #888; cursor: not-allowed; }
.password-section { margin-top: 10px; padding-top: 15px; border-top: 1px dashed #ddd; display: flex; flex-direction: column; gap: 10px; }
.section-label { font-size: 0.85rem; font-weight: bold; color: #555; margin-bottom: 5px; }
.save-btn { background: #c65367; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 10px; }
.save-btn:hover { background: #b04658; }
.delete-account-wrapper { text-align: right; margin-top: 15px; }
.delete-text { font-size: 0.75rem; color: #aaa; text-decoration: underline; cursor: pointer; }
.delete-text:hover { color: #d9534f; }

/* ★ 닉네임 중복 확인용 추가 스타일 (회원가입 폼과 통일) */
.nickname-wrapper {
  display: flex;
  gap: 8px;
  width: 100%;
}
.nickname-wrapper input {
  flex: 1; 
}
.check-btn {
  padding: 0 15px;
  background-color: white;
  color: #c65367;
  border: 1px solid #c65367;
  border-radius: 6px;
  font-weight: bold;
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease-in-out;
}
.check-btn:hover {
  background-color: #c65367;
  color: white;
}
.success-text { color: #2e7d32; font-size: 0.8rem; margin-top: -2px; padding-left: 4px; }
.error-text { color: #d32f2f; font-size: 0.8rem; margin-top: -2px; padding-left: 4px; }
</style>