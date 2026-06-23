<template>
  <div class="product-color-chart">
    <svg viewBox="0 0 100 100" role="img" :aria-label="`${product?.name || 'Product'} color options`">
      <defs>
        <filter id="selectedShadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="0" dy="1.5" stdDeviation="1.8" flood-color="#2d2524" flood-opacity="0.24" />
        </filter>
      </defs>

      <rect x="0" y="0" width="100" height="100" rx="3" class="plot-bg" />
      <line x1="6" y1="50" x2="94" y2="50" class="axis" />
      <line x1="50" y1="6" x2="50" y2="94" class="axis" />

      <ellipse
        v-if="goodEllipse"
        :cx="goodEllipse.cx"
        :cy="goodEllipse.cy"
        :rx="goodEllipse.rx"
        :ry="goodEllipse.ry"
        class="range range-good"
      />
      <ellipse
        v-if="bestEllipse"
        :cx="bestEllipse.cx"
        :cy="bestEllipse.cy"
        :rx="bestEllipse.rx"
        :ry="bestEllipse.ry"
        class="range range-best"
      />

      <text x="4" y="53" class="axis-label">Warm</text>
      <text x="83" y="53" class="axis-label">Cool</text>
      <text x="52" y="8" class="axis-label">Light</text>
      <text x="52" y="96" class="axis-label">Deep</text>

      <g
        v-for="point in chartPoints"
        :key="point.id"
        class="point-group"
        :class="{ selected: point.isSelected }"
        :filter="point.isSelected ? 'url(#selectedShadow)' : null"
        @click="selectOption(point.option)"
      >
        <circle
          v-if="point.grade === 'CAUTION'"
          :cx="point.x"
          :cy="point.y"
          r="5.6"
          class="caution-ring"
        />
        <circle
          :cx="point.x"
          :cy="point.y"
          :r="point.isSelected ? 3.8 : 3.2"
          :fill="point.color"
          class="dot"
          :class="point.grade.toLowerCase()"
        />
        <text
          :x="point.labelX"
          :y="point.labelY"
          class="point-label"
          :class="{ selected: point.isSelected }"
        >
          {{ point.label }}
        </text>
        <g v-if="point.grade === 'BEST'" :transform="`translate(${point.badgeX}, ${point.badgeY})`">
          <rect x="-6.8" y="-4.7" width="13.6" height="6.8" rx="2" class="best-badge-bg" />
          <text x="0" y="0.3" text-anchor="middle" class="best-badge-text">BEST</text>
        </g>
      </g>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  product: {
    type: Object,
    default: () => ({}),
  },
  options: {
    type: Array,
    default: () => [],
  },
  userToneProfile: {
    type: Object,
    default: () => ({}),
  },
  modelValue: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'select'])

const selectedId = computed(() => String(props.modelValue?.id || props.options[0]?.id || ''))
const rangeProfile = computed(() => {
  return props.userToneProfile?.range_profile || props.userToneProfile?.rangeProfile || {}
})

const bestEllipse = computed(() => rangeToEllipse(rangeProfile.value.best))
const goodEllipse = computed(() => rangeToEllipse(rangeProfile.value.good))

const chartPoints = computed(() => {
  return props.options.map((option, index) => {
    const x = clamp(option.coolness)
    const y = clamp(100 - clamp(option.brightness))
    const grade = gradeFor(option)
    const isSelected = String(option.id) === selectedId.value
    const label = String(option.option_no || option.option_name || index + 1).slice(0, 12)
    return {
      id: option.id || `${index}`,
      option,
      x,
      y,
      label,
      labelX: Math.min(94, Math.max(6, x + 3.8)),
      labelY: Math.min(96, Math.max(5, y - 3.4)),
      badgeX: Math.min(91, Math.max(9, x + 8)),
      badgeY: Math.min(95, Math.max(7, y - 7)),
      color: option.hex_code || option.hexCode || option.hex || '#c65367',
      grade,
      isSelected,
    }
  })
})

const selectOption = (option) => {
  emit('update:modelValue', option)
  emit('select', option)
}

const gradeFor = (option) => {
  const score = Number(option.match_score ?? option.matchScore ?? option.score ?? 0)
  if (String(option.grade || '').toUpperCase()) {
    return String(option.grade).toUpperCase()
  }
  if (score >= 85) return 'BEST'
  if (score >= 70) return 'GOOD'
  if (score >= 55) return 'OK'
  return 'CAUTION'
}

const rangeToEllipse = (range) => {
  if (!range?.coolness || !range?.brightness) return null
  const [coolMin, coolMax] = range.coolness.map(clamp)
  const [brightMin, brightMax] = range.brightness.map(clamp)
  const yMin = clamp(100 - brightMax)
  const yMax = clamp(100 - brightMin)
  return {
    cx: (coolMin + coolMax) / 2,
    cy: (yMin + yMax) / 2,
    rx: Math.max(4, (coolMax - coolMin) / 2),
    ry: Math.max(4, (yMax - yMin) / 2),
  }
}

const clamp = (value) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.min(100, Math.max(0, Math.round(number)))
}
</script>

<style scoped>
.product-color-chart {
  width: 100%;
  aspect-ratio: 16 / 10;
  min-height: 320px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: #fffaf7;
  overflow: hidden;
}

svg {
  width: 100%;
  height: 100%;
  display: block;
}

.plot-bg {
  fill: #fffaf7;
}

.axis {
  stroke: rgba(94, 74, 70, 0.2);
  stroke-width: 0.35;
}

.axis-label {
  fill: #8e7e79;
  font-size: 3px;
  font-weight: 800;
}

.range {
  pointer-events: none;
}

.range-good {
  fill: rgba(145, 190, 63, 0.14);
  stroke: rgba(145, 190, 63, 0.42);
  stroke-width: 0.5;
}

.range-best {
  fill: rgba(198, 83, 103, 0.14);
  stroke: rgba(198, 83, 103, 0.45);
  stroke-width: 0.55;
}

.point-group {
  cursor: pointer;
}

.dot {
  stroke: rgba(255, 255, 255, 0.95);
  stroke-width: 0.85;
}

.dot.best {
  stroke: #c65367;
  stroke-width: 1.2;
}

.dot.good {
  stroke: #7aa52e;
}

.dot.caution {
  stroke: #d6a400;
}

.caution-ring {
  fill: rgba(255, 205, 66, 0.2);
  stroke: rgba(214, 164, 0, 0.6);
  stroke-width: 0.6;
}

.point-label {
  fill: #2d2524;
  font-size: 2.8px;
  font-weight: 800;
  paint-order: stroke;
  stroke: rgba(255, 250, 247, 0.92);
  stroke-width: 1.6px;
}

.point-label.selected {
  fill: #c65367;
}

.best-badge-bg {
  fill: #c65367;
}

.best-badge-text {
  fill: white;
  font-size: 2px;
  font-weight: 900;
}
</style>
