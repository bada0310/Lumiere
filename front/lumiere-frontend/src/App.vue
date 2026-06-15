<script setup>
import { RouterView } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
</script>

<template>
  <AppHeader />
  <RouterView />
</template>

<style scoped>
</style>

<!--
App.vue에는 페이지를 직접 넣지 않는다.
App.vue에는 공통 헤더와 RouterView만 둔다.
router/index.js에서 주소와 페이지를 연결한다.
-->