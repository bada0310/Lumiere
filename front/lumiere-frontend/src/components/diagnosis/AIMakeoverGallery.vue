<template>
  <div class="ai-makeover-gallery">
    <div v-if="showAction" class="ai-makeover-gallery__empty">
      <strong>AI 메이크오버 이미지가 아직 생성되지 않았어요.</strong>
      <p>진단 결과의 고정 팔레트를 바탕으로 스타일별 이미지를 별도로 생성합니다.</p>
      <button type="button" :disabled="loading" @click="$emit('start')">
        {{ loading ? '요청 중...' : 'AI 메이크오버 생성하기' }}
      </button>
    </div>

    <MakeoverLoadingSkeleton v-else-if="!styles.length && (loading || isActive)" :count="skeletonCount" :message="loadingMessage" />

    <div v-if="styles.length" class="ai-makeover-gallery__list">
      <article
        v-for="look in styles"
        :key="look.key"
        class="look-card"
        :class="{
          active: selectedKey === look.key,
          'look-card--failed': isLookFailed(look),
          'look-card--loading': isLookLoading(look),
        }"
      @click="$emit('select', look.key)"
    >
        <div
          class="look-card__visual"
          :class="[
            `look-card__visual--${look.key}`,
            { 'look-card__visual--guide': !hasLookImage(look) },
          ]"
        >
          <img
            v-if="hasLookImage(look)"
            :src="getLookImageUrl(look)"
            :alt="look.title || look.name || 'AI 메이크업 이미지'"
          />
          <div v-else class="makeup-model" :style="makeupStyleVars(look)" aria-hidden="true">
            <span class="makeup-model__glow"></span>
            <span class="makeup-model__hair makeup-model__hair--back"></span>
            <span class="makeup-model__neck"></span>
            <span class="makeup-model__shoulders"></span>
            <span class="makeup-model__ear makeup-model__ear--left"></span>
            <span class="makeup-model__ear makeup-model__ear--right"></span>
            <span class="makeup-model__face"></span>
            <span class="makeup-model__face-light"></span>
            <span class="makeup-model__hair makeup-model__hair--left"></span>
            <span class="makeup-model__hair makeup-model__hair--right"></span>
            <span class="makeup-model__bang makeup-model__bang--left"></span>
            <span class="makeup-model__bang makeup-model__bang--right"></span>
            <span class="makeup-model__brow makeup-model__brow--left"></span>
            <span class="makeup-model__brow makeup-model__brow--right"></span>
            <span class="makeup-model__eye-shadow makeup-model__eye-shadow--left"></span>
            <span class="makeup-model__eye-shadow makeup-model__eye-shadow--right"></span>
            <span class="makeup-model__eye makeup-model__eye--left"></span>
            <span class="makeup-model__eye makeup-model__eye--right"></span>
            <span class="makeup-model__liner makeup-model__liner--left"></span>
            <span class="makeup-model__liner makeup-model__liner--right"></span>
            <span class="makeup-model__nose"></span>
            <span class="makeup-model__blush makeup-model__blush--left"></span>
            <span class="makeup-model__blush makeup-model__blush--right"></span>
            <span class="makeup-model__lip"></span>
            <span class="makeup-model__lip-gloss"></span>
            <span class="makeup-model__swatches">
              <i class="makeup-model__swatch makeup-model__swatch--eye"></i>
              <i class="makeup-model__swatch makeup-model__swatch--blush"></i>
              <i class="makeup-model__swatch makeup-model__swatch--lip"></i>
            </span>
          </div>
          <em v-if="!hasLookImage(look)">
            {{ isLookFailed(look) ? '생성 실패' : '메이크업 프리뷰' }}
          </em>
        </div>

        <div class="look-card__copy">
          <strong>{{ look.title || look.name }}</strong>
          <small v-if="look.status || hasLookImage(look)" class="look-card__status">
            {{ statusLabel(effectiveLookStatus(look)) }}
          </small>
          <p>{{ look.description }}</p>
          <ul v-if="look.points?.length" class="look-card__points">
            <li v-for="point in look.points" :key="point">
              <span
                class="point-icon"
                :class="pointIconClass(point)"
                aria-hidden="true"
              >
                <span class="point-icon__base"></span>
                <span class="point-icon__detail"></span>
              </span>
              <span>{{ point }}</span>
            </li>
          </ul>
          <p class="look-card__disclaimer">
            {{ look.disclaimer || defaultDisclaimer }}
          </p>
        </div>

        <button v-if="isLookFailed(look)" type="button" @click="$emit('retry', look.key)">다시 생성</button>
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
  sourceImageUrl: {
    type: String,
    default: '',
  },
  makeupGuide: {
    type: Object,
    default: () => ({}),
  },
  toneKey: {
    type: String,
    default: '',
  },
})

defineEmits(['start', 'retry', 'select'])

const defaultDisclaimer = 'AI 기술로 생성된 예시 메이크업 이미지로, 실제 화장 결과와 제품 발색은 다를 수 있어요.'
const activeStatuses = ['queued', 'running', 'pending', 'loading']

const normalizeStatus = (status) => String(status || '').toLowerCase()
const getLookImageUrl = (look) => look?.image_url || look?.imageUrl || look?.image || ''
const hasLookImage = (look) => Boolean(getLookImageUrl(look))

const effectiveLookStatus = (look) => {
  if (hasLookImage(look)) return 'complete'
  return normalizeStatus(look?.status || 'none')
}

const isLookLoading = (look) => {
  if (hasLookImage(look)) return false
  return activeStatuses.includes(normalizeStatus(look?.status))
}

const isLookFailed = (look) => {
  if (hasLookImage(look)) return false
  return normalizeStatus(look?.status) === 'failed'
}

const isActive = computed(() => {
  if (props.styles.length) {
    return props.styles.some((look) => isLookLoading(look))
  }

  return activeStatuses.includes(normalizeStatus(props.status))
})
const showAction = computed(() => !props.styles.length && !isActive.value && !['complete', 'partial'].includes(normalizeStatus(props.status)))
const skeletonCount = computed(() => Math.min(Math.max(props.styles.length || 3, 3), 3))
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
    partial: '일부 완료',
    failed: '실패',
    skipped: '보류',
  })[status] || status

const pointIconClass = (point) => {
  const text = String(point || '').toLowerCase()

  if (text.includes('아이라인') || text.includes('라이너') || text.includes('eyeline') || text.includes('liner')) {
    return 'point-icon--liner'
  }

  if (text.includes('블러셔') || text.includes('블러쉬') || text.includes('blush')) {
    return 'point-icon--blush'
  }

  if (text.includes('립') || text.includes('mlbb') || text.includes('lip')) {
    return 'point-icon--lip'
  }

  if (text.includes('섀도우') || text.includes('쉐도우') || text.includes('shadow') || text.includes('브라운') || text.includes('핑크 코랄')) {
    return 'point-icon--shadow'
  }

  return 'point-icon--swatch'
}
const styleSettings = {
  daily: {
    lipGroups: ['lip'],
    blushGroups: ['blush'],
    eyeGroups: ['base', 'shading'],
    lipDepth: 0.18,
    linerAlpha: 0.42,
    shadowAlpha: 0.36,
    blushAlpha: 0.42,
    lipAlpha: 0.68,
    bgAlpha: 0.18,
  },
  lovely: {
    lipGroups: ['lip'],
    blushGroups: ['blush'],
    eyeGroups: ['point', 'base', 'aegyosal'],
    lipDepth: 0.28,
    linerAlpha: 0.46,
    shadowAlpha: 0.5,
    blushAlpha: 0.6,
    lipAlpha: 0.84,
    bgAlpha: 0.24,
  },
  natural_daily: {
    lipGroups: ['lip'],
    blushGroups: ['blush'],
    eyeGroups: ['base', 'shading'],
    lipDepth: 0.18,
    linerAlpha: 0.42,
    shadowAlpha: 0.36,
    blushAlpha: 0.42,
    lipAlpha: 0.68,
    bgAlpha: 0.18,
  },
  pure_daily: {
    lipGroups: ['lip'],
    blushGroups: ['blush'],
    eyeGroups: ['highlighter', 'aegyosal', 'base'],
    lipDepth: 0.12,
    linerAlpha: 0.28,
    shadowAlpha: 0.28,
    blushAlpha: 0.36,
    lipAlpha: 0.62,
    bgAlpha: 0.2,
  },
  romantic: {
    lipGroups: ['lip'],
    blushGroups: ['blush'],
    eyeGroups: ['point', 'base', 'shading'],
    lipDepth: 0.28,
    linerAlpha: 0.5,
    shadowAlpha: 0.48,
    blushAlpha: 0.56,
    lipAlpha: 0.82,
    bgAlpha: 0.24,
  },
  chic: {
    lipGroups: ['lip'],
    blushGroups: ['blush'],
    eyeGroups: ['shading', 'eyeliner', 'point'],
    lipDepth: 0.38,
    linerAlpha: 0.72,
    shadowAlpha: 0.54,
    blushAlpha: 0.32,
    lipAlpha: 0.78,
    bgAlpha: 0.16,
  },
  smoky: {
    lipGroups: ['lip'],
    blushGroups: ['blush'],
    eyeGroups: ['eyeliner', 'shading', 'point'],
    lipDepth: 0.48,
    linerAlpha: 0.82,
    shadowAlpha: 0.72,
    blushAlpha: 0.28,
    lipAlpha: 0.82,
    bgAlpha: 0.14,
  },
}

const toneFallbacks = [
  {
    tests: ['summer', 'cool'],
    bgA: '#EAF7F8',
    bgB: '#F6EAF4',
    eye: '#B39AC8',
    liner: '#504050',
    blush: '#E89CB6',
    lip: '#D9638B',
  },
  {
    tests: ['winter', 'cool'],
    bgA: '#EAF0F8',
    bgB: '#F4E8F5',
    eye: '#837092',
    liner: '#25212B',
    blush: '#D583A5',
    lip: '#C74778',
  },
  {
    tests: ['spring', 'warm'],
    bgA: '#FFF4DF',
    bgB: '#FFE7E6',
    eye: '#D9A46E',
    liner: '#6F4A37',
    blush: '#F3A179',
    lip: '#E66F61',
  },
  {
    tests: ['autumn', 'warm'],
    bgA: '#F7E8D3',
    bgB: '#EFDCD4',
    eye: '#A87955',
    liner: '#4C3329',
    blush: '#D48768',
    lip: '#B75B48',
  },
]

const defaultFallback = {
  bgA: '#F8EEF0',
  bgB: '#EEF5F7',
  eye: '#B895A7',
  liner: '#4C3B3E',
  blush: '#E397A8',
  lip: '#D96684',
}

const asColorArray = (value) => (Array.isArray(value) ? value : [])

const normalizeHex = (value) => {
  const raw = String(value || '').trim()
  if (/^#[0-9a-f]{3}$/i.test(raw)) {
    return `#${raw
      .slice(1)
      .split('')
      .map((char) => char + char)
      .join('')}`.toUpperCase()
  }
  if (/^#[0-9a-f]{6}$/i.test(raw)) return raw.toUpperCase()
  return ''
}

const hexToRgb = (hex) => {
  const normalized = normalizeHex(hex)
  if (!normalized) return [214, 110, 132]
  const value = Number.parseInt(normalized.slice(1), 16)
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255]
}

const rgbString = (hex) => hexToRgb(hex).join(', ')

const mixHex = (hex, targetHex, amount = 0.3) => {
  const source = hexToRgb(hex)
  const target = hexToRgb(targetHex)
  const mixed = source.map((channel, index) => Math.round(channel + (target[index] - channel) * amount))
  return `#${mixed.map((channel) => channel.toString(16).padStart(2, '0')).join('')}`.toUpperCase()
}

const getFallbackPalette = () => {
  const normalizedToneKey = String(props.toneKey || '').toLowerCase().replace(/-/g, '_')
  return toneFallbacks.find((palette) => palette.tests.every((test) => normalizedToneKey.includes(test))) || defaultFallback
}

const getChipHex = (items, fallback, preferredIndex = 0) => {
  const chips = asColorArray(items)
    .map((item) => normalizeHex(typeof item === 'string' ? item : item?.hex))
    .filter(Boolean)
  return chips[preferredIndex] || chips[0] || fallback
}

const getEyeHex = (guide, setting, fallback) => {
  const eyeGuide = guide?.eye || {}
  const colors = setting.eyeGroups.flatMap((group) => asColorArray(eyeGuide[group]))
  return getChipHex(colors, fallback)
}

const makeupStyleVars = (look) => {
  const fallback = getFallbackPalette()
  const setting = styleSettings[look?.key] || styleSettings.natural_daily
  const guide = props.makeupGuide || {}
  const isLovely = ['lovely', 'romantic'].includes(look?.key)
  const lip = getChipHex(guide?.lip?.chips, fallback.lip, isLovely ? 1 : 0)
  const blush = getChipHex(guide?.blush?.chips, fallback.blush, isLovely ? 1 : 0)
  const eye = getEyeHex(guide, setting, fallback.eye)
  const liner = getChipHex(guide?.eye?.eyeliner, fallback.liner)
  const lipDeep = mixHex(lip, '#4B2230', setting.lipDepth)
  const eyeDeep = mixHex(eye, liner, look?.key === 'smoky' ? 0.55 : 0.25)

  return {
    '--model-bg-a': fallback.bgA,
    '--model-bg-b': fallback.bgB,
    '--model-accent-rgb': rgbString(lip),
    '--model-bg-alpha': setting.bgAlpha,
    '--makeup-eye-rgb': rgbString(eyeDeep),
    '--makeup-liner': liner,
    '--makeup-blush-rgb': rgbString(blush),
    '--makeup-lip': lip,
    '--makeup-lip-deep': lipDeep,
    '--makeup-shadow-alpha': setting.shadowAlpha,
    '--makeup-liner-alpha': setting.linerAlpha,
    '--makeup-blush-alpha': setting.blushAlpha,
    '--makeup-lip-alpha': setting.lipAlpha,
  }
}
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
  padding: 24px 26px 22px;
  border: 1px solid #f0ded8;
  border-radius: 18px;
  background: #fffaf8;
  display: grid;
  gap: 18px;
  box-shadow: 0 10px 24px rgba(88, 55, 45, 0.04);
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

.look-card__visual,
.look-card__placeholder {
  width: 100%;
  aspect-ratio: 4 / 5;
  border-radius: 13px;
  background:
    radial-gradient(circle at 50% 36%, rgba(255, 255, 255, 0.82) 0 11%, transparent 12%),
    radial-gradient(ellipse at 50% 56%, rgba(120, 75, 78, 0.28) 0 22%, transparent 23%),
    linear-gradient(135deg, #fff1eb, #f1d7e0);
  overflow: hidden;
}

.look-card__visual {
  position: relative;
}

.look-card__visual img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.makeup-model {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background:
    radial-gradient(circle at 72% 18%, rgba(var(--model-accent-rgb), var(--model-bg-alpha)) 0 16%, transparent 32%),
    radial-gradient(circle at 28% 30%, rgba(255, 255, 255, 0.88) 0 10%, transparent 28%),
    linear-gradient(135deg, var(--model-bg-a), var(--model-bg-b));
  isolation: isolate;
}

.makeup-model span,
.makeup-model i {
  position: absolute;
  display: block;
}

.makeup-model__glow {
  inset: 8% 18% 0;
  border-radius: 999px;
  background: radial-gradient(ellipse at 50% 28%, rgba(255, 255, 255, 0.78) 0 18%, rgba(255, 255, 255, 0.18) 42%, transparent 68%);
  filter: blur(8px);
  z-index: 0;
}

.makeup-model__hair {
  background:
    radial-gradient(circle at 28% 18%, rgba(255, 255, 255, 0.12), transparent 18%),
    linear-gradient(120deg, #1d1b1e 0%, #372b2c 48%, #151416 100%);
  box-shadow: inset -10px -8px 18px rgba(0, 0, 0, 0.28);
}

.makeup-model__hair--back {
  left: 29%;
  top: 7%;
  width: 42%;
  height: 82%;
  border-radius: 45% 45% 36% 36%;
  z-index: 1;
}

.makeup-model__neck {
  left: 44%;
  top: 64%;
  width: 12%;
  height: 22%;
  border-radius: 0 0 44% 44%;
  background: linear-gradient(90deg, #e8bea8, #f7d4c3 48%, #dca58f);
  z-index: 2;
}

.makeup-model__shoulders {
  left: 25%;
  top: 78%;
  width: 50%;
  height: 28%;
  border-radius: 48% 48% 0 0;
  background: linear-gradient(135deg, rgba(42, 38, 42, 0.9), rgba(83, 72, 75, 0.8));
  z-index: 1;
}

.makeup-model__ear {
  top: 38%;
  width: 6%;
  height: 13%;
  border-radius: 50%;
  background: linear-gradient(135deg, #e7b8a2, #f5cdbc);
  z-index: 2;
}

.makeup-model__ear--left {
  left: 32.5%;
}

.makeup-model__ear--right {
  right: 32.5%;
}

.makeup-model__face {
  left: 35%;
  top: 15%;
  width: 30%;
  height: 61%;
  border-radius: 46% 46% 48% 48% / 38% 38% 56% 56%;
  background:
    radial-gradient(circle at 38% 39%, rgba(255, 255, 255, 0.38) 0 5%, transparent 16%),
    radial-gradient(circle at 61% 39%, rgba(255, 255, 255, 0.32) 0 5%, transparent 16%),
    linear-gradient(100deg, #e4b49f 0%, #f8d6c6 44%, #f0c0ad 100%);
  box-shadow:
    inset 10px -8px 16px rgba(139, 83, 72, 0.16),
    inset -8px -10px 16px rgba(139, 83, 72, 0.13),
    0 12px 22px rgba(89, 57, 55, 0.16);
  z-index: 3;
}

.makeup-model__face-light {
  left: 43%;
  top: 24%;
  width: 14%;
  height: 32%;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.3), transparent);
  filter: blur(4px);
  z-index: 4;
}

.makeup-model__hair--left {
  left: 29%;
  top: 14%;
  width: 15%;
  height: 69%;
  border-radius: 70% 18% 30% 45%;
  z-index: 5;
}

.makeup-model__hair--right {
  right: 29%;
  top: 14%;
  width: 15%;
  height: 69%;
  border-radius: 18% 70% 45% 30%;
  z-index: 5;
}

.makeup-model__bang {
  top: 9%;
  height: 28%;
  background: linear-gradient(135deg, #211d20, #4a3937);
  z-index: 6;
}

.makeup-model__bang--left {
  left: 34%;
  width: 18%;
  border-radius: 90% 18% 65% 24%;
  transform: rotate(10deg);
}

.makeup-model__bang--right {
  left: 48%;
  width: 18%;
  border-radius: 18% 90% 24% 65%;
  transform: rotate(-8deg);
}

.makeup-model__brow {
  top: 35.5%;
  width: 8%;
  height: 1.8%;
  border-radius: 999px;
  background: rgba(42, 30, 31, 0.68);
  z-index: 7;
}

.makeup-model__brow--left {
  left: 40%;
  transform: rotate(-7deg);
}

.makeup-model__brow--right {
  right: 40%;
  transform: rotate(7deg);
}

.makeup-model__eye-shadow {
  top: 38%;
  width: 9.5%;
  height: 5.4%;
  border-radius: 999px 999px 70% 70%;
  background: radial-gradient(ellipse at 50% 60%, rgba(var(--makeup-eye-rgb), var(--makeup-shadow-alpha)) 0 36%, transparent 72%);
  filter: blur(2.4px);
  mix-blend-mode: multiply;
  z-index: 7;
}

.makeup-model__eye-shadow--left {
  left: 39.1%;
  transform: rotate(3deg);
}

.makeup-model__eye-shadow--right {
  right: 39.1%;
  transform: rotate(-3deg);
}

.makeup-model__eye {
  top: 41%;
  width: 6.6%;
  height: 2.6%;
  border-radius: 999px;
  background:
    radial-gradient(circle at 50% 50%, #2f2525 0 28%, transparent 31%),
    linear-gradient(#fff, #f2e6e4);
  box-shadow: 0 1px 1px rgba(80, 38, 38, 0.16);
  z-index: 8;
}

.makeup-model__eye--left {
  left: 40.2%;
}

.makeup-model__eye--right {
  right: 40.2%;
}

.makeup-model__liner {
  top: 40.3%;
  width: 7.6%;
  height: 1.4%;
  border-radius: 999px;
  background: var(--makeup-liner);
  opacity: var(--makeup-liner-alpha);
  z-index: 9;
}

.makeup-model__liner--left {
  left: 39.7%;
  transform: rotate(3deg);
}

.makeup-model__liner--right {
  right: 39.7%;
  transform: rotate(-3deg);
}

.makeup-model__nose {
  left: 49%;
  top: 43%;
  width: 2.2%;
  height: 13%;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(137, 77, 68, 0.14), rgba(137, 77, 68, 0.26));
  filter: blur(0.8px);
  z-index: 7;
}

.makeup-model__blush {
  top: 50%;
  width: 10%;
  height: 7.5%;
  border-radius: 50%;
  background: radial-gradient(ellipse, rgba(var(--makeup-blush-rgb), var(--makeup-blush-alpha)) 0 30%, transparent 74%);
  filter: blur(5px);
  mix-blend-mode: multiply;
  z-index: 7;
}

.makeup-model__blush--left {
  left: 38.2%;
  transform: rotate(-8deg);
}

.makeup-model__blush--right {
  right: 38.2%;
  transform: rotate(8deg);
}

.makeup-model__lip {
  left: 45.2%;
  top: 61%;
  width: 9.6%;
  height: 4.2%;
  border-radius: 48% 48% 56% 56%;
  background:
    radial-gradient(ellipse at 50% 24%, rgba(255, 255, 255, 0.24) 0 15%, transparent 28%),
    linear-gradient(180deg, var(--makeup-lip), var(--makeup-lip-deep));
  opacity: var(--makeup-lip-alpha);
  filter: blur(0.3px);
  mix-blend-mode: multiply;
  z-index: 8;
}

.makeup-model__lip-gloss {
  left: 48%;
  top: 62.1%;
  width: 4%;
  height: 0.8%;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.28);
  filter: blur(0.5px);
  z-index: 9;
}

.makeup-model__swatches {
  right: 12px;
  bottom: 12px;
  z-index: 10;
  display: flex;
  gap: 5px;
  padding: 5px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.74);
  box-shadow: 0 6px 18px rgba(78, 47, 50, 0.12);
}

.makeup-model__swatch {
  width: 13px;
  height: 13px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.84);
  box-shadow: inset 0 -2px 4px rgba(0, 0, 0, 0.12);
}

.makeup-model__swatch--eye {
  background: rgb(var(--makeup-eye-rgb));
}

.makeup-model__swatch--blush {
  background: rgb(var(--makeup-blush-rgb));
}

.makeup-model__swatch--lip {
  background: var(--makeup-lip);
}

.look-card__visual--preview::after {
  position: absolute;
  inset: 0;
  content: '';
  pointer-events: none;
  mix-blend-mode: soft-light;
  opacity: 0.18;
}

.look-card__visual--preview em,
.look-card__visual--guide em {
  position: absolute;
  left: 10px;
  bottom: 10px;
  z-index: 12;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: #8b3a4a;
  font-size: 11px;
  font-style: normal;
  font-weight: 900;
}

.look-card__visual--preview.look-card__visual--natural_daily img {
  filter: brightness(1.02) contrast(0.99) saturate(1.02);
}

.look-card__visual--preview.look-card__visual--natural_daily::after {
  background: linear-gradient(135deg, rgba(244, 214, 186, 0.36), rgba(255, 247, 236, 0.38));
}

.look-card__visual--preview.look-card__visual--pure_daily img {
  filter: brightness(1.04) contrast(0.97) saturate(0.96) hue-rotate(-3deg);
}

.look-card__visual--preview.look-card__visual--pure_daily::after {
  background: linear-gradient(135deg, rgba(227, 217, 245, 0.42), rgba(213, 233, 250, 0.42));
}

.look-card__visual--preview.look-card__visual--romantic img {
  filter: brightness(1.03) contrast(0.99) saturate(1.04) hue-rotate(-5deg);
}

.look-card__visual--preview.look-card__visual--romantic::after {
  background: linear-gradient(135deg, rgba(255, 200, 218, 0.52), rgba(244, 164, 190, 0.34));
}

.look-card__visual--preview.look-card__visual--chic img {
  filter: brightness(0.98) contrast(1.06) saturate(0.94) grayscale(0.04);
}

.look-card__visual--preview.look-card__visual--chic::after {
  background: linear-gradient(135deg, rgba(222, 218, 216, 0.42), rgba(166, 154, 162, 0.32));
}

.look-card__visual--preview.look-card__visual--smoky img {
  filter: brightness(0.94) contrast(1.11) saturate(0.9);
}

.look-card__visual--preview.look-card__visual--smoky::after {
  background: linear-gradient(135deg, rgba(126, 117, 134, 0.48), rgba(62, 56, 70, 0.36));
}

.makeup-preview {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  opacity: var(--makeup-opacity, 0.9);
}

.makeup-preview span {
  position: absolute;
  display: block;
}

.makeup-preview__eye {
  top: var(--eye-top, 39%);
  width: var(--eye-width, 15%);
  height: var(--eye-height, 5.2%);
  border-radius: 999px 999px 64% 64%;
  background:
    radial-gradient(ellipse at 50% 70%, var(--eye-point, transparent) 0 30%, transparent 64%),
    linear-gradient(90deg, transparent 0 5%, var(--eye-shadow, rgba(142, 94, 86, 0.32)) 24% 76%, transparent 95%);
  filter: blur(var(--eye-blur, 3.2px));
  mix-blend-mode: multiply;
}

.makeup-preview__eye--left {
  left: var(--eye-left-x, 31%);
  transform: rotate(var(--eye-left-rotate, 2deg));
}

.makeup-preview__eye--right {
  left: var(--eye-right-x, 54%);
  transform: rotate(var(--eye-right-rotate, -2deg));
}

.makeup-preview__liner {
  top: var(--liner-top, 42%);
  width: var(--liner-width, 13%);
  height: 2px;
  border-radius: 999px;
  background: var(--liner-color, rgba(74, 47, 45, 0.42));
  box-shadow: 0 1px 4px rgba(60, 35, 36, 0.18);
  opacity: var(--liner-opacity, 0.5);
}

.makeup-preview__liner--left {
  left: var(--liner-left-x, 32%);
  transform: rotate(var(--liner-left-rotate, 4deg));
}

.makeup-preview__liner--right {
  left: var(--liner-right-x, 55%);
  transform: rotate(var(--liner-right-rotate, -4deg));
}

.makeup-preview__blush {
  top: var(--blush-top, 54%);
  width: var(--blush-width, 13%);
  height: var(--blush-height, 8%);
  border-radius: 50%;
  background: radial-gradient(ellipse, var(--blush-color, rgba(222, 116, 112, 0.34)) 0 28%, transparent 72%);
  filter: blur(var(--blush-blur, 7px));
  mix-blend-mode: multiply;
  opacity: var(--blush-opacity, 0.82);
}

.makeup-preview__blush--left {
  left: var(--blush-left-x, 32%);
  transform: rotate(-9deg);
}

.makeup-preview__blush--right {
  left: var(--blush-right-x, 56%);
  transform: rotate(9deg);
}

.makeup-preview__lip {
  top: var(--lip-top, 68%);
  left: var(--lip-left, 43.6%);
  width: var(--lip-width, 13%);
  height: var(--lip-height, 4.8%);
  border-radius: 48% 48% 56% 56%;
  background:
    radial-gradient(ellipse at 50% 28%, rgba(255, 255, 255, 0.22) 0 13%, transparent 27%),
    linear-gradient(180deg, var(--lip-top-color, rgba(195, 90, 91, 0.48)), var(--lip-bottom-color, rgba(148, 56, 67, 0.55)));
  filter: blur(var(--lip-blur, 1.1px));
  mix-blend-mode: multiply;
  opacity: var(--lip-opacity, 0.74);
}

.makeup-preview__gloss {
  top: calc(var(--lip-top, 68%) + 1.1%);
  left: calc(var(--lip-left, 43.6%) + 3.8%);
  width: calc(var(--lip-width, 13%) * 0.42);
  height: 1.3%;
  border-radius: 999px;
  background: rgba(255, 255, 255, var(--gloss-opacity, 0.18));
  filter: blur(1px);
}

.look-card__visual--natural_daily {
  --makeup-opacity: 0.86;
  --eye-shadow: rgba(168, 116, 96, 0.3);
  --eye-point: rgba(216, 156, 130, 0.2);
  --liner-color: rgba(98, 62, 53, 0.32);
  --liner-opacity: 0.38;
  --blush-color: rgba(223, 127, 103, 0.34);
  --blush-opacity: 0.72;
  --lip-top-color: rgba(199, 103, 88, 0.44);
  --lip-bottom-color: rgba(157, 72, 72, 0.5);
  --lip-opacity: 0.62;
}

.look-card__visual--pure_daily {
  --makeup-opacity: 0.9;
  --eye-shadow: rgba(171, 133, 177, 0.28);
  --eye-point: rgba(229, 188, 206, 0.3);
  --liner-color: rgba(91, 66, 85, 0.26);
  --liner-opacity: 0.3;
  --blush-color: rgba(232, 137, 166, 0.34);
  --blush-opacity: 0.7;
  --lip-top-color: rgba(216, 112, 136, 0.45);
  --lip-bottom-color: rgba(177, 79, 111, 0.5);
  --lip-opacity: 0.62;
  --gloss-opacity: 0.28;
}

.look-card__visual--romantic {
  --makeup-opacity: 0.94;
  --eye-shadow: rgba(186, 96, 126, 0.38);
  --eye-point: rgba(239, 155, 184, 0.36);
  --liner-color: rgba(114, 54, 72, 0.42);
  --liner-opacity: 0.48;
  --blush-color: rgba(233, 95, 136, 0.48);
  --blush-width: 15%;
  --blush-height: 9%;
  --blush-opacity: 0.88;
  --lip-top-color: rgba(210, 76, 111, 0.58);
  --lip-bottom-color: rgba(160, 54, 91, 0.66);
  --lip-opacity: 0.76;
  --gloss-opacity: 0.24;
}

.look-card__visual--chic {
  --makeup-opacity: 0.92;
  --eye-shadow: rgba(92, 70, 72, 0.42);
  --eye-point: rgba(161, 117, 120, 0.18);
  --eye-height: 5.7%;
  --liner-color: rgba(36, 30, 31, 0.62);
  --liner-opacity: 0.72;
  --liner-width: 14.5%;
  --blush-color: rgba(169, 91, 91, 0.28);
  --blush-opacity: 0.58;
  --lip-top-color: rgba(150, 67, 72, 0.56);
  --lip-bottom-color: rgba(95, 42, 51, 0.68);
  --lip-opacity: 0.72;
}

.look-card__visual--smoky {
  --makeup-opacity: 0.96;
  --eye-shadow: rgba(54, 45, 58, 0.68);
  --eye-point: rgba(116, 89, 118, 0.4);
  --eye-width: 17%;
  --eye-height: 7.4%;
  --eye-blur: 4.4px;
  --liner-color: rgba(23, 20, 26, 0.78);
  --liner-opacity: 0.82;
  --liner-width: 15.5%;
  --blush-color: rgba(124, 75, 89, 0.22);
  --blush-opacity: 0.48;
  --lip-top-color: rgba(119, 57, 75, 0.6);
  --lip-bottom-color: rgba(72, 37, 52, 0.76);
  --lip-opacity: 0.78;
  --gloss-opacity: 0.12;
}

.look-card__placeholder {
  display: grid;
  place-items: center;
  color: #9e4655;
  font-weight: 900;
  text-align: center;
}

.look-card__placeholder--natural_daily {
  background:
    radial-gradient(circle at 50% 36%, rgba(255, 255, 255, 0.82) 0 11%, transparent 12%),
    radial-gradient(ellipse at 50% 56%, rgba(120, 75, 78, 0.22) 0 22%, transparent 23%),
    linear-gradient(135deg, #f7e5d7, #f9f2e9);
}

.look-card__placeholder--pure_daily {
  background:
    radial-gradient(circle at 50% 36%, rgba(255, 255, 255, 0.84) 0 11%, transparent 12%),
    radial-gradient(ellipse at 50% 56%, rgba(116, 92, 128, 0.2) 0 22%, transparent 23%),
    linear-gradient(135deg, #f2e7f5, #e7f1fb);
}

.look-card__placeholder--romantic {
  background:
    radial-gradient(circle at 50% 36%, rgba(255, 255, 255, 0.84) 0 11%, transparent 12%),
    radial-gradient(ellipse at 50% 56%, rgba(154, 74, 104, 0.24) 0 22%, transparent 23%),
    linear-gradient(135deg, #ffe6ee, #f5d6e1);
}

.look-card__placeholder--chic {
  background:
    radial-gradient(circle at 50% 36%, rgba(255, 255, 255, 0.82) 0 11%, transparent 12%),
    radial-gradient(ellipse at 50% 56%, rgba(64, 57, 65, 0.26) 0 22%, transparent 23%),
    linear-gradient(135deg, #e9e4e2, #d4d0d4);
}

.look-card__placeholder--smoky {
  background:
    radial-gradient(circle at 50% 36%, rgba(255, 255, 255, 0.78) 0 11%, transparent 12%),
    radial-gradient(ellipse at 50% 56%, rgba(51, 45, 58, 0.34) 0 22%, transparent 23%),
    linear-gradient(135deg, #ddd3da, #9f9aa8);
}

.look-card__copy {
  min-width: 0;
  display: grid;
  gap: 7px;
}

.look-card__copy strong,
.look-card__copy > p:not(.look-card__disclaimer) {
  margin: 0;
  color: #3f3633;
  font-size: 16px;
  line-height: 1.75;
  font-weight: 500;
  text-align: center;
  word-break: keep-all;
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

.look-card__points {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.look-card__points li {
  min-width: 0;
  display: grid;
  justify-items: center;
  gap: 10px;
  color: #4d4441;
  font-size: 13px;
  font-weight: 700;
  text-align: center;
  line-height: 1.4;
  word-break: keep-all;
}

.point-icon {
  position: relative;
  width: 58px;
  height: 58px;
  border-radius: 999px;
  background: #f9efec;
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.85),
    0 8px 18px rgba(94, 61, 55, 0.1);
  overflow: hidden;
}

.point-icon__base,
.point-icon__detail {
  position: absolute;
  display: block;
}

.point-icon--shadow {
  background:
    radial-gradient(circle at 32% 34%, #d8a082 0 12%, transparent 13%),
    radial-gradient(circle at 66% 34%, #c47f68 0 12%, transparent 13%),
    radial-gradient(circle at 32% 68%, #b86c55 0 12%, transparent 13%),
    radial-gradient(circle at 66% 68%, #e0b49d 0 12%, transparent 13%),
    #f7e5dd;
}

.point-icon--shadow .point-icon__base {
  inset: 9px;
  border-radius: 999px;
  border: 1px solid rgba(126, 76, 63, 0.16);
}

.point-icon--liner {
  background: #f8efed;
}

.point-icon--liner .point-icon__base {
  left: 27px;
  top: 10px;
  width: 5px;
  height: 38px;
  border-radius: 999px;
  background: linear-gradient(180deg, #1f1c1d, #4b4141);
  transform: rotate(42deg);
}

.point-icon--liner .point-icon__detail {
  left: 16px;
  top: 37px;
  width: 22px;
  height: 3px;
  border-radius: 999px;
  background: #1f1c1d;
  transform: rotate(-28deg);
}

.point-icon--blush {
  background:
    radial-gradient(circle at 45% 40%, rgba(255, 255, 255, 0.55) 0 12%, transparent 22%),
    radial-gradient(circle at 50% 50%, #ef8f9c 0 42%, #d9667b 72%, #c65367 100%);
}

.point-icon--blush .point-icon__base {
  inset: 8px;
  border-radius: 999px;
  background: radial-gradient(circle at 38% 32%, rgba(255, 255, 255, 0.45), transparent 32%);
}

.point-icon--lip {
  background: #f9eeec;
}

.point-icon--lip .point-icon__base {
  left: 12px;
  top: 24px;
  width: 34px;
  height: 15px;
  border-radius: 50% 50% 58% 58%;
  background:
    radial-gradient(ellipse at 50% 24%, rgba(255, 255, 255, 0.28) 0 14%, transparent 28%),
    linear-gradient(180deg, #d95e6d, #a83f4a);
  transform: rotate(2deg);
}

.point-icon--lip .point-icon__detail {
  left: 17px;
  top: 29px;
  width: 24px;
  height: 1px;
  background: rgba(118, 39, 47, 0.42);
}

.point-icon--swatch {
  background:
    radial-gradient(circle at 35% 30%, rgba(255, 255, 255, 0.9), transparent 28%),
    linear-gradient(135deg, #f4c0bd, #d86b82);
}


.look-card__disclaimer {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #f1e4de;
  color: #9b8d88 !important;
  font-size: 11px !important;
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
