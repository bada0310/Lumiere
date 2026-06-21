<template>
  <div class="community-subpage">
    <div class="community-subpage-grid">
      <aside class="left-sidebar">
        <ToneLounge
          :lounge="currentLounge"
          :recent-count="recentCount"
          @change-lounge="goCommunity"
          @select-menu="openSidebarMenu"
        />
      </aside>

      <main class="main-area">
        <CommunityPostForm
          :initial-category="initialCategory"
          :error-message="errorMessage"
          @back="goCommunity"
          @submit="submitPost"
        />
      </main>

      <CommunityRightSidebar
        :weekly-popular-posts="weeklyPopularPosts"
        :show-recommendations="false"
        @open-board="openBoard"
        @open-post="openPost"
        @select-tag="openTagFilter"
        @open-tag-explorer="openTagExplorer"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import CommunityPostForm from '@/components/community/CommunityPostForm.vue'
import CommunityRightSidebar from '@/components/community/CommunityRightSidebar.vue'
import ToneLounge from '@/components/community/ToneLounge.vue'
import { useRequireLogin } from '@/composables/useRequireLogin'
import { DEFAULT_COMMUNITY_CATEGORY, getCommunityCategoryByKey } from '@/data/communityCategories'
import { getLoungeThemeByKey } from '@/data/loungeThemes'
import { mockCommunityPosts } from '@/data/communitySidebarMock'
import { createPost } from '@/services/communityApi'
import { normalizeTagDisplayName } from '@/utils/communityTags'

const route = useRoute()
const router = useRouter()
const { requireLogin, handleAuthFailure } = useRequireLogin()
const errorMessage = ref('')

const initialCategory = computed(() => {
  const category = getCommunityCategoryByKey(String(route.query.category || DEFAULT_COMMUNITY_CATEGORY))
  return category.boardType === 'post-category' ? category.key : DEFAULT_COMMUNITY_CATEGORY
})
const currentLounge = computed(() => getLoungeThemeByKey(route.query.lounge || 'summer-cool-light'))
const recentCount = computed(() => {
  try {
    const parsed = JSON.parse(localStorage.getItem('community_recent_post_ids') || '[]')
    return Array.isArray(parsed) ? Math.min(parsed.length, 10) : 0
  } catch {
    return 0
  }
})
const weeklyPopularPosts = computed(() =>
  mockCommunityPosts.slice().sort((a, b) => b.like_count - a.like_count).slice(0, 5),
)

const submitPost = async (payload) => {
  errorMessage.value = ''

  if (
    !requireLogin({
      message: '게시글 작성은 로그인 후 이용할 수 있어요.',
      redirect: router.resolve({ name: 'community-create', query: route.query }).fullPath,
    })
  ) {
    return
  }

  try {
    const createdPost = await createPost({
      title: payload.title,
      content: payload.content,
      category: payload.category || getCommunityCategoryByKey(initialCategory.value).apiValue,
      image_url: payload.image_url,
      product_ids: payload.product_ids,
    })

    router.push({
      name: 'community-detail',
      params: { id: createdPost.id },
      query: { category: initialCategory.value, lounge: currentLounge.value.key },
    })
  } catch (error) {
    console.error('게시글 등록 실패:', error.response?.data || error)
    if (handleAuthFailure(error)) return
    errorMessage.value = '게시글 등록에 실패했습니다. 입력값을 확인해주세요.'
  }
}

const goCommunity = () => {
  router.push({ name: 'community', query: { category: initialCategory.value } })
}

const openBoard = (categoryKey) => {
  if (categoryKey === 'popular-product-tags') {
    openTagExplorer()
    return
  }

  router.push({ name: 'community', query: { category: categoryKey } })
}

const openTagExplorer = () => {
  router.push({
    name: 'community',
    query: {
      category: initialCategory.value,
      mode: 'tags',
    },
  })
}

const openTagFilter = (tag) => {
  const tagName = normalizeTagDisplayName(tag?.name || tag)
  router.push({
    name: 'community',
    query: {
      category: initialCategory.value,
      tag: tagName.replace(/^#/, ''),
    },
  })
}

const openSidebarMenu = (menuKey) => {
  router.push({
    name: 'community',
    query: {
      category: initialCategory.value,
      view: menuKey,
    },
  })
}

const openPost = (post) => {
  router.push({
    name: 'community-detail',
    params: { id: post.id },
    query: {
      category: initialCategory.value,
      lounge: currentLounge.value.key,
    },
  })
}
</script>

<style scoped>
.community-subpage {
  width: 100%;
  background: #fdf8f6;
  font-family: "Pretendard Variable", Pretendard, "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
}

.community-subpage-grid {
  width: min(1180px, calc(100vw - 40px));
  margin: 0 auto;
  padding: 34px 0 92px;
  display: grid;
  grid-template-columns: 220px minmax(560px, 1fr) 230px;
  gap: 24px;
  align-items: start;
}

.left-sidebar {
  position: sticky;
  top: 96px;
}

.main-area {
  min-width: 0;
}

@media (max-width: 1120px) {
  .community-subpage-grid {
    grid-template-columns: 220px minmax(0, 1fr);
  }

  :deep(.right-sidebar) {
    grid-column: 2;
  }
}

@media (max-width: 860px) {
  .community-subpage-grid {
    width: min(100% - 28px, 680px);
    grid-template-columns: 1fr;
  }

  .left-sidebar {
    position: static;
  }

  :deep(.right-sidebar) {
    grid-column: auto;
  }
}
</style>
