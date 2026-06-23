<template>
  <div class="page">
    <main class="upload-page">
      <button class="back" type="button" @click="router.back()">이전으로</button>

      <section class="title-section">
        <h1>AI 퍼스널 컬러 진단</h1>
        <p>정확한 진단을 위해 자연광에서 정면 사진을 업로드해 주세요.</p>
      </section>

      <section class="steps" aria-label="진단 단계">
        <div class="step active">1</div>
        <div class="line active"></div>
        <div class="step">2</div>
        <div class="line"></div>
        <div class="step">3</div>
      </section>

      <section class="step-labels">
        <span class="active-text">사진 업로드</span>
        <span>AI 분석</span>
        <span>결과 확인</span>
      </section>

      <section class="upload-card">
        <div class="top-grid">
          <div class="guide-box">
            <h2>촬영 가이드</h2>

            <div class="guide-list">
              <div v-for="item in guideItems" :key="item.title" class="guide-item">
                <span aria-hidden="true">{{ item.icon }}</span>
                <p>
                  <strong>{{ item.title }}</strong>
                  <br />
                  {{ item.description }}
                </p>
              </div>
            </div>
          </div>

          <div class="upload-box">
            <h2>사진 업로드</h2>

            <div class="upload-area">
              <div class="camera-icon">CAM</div>
              <p>
                사진을 업로드하거나
                <br />
                카메라로 촬영해 주세요.
              </p>

              <input
                ref="fileInput"
                class="file-input"
                type="file"
                accept="image/jpeg,image/png"
                @change="handleFileChange"
              />
              <button class="primary-btn" type="button" :disabled="submitting" @click="openFilePicker">
                카메라 / 갤러리에서 선택
              </button>
              <button v-if="selectedFile" class="outline-btn" type="button" :disabled="submitting" @click="clearSelectedFile">
                다른 사진으로 변경
              </button>

              <small>JPG, PNG 파일만 업로드 가능해요. 최대 10MB</small>
            </div>
          </div>

          <div class="preview-box">
            <h2>업로드한 이미지</h2>

            <div class="preview-image">
              <img v-if="previewUrl" :src="previewUrl" alt="업로드 이미지 미리보기" class="preview-photo" />
              <div v-else class="face-placeholder">FACE</div>
            </div>

            <button class="outline-btn full" type="button" :disabled="submitting" @click="openFilePicker">
              다른 사진으로 변경
            </button>
          </div>
        </div>

        <div class="example-grid">
          <div class="example-box">
            <h3>좋은 사진 조건</h3>
            <div class="condition-grid">
              <div v-for="item in goodPhotoConditions" :key="item.title" class="condition-card good">
                <span aria-hidden="true">{{ item.icon }}</span>
                <strong>{{ item.title }}</strong>
                <p>{{ item.description }}</p>
              </div>
            </div>
            <p class="condition-note good-text">피부 본연의 색이 드러나는 밝고 차분한 사진이 가장 안정적이에요.</p>
          </div>

          <div class="example-box">
            <h3>피하면 좋은 조건</h3>
            <div class="condition-grid">
              <div v-for="item in badPhotoConditions" :key="item.title" class="condition-card bad">
                <span aria-hidden="true">{{ item.icon }}</span>
                <strong>{{ item.title }}</strong>
                <p>{{ item.description }}</p>
              </div>
            </div>
            <p class="condition-note bad-text">조명색, 배경색, 머리카락 그림자가 얼굴 색을 바꾸면 분석 정확도가 낮아져요.</p>
          </div>
        </div>

        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

        <button type="button" class="analysis-btn" :disabled="!selectedFile || submitting" @click="submitDiagnosis">
          {{ submitting ? '준비 중...' : '분석 시작하기' }}
        </button>

        <p class="privacy">업로드한 이미지는 진단 분석과 결과 저장을 위해 사용됩니다.</p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useRequireLogin } from '@/composables/useRequireLogin'

const router = useRouter()
const { requireLogin } = useRequireLogin()

const fileInput = ref(null)
const selectedFile = ref(null)
const previewUrl = ref('')
const submitting = ref(false)
const errorMessage = ref('')

const guideItems = [
  { icon: '☼', title: '밝은 자연광', description: '그늘이나 어두운 조명은 피해주세요.' },
  { icon: '◎', title: '정면 촬영', description: '고개를 기울이거나 돌리지 말아주세요.' },
  { icon: 'N', title: '필터 없이', description: '보정이나 필터를 적용하지 않은 사진이 좋아요.' },
  { icon: '□', title: '얼굴 노출', description: '안경, 모자, 진한 색조 렌즈는 가능하면 빼주세요.' },
  { icon: '⌁', title: '헤어라인 확인', description: '이마와 얼굴 윤곽이 보이면 더 정확해요.' },
]

const goodPhotoConditions = [
  { icon: '☼', title: '균일한 자연광', description: '창가의 부드러운 빛처럼 얼굴 전체가 고르게 밝은 사진' },
  { icon: '□', title: '무채색 배경', description: '흰색, 회색, 베이지처럼 피부색에 영향을 덜 주는 배경' },
  { icon: '◎', title: '정면 얼굴', description: '이마부터 턱선까지 얼굴 윤곽이 또렷하게 보이는 구도' },
  { icon: '⌁', title: '정리된 머리카락', description: '앞머리와 옆머리가 볼, 이마, 턱을 가리지 않는 상태' },
]

const badPhotoConditions = [
  { icon: '◐', title: '색이 강한 조명', description: '노란 조명, 푸른 조명, 역광처럼 피부 톤을 바꾸는 빛' },
  { icon: '▣', title: '원색 배경', description: '빨강, 초록, 파랑 벽지나 커튼처럼 얼굴에 색이 반사되는 배경' },
  { icon: '✦', title: '메이크업/보정', description: '진한 베이스, 색조 렌즈, 필터, 피부 보정이 들어간 사진' },
  { icon: '⌁', title: '얼굴을 가린 머리', description: '그림자나 머리카락이 이마, 볼, 턱선을 덮는 사진' },
]

const openFilePicker = () => {
  fileInput.value?.click()
}

const revokePreview = () => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
}

const handleFileChange = (event) => {
  const file = event.target.files?.[0]
  errorMessage.value = ''
  if (!file) return

  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    clearSelectedFile()
    errorMessage.value = 'JPG 또는 PNG 이미지만 업로드할 수 있어요.'
    return
  }

  if (file.size > 10 * 1024 * 1024) {
    clearSelectedFile()
    errorMessage.value = '10MB 이하 이미지를 업로드해 주세요.'
    return
  }

  revokePreview()
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
}

const clearSelectedFile = () => {
  selectedFile.value = null
  revokePreview()
  if (fileInput.value) fileInput.value.value = ''
}

const fileToDataUrl = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })

const submitDiagnosis = async () => {
  if (!selectedFile.value || submitting.value) return

  if (
    !requireLogin({
      message: 'AI 퍼스널 컬러 진단은 로그인 후 이용할 수 있어요.',
      redirect: '/upload',
    })
  ) {
    return
  }

  submitting.value = true
  errorMessage.value = ''

  try {
    const previewDataUrl = await fileToDataUrl(selectedFile.value)
    router.push({
      name: 'loading',
      state: {
        diagnosisFile: selectedFile.value,
        previewUrl: previewDataUrl,
      },
    })
  } catch (error) {
    errorMessage.value = '이미지를 준비하지 못했어요. 다시 시도해 주세요.'
    submitting.value = false
  }
}

onBeforeUnmount(revokePreview)
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #fffaf7;
}

.upload-page {
  padding: 32px 48px 48px;
  background: linear-gradient(180deg, #fffaf7 0%, #fbf4f1 100%);
}

.back {
  border: 0;
  background: transparent;
  color: #6d625f;
  cursor: pointer;
  font: inherit;
  margin-bottom: 8px;
}

.title-section {
  text-align: center;
}

.title-section h1 {
  font-family: var(--font-title-serif) !important;
  font-size: 30px;
  margin-bottom: 8px;
}

.title-section p {
  color: #555;
}

.steps {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 30px;
}

.step {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: white;
  border: 1px solid #ddd;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #777;
  font-weight: 800;
}

.step.active {
  background: #c65367;
  color: white;
  border-color: #c65367;
}

.line {
  width: 220px;
  height: 1px;
  background: #ddd;
}

.line.active {
  background: #e5a8b1;
  border-top: 1px dashed #e5a8b1;
}

.step-labels {
  width: 520px;
  margin: 10px auto 28px;
  display: flex;
  justify-content: space-between;
  color: #777;
  font-size: 14px;
}

.active-text {
  color: #c65367;
  font-weight: 700;
}

.upload-card {
  max-width: 1280px;
  margin: 0 auto;
  padding: 36px 42px 28px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid #eaded8;
  border-radius: 16px;
}

.top-grid {
  display: grid;
  grid-template-columns: 1fr 1.25fr 1fr;
  gap: 36px;
}

.guide-box,
.upload-box,
.preview-box,
.example-box {
  background: rgba(255, 255, 255, 0.86);
  border-radius: 14px;
}

.guide-box,
.upload-box,
.preview-box {
  padding: 24px;
}

h2 {
  font-size: 18px;
  margin-bottom: 18px;
}

.guide-list {
  border: 1px solid #eaded8;
  border-radius: 12px;
  padding: 24px 22px;
}

.guide-item {
  display: flex;
  gap: 14px;
  margin-bottom: 26px;
}

.guide-item:last-child {
  margin-bottom: 0;
}

.guide-item span {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #fff0f1;
  color: #c65367;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 900;
  flex: 0 0 auto;
}

.guide-item p {
  margin: 0;
  line-height: 1.6;
  font-size: 14px;
}

.upload-area {
  min-height: 348px;
  border: 2px dashed #e9b9c2;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.camera-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #fff0f1;
  color: #c65367;
  display: grid;
  place-items: center;
  font-size: 15px;
  font-weight: 900;
  margin-bottom: 20px;
}

.upload-area p {
  text-align: center;
  line-height: 1.5;
  color: #555;
}

.primary-btn,
.outline-btn {
  width: 230px;
  min-height: 44px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  margin-top: 12px;
  padding: 10px 14px;
}

.primary-btn {
  background: #c65367;
  color: white;
  border: none;
}

.outline-btn {
  background: white;
  color: #c65367;
  border: 1px solid #d98c99;
}

.upload-area small {
  margin-top: 20px;
  color: #777;
}

.file-input {
  display: none;
}

.primary-btn:disabled,
.outline-btn:disabled,
.analysis-btn:disabled {
  cursor: not-allowed;
  opacity: 0.56;
}

.preview-image {
  height: 286px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f6e7df, #fff4ef);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
  overflow: hidden;
}

.face-placeholder {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: #f0c8bd;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9e4655;
  font-weight: 900;
}

.preview-photo {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  object-fit: cover;
  display: block;
}

.full {
  width: 100%;
}

.example-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  margin-top: 24px;
}

.example-box {
  border: 1px solid #eaded8;
  padding: 22px 24px;
}

.example-box h3 {
  color: #c65367;
  font-size: 16px;
  margin-bottom: 18px;
}

.condition-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.condition-card {
  min-height: 132px;
  border-radius: 10px;
  padding: 16px 14px;
  border: 1px solid transparent;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.condition-card span {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 15px;
}

.condition-card strong {
  color: #2d2524;
  font-size: 14px;
}

.condition-card p {
  margin: 0;
  color: #6b625f;
  font-size: 12px;
  line-height: 1.45;
}

.condition-card.good {
  background: linear-gradient(135deg, #fffaf4, #f7fbf4);
  border-color: #e7ead8;
}

.condition-card.good span {
  background: #eef6e8;
  color: #678748;
}

.condition-card.bad {
  background: linear-gradient(135deg, #fff4f1, #f7f0ed);
  border-color: #ead8d1;
}

.condition-card.bad span {
  background: #f8e1dc;
  color: #b35a4b;
}

.condition-note {
  margin-top: 16px;
  font-size: 14px;
  line-height: 1.6;
}

.good-text {
  color: #4d8b61;
}

.bad-text {
  color: #9b5a4f;
}

.analysis-btn {
  border: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: min(420px, 100%);
  min-height: 52px;
  margin: 28px auto 16px;
  border-radius: 8px;
  background: #c65367;
  color: white;
  text-decoration: none;
  font-weight: 700;
}

.error-message {
  max-width: 560px;
  margin: 22px auto 0;
  color: #b44352;
  font-size: 14px;
  font-weight: 700;
  text-align: center;
}

.privacy {
  text-align: center;
  color: #777;
  font-size: 14px;
}

@media (max-width: 1080px) {
  .top-grid,
  .example-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .upload-page {
    padding: 22px 16px 40px;
  }

  .upload-card {
    padding: 20px 16px;
  }

  .step-labels {
    width: 100%;
  }

  .line {
    width: 64px;
  }

  .condition-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
