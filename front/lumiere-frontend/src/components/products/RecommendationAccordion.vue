<template>
  <article class="recommendation-accordion">
    <div class="section-head">
      <div>
        <h2>내 추천 결과</h2>
        <p>옵션을 누르면 추천 이유와 사용 팁을 확인할 수 있습니다.</p>
      </div>
    </div>

    <section v-for="group in groups" :key="group.grade" class="grade-group">
      <header>
        <span :class="['grade-dot', group.grade.toLowerCase()]"></span>
        <h3>{{ group.label }}</h3>
        <em>{{ group.options.length }}</em>
      </header>

      <RecommendationAccordionItem
        v-for="option in group.options"
        :key="option.id"
        :option="option"
        :is-open="String(openOptionId) === String(option.id)"
        :is-selected="String(selectedOption?.id || '') === String(option.id)"
        @toggle="toggleOption"
      />

      <p v-if="!group.options.length" class="empty-line">해당 옵션이 없습니다.</p>
    </section>
  </article>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

import RecommendationAccordionItem from '@/components/products/RecommendationAccordionItem.vue'

const props = defineProps({
  options: {
    type: Array,
    default: () => [],
  },
  selectedOption: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['select'])
const openOptionId = ref('')

const groups = computed(() => {
  const order = [
    { grade: 'BEST', label: 'BEST' },
    { grade: 'GOOD', label: 'GOOD' },
    { grade: 'CAUTION', label: 'CAUTION' },
    { grade: 'PENDING', label: 'Pending analysis' },
  ]
  return order.map((item) => ({
    ...item,
    options: props.options.filter((option) => normalizedGrade(option) === item.grade),
  }))
})

const toggleOption = (option) => {
  const id = String(option?.id || '')
  openOptionId.value = openOptionId.value === id ? '' : id
  emit('select', option)
}

watch(
  () => props.selectedOption?.id,
  (id) => {
    if (id && !openOptionId.value) openOptionId.value = String(id)
  },
  { immediate: true },
)

const normalizedGrade = (option) => {
  const status = String(option?.analysis_status || option?.analysisStatus || '').toUpperCase()
  const grade = String(option?.grade || '').toUpperCase()
  if (status === 'PENDING_COLOR_ANALYSIS' || grade === 'PENDING') return 'PENDING'
  if (grade === 'BEST' || grade === 'GOOD' || grade === 'CAUTION') return grade
  const rawScore = option?.match_score
  if (rawScore === null || rawScore === undefined || rawScore === '') return ''
  const score = Number(rawScore)
  if (!Number.isFinite(score)) return ''
  if (score >= 85) return 'BEST'
  if (score >= 70) return 'GOOD'
  return 'CAUTION'
}
</script>

<style scoped>
.recommendation-accordion {
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  padding: 24px;
}

.section-head {
  margin-bottom: 18px;
}

.section-head h2 {
  margin: 0 0 8px;
}

.section-head p {
  margin: 0;
  color: #6b625f;
}

.grade-group + .grade-group {
  margin-top: 18px;
}

.grade-group header {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}

.grade-group h3 {
  margin: 0;
  font-size: 15px;
}

.grade-group em {
  margin-left: auto;
  color: #8e7e79;
  font-style: normal;
  font-weight: 900;
}

.grade-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.grade-dot.best {
  background: #c65367;
}

.grade-dot.good {
  background: #7aa52e;
}

.grade-dot.caution {
  background: #d6a400;
}

.grade-dot.pending {
  background: #d9d3cf;
  border: 1px dashed rgba(94, 74, 70, 0.55);
}

.empty-line {
  margin: 0;
  border: 1px dashed #eaded8;
  border-radius: 8px;
  color: #8e7e79;
  padding: 12px;
  text-align: center;
}
</style>
