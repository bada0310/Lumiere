<template>
  <div class="skin-balance-chart">
    <svg viewBox="0 0 240 220" role="img" aria-label="피부 특성 밸런스 차트">
      <polygon
        v-for="level in gridLevels"
        :key="level"
        :points="polygonPoints(level)"
        class="grid-polygon"
      />

      <line
        v-for="axis in axisLines"
        :key="axis.key"
        :x1="center.x"
        :y1="center.y"
        :x2="axis.x"
        :y2="axis.y"
        class="axis-line"
      />

      <polygon :points="averagePoints" class="average-polygon" />
      <polygon :points="valuePoints" class="value-polygon" />

      <circle
        v-for="point in valuePointList"
        :key="point.key"
        :cx="point.x"
        :cy="point.y"
        r="2.4"
        class="value-point"
      />

      <text
        v-for="label in labelPoints"
        :key="label.key"
        :x="label.x"
        :y="label.y"
        text-anchor="middle"
        dominant-baseline="middle"
        class="axis-label"
      >
        {{ label.name }}
      </text>
    </svg>

    <div class="legend">
      <span><i class="legend-line legend-line--value"></i>나의 특성</span>
      <span><i class="legend-line legend-line--average"></i>평균</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  axes: {
    type: Array,
    default: () => [],
  },
})

const center = { x: 120, y: 102 }
const radius = 72
const labelRadius = 94
const gridLevels = [0.25, 0.5, 0.75, 1]

const clamp = (value) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.min(100, Math.max(0, number))
}

const normalizedAxes = computed(() => {
  const axes = props.axes.length ? props.axes : [{ key: 'empty', name: '-', value: 0, average: 50 }]
  return axes.map((axis) => ({
    ...axis,
    value: clamp(axis.value),
    average: clamp(axis.average ?? 50),
  }))
})

const pointAt = (index, ratio, targetRadius = radius) => {
  const count = normalizedAxes.value.length
  const angle = (Math.PI * 2 * index) / count - Math.PI / 2
  return {
    x: center.x + Math.cos(angle) * targetRadius * ratio,
    y: center.y + Math.sin(angle) * targetRadius * ratio,
  }
}

const pointsFor = (field) => {
  return normalizedAxes.value
    .map((axis, index) => {
      const point = pointAt(index, axis[field] / 100)
      return `${point.x},${point.y}`
    })
    .join(' ')
}

const polygonPoints = (level) => {
  return normalizedAxes.value
    .map((_, index) => {
      const point = pointAt(index, level)
      return `${point.x},${point.y}`
    })
    .join(' ')
}

const axisLines = computed(() =>
  normalizedAxes.value.map((axis, index) => {
    const point = pointAt(index, 1)
    return { ...axis, ...point }
  }),
)

const valuePoints = computed(() => pointsFor('value'))
const averagePoints = computed(() => pointsFor('average'))

const valuePointList = computed(() =>
  normalizedAxes.value.map((axis, index) => {
    const point = pointAt(index, axis.value / 100)
    return { ...axis, ...point }
  }),
)

const labelPoints = computed(() =>
  normalizedAxes.value.map((axis, index) => {
    const point = pointAt(index, 1, labelRadius)
    return { ...axis, ...point }
  }),
)
</script>

<style scoped>
.skin-balance-chart {
  min-height: 258px;
  display: grid;
  place-items: center;
  gap: 12px;
}

svg {
  width: min(100%, 360px);
  height: auto;
  overflow: visible;
}

.grid-polygon {
  fill: none;
  stroke: #eaded8;
  stroke-width: 1;
}

.axis-line {
  stroke: #eaded8;
  stroke-width: 1;
}

.average-polygon {
  fill: rgba(134, 139, 151, 0.08);
  stroke: #9aa1ad;
  stroke-dasharray: 4 4;
  stroke-width: 1.5;
}

.value-polygon {
  fill: rgba(198, 83, 103, 0.18);
  stroke: #c65367;
  stroke-width: 2;
}

.value-point {
  fill: #c65367;
}

.axis-label {
  fill: #3c3331;
  font-size: 11px;
  font-weight: 700;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 22px;
  color: #786b67;
  font-size: 12px;
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.legend-line {
  width: 18px;
  height: 0;
  border-top: 2px solid #c65367;
}

.legend-line--average {
  border-color: #9aa1ad;
  border-top-style: dashed;
}
</style>
