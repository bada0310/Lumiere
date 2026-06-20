<template>
  <form class="comment-form" @submit.prevent="submit">
    <input
      v-model.trim="content"
      :disabled="disabled"
      :placeholder="disabled ? '로그인 후 댓글을 작성할 수 있어요.' : '댓글을 입력해주세요...'"
    />
    <button type="submit" :disabled="disabled || !content">등록</button>
  </form>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['submit'])
const content = ref('')

const submit = () => {
  if (!content.value) return
  emit('submit', content.value)
  content.value = ''
}
</script>

<style scoped>
.comment-form {
  display: grid;
  grid-template-columns: 1fr 110px;
  gap: 10px;
  margin-bottom: 20px;
}

.comment-form input {
  height: 42px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  padding: 0 14px;
  font: inherit;
}

.comment-form button {
  border: none;
  border-radius: 8px;
  background: #f3d7dd;
  color: #c65367;
  font-weight: 600;
  cursor: pointer;
}

.comment-form button:disabled,
.comment-form input:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

@media (max-width: 760px) {
  .comment-form {
    grid-template-columns: 1fr;
  }
}
</style>
