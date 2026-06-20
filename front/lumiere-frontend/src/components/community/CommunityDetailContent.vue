<template>
  <article class="detail-card">
    <button type="button" class="back-btn" @click="$emit('back')">← 목록으로 돌아가기</button>

    <div class="detail-head">
      <span class="category-pill">{{ categoryLabel }}</span>
      <h1>{{ post.title }}</h1>
      <button type="button" class="follow-btn">+ 팔로우</button>
      <button type="button" class="more-btn" aria-label="더보기">⋯</button>
    </div>

    <div class="author-row">
      <img :src="post.userAvatar" alt="" />
      <strong>{{ post.author }}</strong>
      <span>{{ post.userTone }}</span>
      <small>{{ post.time }}</small>
    </div>

    <div class="hash-row">
      <span v-for="tag in displayHashTags" :key="tag">#{{ tag }}</span>
    </div>

    <p class="body-text">{{ post.content }}</p>

    <CommunityImageSlider :images="displayImages" />

    <div v-if="post.products?.length" class="product-grid">
      <div v-for="product in post.products.slice(0, 2)" :key="product.id" class="product-card">
        <span class="product-thumb"></span>
        <div>
          <strong>{{ product.brand }}</strong>
          <p>{{ product.name }}</p>
        </div>
      </div>
    </div>

    <div class="action-row">
      <button type="button" :class="{ liked: post.is_liked }" @click="$emit('like', post)">
        {{ post.is_liked ? '♥' : '♡' }} <span>{{ post.like_count }}</span>
      </button>
      <button type="button">댓글 <span>{{ post.comment_count }}</span></button>
      <span class="spacer"></span>
      <button type="button">공유</button>
      <button type="button">저장</button>
    </div>

    <section class="comment-section">
      <div class="comment-head">
        <h2>댓글 {{ comments.length }}</h2>
        <select v-model="commentSort">
          <option value="latest">최신순</option>
          <option value="oldest">등록순</option>
        </select>
      </div>

      <CommentForm :disabled="!isLoggedIn" @submit="$emit('submit-comment', $event)" />
      <CommentThread :comments="comments" :sort="commentSort" @like-comment="$emit('like-comment', $event)" />
    </section>
  </article>
</template>

<script setup>
import { computed, ref } from 'vue'
import CommentForm from '@/components/community/CommentForm.vue'
import CommentThread from '@/components/community/CommentThread.vue'
import CommunityImageSlider from '@/components/community/CommunityImageSlider.vue'
import { getCommunityCategoryByApiValue } from '@/data/communityCategories'

const props = defineProps({
  post: {
    type: Object,
    required: true,
  },
  comments: {
    type: Array,
    default: () => [],
  },
  isLoggedIn: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['back', 'like', 'submit-comment', 'like-comment'])

const commentSort = ref('latest')

const categoryLabel = computed(
  () => getCommunityCategoryByApiValue(props.post?.category)?.label || '커뮤니티',
)

const displayHashTags = computed(() => {
  const base = [categoryLabel.value, props.post?.userTone, '데일리룩']
  return base.filter(Boolean).map((tag) => String(tag).replace(/\s/g, ''))
})

const displayImages = computed(() => {
  const images = props.post?.image_url ? [props.post.image_url] : []
  return images.length
    ? images
    : [
        'https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=400&q=80',
        'https://images.unsplash.com/photo-1631214540242-3cd8c4f8bbdd?w=400&q=80',
        'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400&q=80',
      ]
})
</script>

<style scoped>
.detail-card {
  background: #ffffff;
  border: 1px solid #eaded8;
  border-radius: 14px;
  padding: 28px 30px;
  font-family: "Pretendard Variable", Pretendard, "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
}

.back-btn {
  border: none;
  background: transparent;
  color: #5f5754;
  cursor: pointer;
  font-size: 0.9rem;
  margin-bottom: 22px;
}

.detail-head {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 12px;
  align-items: center;
}

.category-pill {
  grid-column: 1 / -1;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #f0c9d1;
  background: #fff5f6;
  color: #c65367;
  font-size: 0.82rem;
  font-weight: 600;
}

.detail-head h1 {
  margin: 4px 0 0;
  color: #171312;
  font-size: 1.72rem;
  line-height: 1.35;
  font-weight: 700;
}

.follow-btn {
  height: 38px;
  padding: 0 16px;
  border: 1px solid #f0c9d1;
  border-radius: 8px;
  background: #fff5f6;
  color: #c65367;
  font-weight: 600;
  cursor: pointer;
}

.more-btn {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  cursor: pointer;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 18px 0;
}

.author-row img {
  width: 38px;
  height: 38px;
  border-radius: 50%;
}

.author-row strong {
  font-size: 0.94rem;
  font-weight: 600;
}

.author-row span {
  padding: 4px 8px;
  border-radius: 8px;
  background: #fff5f6;
  color: #c65367;
  font-size: 0.75rem;
}

.author-row small {
  color: #9d918d;
}

.hash-row {
  display: flex;
  gap: 12px;
  margin: 18px 0;
  color: #c65367;
  font-weight: 600;
  flex-wrap: wrap;
}

.body-text {
  color: #3f3633;
  line-height: 1.75;
  margin-bottom: 0;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 24px 0 20px;
}

.product-card {
  display: flex;
  gap: 12px;
  align-items: center;
  border: 1px solid #eaded8;
  border-radius: 10px;
  padding: 12px;
}

.product-thumb {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  background: #f6dfe3;
}

.product-card strong {
  display: block;
  font-weight: 600;
}

.product-card p {
  color: #6d5f5b;
  font-size: 0.82rem;
}

.action-row {
  display: flex;
  gap: 22px;
  border-bottom: 1px solid #f0e5e0;
  padding-bottom: 20px;
}

.action-row button {
  border: none;
  background: transparent;
  color: #5f5754;
  cursor: pointer;
  font-size: 0.95rem;
}

.action-row .liked {
  color: #c65367;
}

.spacer {
  flex: 1;
}

.comment-section {
  padding-top: 22px;
}

.comment-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.comment-head h2 {
  font-size: 1rem;
  font-weight: 700;
}

.comment-head select {
  border: none;
  background: transparent;
  color: #5f5754;
  font: inherit;
}

@media (max-width: 760px) {
  .detail-card {
    padding: 22px;
  }

  .product-grid {
    grid-template-columns: 1fr;
  }
}
</style>
