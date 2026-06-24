<template>
  <ProductColorChart
    :model-value="modelValue"
    :product="product"
    :options="options"
    :user-tone-profile="userToneProfile"
    @update:model-value="$emit('update:modelValue', $event)"
    @select="$emit('select', $event)"
  />
</template>

<script setup>
import ProductColorChart from '@/components/products/ProductColorChart.vue'

defineProps({
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

defineEmits(['update:modelValue', 'select'])
</script>
