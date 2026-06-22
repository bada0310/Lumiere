<template>
  <article class="style-guide-card">
    <div class="style-guide-card__head">
      <span class="style-guide-card__icon" aria-hidden="true">{{ icon }}</span>
      <div>
        <h3>{{ title }}</h3>
        <p v-if="description">{{ description }}</p>
      </div>
    </div>

    <ColorChipList v-if="colors.length" :colors="colors" :label="`${title} 컬러`" compact />

    <ul v-if="items.length" class="style-guide-card__list">
      <li v-for="item in items" :key="itemKey(item)">
        <strong>{{ itemName(item) }}</strong>
        <small v-if="itemDescription(item)">{{ itemDescription(item) }}</small>
      </li>
    </ul>

    <p v-if="!colors.length && !items.length" class="style-guide-card__empty">추천 데이터가 아직 없어요.</p>
  </article>
</template>

<script setup>
import ColorChipList from '@/components/diagnosis/ColorChipList.vue'

defineProps({
  icon: {
    type: String,
    default: '✦',
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: '',
  },
  colors: {
    type: Array,
    default: () => [],
  },
  items: {
    type: Array,
    default: () => [],
  },
})

const itemName = (item) => (typeof item === 'string' ? item : item?.name || item?.title || item?.description || '')
const itemDescription = (item) => (typeof item === 'string' ? '' : item?.description || item?.tone || item?.material || '')
const itemKey = (item) => `${itemName(item)}-${itemDescription(item)}`
</script>

<style scoped>
.style-guide-card {
  min-height: 148px;
  padding: 16px;
  border: 1px solid #eaded8;
  border-radius: 10px;
  background: #fff;
  display: grid;
  align-content: start;
  gap: 14px;
}

.style-guide-card__head {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 12px;
  align-items: start;
}

.style-guide-card__icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f6e5ec;
  color: #9d4b61;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  font-weight: 900;
}

.style-guide-card h3 {
  margin: 0;
  color: #9e4655;
  font-size: 15px;
}

.style-guide-card__head p {
  margin: 4px 0 0;
  color: #7d706c;
  font-size: 12px;
  line-height: 1.45;
}

.style-guide-card__list {
  margin: 0;
  padding-left: 18px;
  color: #6d625f;
  font-size: 12px;
  line-height: 1.65;
}

.style-guide-card__list li {
  margin-bottom: 6px;
}

.style-guide-card__list strong,
.style-guide-card__list small {
  display: block;
}

.style-guide-card__list small {
  color: #8e7e79;
}

.style-guide-card__empty {
  margin: 0;
  color: #8e7e79;
  font-size: 12px;
}
</style>
