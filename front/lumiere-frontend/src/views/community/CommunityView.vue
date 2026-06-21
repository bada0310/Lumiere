<template>
  <div class="community-page">
    <section class="community-hero">
      <h1>톤 커뮤니티 <span>✨</span></h1>
      <p>
        내 퍼스널컬러에 맞는 사람들과 함께 정보를 나누고<br />
        나에게 어울리는 조합을 찾아보세요.
      </p>
    </section>

    <div class="community-container">
      <aside class="left-sidebar">
        <ToneLounge
          :lounge="currentLounge"
          :active-menu="activeMenu"
          :recent-count="recentPostIds.length"
          @change-lounge="openLoungeSelector"
          @select-menu="selectSidebarMenu"
        />
      </aside>

      <main class="main-feed-area">
        <FullTagExplorer
          v-if="tagExploreMode"
          :tags="popularProductTags"
          :initial-selected-tags="appliedTagFilters"
          @back="closeTagExplorer"
          @apply="applyTagExplorerSelection"
        />

        <template v-else>
          <CategoryBar
            v-model="activeCategoryKey"
            :total-count="boardCount"
            :sort="filters.sortBy"
            @filter="onFilterChange"
            @search="onSearch"
          />

          <SelectedTagBar
            :tags="appliedTagFilters"
            @remove="removeTagFilter"
            @clear="clearTagFilters"
            @explore="openTagExplorer"
          />

          <section class="feed-panel">
            <div v-if="isLoading" class="state-box">게시글을 불러오는 중입니다.</div>
            <div v-else-if="errorMessage" class="state-box error">{{ errorMessage }}</div>

            <div v-else-if="activeCategory.boardType === 'notices'" class="special-board">
              <article v-for="notice in loungeNotices" :key="notice.id" class="special-card">
                <strong>{{ notice.title }}</strong>
                <span>{{ notice.date }}</span>
                <p>라운지 운영과 커뮤니티 이용에 필요한 공지사항입니다.</p>
              </article>
            </div>

            <div v-else-if="activeCategory.boardType === 'recommended-lounges'" class="special-board">
              <button
                v-for="lounge in recommendedLounges"
                :key="lounge.key"
                type="button"
                class="lounge-board-card"
                @click="selectLounge(lounge)"
              >
                <span class="lounge-color" :style="{ backgroundColor: lounge.color }"></span>
                <strong>{{ lounge.koreanName }}</strong>
                <small>{{ lounge.members.toLocaleString() }}명 활동 중</small>
              </button>
            </div>

            <div v-else-if="paginatedPosts.length === 0" class="empty-state">
              <strong>{{ emptyStateTitle }}</strong>
              <p>{{ emptyStateDescription }}</p>
              <div class="empty-actions">
                <button v-if="appliedTagFilters.length" type="button" @click="clearTagFilters">
                  필터 초기화
                </button>
                <button v-if="appliedTagFilters.length" type="button" @click="openTagExplorer">
                  전체 태그 다시 탐색
                </button>
                <button v-if="canWriteInActiveCategory" type="button" @click="openCreatePage">글쓰기</button>
              </div>
            </div>

            <div v-else class="feed-list">
              <PostItem
                v-for="post in paginatedPosts"
                :key="post.id"
                :post="post"
                @like="toggleLike"
                @edit="editPost"
                @delete="deletePost"
              />
            </div>

            <div v-if="totalPages > 1 && !isSpecialStaticBoard" class="pagination">
              <button type="button" :disabled="currentPage === 1" @click="currentPage -= 1">이전</button>
              <button
                v-for="page in totalPages"
                :key="page"
                type="button"
                :class="{ active: page === currentPage }"
                @click="currentPage = page"
              >
                {{ page }}
              </button>
              <button type="button" :disabled="currentPage === totalPages" @click="currentPage += 1">다음</button>
            </div>
          </section>
        </template>
      </main>

      <CommunityRightSidebar
        :weekly-popular-posts="weeklyPopularPosts"
        :selected-tags="appliedTagFilters"
        @select-lounge="selectLounge"
        @open-board="openBoard"
        @open-post="openPost"
        @select-tag="toggleSidebarTag"
        @open-tag-explorer="openTagExplorer"
      />

      <WriteButton v-if="canWriteInActiveCategory && !tagExploreMode" @write="openCreatePage" />
    </div>

    <LoungeSelectorModal
      v-if="isLoungeSelectorOpen"
      :selected-key="currentLounge.key"
      @close="closeLoungeSelector"
      @select="selectLounge"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import CategoryBar from '@/components/community/CategoryBar.vue'
import CommunityRightSidebar from '@/components/community/CommunityRightSidebar.vue'
import FullTagExplorer from '@/components/community/FullTagExplorer.vue'
import LoungeSelectorModal from '@/components/community/LoungeSelectorModal.vue'
import PostItem from '@/components/community/PostItem.vue'
import SelectedTagBar from '@/components/community/SelectedTagBar.vue'
import ToneLounge from '@/components/community/ToneLounge.vue'
import WriteButton from '@/components/community/WriteButton.vue'
import { useRequireLogin } from '@/composables/useRequireLogin'
import {
  DEFAULT_COMMUNITY_CATEGORY,
  getCommunityCategoryByKey,
} from '@/data/communityCategories'
import {
  getLoungeThemeByKey,
  getLoungeThemeFromPersonalColor,
} from '@/data/loungeThemes'
import {
  loungeNotices,
  mockCommunityPosts,
  popularProductTags,
  recommendedLounges,
} from '@/data/communitySidebarMock'
import {
  deletePostById,
  getCurrentUserId,
  getPosts,
  togglePostLike,
  updatePost,
} from '@/services/communityApi'
import {
  dedupeTagNames,
  getTagSearchKey,
  matchesPostByTags,
  normalizeTagDisplayName,
  parseQueryTags,
  serializeTagsForQuery,
} from '@/utils/communityTags'

const PAGE_SIZE = 5

const route = useRoute()
const router = useRouter()
const { requireLogin, handleAuthFailure } = useRequireLogin()

const userPersonalColor = ref({
  season: 'summer',
  temperature: 'cool',
  tone: 'light',
})

const activeCategoryKey = ref(
  getCommunityCategoryByKey(route.query.category || DEFAULT_COMMUNITY_CATEGORY).key,
)
const filters = reactive({
  q: '',
  sortBy: 'latest',
})
const posts = ref([])
const isLoading = ref(false)
const errorMessage = ref('')
const currentPage = ref(1)
const isLoungeSelectorOpen = ref(false)
const activeMenu = ref(String(route.query.view || 'all'))
const recentPostIds = ref([])

const defaultLounge = computed(() => getLoungeThemeFromPersonalColor(userPersonalColor.value))
const currentLounge = computed(() =>
  route.params.loungeKey ? getLoungeThemeByKey(route.params.loungeKey) : defaultLounge.value,
)
const activeCategory = computed(() => getCommunityCategoryByKey(activeCategoryKey.value))
const canWriteInActiveCategory = computed(() => activeCategory.value.boardType === 'post-category')
const currentUserId = computed(() => getCurrentUserId())
const isSpecialStaticBoard = computed(() =>
  ['notices', 'recommended-lounges'].includes(activeCategory.value.boardType),
)
const tagExploreMode = computed(() => route.query.mode === 'tags')
const singleTagFilter = computed(() => parseQueryTags(route.query.tag))
const multiTagFilters = computed(() => parseQueryTags(route.query.tags))
const appliedTagFilters = computed(() =>
  dedupeTagNames([...singleTagFilter.value, ...multiTagFilters.value]),
)
const emptyStateTitle = computed(() =>
  appliedTagFilters.value.length
    ? '선택한 태그가 포함된 게시글이 아직 없어요.'
    : '아직 등록된 게시글이 없습니다.',
)
const emptyStateDescription = computed(() =>
  appliedTagFilters.value.length
    ? '다른 인기 태그를 선택해보세요.'
    : '첫 번째 글을 작성해보세요.',
)

const normalizePost = (post) => ({
  ...post,
  id: post.id,
  category: post.category || 'LIFE_ITEM',
  author: post.author_nickname || post.author_username || post.author || '익명',
  userTone: currentLounge.value.koreanName,
  time: post.time || formatDate(post.created_at),
  products: post.products || [],
  image_url: post.image_url || '',
  like_count: post.like_count ?? 0,
  comment_count: post.comment_count ?? 0,
  is_liked: post.is_liked || false,
  canEdit: currentUserId.value && post.author_id === currentUserId.value,
  userAvatar: post.author_profile_image_url || post.userAvatar || null,
})

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const filteredPosts = computed(() => {
  const keyword = filters.q.toLowerCase()
  const tagFilters = appliedTagFilters.value
  const boardType = activeCategory.value.boardType
  let pool =
    boardType === 'post-category'
      ? posts.value.filter((post) => post.category === activeCategory.value.apiValue)
      : boardType === 'popular-posts'
        ? posts.value
        : boardType === 'popular-tags'
          ? posts.value.filter((post) => post.products?.length)
          : []

  if (activeMenu.value === 'liked') {
    pool = posts.value.filter((post) => post.is_liked)
  }

  if (activeMenu.value === 'recent') {
    pool = recentPostIds.value
      .map((postId) => posts.value.find((post) => String(post.id) === String(postId)))
      .filter(Boolean)
  }

  const fallbackPool =
    activeMenu.value === 'all' && boardType === 'popular-tags' && pool.length === 0
      ? posts.value
      : pool

  return fallbackPool.filter((post) => {
    const matchesKeyword =
      !keyword ||
      post.title.toLowerCase().includes(keyword) ||
      post.content.toLowerCase().includes(keyword)

    return matchesKeyword && matchesPostByTags(post, tagFilters, 'or')
  })
})

const sortedPosts = computed(() => {
  const copied = [...filteredPosts.value]
  if (filters.sortBy === 'popular' || activeCategory.value.boardType === 'popular-posts') {
    return copied.sort((a, b) => b.like_count - a.like_count)
  }
  return copied
})

const boardCount = computed(() => {
  if (activeCategory.value.boardType === 'notices') return loungeNotices.length
  if (activeCategory.value.boardType === 'recommended-lounges') return recommendedLounges.length
  return filteredPosts.value.length
})
const totalPages = computed(() => Math.max(1, Math.ceil(sortedPosts.value.length / PAGE_SIZE)))
const paginatedPosts = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return sortedPosts.value.slice(start, start + PAGE_SIZE)
})
const weeklyPopularPosts = computed(() =>
  [...posts.value].sort((a, b) => b.like_count - a.like_count).slice(0, 5),
)

const cleanQuery = (query) => {
  const nextQuery = { ...query }
  Object.keys(nextQuery).forEach((key) => {
    if (nextQuery[key] === undefined || nextQuery[key] === null || nextQuery[key] === '') {
      delete nextQuery[key]
    }
  })
  return nextQuery
}

const replaceCommunityQuery = (updates = {}, method = 'replace') => {
  router[method]({
    name: route.name || 'community',
    params: route.params,
    query: cleanQuery({
      ...route.query,
      ...updates,
    }),
  })
}

const syncRoute = () => {
  replaceCommunityQuery({
    category: activeCategoryKey.value,
    view: activeMenu.value,
  })
}

const loadRecentPostIds = () => {
  try {
    const parsed = JSON.parse(localStorage.getItem('community_recent_post_ids') || '[]')
    recentPostIds.value = Array.isArray(parsed) ? parsed.slice(0, 10) : []
  } catch {
    recentPostIds.value = []
  }
}

const fetchPosts = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const apiPosts = (await getPosts()).map(normalizePost)
    posts.value = apiPosts.length ? apiPosts : mockCommunityPosts.map(normalizePost)
  } catch (error) {
    console.error('커뮤니티 게시글 조회 실패, mock 데이터를 사용합니다:', error)
    posts.value = mockCommunityPosts.map(normalizePost)
    errorMessage.value = ''
  } finally {
    isLoading.value = false
  }
}

const onFilterChange = (filterData) => {
  activeCategoryKey.value = filterData.category
  activeMenu.value = 'all'
  filters.sortBy = filterData.sortBy
  currentPage.value = 1
  syncRoute()
}

const onSearch = (keyword) => {
  filters.q = keyword.trim()
  currentPage.value = 1
}

const openLoungeSelector = () => {
  isLoungeSelectorOpen.value = true
}

const closeLoungeSelector = () => {
  isLoungeSelectorOpen.value = false
}

const selectLounge = (lounge) => {
  isLoungeSelectorOpen.value = false
  router.push({
    name: 'community-lounge',
    params: { loungeKey: lounge.key },
    query: { category: activeCategoryKey.value },
  })
}

const openBoard = (categoryKey) => {
  if (categoryKey === 'popular-product-tags') {
    openTagExplorer()
    return
  }

  activeCategoryKey.value = getCommunityCategoryByKey(categoryKey).key
  activeMenu.value = 'all'
  currentPage.value = 1
  replaceCommunityQuery({
    category: activeCategoryKey.value,
    view: activeMenu.value,
    mode: undefined,
  })
}

const openTagExplorer = () => {
  currentPage.value = 1
  replaceCommunityQuery({ mode: 'tags' }, 'push')
}

const closeTagExplorer = () => {
  replaceCommunityQuery({ mode: undefined })
}

const toggleSidebarTag = (tag) => {
  const tagName = normalizeTagDisplayName(tag?.name || tag)
  if (!tagName) return

  const tagKey = getTagSearchKey(tagName)
  const isOnlyActiveTag =
    appliedTagFilters.value.length === 1 && getTagSearchKey(appliedTagFilters.value[0]) === tagKey

  currentPage.value = 1
  replaceCommunityQuery({
    tag: isOnlyActiveTag ? undefined : tagName.replace(/^#/, ''),
    tags: undefined,
    mode: undefined,
  })
}

const applyTagExplorerSelection = (tags) => {
  currentPage.value = 1
  const serializedTags = serializeTagsForQuery(tags)
  replaceCommunityQuery({
    tag: undefined,
    tags: serializedTags || undefined,
    mode: undefined,
  })
}

const removeTagFilter = (tag) => {
  const targetKey = getTagSearchKey(tag)
  const nextSingleTags = singleTagFilter.value.filter((item) => getTagSearchKey(item) !== targetKey)
  const nextMultiTags = multiTagFilters.value.filter((item) => getTagSearchKey(item) !== targetKey)

  currentPage.value = 1
  replaceCommunityQuery({
    tag: nextSingleTags[0] ? nextSingleTags[0].replace(/^#/, '') : undefined,
    tags: serializeTagsForQuery(nextMultiTags) || undefined,
  })
}

const clearTagFilters = () => {
  currentPage.value = 1
  replaceCommunityQuery({
    tag: undefined,
    tags: undefined,
  })
}

const selectSidebarMenu = (menuKey) => {
  activeMenu.value = menuKey
  if (activeCategory.value.boardType !== 'post-category') {
    activeCategoryKey.value = DEFAULT_COMMUNITY_CATEGORY
  }
  if (menuKey === 'recent') {
    loadRecentPostIds()
  }
  currentPage.value = 1
  replaceCommunityQuery({
    category: activeCategoryKey.value,
    view: activeMenu.value,
    mode: undefined,
  })
}

const openPost = (post) => {
  router.push({
    name: 'community-detail',
    params: { id: post.id },
    query: {
      category: activeCategoryKey.value,
      lounge: currentLounge.value.key,
    },
  })
}

const toggleLike = async (post) => {
  if (!requireLogin({ message: '좋아요는 로그인 후 이용할 수 있어요.' })) return

  if (String(post.id).startsWith('mock-')) {
    post.is_liked = !post.is_liked
    post.like_count += post.is_liked ? 1 : -1
    return
  }

  try {
    const response = await togglePostLike(post.id)
    post.is_liked = response.is_liked
    post.like_count += response.is_liked ? 1 : -1
  } catch (error) {
    console.error('좋아요 처리 실패:', error)
    if (handleAuthFailure(error)) return
    alert('좋아요 처리에 실패했습니다.')
  }
}

const openCreatePage = () => {
  if (!canWriteInActiveCategory.value) return

  const targetRoute = {
    name: 'community-create',
    query: {
      category: activeCategoryKey.value,
      lounge: currentLounge.value.key,
    },
  }

  if (
    !requireLogin({
      message: '게시글 작성은 로그인 후 이용할 수 있어요.',
      redirect: router.resolve(targetRoute).fullPath,
    })
  ) {
    return
  }

  router.push(targetRoute)
}

const editPost = async (post) => {
  if (!requireLogin()) return

  const title = window.prompt('수정할 제목을 입력해주세요.', post.title)
  if (title === null) return
  const content = window.prompt('수정할 내용을 입력해주세요.', post.content)
  if (content === null) return

  try {
    const updatedPost = await updatePost(post.id, {
      title: title.trim(),
      content: content.trim(),
      category: post.category,
      image_url: post.image_url,
      product_ids: post.products?.map((product) => product.id) || [],
    })
    Object.assign(post, normalizePost(updatedPost))
  } catch (error) {
    console.error('게시글 수정 실패:', error)
    if (handleAuthFailure(error)) return
    alert('게시글 수정에 실패했습니다.')
  }
}

const deletePost = async (post) => {
  if (!confirm('게시글을 삭제하시겠습니까?')) return

  if (String(post.id).startsWith('mock-')) {
    posts.value = posts.value.filter((item) => item.id !== post.id)
    return
  }

  try {
    await deletePostById(post.id)
    posts.value = posts.value.filter((item) => item.id !== post.id)
  } catch (error) {
    console.error('게시글 삭제 실패:', error)
    if (handleAuthFailure(error)) return
    alert('게시글 삭제에 실패했습니다.')
  }
}

watch(
  () => route.query.category,
  (category) => {
    activeCategoryKey.value = getCommunityCategoryByKey(category || DEFAULT_COMMUNITY_CATEGORY).key
    currentPage.value = 1
  },
)

watch(
  () => route.query.view,
  (view) => {
    activeMenu.value = ['all', 'liked', 'recent'].includes(view) ? view : 'all'
    if (activeMenu.value === 'recent') {
      loadRecentPostIds()
    }
    currentPage.value = 1
  },
)

watch(
  () => [route.query.tag, route.query.tags, route.query.mode],
  () => {
    currentPage.value = 1
  },
)

watch(filteredPosts, () => {
  if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
})

onMounted(() => {
  loadRecentPostIds()
  if (!route.query.category) syncRoute()
  fetchPosts()
})
</script>

<style scoped>
.community-page {
  width: 100%;
  background: #fdf8f6;
  font-family: "Pretendard Variable", Pretendard, "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
  letter-spacing: 0;
  color: #2d2524;
}

.community-hero {
  width: min(1180px, calc(100vw - 40px));
  margin: 0 auto;
  padding: 44px 0 30px;
  text-align: center;
}

.community-hero h1 {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: #1f1918;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.25;
}

.community-hero h1 span {
  color: #c65367;
  font-size: 1.05rem;
  line-height: 1;
  transform: translateY(-4px);
  display: inline-block;
}

.community-hero p {
  margin-top: 14px;
  color: #5f5754;
  font-size: 0.9rem;
  line-height: 1.7;
  font-weight: 400;
}

.community-container {
  width: min(1180px, calc(100vw - 40px));
  margin: 0 auto;
  padding: 0 0 92px;
  display: grid;
  grid-template-columns: 220px minmax(520px, 1fr) 230px;
  align-items: start;
  gap: 24px;
}

.left-sidebar,
:deep(.right-sidebar) {
  position: sticky;
  top: 96px;
}

.main-feed-area {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.feed-panel,
.feed-list,
.special-board {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.state-box,
.empty-state,
.special-card,
.lounge-board-card {
  background: white;
  border: 1px solid #f0e3df;
  border-radius: 14px;
  padding: 24px;
  color: #6b625f;
}

.state-box,
.empty-state {
  padding: 36px 24px;
  text-align: center;
}

.state-box.error {
  color: #b04658;
}

.empty-state strong {
  display: block;
  color: #3f3633;
  font-size: 1.05rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.empty-state p {
  color: #7c706c;
  margin-bottom: 18px;
}

.empty-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.empty-state button {
  height: 40px;
  padding: 0 18px;
  border: none;
  border-radius: 8px;
  background: #8b3a4a;
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.special-card strong {
  display: block;
  color: #3f3633;
  font-weight: 700;
}

.special-card span {
  display: block;
  margin-top: 5px;
  color: #c65367;
  font-size: 0.82rem;
}

.special-card p {
  margin-top: 12px;
  color: #6d5f5b;
  line-height: 1.55;
}

.lounge-board-card {
  display: grid;
  grid-template-columns: 42px 1fr auto;
  align-items: center;
  gap: 12px;
  text-align: left;
  cursor: pointer;
  font: inherit;
}

.lounge-board-card:hover {
  border-color: #e0a8b5;
}

.lounge-color {
  width: 42px;
  height: 42px;
  border-radius: 10px;
}

.lounge-board-card strong {
  color: #3f3633;
  font-weight: 700;
}

.lounge-board-card small {
  color: #8b807c;
}

.pagination {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.pagination button {
  min-width: 36px;
  height: 36px;
  border: 1px solid #eaded8;
  border-radius: 8px;
  background: white;
  color: #5f5754;
  cursor: pointer;
}

.pagination button.active {
  background: #8b3a4a;
  color: white;
  border-color: #8b3a4a;
}

.pagination button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (max-width: 1120px) {
  .community-container {
    grid-template-columns: 220px minmax(0, 1fr);
  }

  :deep(.right-sidebar) {
    position: static;
    grid-column: 2;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .community-container {
    width: min(100% - 28px, 680px);
    grid-template-columns: 1fr;
  }

  .left-sidebar,
  :deep(.right-sidebar) {
    position: static;
    grid-column: auto;
  }

  :deep(.right-sidebar) {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .community-container {
    width: min(100% - 20px, 680px);
    padding-top: 22px;
  }

  .lounge-board-card {
    grid-template-columns: 42px 1fr;
  }

  .lounge-board-card small {
    grid-column: 2;
  }
}
</style>
