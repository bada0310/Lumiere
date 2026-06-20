<template>
  <form class="create-card" @submit.prevent="submit">
    <button type="button" class="back-btn" @click="$emit('back')">← 목록으로 돌아가기</button>

    <header>
      <h1>새로운 게시글 작성</h1>
      <p>나의 경험과 정보를 공유해보세요!</p>
    </header>

    <CommunityPostCategorySelector v-model="form.category" />

    <label>
      제목
      <input v-model.trim="form.title" maxlength="100" placeholder="제목을 입력해주세요 (최대 100자)" required />
      <small>{{ form.title.length }} / 100</small>
    </label>

    <label>
      내용
      <div class="toolbar">
        <button type="button">B</button>
        <button type="button"><em>I</em></button>
        <button type="button"><u>U</u></button>
        <button type="button">S</button>
        <span></span>
        <button type="button">•</button>
        <button type="button">1.</button>
        <button type="button">“”</button>
        <button type="button">↗</button>
        <button type="button">☺</button>
      </div>
      <textarea v-model.trim="form.content" placeholder="내용을 입력해주세요" required></textarea>
    </label>

    <CommunityImageUploader v-model="previewImages" />

    <ProductTagSelector
      v-model:product-ids-text="productIdsText"
      v-model:hash-tags="hashTagText"
    />

    <section class="visibility">
      <h2>공개 설정</h2>
      <div class="radio-row">
        <label>
          <input v-model="visibility" type="radio" value="public" />
          <span>전체 공개</span>
          <small>모든 이용자가 게시글을 볼 수 있어요.</small>
        </label>
        <label>
          <input v-model="visibility" type="radio" value="lounge" />
          <span>라운지 멤버만</span>
          <small>라운지 멤버에게만 보여요.</small>
        </label>
        <label>
          <input v-model="visibility" type="radio" value="private" />
          <span>비공개</span>
          <small>나만 볼 수 있는 게시글이에요.</small>
        </label>
      </div>
    </section>

    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <footer>
      <button type="button" class="draft-btn">임시 저장</button>
      <button type="submit" class="submit-btn">게시글 등록</button>
    </footer>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import CommunityImageUploader from '@/components/community/CommunityImageUploader.vue'
import CommunityPostCategorySelector from '@/components/community/CommunityPostCategorySelector.vue'
import ProductTagSelector from '@/components/community/ProductTagSelector.vue'
import { DEFAULT_COMMUNITY_CATEGORY, getCommunityCategoryByKey } from '@/data/communityCategories'

const props = defineProps({
  initialCategory: {
    type: String,
    default: 'life-item',
  },
  errorMessage: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['back', 'submit'])
const initialPostCategory = getCommunityCategoryByKey(props.initialCategory)
const safeInitialCategory =
  initialPostCategory.boardType === 'post-category'
    ? initialPostCategory
    : getCommunityCategoryByKey(DEFAULT_COMMUNITY_CATEGORY)

const form = reactive({
  title: '',
  content: '',
  category: safeInitialCategory.apiValue,
  image_url: '',
})
const productIdsText = ref('')
const hashTagText = ref('')
const visibility = ref('public')
const previewImages = ref([
  'https://images.unsplash.com/photo-1631214540242-3cd8c4f8bbdd?w=120&q=80',
  'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=120&q=80',
  'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=120&q=80',
])

const submit = () => {
  const product_ids = productIdsText.value
    .split(',')
    .map((value) => Number(value.trim()))
    .filter((value) => Number.isInteger(value) && value > 0)

  emit('submit', {
    ...form,
    image_url: previewImages.value[0] || '',
    product_ids,
    visibility: visibility.value,
    hashtags: hashTagText.value,
  })
}
</script>

<style scoped>
.create-card {
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
  margin-bottom: 10px;
}

header {
  text-align: center;
  margin-bottom: 28px;
}

header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #171312;
}

header p {
  margin-top: 8px;
  color: #5f5754;
}

label {
  display: block;
  color: #2f2826;
  font-weight: 600;
  margin-top: 18px;
}

input,
textarea {
  width: 100%;
  border: 1px solid #eaded8;
  border-radius: 8px;
  margin-top: 9px;
  padding: 0 14px;
  font: inherit;
}

input {
  height: 42px;
}

textarea {
  min-height: 130px;
  padding: 14px;
  resize: vertical;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

label small {
  display: block;
  text-align: right;
  color: #9d918d;
  margin-top: 6px;
  font-weight: 400;
}

.toolbar {
  height: 40px;
  border: 1px solid #eaded8;
  border-bottom: none;
  border-radius: 8px 8px 0 0;
  margin-top: 9px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 10px;
}

.toolbar button {
  border: none;
  background: transparent;
  width: 30px;
  height: 28px;
  cursor: pointer;
  font: inherit;
}

.toolbar span {
  width: 1px;
  height: 20px;
  background: #eaded8;
}

.visibility {
  margin-top: 22px;
}

.visibility h2 {
  font-size: 0.95rem;
  font-weight: 600;
}

.radio-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border: 1px solid #eaded8;
  border-radius: 10px;
  padding: 16px;
  gap: 18px;
}

.radio-row label {
  margin: 0;
  display: grid;
  grid-template-columns: 18px 1fr;
  gap: 4px 8px;
}

.radio-row small {
  grid-column: 2;
  color: #8b807c;
  font-weight: 400;
}

.error-message {
  margin-top: 16px;
  color: #c65367;
}

footer {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
  margin-top: 26px;
}

footer button {
  height: 46px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.draft-btn {
  border: 1px solid #e0a8b5;
  background: white;
  color: #c65367;
}

.submit-btn {
  border: none;
  background: #c65367;
  color: white;
}

@media (max-width: 760px) {
  .radio-row,
  footer {
    grid-template-columns: 1fr;
  }
}
</style>
