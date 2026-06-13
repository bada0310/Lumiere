<template>
  <div class="post-card-wrapper">
    <div class="post-user-info">
      <img :src="post.userAvatar || 'https://via.placeholder.com/40'" class="user-avatar" alt="avatar"/>
      <div class="user-meta">
        <span class="nickname">{{ post.author }}</span>
        <span class="user-tone-tag">{{ post.userTone }}</span>
        <span class="time">{{ post.time }}</span>
      </div>
    </div>

    <div class="post-main-content" @click="goToDetail">
      <div class="text-area">
        <h3 class="post-title">{{ post.title }}</h3>
        <p class="post-body">{{ post.content }}</p>
        
        <div class="product-tags">
          <span v-for="tag in post.tags" :key="tag" class="tag-item" @click.stop="goToProduct(tag)">
            {{ tag }}
          </span>
        </div>
      </div>
      
      <div v-if="post.images && post.images.length" class="post-image-gallery">
        <img v-for="(img, idx) in post.images.slice(0, 2)" :key="idx" :src="img" alt="post-thumbnail" />
      </div>
    </div>

    <div class="post-card-footer">
      <div class="interaction-buttons">
        <button class="like-btn" :class="{ liked: post.isLiked }" @click.stop="toggleLike">
          ❤️ <span>{{ post.likes }}</span>
        </button>
        <button class="comment-btn">
          💬 <span>{{ post.comments }}</span>
        </button>
      </div>
      <button class="scrap-btn">🔖</button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const props = defineProps({
  post: {
    type: Object,
    required: true
  }
});

const router = useRouter();

const goToDetail = () => {
  router.push(`/community/detail/${props.post.id}`);
};

const goToProduct = (tagName) => {
  // 제품 태그 클릭 시 제품 상세로 라우팅 연동 연계
  router.push({ name: 'ProductDetail', query: { q: tagName } });
};

const toggleLike = () => {
  // 좋아요 처리 로직 공간
  console.log('좋아요 토글:', props.post.id);
};
</script>

<style scoped>
.post-card-wrapper { background: white; border: 1px solid #f0f0f0; border-radius: 16px; padding: 24px; margin-bottom: 16px; }
.post-user-info { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.user-avatar { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; }
.user-meta { display: flex; align-items: center; gap: 8px; }
.nickname { font-weight: bold; font-size: 0.9rem; }
.user-tone-tag { background: #fff5f6; color: #8b3a4a; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
.time { color: #aaa; font-size: 0.8rem; }

.post-main-content { display: flex; gap: 20px; justify-content: space-between; cursor: pointer; margin-bottom: 16px; }
.text-area { flex: 1; }
.post-title { font-size: 1.1rem; margin: 0 0 8px 0; font-weight: 700; color: #222; }
.post-body { font-size: 0.9rem; color: #666; line-height: 1.5; margin: 0 0 16px 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.product-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag-item { background: #f5f5f5; border: 1px solid #e8e8e8; color: #555; font-size: 0.8rem; padding: 4px 10px; border-radius: 6px; cursor: pointer; }
.tag-item:hover { border-color: #8b3a4a; color: #8b3a4a; }

.post-image-gallery { display: flex; gap: 8px; }
.post-image-gallery img { width: 90px; height: 90px; border-radius: 8px; object-fit: cover; }

.post-card-footer { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #fafafa; padding-top: 12px; }
.interaction-buttons { display: flex; gap: 16px; }
.interaction-buttons button, .scrap-btn { background: none; border: none; cursor: pointer; display: flex; align-items: center; gap: 6px; font-size: 0.9rem; color: #666; }
.like-btn.liked { color: #8b3a4a; font-weight: bold; }
</style>