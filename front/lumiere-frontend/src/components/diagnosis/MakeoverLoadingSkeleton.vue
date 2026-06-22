<template>
  <div class="makeover-skeleton" role="status" aria-live="polite">
    <article v-for="index in count" :key="index" class="makeover-skeleton__card">
      <div class="makeover-skeleton__image"></div>
      <div class="makeover-skeleton__line makeover-skeleton__line--short"></div>
      <div class="makeover-skeleton__line"></div>
    </article>
    <p class="makeover-skeleton__message">{{ message }}</p>
  </div>
</template>

<script setup>
defineProps({
  count: {
    type: Number,
    default: 3,
  },
  message: {
    type: String,
    default: 'AI 메이크오버 이미지를 생성하고 있어요.',
  },
})
</script>

<style scoped>
.makeover-skeleton {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(3, minmax(160px, 1fr));
  gap: 16px;
}

.makeover-skeleton__card {
  padding: 12px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fffaf7;
}

.makeover-skeleton__image,
.makeover-skeleton__line {
  border-radius: 8px;
  background: linear-gradient(90deg, #f6e4df 0%, #fff7f5 48%, #f6e4df 100%);
  background-size: 220% 100%;
  animation: shimmer 1.3s ease-in-out infinite;
}

.makeover-skeleton__image {
  width: 100%;
  aspect-ratio: 1.5 / 1;
  margin-bottom: 12px;
}

.makeover-skeleton__line {
  height: 12px;
  margin-top: 8px;
}

.makeover-skeleton__line--short {
  width: 48%;
}

.makeover-skeleton__message {
  grid-column: 1 / -1;
  margin: 0;
  color: #8e7e79;
  font-size: 13px;
  text-align: center;
}

@keyframes shimmer {
  0% {
    background-position: 120% 0;
  }
  100% {
    background-position: -120% 0;
  }
}

@media (max-width: 840px) {
  .makeover-skeleton {
    grid-template-columns: 1fr;
  }
}
</style>
