<template>
  <section class="diagnosis-loading-story" aria-live="polite">
    <div class="diagnosis-loading-story__preview">
      <img v-if="previewUrl" :src="previewUrl" alt="업로드한 진단 이미지" />
      <div v-else class="diagnosis-loading-story__placeholder">FACE</div>
    </div>

    <div class="diagnosis-loading-story__content">
      <p class="diagnosis-loading-story__eyebrow">AI Personal Color Analysis</p>
      <h1>퍼스널 컬러를 분석하고 있어요</h1>
      <p>{{ message }}</p>

      <div class="diagnosis-loading-story__steps">
        <div
          v-for="(step, index) in steps"
          :key="step.key"
          class="diagnosis-loading-story__step"
          :class="stepClass(step.key)"
        >
          <span class="diagnosis-loading-story__dot">
            <template v-if="isDone(step.key)">✓</template>
            <template v-else>{{ index + 1 }}</template>
          </span>
          <div>
            <strong>{{ step.title }}</strong>
            <small>{{ step.description }}</small>
          </div>
        </div>
      </div>

      <p v-if="error" class="diagnosis-loading-story__error">{{ error }}</p>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  steps: {
    type: Array,
    required: true,
  },
  currentStep: {
    type: String,
    required: true,
  },
  previewUrl: {
    type: String,
    default: '',
  },
  message: {
    type: String,
    default: '업로드한 사진을 바탕으로 피부 톤과 분위기를 분석하고 있어요.',
  },
  error: {
    type: String,
    default: '',
  },
})

const currentIndex = () => props.steps.findIndex((step) => step.key === props.currentStep)
const stepIndex = (key) => props.steps.findIndex((step) => step.key === key)
const isDone = (key) => stepIndex(key) < currentIndex()
const stepClass = (key) => ({
  'is-done': isDone(key),
  'is-active': key === props.currentStep,
})
</script>

<style scoped>
.diagnosis-loading-story {
  max-width: 1040px;
  margin: 0 auto;
  padding: 28px;
  border: 1px solid #eaded8;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  display: grid;
  grid-template-columns: minmax(260px, 0.82fr) minmax(0, 1fr);
  gap: 28px;
  box-shadow: 0 22px 60px rgba(88, 55, 45, 0.06);
}

.diagnosis-loading-story__preview {
  min-height: 440px;
  border-radius: 14px;
  background: linear-gradient(135deg, #f6e7df, #fff4ef);
  overflow: hidden;
  display: grid;
  place-items: center;
}

.diagnosis-loading-story__preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.diagnosis-loading-story__placeholder {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: #f0c8bd;
  color: #9e4655;
  display: grid;
  place-items: center;
  font-size: 22px;
  font-weight: 900;
}

.diagnosis-loading-story__content {
  min-width: 0;
  display: grid;
  align-content: center;
}

.diagnosis-loading-story__eyebrow {
  margin: 0 0 8px;
  color: #c65367;
  font-size: 13px;
  font-weight: 900;
}

.diagnosis-loading-story h1 {
  margin: 0;
  color: #211c1b;
  font-size: clamp(28px, 4vw, 44px);
  letter-spacing: 0;
}

.diagnosis-loading-story__content > p:not(.diagnosis-loading-story__eyebrow):not(.diagnosis-loading-story__error) {
  margin: 14px 0 26px;
  color: #6d625f;
  line-height: 1.65;
}

.diagnosis-loading-story__steps {
  display: grid;
  gap: 0;
}

.diagnosis-loading-story__step {
  position: relative;
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 14px;
  padding-bottom: 22px;
  color: #8e7e79;
}

.diagnosis-loading-story__step:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 16px;
  top: 36px;
  bottom: 4px;
  width: 1px;
  background: #eaded8;
}

.diagnosis-loading-story__dot {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid #eaded8;
  background: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 900;
  z-index: 1;
}

.diagnosis-loading-story__step strong,
.diagnosis-loading-story__step small {
  display: block;
}

.diagnosis-loading-story__step strong {
  color: #5f5754;
}

.diagnosis-loading-story__step small {
  margin-top: 4px;
  line-height: 1.45;
}

.diagnosis-loading-story__step.is-done .diagnosis-loading-story__dot,
.diagnosis-loading-story__step.is-active .diagnosis-loading-story__dot {
  border-color: #c65367;
  background: #c65367;
  color: #fff;
}

.diagnosis-loading-story__step.is-active strong {
  color: #c65367;
}

.diagnosis-loading-story__error {
  margin: 4px 0 0;
  color: #b44352;
  font-size: 14px;
  font-weight: 800;
}

@media (max-width: 840px) {
  .diagnosis-loading-story {
    grid-template-columns: 1fr;
    padding: 18px;
  }

  .diagnosis-loading-story__preview {
    min-height: 280px;
  }
}
</style>
