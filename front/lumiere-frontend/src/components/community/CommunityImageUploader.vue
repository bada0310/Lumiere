<template>
  <section class="image-upload">
    <h2>이미지 첨부 <span>(선택)</span></h2>
    <label class="upload-box">
      <input type="file" accept="image/*" multiple @change="onFileChange" />
      <strong>＋</strong>
      <p>이미지를 드래그하거나 클릭하여 업로드하세요</p>
      <small>JPG, PNG 파일만 가능 (최대 10MB)</small>
    </label>
    <div class="preview-row">
      <div v-for="image in modelValue" :key="image" class="preview" :style="{ backgroundImage: `url(${image})` }">
        <button type="button" aria-label="이미지 삭제" @click="removeImage(image)">×</button>
      </div>
      <button v-for="n in emptySlots" :key="n" type="button" class="empty-slot">+</button>
      <small>최대 10장까지 첨부 가능</small>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue'])

const emptySlots = computed(() => Math.max(0, Math.min(5, 10 - props.modelValue.length)))

const onFileChange = (event) => {
  const files = Array.from(event.target.files || []).slice(0, 10 - props.modelValue.length)
  const previews = files.map((file) => URL.createObjectURL(file))
  emit('update:modelValue', [...props.modelValue, ...previews].slice(0, 10))
  event.target.value = ''
}

const removeImage = (image) => {
  emit('update:modelValue', props.modelValue.filter((item) => item !== image))
}
</script>

<style scoped>
.image-upload {
  margin-top: 22px;
}

.image-upload h2 {
  font-size: 0.95rem;
  font-weight: 600;
}

.image-upload span {
  color: #9d918d;
  font-weight: 400;
}

.upload-box {
  margin-top: 10px;
  border: 1px dashed #e0a8b5;
  border-radius: 10px;
  height: 82px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9d6a75;
  cursor: pointer;
}

.upload-box input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.upload-box p {
  color: #7a6d69;
}

.upload-box small {
  color: #9d918d;
}

.preview-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.preview,
.empty-slot {
  width: 70px;
  height: 52px;
  border-radius: 8px;
  border: 1px solid #eaded8;
}

.preview {
  position: relative;
  background-size: cover;
  background-position: center;
}

.preview button {
  position: absolute;
  top: -7px;
  right: -7px;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 50%;
  background: #8b3a4a;
  color: white;
  cursor: pointer;
}

.empty-slot {
  background: #fff8f8;
  color: #c65367;
  cursor: pointer;
  font-size: 1.2rem;
}

.preview-row small {
  margin-left: auto;
  color: #9d918d;
}
</style>
