<template>
  <div class="comments">
    <article v-for="comment in sortedComments" :key="comment.id" class="comment-item">
      <img :src="avatarUrl(comment)" alt="" />
      <div class="comment-body">
        <div class="comment-meta">
          <strong>{{ comment.author_nickname || comment.author_username || '익명' }}</strong>
          <span>{{ formatDate(comment.created_at) }}</span>
        </div>
        <p>{{ comment.content }}</p>
        <div class="comment-actions">
          <button
            type="button"
            class="comment-like"
            :class="{ liked: comment.is_liked }"
            @click="$emit('like-comment', comment)"
          >
            {{ comment.is_liked ? '♥' : '♡' }} {{ comment.like_count || 0 }}
          </button>
          <button type="button" class="reply-btn" disabled>답글</button>
        </div>

        <div v-if="comment.replies?.length" class="replies">
          <article v-for="reply in comment.replies" :key="reply.id" class="comment-item reply">
            <img :src="avatarUrl(reply)" alt="" />
            <div>
              <div class="comment-meta">
                <strong>{{ reply.author_nickname || reply.author_username || '익명' }}</strong>
                <span>{{ formatDate(reply.created_at) }}</span>
              </div>
              <p>{{ reply.content }}</p>
            </div>
          </article>
        </div>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  comments: {
    type: Array,
    default: () => [],
  },
  sort: {
    type: String,
    default: 'latest',
  },
})

defineEmits(['like-comment'])

const sortedComments = computed(() => {
  const copied = [...props.comments]
  return props.sort === 'latest' ? copied.reverse() : copied
})

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const avatarUrl = (comment) => `https://i.pravatar.cc/100?u=${comment.author_username || comment.id}`
</script>

<style scoped>
.comments {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.comment-item {
  display: flex;
  gap: 12px;
}

.comment-item img {
  width: 34px;
  height: 34px;
  border-radius: 50%;
}

.comment-body {
  min-width: 0;
  flex: 1;
}

.comment-meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.comment-meta strong {
  font-weight: 600;
}

.comment-meta span {
  color: #9d918d;
  font-size: 0.78rem;
}

.comment-item p {
  margin: 6px 0;
  color: #4f4542;
  line-height: 1.55;
}

.comment-actions {
  display: flex;
  gap: 12px;
}

.comment-actions button {
  border: none;
  background: transparent;
  cursor: pointer;
  font: inherit;
}

.comment-like {
  color: #c65367;
}

.comment-like.liked {
  font-weight: 700;
}

.reply-btn {
  color: #9d918d;
}

.reply-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.replies {
  margin-top: 14px;
  padding-left: 14px;
  border-left: 2px solid #f0e5e0;
}

.reply {
  margin-top: 12px;
}
</style>
