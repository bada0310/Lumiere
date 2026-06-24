<template>
  <section class="original-image-card" aria-label="진단에 사용된 이미지">
    <div class="original-image-card__head">
      <span>진단 원본 이미지</span>
      <strong>진단에 사용된 이미지</strong>
    </div>

    <div class="original-image-card__frame" :class="{ empty: !imageUrl }">
      <img v-if="imageUrl" :src="imageUrl" :alt="alt" />
      <p v-else>진단 원본 이미지를 불러올 수 없습니다.</p>
    </div>
  </section>
</template>

<script setup>
defineProps({
  imageUrl: {
    type: String,
    default: '',
  },
  alt: {
    type: String,
    default: '진단에 사용된 이미지',
  },
})
</script>

<style scoped>
.original-image-card {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fffaf7;
}

.original-image-card__head {
  display: grid;
  gap: 3px;
}

.original-image-card__head span {
  color: #9e4655;
  font-size: 12px;
  font-weight: 800;
}

.original-image-card__head strong {
  color: #3c3331;
  font-size: 14px;
}

.original-image-card__frame {
  width: 100%;
  aspect-ratio: 4 / 3;
  border: 1px solid #eee3df;
  border-radius: 10px;
  background: #fff;
  overflow: hidden;
  display: grid;
  place-items: center;
}

.original-image-card__frame img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.original-image-card__frame.empty {
  padding: 18px;
  background: #f8eeee;
}

.original-image-card__frame p {
  margin: 0;
  color: #8e7e79;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.5;
  text-align: center;
}
</style>
