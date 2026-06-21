<template>
  <div class="post-card-wrapper">
    <div class="post-user-info">
      <UserAvatar :src="post.userAvatar" :alt="`${post.author} 프로필 이미지`" size="md" />
      <div class="user-meta">
        <span class="nickname">{{ post.author }}</span>
        <span class="user-tone-tag">{{ post.userTone }}</span>
      </div>
      <span class="time">{{ post.time }}</span>
    </div>

    <div class="post-main-content" @click="goToDetail">
      <div class="text-area">
        <h3 class="post-title">{{ post.title }}</h3>
        <p class="post-body">{{ post.content }}</p>
        
        <div class="product-tags">
          <span v-for="product in post.products" :key="product.id" class="tag-item" @click.stop="goToProduct(product)">
            {{ product.brand }} {{ product.name }}
          </span>
        </div>
      </div>
      
      <div v-if="post.image_url" class="post-image-gallery">
        <img :src="post.image_url" alt="post-image" />
      </div>
    </div>

    <div class="post-card-footer">
      <div class="interaction-buttons">
        <button class="action-btn like-btn" @click.stop="toggleLike">
          {{ post.is_liked ? '❤️' : '🤍' }} {{ post.like_count }}
        </button>
        <button class="action-btn comment-btn" @click.stop="goToDetail">
          💬 {{ post.comment_count }}
        </button>
      </div>
      <div class="owner-actions" v-if="post.canEdit">
        <button class="action-btn" @click.stop="emit('edit', post)">수정</button>
        <button class="action-btn delete-btn" @click.stop="emit('delete', post)">삭제</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import UserAvatar from '@/components/user/UserAvatar.vue';

const props = defineProps({
  post: Object
});
const emit = defineEmits(['like', 'edit', 'delete']);

const router = useRouter();

const goToDetail = () => router.push({
  name: 'community-detail',
  params: { id: props.post.id },
});
const goToProduct = (product) => router.push({ name: 'product-detail', params: { id: product.id } });
const toggleLike = () => emit('like', props.post);
</script>

<style scoped>
.post-card-wrapper { 
  background: white; border: 1px solid #f0f0f0; border-radius: 16px; 
  padding: 24px; cursor: pointer; transition: border-color 0.2s;
  font-family: "Pretendard", "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
  letter-spacing: 0;
}
.post-card-wrapper:hover { border-color: #8b3a4a; }

.post-user-info { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.user-meta { display: flex; align-items: center; gap: 8px; flex: 1; }
.nickname { font-weight: 600; font-size: 0.9rem; color: #333; }
.user-tone-tag { background: #fff5f6; color: #8b3a4a; font-size: 0.72rem; padding: 4px 8px; border-radius: 6px; font-weight: 500; }
.time { color: #aaa; font-size: 0.85rem; }

.post-main-content { display: flex; gap: 30px; justify-content: space-between; margin-bottom: 20px; }
.text-area { flex: 1; }
.post-title { font-size: 1.08rem; margin: 0 0 10px 0; font-weight: 600; color: #222; line-height: 1.45; }
.post-body { font-size: 0.9rem; color: #666; line-height: 1.65; margin: 0 0 16px 0; font-weight: 400; }

.product-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tag-item { background: #f5f5f5; color: #555; font-size: 0.78rem; padding: 6px 12px; border-radius: 20px; font-weight: 400; }
.tag-item:hover { background: #eee; }

/* 이미지 나란히 배치 */
.post-image-gallery { display: flex; gap: 10px; }
.post-image-gallery img { width: 120px; height: 120px; border-radius: 12px; object-fit: cover; border: 1px solid #f0f0f0; }

.post-card-footer { display: flex; justify-content: space-between; align-items: center; }
.interaction-buttons { display: flex; gap: 16px; }
.action-btn { background: none; border: none; font-size: 0.88rem; color: #666; cursor: pointer; display: flex; align-items: center; gap: 6px; font-family: inherit; font-weight: 400; }
.like-btn:hover { color: #8b3a4a; font-weight: 600; }
.owner-actions { display: flex; gap: 10px; }
.delete-btn { color: #b04658; }
</style>
