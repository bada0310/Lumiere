<template>
  <div class="color-chip-list" :class="{ 'color-chip-list--compact': compact }" role="list" :aria-label="label">
    <div
      v-for="color in normalizedColors"
      :key="`${color.name}-${color.hex}`"
      class="color-chip-list__item"
      role="listitem"
      :title="color.description || `${color.name} ${color.hex}`"
      :aria-label="`${color.name} ${color.hex}`"
    >
      <span class="color-chip-list__swatch" :style="{ backgroundColor: color.hex }"></span>
      <span class="color-chip-list__copy">
        <strong>{{ color.name }}</strong>
        <small v-if="showHex">{{ color.hex }}</small>
      </span>
    </div>

    <p v-if="!normalizedColors.length && emptyText" class="color-chip-list__empty">{{ emptyText }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  colors: {
    type: Array,
    default: () => [],
  },
  label: {
    type: String,
    default: '컬러칩',
  },
  compact: {
    type: Boolean,
    default: false,
  },
  showHex: {
    type: Boolean,
    default: false,
  },
  emptyText: {
    type: String,
    default: '',
  },
})

const normalizedColors = computed(() =>
  props.colors
    .filter(Boolean)
    .map((color, index) => ({
      name: color.nameKo || color.name || `컬러 ${index + 1}`,
      hex: color.hex || '#E7D8D7',
      description: color.description || color.reason || '',
    })),
)
</script>

<style scoped>
.color-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.color-chip-list__item {
  min-width: 0;
  max-width: 172px;
  min-height: 40px;
  padding: 7px 10px 7px 8px;
  border: 1px solid #eee3df;
  border-radius: 999px;
  background: #fffaf7;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.color-chip-list__swatch {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.08);
  flex: 0 0 auto;
}

.color-chip-list__copy {
  min-width: 0;
  display: grid;
  gap: 1px;
}

.color-chip-list__copy strong,
.color-chip-list__copy small {
  min-width: 0;
  overflow-wrap: anywhere;
}

.color-chip-list__copy strong {
  color: #534845;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.25;
}

.color-chip-list__copy small {
  color: #8e7e79;
  font-size: 10px;
}

.color-chip-list--compact .color-chip-list__item {
  max-width: 142px;
  min-height: 36px;
  padding: 6px 9px 6px 7px;
}

.color-chip-list--compact .color-chip-list__swatch {
  width: 21px;
  height: 21px;
}

.color-chip-list__empty {
  margin: 0;
  color: #8e7e79;
  font-size: 12px;
}
</style>
