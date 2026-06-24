<template>
  <div class="accordion-item" :class="{ open: isOpen, selected: isSelected }">
    <button
      class="item-trigger"
      type="button"
      :aria-expanded="isOpen ? 'true' : 'false'"
      @click="$emit('toggle', option)"
    >
      <span class="swatch" :class="{ pending: isPending }" :style="{ backgroundColor: color }"></span>
      <span class="item-copy">
        <strong>{{ optionLabel }}</strong>
        <em>{{ option.short_reason || option.reason || fallbackShortReason }}</em>
      </span>
      <span class="score">{{ scoreLabel }}</span>
      <span class="chevron" aria-hidden="true">{{ isOpen ? '−' : '+' }}</span>
    </button>

    <transition name="accordion">
      <div v-if="isOpen" class="item-panel">
        <p class="grade-line">
          <strong>{{ gradeLabel }}</strong>
          <span>{{ toneFeature }}</span>
        </p>
        <p>{{ option.detail_reason || option.reason || fallbackDetailReason }}</p>
        <p class="tip">{{ option.usage_tip || fallbackUsageTip }}</p>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  option: {
    type: Object,
    required: true,
  },
  isOpen: {
    type: Boolean,
    default: false,
  },
  isSelected: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['toggle'])

const isPending = computed(() => {
  const status = String(props.option.analysis_status || props.option.analysisStatus || '').toUpperCase()
  const grade = String(props.option.grade || '').toUpperCase()
  return status === 'PENDING_COLOR_ANALYSIS' || grade === 'PENDING'
})

const color = computed(() => props.option.hex_code || props.option.hex || '#d9d3cf')
const optionLabel = computed(() => {
  return [props.option.option_no, props.option.display_name || props.option.option_name].filter(Boolean).join(' ') || '기본 옵션'
})
const gradeLabel = computed(() => (isPending.value ? '분석 대기' : props.option.grade || '분석 완료'))
const scoreLabel = computed(() => {
  if (isPending.value) return '분석 대기'
  const rawScore = props.option.match_score
  if (rawScore === null || rawScore === undefined || rawScore === '') return gradeLabel.value
  const score = Number(rawScore)
  return Number.isFinite(score) ? `${Math.round(score)}점` : gradeLabel.value
})
const toneFeature = computed(() => {
  if (isPending.value) return '색상 확인 필요'
  const brightness = Number(props.option.brightness)
  const saturation = Number(props.option.saturation)
  const coolness = Number(props.option.coolness)
  const lightWord = brightness >= 65 ? '라이트' : brightness <= 42 ? '딥' : '중명도'
  const chromaWord = saturation >= 65 ? '고채도' : saturation <= 40 ? '저채도' : '중채도'
  const tempWord = coolness >= 60 ? '쿨' : coolness <= 40 ? '웜' : '중성'
  return `${lightWord} · ${chromaWord} · ${tempWord}`
})
const fallbackShortReason = computed(() => (isPending.value ? '색상 확인이 필요합니다.' : '색상 분석값을 기준으로 추천 등급을 계산했습니다.'))
const fallbackDetailReason = computed(() => {
  if (isPending.value) return '옵션은 감지했지만 대표 색상을 아직 확정하지 못했습니다.'
  return `명도 ${metric(props.option.brightness)}, 채도 ${metric(props.option.saturation)}, 쿨니스 ${metric(props.option.coolness)} 기준으로 분류했습니다.`
})
const fallbackUsageTip = computed(() => {
  if (isPending.value) return 'HEX 색상을 확인하거나 직접 수정하면 추천 점수를 다시 계산할 수 있습니다.'
  if (gradeLabel.value === 'CAUTION') return '포인트 사용이나 양 조절로 톤 차이를 완화해보세요.'
  return '실제 발색은 조명과 피부톤에 따라 달라질 수 있습니다.'
})

const metric = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? Math.round(number) : '-'
}
</script>

<style scoped>
.accordion-item {
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: white;
  overflow: hidden;
}

.accordion-item + .accordion-item {
  margin-top: 8px;
}

.accordion-item.selected {
  border-color: #c65367;
  box-shadow: 0 10px 24px rgba(198, 83, 103, 0.12);
}

.item-trigger {
  width: 100%;
  min-height: 64px;
  border: none;
  background: transparent;
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr) auto 20px;
  gap: 10px;
  align-items: center;
  padding: 12px;
  color: #2d2524;
  text-align: left;
  cursor: pointer;
}

.swatch {
  width: 20px;
  height: 20px;
  border: 1px solid rgba(45, 37, 36, 0.12);
  border-radius: 50%;
}

.swatch.pending {
  background-color: #d9d3cf !important;
  border: 1px dashed rgba(94, 74, 70, 0.55);
}

.item-copy {
  min-width: 0;
}

.item-copy strong,
.item-copy em {
  display: block;
}

.item-copy strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.item-copy em {
  margin-top: 3px;
  overflow: hidden;
  color: #7a6d69;
  font-size: 12px;
  font-style: normal;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.score {
  color: #c65367;
  font-size: 13px;
  font-weight: 900;
  white-space: nowrap;
}

.chevron {
  color: #8e7e79;
  font-size: 20px;
  line-height: 1;
  text-align: center;
}

.item-panel {
  padding: 0 14px 14px 44px;
  color: #5f5754;
  line-height: 1.62;
}

.item-panel p {
  margin: 8px 0 0;
}

.grade-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.grade-line strong {
  border-radius: 999px;
  background: #fff0f1;
  color: #c65367;
  font-size: 12px;
  padding: 4px 8px;
}

.grade-line span,
.tip {
  color: #8e5f48;
}

.accordion-enter-active,
.accordion-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.accordion-enter-from,
.accordion-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 620px) {
  .item-trigger {
    grid-template-columns: 22px minmax(0, 1fr) 20px;
  }

  .score {
    grid-column: 2;
    justify-self: start;
  }
}
</style>
