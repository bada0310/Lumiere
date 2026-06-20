<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <section
      ref="modalRef"
      class="selector-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="lounge-selector-title"
      tabindex="-1"
    >
      <header class="modal-header">
        <div>
          <h2 id="lounge-selector-title">라운지 선택</h2>
          <p>이동할 퍼스널컬러 라운지를 선택해주세요.</p>
        </div>
        <button ref="closeButtonRef" type="button" class="close-btn" @click="emit('close')">×</button>
      </header>

      <div class="season-sections">
        <section v-for="season in seasons" :key="season" class="season-section">
          <h3>{{ SEASON_LABELS[season] }}</h3>
          <div class="theme-grid">
            <button
              v-for="theme in themesBySeason(season)"
              :key="theme.key"
              type="button"
              class="theme-card"
              :class="{ selected: theme.key === selectedKey }"
              :style="{ '--theme-color': theme.color }"
              @click="emit('select', theme)"
            >
              <span class="theme-name">{{ theme.koreanName }}</span>
              <span class="theme-meta">{{ TEMPERATURE_LABELS[theme.temperature] }} · {{ TONE_LABELS[theme.tone] }}</span>
            </button>
          </div>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  LOUNGE_THEMES,
  SEASON_LABELS,
  TEMPERATURE_LABELS,
  TONE_LABELS,
} from '@/data/loungeThemes'

defineProps({
  selectedKey: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close', 'select'])

const modalRef = ref(null)
const closeButtonRef = ref(null)
const seasons = ['spring', 'summer', 'autumn', 'winter']

const themesBySeason = (season) => LOUNGE_THEMES.filter((theme) => theme.season === season)

const focusableSelector =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

const onKeydown = (event) => {
  if (event.key === 'Escape') {
    emit('close')
    return
  }

  if (event.key !== 'Tab' || !modalRef.value) return

  const focusable = [...modalRef.value.querySelectorAll(focusableSelector)].filter(
    (element) => !element.disabled,
  )
  if (!focusable.length) return

  const first = focusable[0]
  const last = focusable[focusable.length - 1]

  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

onMounted(async () => {
  document.addEventListener('keydown', onKeydown)
  await nextTick()
  closeButtonRef.value?.focus()
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1300;
  background: rgba(31, 21, 20, 0.46);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
}

.selector-modal {
  width: min(980px, 100%);
  max-height: min(82vh, 780px);
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid #eaded8;
  display: flex;
  flex-direction: column;
  outline: none;
  font-family: "Pretendard", "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
  letter-spacing: 0;
}

.modal-header {
  padding: 24px 26px 18px;
  border-bottom: 1px solid #f0e5e0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.modal-header h2 {
  font-size: 1.35rem;
  color: #2f2826;
  font-weight: 700;
}

.modal-header p {
  margin-top: 6px;
  color: #746763;
  font-size: 0.92rem;
  font-weight: 400;
}

.close-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid #eaded8;
  background: #ffffff;
  color: #6d5f5b;
  cursor: pointer;
  font-size: 1.5rem;
}

.season-sections {
  overflow-y: auto;
  padding: 22px 26px 28px;
}

.season-section + .season-section {
  margin-top: 26px;
}

.season-section h3 {
  margin-bottom: 12px;
  font-size: 1rem;
  color: #3f3633;
  font-weight: 700;
}

.theme-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.theme-card {
  min-height: 84px;
  border: 2px solid transparent;
  border-radius: 10px;
  background-color: var(--theme-color);
  background-image: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(0,0,0,0.08));
  color: #ffffff;
  padding: 15px;
  cursor: pointer;
  text-align: left;
}

.theme-card.selected {
  border-color: #2f2826;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.72) inset;
}

.theme-card:hover {
  filter: brightness(0.96);
}

.theme-name {
  display: block;
  font-weight: 700;
  margin-bottom: 8px;
}

.theme-meta {
  display: inline-flex;
  border: 1px solid rgba(255,255,255,0.28);
  background: rgba(255,255,255,0.16);
  border-radius: 999px;
  padding: 3px 8px;
  color: rgba(255,255,255,0.86);
  font-size: 0.74rem;
}

@media (max-width: 760px) {
  .modal-backdrop {
    align-items: flex-end;
    padding: 0;
  }

  .selector-modal {
    width: 100%;
    max-height: 92vh;
    border-radius: 16px 16px 0 0;
  }

  .theme-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
