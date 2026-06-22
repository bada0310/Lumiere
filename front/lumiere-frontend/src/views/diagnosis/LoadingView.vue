<template>
  <div class="page">
    <main class="loading-page">
      <section class="steps" aria-label="진단 단계">
        <div class="step done">✓</div>
        <div class="line active"></div>
        <div class="step active">2</div>
        <div class="line"></div>
        <div class="step">3</div>
      </section>

      <section class="step-labels">
        <span class="done-text">사진 업로드</span>
        <span class="active-text">AI 분석</span>
        <span>결과 확인</span>
      </section>

      <DiagnosisLoadingStory
        :steps="analysisSteps"
        :current-step="currentStep"
        :preview-url="previewUrl"
        :message="currentMessage"
        :error="errorMessage"
      />

      <div class="loading-actions">
        <button v-if="errorMessage" type="button" class="outline-btn" @click="router.push('/upload')">다시 업로드하기</button>
        <button v-else type="button" class="outline-btn" @click="router.push('/upload')">분석 취소</button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import DiagnosisLoadingStory from '@/components/diagnosis/DiagnosisLoadingStory.vue'
import { createDiagnosis } from '@/services/diagnosisApi'

const router = useRouter()

const historyState = window.history.state || {}
const diagnosisFile = historyState.diagnosisFile || null
const previewUrl = ref(historyState.previewUrl || '')
const errorMessage = ref('')
const currentStep = ref('uploaded')
const stepTimer = ref(null)

const analysisSteps = [
  {
    key: 'uploaded',
    title: '사진 업로드 완료',
    description: '업로드한 이미지를 분석 준비 중이에요.',
  },
  {
    key: 'face_analysis',
    title: '얼굴 정보 분석 중',
    description: '피부 톤과 전체 인상을 읽고 있어요.',
  },
  {
    key: 'tone_detection',
    title: '퍼스널 컬러 판별 중',
    description: '고정 toneKey 중 가장 가까운 타입을 찾고 있어요.',
  },
  {
    key: 'makeup_guide',
    title: '메이크업 가이드 정리 중',
    description: 'DB의 고정 팔레트를 바탕으로 컬러칩을 준비해요.',
  },
  {
    key: 'result_ready',
    title: '결과 준비 중',
    description: '결과 페이지를 정리하고 있어요.',
  },
]

const currentMessage = computed(() => {
  const step = analysisSteps.find((item) => item.key === currentStep.value)
  return step?.description || '업로드한 사진을 바탕으로 피부 톤과 분위기를 분석하고 있어요.'
})

const advanceSteps = () => {
  let index = 0
  currentStep.value = analysisSteps[index].key
  stepTimer.value = window.setInterval(() => {
    index = Math.min(index + 1, analysisSteps.length - 1)
    currentStep.value = analysisSteps[index].key
    if (index >= analysisSteps.length - 1 && stepTimer.value) {
      window.clearInterval(stepTimer.value)
      stepTimer.value = null
    }
  }, 1400)
}

const submitDiagnosis = async () => {
  if (!diagnosisFile) {
    errorMessage.value = '분석할 이미지가 없어요. 다시 업로드해 주세요.'
    return
  }

  advanceSteps()

  try {
    const result = await createDiagnosis(diagnosisFile)
    currentStep.value = 'result_ready'
    router.replace(`/diagnosis/results/${result.id}`)
  } catch (error) {
    const detail = error?.response?.data?.detail
    errorMessage.value = detail || '진단 요청을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.'
  }
}

onMounted(submitDiagnosis)
onBeforeUnmount(() => {
  if (stepTimer.value) window.clearInterval(stepTimer.value)
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #fffaf7;
}

.loading-page {
  min-height: 100vh;
  padding: 32px 48px 48px;
  background: linear-gradient(180deg, #fffaf7 0%, #fbf4f1 100%);
}

.steps {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 4px;
}

.step {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: white;
  border: 1px solid #ddd;
  color: #777;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.step.done,
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
  background: #d98c99;
}

.step-labels {
  width: 560px;
  margin: 10px auto 30px;
  display: flex;
  justify-content: space-between;
  color: #777;
  font-size: 14px;
}

.done-text,
.active-text {
  color: #c65367;
  font-weight: 700;
}

.loading-actions {
  margin-top: 22px;
  text-align: center;
}

.outline-btn {
  min-width: 180px;
  min-height: 44px;
  border: 1px solid #d98c99;
  border-radius: 8px;
  background: #fff;
  color: #c65367;
  font-weight: 800;
  cursor: pointer;
}

@media (max-width: 720px) {
  .loading-page {
    padding: 22px 16px 40px;
  }

  .step-labels {
    width: 100%;
  }

  .line {
    width: 64px;
  }
}
</style>
