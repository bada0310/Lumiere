<template>
  <div class="comments">
    <article v-for="comment in sortedComments" :key="comment.id" class="comment-item">
      <UserAvatar
        :src="comment.author_profile_image_url"
        :alt="`${comment.author_nickname || comment.author_username || '익명'} 프로필 이미지`"
        size="sm"
      />
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
          <button type="button" class="reply-btn" @click="toggleReply(comment.id)">
            답글
          </button>
        </div>

        <form v-if="activeReplyId === comment.id" class="reply-form" @submit.prevent="submitReply(comment)">
          <input v-model.trim="replyContent" placeholder="답글을 입력해주세요..." />
          <button type="submit" :disabled="!replyContent">등록</button>
          <button type="button" class="cancel-btn" @click="closeReply">취소</button>
        </form>

        <div v-if="comment.replies?.length" class="replies">
          <article v-for="reply in comment.replies" :key="reply.id" class="comment-item reply">
            <UserAvatar
              :src="reply.author_profile_image_url"
              :alt="`${reply.author_nickname || reply.author_username || '익명'} 프로필 이미지`"
              size="sm"
            />
            <div class="comment-body">
              <div class="comment-meta">
                <strong>{{ reply.author_nickname || reply.author_username || '익명' }}</strong>
                <span>{{ formatDate(reply.created_at) }}</span>
              </div>
              <p>{{ reply.content }}</p>
              <div class="comment-actions">
                <button
                  type="button"
                  class="comment-like"
                  :class="{ liked: reply.is_liked }"
                  @click="$emit('like-comment', reply)"
                >
                  {{ reply.is_liked ? '♥' : '♡' }} {{ reply.like_count || 0 }}
                </button>
              </div>
            </div>
          </article>
        </div>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import UserAvatar from '@/components/user/UserAvatar.vue'

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

const emit = defineEmits(['like-comment', 'submit-reply'])

const activeReplyId = ref(null)
const replyContent = ref('')

const sortedComments = computed(() => {
  const copied = [...props.comments]
  return props.sort === 'latest' ? copied.reverse() : copied
})

const toggleReply = (commentId) => {
  activeReplyId.value = activeReplyId.value === commentId ? null : commentId
  replyContent.value = ''
}

const closeReply = () => {
  activeReplyId.value = null
  replyContent.value = ''
}

const submitReply = (comment) => {
  if (!replyContent.value) return
  emit('submit-reply', { comment, content: replyContent.value })
  closeReply()
}

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

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

.comment-like,
.reply-btn {
  color: #c65367;
}

.comment-like.liked {
  font-weight: 700;
}

.reply-form {
  display: grid;
  grid-template-columns: 1fr 70px 60px;
  gap: 8px;
  margin: 10px 0 14px;
}

.reply-form input {
  height: 38px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  padding: 0 12px;
  font: inherit;
}

.reply-form button {
  border: none;
  border-radius: 8px;
  background: #f3d7dd;
  color: #c65367;
  font-weight: 600;
  cursor: pointer;
}

.reply-form button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.reply-form .cancel-btn {
  background: #f8f2f0;
  color: #6d5f5b;
}

.replies {
  margin-top: 14px;
  padding-left: 14px;
  border-left: 2px solid #f0e5e0;
}

.reply {
  margin-top: 12px;
}

@media (max-width: 640px) {
  .reply-form {
    grid-template-columns: 1fr;
  }
}
</style>
