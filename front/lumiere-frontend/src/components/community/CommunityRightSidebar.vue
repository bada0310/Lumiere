<template>
  <aside class="right-sidebar">
    <div class="right-widget">
      <h3>인기 제품 태그</h3>
      <PopularTagCloud
        :tags="popularProductTags"
        :selected-tags="selectedTags"
        :preview-limit="8"
        description="태그를 클릭하면 관련 게시글이 필터링돼요."
        @select-tag="$emit('select-tag', $event)"
        @open-tag-explorer="$emit('open-tag-explorer')"
      />
    </div>

    <div class="right-widget">
      <h3>이번 주 인기 글</h3>
      <ul class="popular-posts">
        <li
          v-for="(post, index) in weeklyPopularPosts"
          :key="post.id"
          class="clickable-post"
          tabindex="0"
          role="link"
          @click="$emit('open-post', post)"
          @keydown.enter="$emit('open-post', post)"
        >
          <span class="rank" :class="{ highlight: index < 3 }">{{ index + 1 }}</span>
          <p class="title">{{ post.title }}</p>
          <span class="likes">♥ {{ post.like_count }}</span>
        </li>
      </ul>
      <button class="widget-more" type="button" @click="$emit('open-board', 'weekly-popular-posts')">
        더 많은 인기글 보기
      </button>
    </div>

    <div class="right-widget notice-widget">
      <h3>라운지 공지사항</h3>
      <ul class="notice-list">
        <li v-for="notice in loungeNotices" :key="notice.id">
          {{ notice.title }}
          <span class="date">{{ notice.date }}</span>
        </li>
      </ul>
      <button class="text-link" type="button" @click="$emit('open-board', 'lounge-notices')">
        더보기 >
      </button>
    </div>

    <div v-if="showRecommendations" class="right-widget">
      <h3>맞춤 라운지 추천</h3>
      <ul class="recommended-lounges">
        <li v-for="lounge in recommendedLounges" :key="lounge.key" @click="$emit('select-lounge', lounge)">
          <span class="lounge-dot" :style="{ backgroundColor: lounge.color }"></span>
          <div>
            <strong>{{ lounge.koreanName }}</strong>
            <small>{{ lounge.members.toLocaleString() }}명 활동 중</small>
          </div>
        </li>
      </ul>
      <button class="text-link" type="button" @click="$emit('open-board', 'recommended-lounges')">
        더 많은 라운지 보기 >
      </button>
    </div>
  </aside>
</template>

<script setup>
import PopularTagCloud from '@/components/community/PopularTagCloud.vue'
import {
  loungeNotices,
  popularProductTags,
  recommendedLounges,
} from '@/data/communitySidebarMock'

defineProps({
  weeklyPopularPosts: {
    type: Array,
    default: () => [],
  },
  showRecommendations: {
    type: Boolean,
    default: true,
  },
  selectedTags: {
    type: Array,
    default: () => [],
  },
})

defineEmits([
  'select-lounge',
  'open-lounge-selector',
  'open-board',
  'open-post',
  'select-tag',
  'open-tag-explorer',
])
</script>

<style scoped>
.right-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: "Pretendard Variable", Pretendard, "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
}

.right-widget {
  background: #ffffff;
  border: 1px solid #f0e5e0;
  border-radius: 14px;
  padding: 18px;
}

.right-widget h3 {
  font-size: 0.98rem;
  margin: 0 0 14px 0;
  color: #3f3633;
  font-weight: 700;
}

.popular-posts,
.notice-list,
.recommended-lounges {
  display: flex;
  flex-direction: column;
  gap: 11px;
}

.recommended-lounges li {
  display: flex;
  align-items: center;
  gap: 10px;
}

.popular-posts li {
  display: grid;
  grid-template-columns: 18px 1fr auto;
  gap: 9px;
  align-items: start;
}

.clickable-post {
  cursor: pointer;
  border-radius: 8px;
}

.clickable-post:hover .title,
.clickable-post:focus .title {
  color: #c65367;
  text-decoration: underline;
}

.rank {
  color: #9d918d;
  font-weight: 700;
}

.rank.highlight {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #c65367;
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
}

.popular-posts .title {
  margin: 0;
  color: #3f3633;
  font-size: 0.82rem;
  line-height: 1.4;
}

.likes {
  color: #c65367;
  font-size: 0.74rem;
  white-space: nowrap;
}

.widget-more {
  width: 100%;
  height: 36px;
  margin-top: 14px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: white;
  color: #c65367;
  cursor: pointer;
  font-size: 0.82rem;
}

.notice-list li {
  color: #514845;
  font-size: 0.82rem;
  line-height: 1.45;
}

.date {
  display: block;
  color: #a19793;
  font-size: 0.74rem;
  margin-top: 3px;
}

.text-link {
  display: block;
  margin-left: auto;
  margin-top: 12px;
  border: none;
  background: transparent;
  color: #c65367;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
}

.recommended-lounges li {
  cursor: pointer;
}

.lounge-dot {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  flex: 0 0 34px;
}

.recommended-lounges strong {
  display: block;
  color: #3f3633;
  font-size: 0.83rem;
  font-weight: 700;
}

.recommended-lounges small {
  display: block;
  color: #8b807c;
  font-size: 0.74rem;
  margin-top: 2px;
}
</style>
