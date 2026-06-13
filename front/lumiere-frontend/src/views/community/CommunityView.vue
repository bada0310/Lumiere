<template>
  <div class="community-main-layout">
    <ToneLounge :tone="userTone" />
    
    <div class="main-feed-area">
      <CategoryBar @filter="onFilterChange" />
      <div class="feed-list">
        <PostItem v-for="post in posts" :key="post.id" :post="post" />
      </div>
    </div>
    
    <WriteButton />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import ToneLounge from '@/components/community/ToneLounge.vue';
import CategoryBar from '@/components/community/CategoryBar.vue';
import PostItem from '@/components/community/PostItem.vue';
import WriteButton from '@/components/community/WriteButton.vue';

const userTone = ref('여름 쿨 라이트');
const posts = ref([
  { id: 1, title: '여쿨라 인생템 공유해요!', category: '인생템 공유', author: 'subina', likes: 12, comments: 3, productTags: ['틴트'] },
  // ... 더미 데이터
]);

const handleFilter = (category) => { /* 필터 로직 */ };
const filteredPosts = computed(() => posts.value);
</script>