<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="handleClose">
    <div class="modal-content" role="dialog" aria-modal="true" aria-labelledby="profile-edit-title">
      <button class="close-btn" type="button" aria-label="닫기" @click="handleClose">×</button>
      <h2 id="profile-edit-title" class="modal-title">회원정보 수정</h2>

      <form @submit.prevent="submitForm">
        <div class="profile-section">
          <img
            :src="previewImage || defaultImage"
            alt="프로필 이미지 미리보기"
            class="profile-preview"
            @error="handleImageError"
          />
          <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp" hidden @change="handleImageChange" />
          <button type="button" class="img-edit-btn" @click="fileInput?.click()">사진 변경</button>
          <span v-if="imageError" class="error-text">{{ imageError }}</span>
        </div>

        <div class="input-group">
          <label for="profile-username">아이디</label>
          <input id="profile-username" type="text" :value="username" disabled class="read-only" />
        </div>

        <div class="input-group">
          <label for="profile-email">이메일</label>
          <input id="profile-email" type="email" v-model.trim="form.email" required />
        </div>

        <div class="input-group">
          <label for="profile-nickname">닉네임</label>
          <div class="nickname-wrapper">
            <input id="profile-nickname" type="text" v-model.trim="form.nickname" @input="resetNicknameCheck" required />
            <button type="button" class="check-btn" @click="checkNicknameAvailability">중복 확인</button>
          </div>
          <span v-if="nicknameMessage" :class="{ 'success-text': isNicknameAvailable, 'error-text': !isNicknameAvailable }">
            {{ nicknameMessage }}
          </span>
        </div>

        <div class="password-section">
          <label class="section-label">비밀번호 변경 선택</label>
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

        <button type="submit" class="save-btn" :disabled="isSaving">
          {{ isSaving ? '저장 중...' : '수정 완료' }}
        </button>
      </form>

      <div class="delete-account-wrapper">
        <button type="button" class="delete-text" @click="handleDelete">회원 탈퇴</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'

import { DEFAULT_PROFILE_IMAGE } from '@/constants/images'
import { checkNickname } from '@/services/userApi'

const MAX_IMAGE_SIZE = 5 * 1024 * 1024
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

const props = defineProps({
  isOpen: Boolean,
  username: String,
  initialEmail: String,
  initialNickname: String,
  initialImage: String,
  isSaving: Boolean,
})

const emit = defineEmits(['close', 'save', 'delete'])
const fileInput = ref(null)

const defaultImage = DEFAULT_PROFILE_IMAGE
const previewImage = ref(props.initialImage || DEFAULT_PROFILE_IMAGE)
const selectedFile = ref(null)
const imageError = ref('')

const form = reactive({
  email: props.initialEmail || '',
  nickname: props.initialNickname || '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const isNicknameAvailable = ref(true)
const nicknameMessage = ref('')

watch(
  () => props.isOpen,
  (newVal) => {
    if (!newVal) return

    form.email = props.initialEmail || ''
    form.nickname = props.initialNickname || ''
    form.currentPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
    previewImage.value = props.initialImage || DEFAULT_PROFILE_IMAGE
    selectedFile.value = null
    imageError.value = ''
    isNicknameAvailable.value = true
    nicknameMessage.value = ''
  },
)

const handleClose = () => {
  emit('close')
}

const handleImageError = (event) => {
  event.currentTarget.src = DEFAULT_PROFILE_IMAGE
}

const handleImageChange = (event) => {
  const file = event.target.files?.[0]
  imageError.value = ''

  if (!file) return

  if (!ALLOWED_TYPES.includes(file.type)) {
    imageError.value = 'JPG, PNG, WEBP 이미지만 업로드할 수 있어요.'
    event.target.value = ''
    return
  }

  if (file.size > MAX_IMAGE_SIZE) {
    imageError.value = '프로필 이미지는 5MB 이하로 업로드해주세요.'
    event.target.value = ''
    return
  }

  selectedFile.value = file
  previewImage.value = URL.createObjectURL(file)
}

const resetNicknameCheck = () => {
  if (form.nickname === props.initialNickname) {
    isNicknameAvailable.value = true
    nicknameMessage.value = ''
    return
  }

  isNicknameAvailable.value = false
  nicknameMessage.value = ''
}

const checkNicknameAvailability = async () => {
  if (!form.nickname) {
    nicknameMessage.value = '닉네임을 입력해주세요.'
    isNicknameAvailable.value = false
    return
  }

  if (form.nickname === props.initialNickname) {
    nicknameMessage.value = '현재 사용 중인 닉네임입니다.'
    isNicknameAvailable.value = true
    return
  }

  try {
    const result = await checkNickname(form.nickname)
    isNicknameAvailable.value = result.is_available
    nicknameMessage.value = result.message
  } catch (error) {
    console.error('닉네임 중복 확인 실패:', error)
    nicknameMessage.value = '닉네임 확인 중 오류가 발생했어요.'
    isNicknameAvailable.value = false
  }
}

const submitForm = () => {
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

  if (imageError.value) return

  emit('save', {
    email: form.email,
    nickname: form.nickname,
    currentPassword: form.currentPassword,
    newPassword: form.newPassword,
    profileImage: selectedFile.value,
  })
}

const handleDelete = () => {
  if (confirm('정말로 탈퇴하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
    emit('delete')
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  width: min(400px, calc(100vw - 32px));
  padding: 30px;
  border-radius: 12px;
  position: relative;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  font-size: 1.4rem;
  cursor: pointer;
  color: #666;
}

.modal-title {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}

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
  background: #f5dcd6;
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

.save-btn:disabled {
  opacity: 0.65;
  cursor: wait;
}

.save-btn:hover:not(:disabled) {
  background: #b04658;
}

.delete-account-wrapper {
  text-align: right;
  margin-top: 15px;
}

.delete-text {
  border: 0;
  background: transparent;
  font-size: 0.75rem;
  color: #aaa;
  text-decoration: underline;
  cursor: pointer;
}

.delete-text:hover {
  color: #d9534f;
}

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
  text-align: center;
}
</style>
