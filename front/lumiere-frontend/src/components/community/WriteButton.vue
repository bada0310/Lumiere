<template>
  <div class="floating-write-container">
    <button class="write-floating-btn" @click="navigateToWrite">
      <span class="pencil-icon">📝</span> 글쓰기
    </button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const navigateToWrite = () => {
  router.push('/community/write');
};
</script>

<style scoped>
.floating-write-container {
  position: fixed;
  bottom: 40px;
  right: calc((100% - 1100px) / 2 + 20px); /* 메인 컨테이너 레이아웃 우하단 정렬 정합성 */
}

@media (max-width: 1200px) {
  .floating-write-container {
    right: 30px;
  }
}

.write-floating-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: #8b3a4a;
  color: white;
  border: none;
  padding: 14px 24px;
  border-radius: 30px;
  font-size: 1rem;
  font-weight: bold;
  box-shadow: 0 4px 16px rgba(139, 58, 74, 0.3);
  cursor: pointer;
  transition: transform 0.2s, background-color 0.2s;
}

.write-floating-btn:hover {
  background-color: #722e3c;
  transform: translateY(-2px);
}

.pencil-icon {
  font-size: 1.1rem;
}
</style>