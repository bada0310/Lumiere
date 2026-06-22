<template>
  <div class="ai-makeover-gallery">
    <div v-if="showAction" class="ai-makeover-gallery__empty">
      <strong>AI 메이크오버 이미지가 아직 생성되지 않았어요.</strong>
      <p>진단 결과의 고정 팔레트를 바탕으로 스타일별 이미지를 별도로 생성합니다.</p>
      <button type="button" :disabled="loading" @click="$emit('start')">
        {{ loading ? '요청 중...' : 'AI 메이크오버 생성하기' }}
      </button>
    </div>

    <MakeoverLoadingSkeleton v-else-if="loading || isActive" :count="skeletonCount" :message="loadingMessage" />

    <div v-if="styles.length" class="ai-makeover-gallery__list">
      <article
        v-for="look in styles"
        :key="look.key"
        class="look-card"
        :class="{
          active: selectedKey === look.key,
        'look-card--failed': look.status === 'failed',
        'look-card--loading': ['queued', 'running', 'pending', 'loading'].includes(look.status),
      }"
      @click="$emit('select', look.key)"
    >
        <img v-if="look.image_url" :src="look.image_url" :alt="`${look.name} 메이크오버 이미지`" />
        <div v-else class="look-card__placeholder" aria-hidden="true">
          <span>{{ look.name }}</span>
        </div>

        <div class="look-card__copy">
          <strong>{{ look.name }}</strong>
          <small v-if="look.status" class="look-card__status">{{ statusLabel(look.status) }}</small>
          <p>{{ look.description }}</p>
        </div>

        <button v-if="look.status === 'failed'" type="button" @click="$emit('retry', look.key)">다시 생성</button>
      </article>
    </div>

    <p v-if="error" class="ai-makeover-gallery__error">{{ error }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import MakeoverLoadingSkeleton from '@/components/diagnosis/MakeoverLoadingSkeleton.vue'

const props = defineProps({
  styles: {
    type: Array,
    default: () => [],
  },
  status: {
    type: String,
    default: 'none',
  },
  selectedKey: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
})

defineEmits(['start', 'retry', 'select'])

const isActive = computed(() => ['queued', 'running', 'pending', 'loading'].includes(props.status))
const showAction = computed(() => !props.styles.length && !isActive.value && props.status !== 'complete')
const skeletonCount = computed(() => Math.min(Math.max(props.styles.length || 3, 3), 5))
const loadingMessage = computed(() =>
  props.styles.length
    ? '완성된 스타일은 순차적으로 표시됩니다.'
    : '원본 얼굴 특징은 유지하고 메이크업만 자연스럽게 적용하고 있어요.',
)

const statusLabel = (status) =>
  ({
    none: '대기',
    queued: '대기 중',
    pending: '대기 중',
    running: '생성 중',
    loading: '생성 중',
    complete: '완료',
    failed: '실패',
    skipped: '보류',
  })[status] || status
</script>

<style scoped>
.ai-makeover-gallery {
  margin-top: 22px;
}

.ai-makeover-gallery__empty {
  padding: 24px;
  border: 1px dashed #e5b5be;
  border-radius: 10px;
  background: #fffaf7;
  text-align: center;
  color: #6d625f;
}

.ai-makeover-gallery__empty strong {
  display: block;
  color: #9e4655;
}

.ai-makeover-gallery__empty p {
  margin: 8px 0 16px;
  font-size: 13px;
}

.ai-makeover-gallery__empty button,
.look-card button {
  border: 1px solid #c65367;
  border-radius: 8px;
  background: #fff;
  color: #c65367;
  padding: 8px 14px;
  font-weight: 800;
  cursor: pointer;
}

.ai-makeover-gallery__empty button:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.ai-makeover-gallery__list {
  display: grid;
  grid-template-columns: repeat(3, minmax(160px, 1fr));
  gap: 16px;
}

.look-card {
  min-width: 0;
  padding: 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: #fff;
  display: grid;
  gap: 11px;
}

.look-card.active {
  border-color: #c65367;
  background: #fffaf7;
}

.look-card--failed {
  border-color: #e1a2aa;
}

.look-card--loading {
  background: #fffaf7;
}

.look-card img,
.look-card__placeholder {
  width: 100%;
  aspect-ratio: 1.5 / 1;
  border-radius: 8px;
  object-fit: cover;
  background: linear-gradient(135deg, #fff1eb, #f1d7e0);
}

.look-card__placeholder {
  display: grid;
  place-items: center;
  color: #9e4655;
  font-weight: 900;
  text-align: center;
}

.look-card__copy {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.look-card__copy strong,
.look-card__copy p {
  min-width: 0;
  overflow-wrap: anywhere;
}

.look-card__copy strong {
  color: #3f3633;
}

.look-card__status {
  width: fit-content;
  padding: 3px 7px;
  border-radius: 999px;
  background: #fff0f1;
  color: #9e4655;
  font-size: 11px;
  font-weight: 800;
}

.look-card__copy p {
  margin: 0;
  color: #8e7e79;
  font-size: 12px;
  line-height: 1.5;
}

.ai-makeover-gallery__error {
  margin: 14px 0 0;
  color: #b44352;
  font-size: 13px;
  font-weight: 800;
}

@media (max-width: 840px) {
  .ai-makeover-gallery__list {
    grid-template-columns: 1fr;
  }
}
</style>
