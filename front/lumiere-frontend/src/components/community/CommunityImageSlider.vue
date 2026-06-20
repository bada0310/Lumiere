<template>
  <div v-if="images.length" class="image-slider" aria-label="게시글 이미지">
    <button
      type="button"
      class="slide-btn prev"
      aria-label="이전 이미지"
      :disabled="images.length <= visibleCount"
      @click="move(-1)"
    >
      ‹
    </button>
    <div class="image-track">
      <img v-for="image in visibleImages" :key="image" :src="image" alt="" />
    </div>
    <button
      type="button"
      class="slide-btn next"
      aria-label="다음 이미지"
      :disabled="images.length <= visibleCount"
      @click="move(1)"
    >
      ›
    </button>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  images: {
    type: Array,
    default: () => [],
  },
})

const activeIndex = ref(0)
const visibleCount = 3

const visibleImages = computed(() => {
  if (props.images.length <= visibleCount) return props.images
  return Array.from({ length: visibleCount }, (_, index) => {
    const nextIndex = (activeIndex.value + index) % props.images.length
    return props.images[nextIndex]
  })
})

const move = (direction) => {
  if (props.images.length <= visibleCount) return
  activeIndex.value = (activeIndex.value + direction + props.images.length) % props.images.length
}
</script>

<style scoped>
.image-slider {
  position: relative;
  margin: 24px 0;
}

.image-track {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.image-track img {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 10px;
  object-fit: cover;
  background: #f6eeee;
}

.slide-btn {
  position: absolute;
  top: 50%;
  z-index: 2;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid #f0c9d1;
  background: white;
  color: #c65367;
  cursor: pointer;
  transform: translateY(-50%);
}

.slide-btn:disabled {
  opacity: 0.45;
  cursor: default;
}

.prev {
  left: -18px;
}

.next {
  right: -18px;
}

@media (max-width: 760px) {
  .image-track {
    grid-template-columns: 1fr;
  }

  .slide-btn {
    display: none;
  }
}
</style>
