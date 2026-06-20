<template>
  <div class="tag-grid">
    <label>
      제품 태그 <span>(선택)</span>
      <input :value="productIdsText" placeholder="제품 ID를 쉼표로 입력해주세요" @input="updateProductIds" />
    </label>
    <label>
      해시태그 <span>(선택)</span>
      <input :value="hashTags" placeholder="#해시태그를 입력해주세요" @input="$emit('update:hashTags', $event.target.value)" />
    </label>
  </div>
</template>

<script setup>
defineProps({
  productIdsText: {
    type: String,
    default: '',
  },
  hashTags: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:productIdsText', 'update:hashTags'])

const updateProductIds = (event) => {
  emit('update:productIdsText', event.target.value)
}
</script>

<style scoped>
.tag-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px;
}

label {
  display: block;
  color: #2f2826;
  font-weight: 600;
  margin-top: 18px;
}

label span {
  color: #9d918d;
  font-weight: 400;
}

input {
  width: 100%;
  height: 42px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  margin-top: 9px;
  padding: 0 14px;
  font: inherit;
}

@media (max-width: 760px) {
  .tag-grid {
    grid-template-columns: 1fr;
  }
}
</style>
