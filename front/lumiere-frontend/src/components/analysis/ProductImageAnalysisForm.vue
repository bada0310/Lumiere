<template>
  <section class="analysis-form">
    <div class="headline">
      <p class="eyebrow">Product color analysis</p>
      <h1>제품 색상 분석</h1>
      <p>제품 색상표 이미지를 업로드하면 옵션 이름, 대표 색상, 차트 위치를 추출해 메인 퍼스널컬러와 비교합니다.</p>
    </div>

    <div class="form-grid">
      <label
        class="upload-panel"
        :class="{ dragging: isDragging, filled: Boolean(previewUrl) }"
        @dragenter.prevent="isDragging = true"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <input ref="fileInputRef" type="file" accept="image/png,image/jpeg,image/webp" hidden @change="handleFileChange" />
        <div v-if="previewUrl" class="preview-wrap">
          <img :src="previewUrl" alt="업로드한 제품 색상표 미리보기" />
        </div>
        <div v-else class="upload-copy">
          <strong>색상표 이미지 업로드</strong>
          <span>PNG, JPG, WEBP</span>
        </div>
        <button type="button" class="ghost-btn" @click.prevent="openPicker">
          {{ previewUrl ? '이미지 변경' : '파일 선택' }}
        </button>
      </label>

      <form class="meta-panel" @submit.prevent="submit">
        <label>
          <span>제품명</span>
          <input v-model="form.product_name" type="text" placeholder="예: 3CE GUMMY OIL TINT" />
        </label>

        <label>
          <span>브랜드명</span>
          <input v-model="form.brand_name" type="text" placeholder="예: 3CE" />
        </label>

        <label>
          <span>카테고리</span>
          <select v-model="form.category">
            <option value="">자동 또는 미입력</option>
            <option value="LIP">립</option>
            <option value="EYE">아이</option>
            <option value="CHEEK">치크</option>
            <option value="BASE">베이스</option>
            <option value="LENS">렌즈</option>
            <option value="ETC">기타</option>
          </select>
        </label>

        <button type="submit" class="analyze-btn" :disabled="disabled">
          {{ loading ? '분석 중...' : '이미지 분석' }}
        </button>
      </form>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['submit-analysis'])

const fileInputRef = ref(null)
const file = ref(null)
const previewUrl = ref('')
const isDragging = ref(false)
const form = ref({
  product_name: '',
  brand_name: '',
  category: '',
})

const disabled = computed(() => !file.value || props.loading)

const openPicker = () => {
  fileInputRef.value?.click()
}

const handleFileChange = (event) => {
  const nextFile = event.target.files?.[0]
  setFile(nextFile)
}

const handleDrop = (event) => {
  isDragging.value = false
  const nextFile = event.dataTransfer?.files?.[0]
  setFile(nextFile)
}

const setFile = (nextFile) => {
  if (!nextFile) return
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  file.value = nextFile
  previewUrl.value = URL.createObjectURL(nextFile)
}

const submit = () => {
  if (disabled.value) return
  emit('submit-analysis', {
    image: file.value,
    product_name: form.value.product_name.trim(),
    brand_name: form.value.brand_name.trim(),
    category: form.value.category,
  })
}

onBeforeUnmount(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})
</script>

<style scoped>
.analysis-form {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 36px 20px 12px;
}

.headline {
  margin-bottom: 22px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #a04e5f;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}

.headline h1 {
  margin: 0 0 10px;
  font-size: 34px;
  color: #241d1c;
}

.headline p:last-child {
  margin: 0;
  max-width: 760px;
  color: #6a5f5d;
  line-height: 1.6;
}

.form-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 20px;
}

.upload-panel,
.meta-panel {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #eaded8;
  border-radius: 8px;
}

.upload-panel {
  min-height: 360px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

.upload-panel.dragging {
  border-color: #c25f74;
  background: #fff5f6;
}

.upload-panel.filled {
  justify-content: flex-start;
}

.preview-wrap {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 8px;
  overflow: hidden;
  background: #f7f3f1;
}

.preview-wrap img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.upload-copy {
  display: grid;
  gap: 6px;
  text-align: center;
  color: #5f5653;
}

.upload-copy strong {
  font-size: 18px;
  color: #241d1c;
}

.ghost-btn,
.analyze-btn {
  border: none;
  border-radius: 8px;
  min-height: 46px;
  font-weight: 800;
  cursor: pointer;
}

.ghost-btn {
  min-width: 140px;
  background: #f5ece8;
  color: #6c4d45;
}

.meta-panel {
  padding: 22px;
  display: grid;
  gap: 14px;
  align-content: start;
}

.meta-panel label {
  display: grid;
  gap: 8px;
}

.meta-panel span {
  color: #5a504e;
  font-size: 13px;
  font-weight: 700;
}

.meta-panel input,
.meta-panel select {
  width: 100%;
  min-height: 46px;
  border: 1px solid #e5d9d5;
  border-radius: 8px;
  padding: 0 14px;
  background: #fffdfc;
  color: #241d1c;
}

.analyze-btn {
  margin-top: 10px;
  background: #c25f74;
  color: white;
}

.analyze-btn:disabled {
  background: #d8c9c5;
  cursor: not-allowed;
}

@media (max-width: 920px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .headline h1 {
    font-size: 28px;
  }
}
</style>
