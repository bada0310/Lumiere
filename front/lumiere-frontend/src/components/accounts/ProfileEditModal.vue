<template>
  <div class="modal-overlay" v-if="isOpen" @click.self="handleClose">
    <div class="modal-content">
      <button class="close-btn" @click="closeModal">✕</button>
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
          <input type="email" v-model="form.email" required />
        </div>

        <div class="input-group">
          <label>닉네임</label>
          <input type="text" v-model="form.nickname" required />
        </div>

        <div class="password-section">
          <label class="section-label">비밀번호 변경 (선택)</label>
          <div class="input-group">
            <input type="password" v-model="form.currentPassword" placeholder="현재 비밀번호" />
          </div>
          <div class="input-group">
            <input type="password" v-model="form.newPassword" placeholder="새 비밀번호" />
          </div>
          <div class="input-group">
            <input type="password" v-model="form.confirmPassword" placeholder="새 비밀번호 확인" />
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

const props = defineProps({
  isOpen: Boolean,
  username: String, // 부모한테서 아이디도 받아오도록 추가
  initialEmail: String,
  initialNickname: String,
  initialImage: String
})

const emit = defineEmits(['close', 'save', 'delete'])
const fileInput = ref(null)

const defaultImage = 'https://via.placeholder.com/100'
const previewImage = ref(props.initialImage)
const selectedFile = ref(null)

// 폼 데이터에 email도 추가하여 양방향 바인딩되도록 설정
const form = reactive({
  email: props.initialEmail || '',
  nickname: props.initialNickname || '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 모달이 열릴 때마다 초기 데이터로 리셋
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    form.email = props.initialEmail
    form.nickname = props.initialNickname
    form.currentPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
    previewImage.value = props.initialImage
    selectedFile.value = null
  }
})

const handleClose = () => {
  // 1. 현재 폼 데이터와 처음 받아온 데이터(props)가 하나라도 다른지 비교합니다.
  const isChanged = 
    form.email !== props.initialEmail ||
    form.nickname !== props.initialNickname ||
    form.currentPassword !== '' ||
    form.newPassword !== '' ||
    selectedFile.value !== null

  // 2. 변경된 내용이 있다면 확인창 띄우기
  if (isChanged) {
    if (confirm('작성 중인 내용이 저장되지 않았습니다. 정말 창을 닫으시겠습니까?')) {
      emit('close')
    }
  } else {
    // 3. 변경된 내용이 없으면 쿨하게 바로 닫기
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

const submitForm = () => {
  if (form.newPassword || form.confirmPassword) {
    if (form.newPassword !== form.confirmPassword) {
      alert('새 비밀번호가 일치하지 않습니다.')
      return
    }
  }

  // 이제 이메일 변경사항도 함께 부모로 올려보냅니다.
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
/* 모달 배경: 화면 전체를 덮고 반투명하게 만듦 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

/* 모달 본체: 하얀색 박스 */
.modal-content {
  background: white;
  width: 400px;
  padding: 30px;
  border-radius: 12px;
  position: relative;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #666;
}

.modal-title {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}

/* 프로필 이미지 영역 */
.profile-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.profile-preview {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #eaded8;
}

.img-edit-btn {
  background: white;
  border: 1px solid #c65367;
  color: #c65367;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  cursor: pointer;
}
.img-edit-btn:hover {
  background: #fffafa;
}

/* 폼 입력 영역 */
form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.input-group label {
  font-size: 0.85rem;
  font-weight: bold;
  color: #555;
}

.input-group input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  outline: none;
}

.input-group input:focus {
  border-color: #c65367;
}

.read-only {
  background-color: #f5f5f5;
  color: #888;
  cursor: not-allowed;
}

/* 비밀번호 세트 구분 */
.password-section {
  margin-top: 10px;
  padding-top: 15px;
  border-top: 1px dashed #ddd;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-label {
  font-size: 0.85rem;
  font-weight: bold;
  color: #555;
  margin-bottom: 5px;
}

.save-btn {
  background: #c65367;
  color: white;
  border: none;
  padding: 12px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 10px;
}
.save-btn:hover {
  background: #b04658;
}

/* 회원 탈퇴 */
.delete-account-wrapper {
  text-align: right;
  margin-top: 15px;
}

.delete-text {
  font-size: 0.75rem;
  color: #aaa;
  text-decoration: underline;
  cursor: pointer;
}
.delete-text:hover {
  color: #d9534f; /* 마우스 올리면 빨간색으로 경고 */
}
</style>