<template>
  <div class="generated-makeup">
    <img
      v-if="status === 'complete'"
      :src="generatedUrl"
      alt="Gen AI 메이크업 결과 이미지"
      class="generated-makeup__image"
      @error="hasImageError = true"
    />

    <div v-else-if="status === 'loading'" class="generated-makeup__state generated-makeup__state--loading">
      <div class="generated-makeup__skeleton"></div>
      <p>추천 메이크업 이미지를 생성하고 있습니다.</p>
    </div>

    <div v-else-if="status === 'failed'" class="generated-makeup__state">
      <strong>이미지를 표시하지 못했습니다.</strong>
      <button type="button" @click="$emit('retry')">다시 생성</button>
    </div>

    <div v-else class="generated-makeup__state">
      <strong>생성된 메이크업 이미지가 아직 없습니다.</strong>
      <p v-if="uploadedUrl">진단 원본 이미지는 저장되어 있지만 Gen AI 결과는 아직 준비되지 않았습니다.</p>
      <p v-else>진단 이미지가 준비되면 메이크업 결과가 표시됩니다.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  generatedUrl: {
    type: String,
    default: null,
  },
  uploadedUrl: {
    type: String,
    default: null,
  },
  generationStatus: {
    type: String,
    default: null,
  },
})

defineEmits(['retry'])

const hasImageError = ref(false)

watch(
  () => props.generatedUrl,
  () => {
    hasImageError.value = false
  },
)

const status = computed(() => {
  if (props.generationStatus === 'loading') return 'loading'
  if (props.generationStatus === 'failed' || hasImageError.value) return 'failed'
  if (props.generatedUrl) return 'complete'
  return 'empty'
})
</script>

<style scoped>
.generated-makeup {
  width: 100%;
  height: 300px;
  border-radius: 14px;
  overflow: hidden;
  background: #fff1eb;
  box-shadow: inset 0 0 0 1px rgba(198, 83, 103, 0.08);
}

.generated-makeup__image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.generated-makeup__state {
  width: 100%;
  height: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
  color: #8b3a4a;
}

.generated-makeup__state p {
  margin: 0;
  color: #7d706c;
  font-size: 0.9rem;
}

.generated-makeup__state button {
  border: 1px solid #c65367;
  color: #c65367;
  background: white;
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
  font-weight: 700;
}

.generated-makeup__skeleton {
  width: 72%;
  height: 180px;
  border-radius: 12px;
  background: linear-gradient(90deg, #f6e4df 0%, #fff7f5 48%, #f6e4df 100%);
  background-size: 220% 100%;
  animation: shimmer 1.3s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    background-position: 120% 0;
  }
  100% {
    background-position: -120% 0;
  }
}
</style>
