<template>
  <div class="community-subpage">
    <div class="community-subpage-grid">
      <aside class="left-sidebar">
        <ToneLounge :lounge="currentLounge" @change-lounge="goCommunity" />
      </aside>

      <main class="main-area">
        <div v-if="isLoading" class="state-card">게시글을 불러오는 중입니다.</div>
        <div v-else-if="errorMessage" class="state-card error">{{ errorMessage }}</div>
        <div v-else-if="!post" class="state-card">게시글을 찾을 수 없습니다.</div>
        <CommunityDetailContent
          v-else
          :post="post"
          :comments="comments"
          :is-logged-in="isLoggedIn"
          @back="goCommunity"
          @like="toggleLike"
          @submit-comment="submitComment"
          @like-comment="toggleCommentLike"
        />
      </main>

      <CommunityRightSidebar
        :weekly-popular-posts="weeklyPopularPosts"
        :show-recommendations="false"
        @open-board="openBoard"
        @open-post="openPost"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import CommunityDetailContent from '@/components/community/CommunityDetailContent.vue'
import CommunityRightSidebar from '@/components/community/CommunityRightSidebar.vue'
import ToneLounge from '@/components/community/ToneLounge.vue'
import { getLoungeThemeByKey } from '@/data/loungeThemes'
import { mockCommunityPosts } from '@/data/communitySidebarMock'
import {
  createComment,
  getPost,
  getPostComments,
  isAuthenticated,
  toggleCommentLikeById,
  togglePostLike,
} from '@/services/communityApi'

const route = useRoute()
const router = useRouter()

const isLoading = ref(true)
const errorMessage = ref('')
const post = ref(null)
const comments = ref([])

const isLoggedIn = computed(() => isAuthenticated())
const currentLounge = computed(() => getLoungeThemeByKey(route.query.lounge || 'summer-cool-light'))
const weeklyPopularPosts = computed(() =>
  mockCommunityPosts.slice().sort((a, b) => b.like_count - a.like_count).slice(0, 5),
)

const normalizePost = (data) => ({
  ...data,
  author: data.author_nickname || data.author_username || data.author || '익명',
  userTone: currentLounge.value.koreanName,
  time: data.time || formatDate(data.created_at),
  products: data.products || [],
  image_url: data.image_url || '',
  like_count: data.like_count ?? 0,
  comment_count: data.comment_count ?? comments.value.length,
  is_liked: data.is_liked || false,
  userAvatar: data.userAvatar || `https://i.pravatar.cc/100?u=${data.author_username || data.id}`,
})

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const fetchDetail = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const data = await getPost(route.params.id)
    post.value = normalizePost(data)
    comments.value = await getPostComments(route.params.id)
    post.value.comment_count = comments.value.length
  } catch (error) {
    const fallback = mockCommunityPosts.find((item) => String(item.id) === String(route.params.id)) || mockCommunityPosts[0]
    post.value = normalizePost(fallback)
    comments.value = [
      {
        id: 'mock-comment-1',
        author_username: 'warm_day',
        author_nickname: 'warm_day',
        content: '이 조합 정말 좋아요. 립 컬러가 분위기랑 잘 맞네요.',
        like_count: 12,
        is_liked: false,
        created_at: new Date().toISOString(),
      },
    ]
    errorMessage.value = ''
    console.error('게시글 상세 조회 실패, mock 데이터를 사용합니다:', error)
  } finally {
    isLoading.value = false
  }
}

const requireLogin = () => {
  if (isAuthenticated()) return true
  alert('로그인이 필요합니다.')
  return false
}

const toggleLike = async () => {
  if (!post.value) return
  if (!requireLogin()) return

  if (String(post.value.id).startsWith('mock-')) {
    post.value.is_liked = !post.value.is_liked
    post.value.like_count += post.value.is_liked ? 1 : -1
    return
  }

  const response = await togglePostLike(post.value.id)
  post.value.is_liked = response.is_liked
  post.value.like_count += response.is_liked ? 1 : -1
}

const submitComment = async (content) => {
  if (!post.value || !content) return
  if (!requireLogin()) return

  if (String(post.value.id).startsWith('mock-')) {
    comments.value.push({
      id: `mock-comment-${Date.now()}`,
      author_username: 'me',
      author_nickname: 'me',
      content,
      like_count: 0,
      is_liked: false,
      created_at: new Date().toISOString(),
    })
    post.value.comment_count = comments.value.length
    return
  }

  const createdComment = await createComment(post.value.id, content)
  comments.value.push(createdComment)
  post.value.comment_count = comments.value.length
}

const toggleCommentLike = async (comment) => {
  if (!requireLogin()) return

  if (String(comment.id).startsWith('mock-')) {
    comment.is_liked = !comment.is_liked
    comment.like_count = (comment.like_count || 0) + (comment.is_liked ? 1 : -1)
    return
  }

  const response = await toggleCommentLikeById(comment.id)
  comment.is_liked = response.is_liked
  comment.like_count = (comment.like_count || 0) + (comment.is_liked ? 1 : -1)
}

const goCommunity = () => {
  router.push({ name: 'community', query: { category: route.query.category || 'life-item' } })
}

const openBoard = (categoryKey) => {
  router.push({ name: 'community', query: { category: categoryKey } })
}

const openPost = (targetPost) => {
  router.push({
    name: 'community-detail',
    params: { id: targetPost.id },
    query: {
      category: route.query.category || 'life-item',
      lounge: currentLounge.value.key,
    },
  })
}

onMounted(fetchDetail)
</script>

<style scoped>
.community-subpage {
  width: 100%;
  background: #fffafb;
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

.state-card {
  background: white;
  border: 1px solid #eaded8;
  border-radius: 14px;
  padding: 34px;
  text-align: center;
}

.state-card.error {
  color: #c65367;
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
