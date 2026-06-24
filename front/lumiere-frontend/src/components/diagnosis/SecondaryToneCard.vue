<template>
  <section class="secondary-tone-card" aria-label="2순위 퍼스널 컬러 후보">
    <div class="secondary-tone-card__image">
      <img :src="tone.image_url" :alt="`${tone.toneNameKo || tone.toneNameEn || tone.tone_key} 대표 이미지`" />
    </div>

    <div class="secondary-tone-card__body">
      <div class="secondary-tone-card__topline">
        <span>2순위 후보</span>
        <strong v-if="hasConfidence">보조 가능성 {{ tone.confidence }}%</strong>
      </div>
      <h3>{{ tone.toneNameKo || tone.tone_key }}</h3>
      <p class="secondary-tone-card__en">{{ tone.toneNameEn }}</p>
      <p v-if="tone.reason" class="secondary-tone-card__reason">{{ tone.reason }}</p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tone: {
    type: Object,
    required: true,
  },
})

const hasConfidence = computed(() => Number.isFinite(Number(props.tone?.confidence)))
</script>

<style scoped>
.secondary-tone-card {
  margin-top: 18px;
  padding: 14px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fffaf7;
  display: grid;
  grid-template-columns: 76px 1fr;
  gap: 14px;
  align-items: center;
}

.secondary-tone-card__image {
  width: 76px;
  aspect-ratio: 1 / 1;
  border-radius: 10px;
  overflow: hidden;
  background: #f8eeee;
  border: 1px solid rgba(198, 83, 103, 0.12);
}

.secondary-tone-card__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.secondary-tone-card__body {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.secondary-tone-card__topline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.secondary-tone-card__topline span {
  color: #9e4655;
  font-size: 12px;
  font-weight: 900;
}

.secondary-tone-card__topline strong {
  color: #786b67;
  font-size: 12px;
  font-weight: 800;
}

.secondary-tone-card h3 {
  margin: 0;
  color: #2d2524;
  font-size: 17px;
}

.secondary-tone-card__en,
.secondary-tone-card__reason {
  margin: 0;
  color: #756965;
  font-size: 12px;
  line-height: 1.5;
}

.secondary-tone-card__reason {
  margin-top: 2px;
  color: #5f5552;
}

@media (max-width: 520px) {
  .secondary-tone-card {
    grid-template-columns: 64px 1fr;
  }

  .secondary-tone-card__image {
    width: 64px;
  }
}
</style>
