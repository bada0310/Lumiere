<template>
  <article class="product-input-card">
    <div class="image-box">
      <img v-if="imageUrl" :src="imageUrl" :alt="title" />
      <div v-else class="image-fallback"></div>
    </div>

    <div class="summary-body">
      <p v-if="product?.brand" class="brand">{{ product.brand }}</p>
      <h1>{{ title }}</h1>
      <p>{{ description }}</p>

      <form class="link-row" @submit.prevent="handleSubmit">
        <input
          :value="modelValue"
          type="url"
          :placeholder="placeholder"
          :aria-label="placeholder"
          @input="$emit('update:modelValue', $event.target.value)"
        />
        <button type="submit" :disabled="buttonDisabled">
          {{ buttonLabel }}
        </button>
      </form>

      <p v-if="sourceLabel" class="source-label">{{ sourceLabel }}</p>
    </div>

    <aside v-if="selectedOption" class="option-summary">
      <span :style="{ backgroundColor: selectedColor }"></span>
      <p>선택 옵션</p>
      <strong>{{ optionLabel }}</strong>
      <em>{{ scoreLabel }}</em>
    </aside>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  mode: {
    type: String,
    default: 'analysis',
  },
  product: {
    type: Object,
    default: null,
  },
  selectedOption: {
    type: Object,
    default: null,
  },
  imageUrl: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'analyze', 'open-link'])

const isAnalysisMode = computed(() => props.mode === 'analysis')
const title = computed(() => props.product?.name || '제품 컬러 매칭')
const description = computed(() => {
  if (props.product?.description) return props.product.description
  if (props.product?.category) return `${props.product.category} 옵션 색상을 퍼스널컬러 기준으로 비교합니다.`
  return '제품 링크를 입력하면 옵션 색상을 분석하고 메인 퍼스널컬러와 비교합니다.'
})
const placeholder = computed(() => (isAnalysisMode.value ? '분석할 제품 링크를 붙여넣어 주세요.' : '제품 링크'))
const buttonLabel = computed(() => {
  if (props.loading) return '분석 중'
  return isAnalysisMode.value ? (props.product ? '다시 분석' : '분석하기') : '링크 열기'
})
const buttonDisabled = computed(() => props.loading || !props.modelValue.trim())
const sourceLabel = computed(() => {
  if (!props.product || !props.modelValue) return ''
  return isAnalysisMode.value ? `출처: ${props.modelValue}` : ''
})
const isPendingOption = computed(() => {
  const status = String(props.selectedOption?.analysis_status || props.selectedOption?.analysisStatus || '').toUpperCase()
  const grade = String(props.selectedOption?.grade || '').toUpperCase()
  return status === 'PENDING_COLOR_ANALYSIS' || grade === 'PENDING'
})
const selectedColor = computed(() => props.selectedOption?.hex_code || props.selectedOption?.hex || '#d9d3cf')
const optionLabel = computed(() => {
  const option = props.selectedOption || {}
  return [option.option_no, option.display_name || option.option_name].filter(Boolean).join(' ') || option.option || '기본 옵션'
})
const scoreLabel = computed(() => {
  if (isPendingOption.value) return 'Pending analysis'
  const rawScore = props.selectedOption?.match_score
  const grade = props.selectedOption?.grade || ''
  if (rawScore === null || rawScore === undefined || rawScore === '') return grade || '분석 완료'
  const score = Number(rawScore)
  if (!Number.isFinite(score)) return grade || '분석 완료'
  return `${Math.round(score)}점 · ${grade}`
})

const handleSubmit = () => {
  if (buttonDisabled.value) return
  emit(isAnalysisMode.value ? 'analyze' : 'open-link')
}
</script>

<style scoped>
.product-input-card {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) 260px;
  gap: 24px;
  padding: 24px;
  align-items: stretch;
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
}

.image-box {
  display: grid;
  place-items: center;
  height: 220px;
  border-radius: 8px;
  background: #fff1f3;
  overflow: hidden;
}

.image-box img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: white;
}

.image-fallback {
  width: 80px;
  height: 120px;
  border-radius: 12px;
  background: linear-gradient(160deg, #f5b7c3, #c65367);
}

.brand {
  color: #c65367;
  font-size: 13px;
  font-weight: 900;
}

.summary-body h1 {
  margin: 6px 0 12px;
  font-size: 30px;
  letter-spacing: 0;
}

.summary-body p {
  color: #5f5754;
  line-height: 1.6;
}

.link-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 112px;
  gap: 10px;
  margin-top: 24px;
}

.link-row input {
  min-width: 0;
  height: 44px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  padding: 0 14px;
  color: #2d2524;
}

.link-row button {
  height: 44px;
  border: none;
  border-radius: 8px;
  background: #c65367;
  color: white;
  font-weight: 900;
  cursor: pointer;
}

.link-row button:disabled {
  cursor: not-allowed;
  background: #d9c4c4;
}

.source-label {
  margin: 12px 0 0;
  color: #8e7e79;
  font-size: 12px;
  word-break: break-all;
}

.option-summary {
  padding: 22px;
  border-radius: 8px;
  background: #fff8f6;
}

.option-summary span {
  display: block;
  width: 54px;
  height: 54px;
  border: 1px solid rgba(45, 37, 36, 0.1);
  border-radius: 50%;
}

.option-summary p {
  margin: 16px 0 0;
  color: #8e7e79;
  font-weight: 800;
}

.option-summary strong,
.option-summary em {
  display: block;
  margin-top: 8px;
}

.option-summary em {
  color: #c65367;
  font-style: normal;
  font-weight: 900;
}

@media (max-width: 980px) {
  .product-input-card {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .link-row {
    grid-template-columns: 1fr;
  }
}
</style>
