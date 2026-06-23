<template>
  <div class="list-page">
    <header class="list-header">
      <button type="button" class="back-btn" @click="router.push('/mypage')">
        마이페이지로 돌아가기
      </button>
      <div>
        <p class="eyebrow">My page</p>
        <h1>{{ currentConfig.title }}</h1>
        <p class="subtitle">{{ currentConfig.description }}</p>
      </div>
    </header>

    <section class="list-panel">
      <div v-if="isLoading" class="state-msg">목록을 불러오는 중입니다.</div>
      <div v-else-if="items.length === 0" class="state-msg">{{ currentConfig.emptyText }}</div>

      <div v-else class="record-list">
        <article
          v-for="item in items"
          :key="`${item.type}-${item.id}`"
          class="record-card"
          :class="{ 'primary-card': item.isPrimary }"
          @click="openItem(item)"
        >
          <div v-if="item.type === 'liked-options' || item.type === 'diagnoses'" class="thumb-wrap">
            <img v-if="item.image" :src="item.image" :alt="item.title" />
            <span v-else>{{ item.brandInitial }}</span>
          </div>

          <div class="record-body">
            <div class="record-topline">
              <span class="record-date">{{ item.dateLabel }}</span>
              <span v-if="item.badge" class="badge">{{ item.badge }}</span>
            </div>

            <h2>{{ item.title }}</h2>
            <p v-if="item.description">{{ item.description }}</p>
            <p v-if="item.isPrimary" class="primary-note">현재 추천 기준으로 사용 중입니다.</p>

            <div v-if="item.colors?.length" class="swatches">
              <span
                v-for="color in item.colors"
                :key="color"
                :style="{ backgroundColor: color }"
              ></span>
            </div>
          </div>

          <div v-if="item.type === 'diagnoses'" class="record-actions" @click.stop>
            <button
              v-if="!item.isPrimary"
              type="button"
              class="set-primary-btn"
              :disabled="isMutating"
              @click="openSetPrimaryConfirm(item)"
            >
              메인으로 설정
            </button>
            <button
              v-else
              type="button"
              class="unset-primary-btn"
              :disabled="isMutating"
              @click="openUnsetPrimaryConfirm(item)"
            >
              설정 취소
            </button>
            <button
              type="button"
              class="delete-record-btn"
              :disabled="isMutating"
              @click="openDeleteConfirm(item)"
            >
              삭제
            </button>
          </div>

          <span class="open-label">보기</span>
        </article>
      </div>
    </section>

    <nav v-if="!isLoading && pagination.totalPages > 1" class="pagination">
      <button type="button" :disabled="!pagination.previous" @click="loadList(pagination.previous)">
        이전
      </button>
      <span>{{ pagination.page }} / {{ pagination.totalPages }}</span>
      <button type="button" :disabled="!pagination.next" @click="loadList(pagination.next)">
        다음
      </button>
    </nav>

    <p v-if="statusMessage" class="status-msg">{{ statusMessage }}</p>

    <div v-if="confirmState" class="modal-backdrop" @click.self="closeConfirm">
      <section class="confirm-modal" role="dialog" aria-modal="true">
        <h3>{{ confirmState.title }}</h3>
        <p>{{ confirmState.message }}</p>
        <p v-if="actionError" class="action-error">{{ actionError }}</p>
        <div class="modal-actions">
          <button type="button" class="cancel-btn" :disabled="isMutating" @click="closeConfirm">
            취소
          </button>
          <button
            type="button"
            class="confirm-btn"
            :class="{ danger: confirmState.danger }"
            :disabled="isMutating"
            @click="confirmAction"
          >
            {{ isMutating ? '처리 중' : confirmState.confirmText }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getMyPosts } from '@/services/communityApi'
import { deleteDiagnosisResult, getDiagnosisResults, setPrimaryDiagnosis, unsetPrimaryDiagnosis } from '@/services/diagnosisApi'
import { getLikedProductOptions, getUrlAnalysisRecords } from '@/services/engagementApi'
import { normalizeDiagnosisResult } from '@/utils/diagnosisResultTransform'

const PAGE_SIZE = 10

const route = useRoute()
const router = useRouter()

const items = ref([])
const isLoading = ref(false)
const isMutating = ref(false)
const confirmState = ref(null)
const actionError = ref('')
const statusMessage = ref('')
const pagination = ref({
  count: 0,
  page: 1,
  pageSize: PAGE_SIZE,
  totalPages: 0,
  next: null,
  previous: null,
})

const normalizeResponse = (data, page) => {
  if (Array.isArray(data)) {
    return {
      results: data,
      pagination: {
        count: data.length,
        page,
        pageSize: PAGE_SIZE,
        totalPages: data.length ? 1 : 0,
        next: null,
        previous: null,
      },
    }
  }

  return {
    results: data?.results || [],
    pagination: {
      count: data?.count || 0,
      page: data?.page || page,
      pageSize: data?.page_size || PAGE_SIZE,
      totalPages: data?.total_pages || 0,
      next: data?.next || null,
      previous: data?.previous || null,
    },
  }
}

const formatDate = (value) => {
  if (!value) return '날짜 없음'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleDateString('ko-KR')
}

const normalizeDiagnosis = (raw) => {
  const result = normalizeDiagnosisResult(raw) || raw
  const title = result.korean_name || result.personal_color?.korean_name || '진단 결과'
  return {
    type: 'diagnoses',
    id: result.id,
    title,
    description: `신뢰도 ${result.confidence_score ?? result.confidence ?? 0}%`,
    badge: result.is_primary ? '메인 퍼스널컬러' : result.status || 'completed',
    dateLabel: formatDate(result.created_at || result.diagnosed_at),
    image: result.processed_image_url || result.uploaded_image_url || result.profile_image_url || '',
    brandInitial: title.slice(0, 1),
    isPrimary: Boolean(result.is_primary),
  }
}

const normalizeLikedOption = (raw) => {
  const product = raw.product || {}
  const productOption = raw.product_option || {}
  const brand = raw.brand || product.brand || '브랜드 없음'
  const title = raw.name || product.name || '제품명 없음'
  return {
    type: 'liked-options',
    id: raw.id,
    productId: product.id || raw.product_id,
    optionId: productOption.id || raw.option_id,
    title,
    description: [
      brand,
      raw.option || [productOption.option_no, productOption.option_name].filter(Boolean).join(' '),
    ].filter(Boolean).join(' / '),
    badge: '찜한 제품',
    dateLabel: formatDate(raw.created_at),
    image: raw.image_url || productOption.image_url || product.image || product.image_url || '',
    brandInitial: brand.slice(0, 1).toUpperCase(),
  }
}

const normalizeUrlAnalysis = (raw) => ({
  type: 'url-analyses',
  id: raw.id,
  title: raw.title || raw.product_name || raw.source_url || 'URL 분석 기록',
  description: raw.source_url,
  badge: raw.brand || 'URL 분석',
  dateLabel: formatDate(raw.created_at),
  colors: raw.colors || [],
})

const normalizePost = (raw) => ({
  type: 'posts',
  id: raw.id,
  title: raw.title || '제목 없음',
  description: `댓글 ${raw.comment_count ?? 0}개 · 조회 ${raw.view_count ?? 0}`,
  badge: raw.category || '커뮤니티',
  dateLabel: formatDate(raw.created_at),
})

const configs = {
  diagnoses: {
    title: '진단 기록 전체 목록',
    description: '최근 진단부터 모든 퍼스널 컬러 진단 기록을 확인합니다.',
    emptyText: '진단 기록이 없습니다.',
    fetch: (params) => getDiagnosisResults(params),
    normalize: normalizeDiagnosis,
  },
  'liked-options': {
    title: '찜한 제품 옵션 전체 목록',
    description: '저장한 제품 옵션을 최신순으로 확인합니다.',
    emptyText: '찜한 제품 옵션이 없습니다.',
    fetch: (params) => getLikedProductOptions(params),
    normalize: normalizeLikedOption,
  },
  'url-analyses': {
    title: 'URL 분석 기록 전체 목록',
    description: 'URL로 분석한 제품 기록을 최신순으로 확인합니다.',
    emptyText: 'URL 분석 기록이 없습니다.',
    fetch: (params) => getUrlAnalysisRecords(params),
    normalize: normalizeUrlAnalysis,
  },
  posts: {
    title: '내가 쓴 커뮤니티 글 전체 목록',
    description: '작성한 커뮤니티 글을 최신순으로 확인합니다.',
    emptyText: '작성한 커뮤니티 글이 없습니다.',
    fetch: (params) => getMyPosts(params),
    normalize: normalizePost,
  },
}

const currentType = computed(() => route.meta.listType || 'diagnoses')
const currentConfig = computed(() => configs[currentType.value] || configs.diagnoses)

const loadList = async (page = 1) => {
  isLoading.value = true
  try {
    const data = await currentConfig.value.fetch({
      page,
      page_size: PAGE_SIZE,
    })
    const normalized = normalizeResponse(data, page)
    items.value = normalized.results.map(currentConfig.value.normalize)
    pagination.value = normalized.pagination
  } finally {
    isLoading.value = false
  }
}

const safeActionErrorMessage = (type) => {
  if (type === 'set-primary') {
    return '메인 퍼스널컬러 설정에 실패했습니다. 잠시 후 다시 시도해주세요.'
  }
  if (type === 'unset-primary') {
    return '메인 퍼스널컬러 설정 취소에 실패했습니다. 잠시 후 다시 시도해주세요.'
  }
  if (type === 'delete') {
    return '진단 결과 삭제에 실패했습니다. 잠시 후 다시 시도해주세요.'
  }
  return '요청을 처리하지 못했습니다. 잠시 후 다시 시도해주세요.'
}

const successMessage = (type) => {
  if (type === 'set-primary') return '메인 퍼스널컬러로 설정되었습니다.'
  if (type === 'unset-primary') return '메인 퍼스널컬러 설정이 취소되었습니다.'
  if (type === 'delete') return '진단 결과가 삭제되었습니다.'
  return ''
}

const openSetPrimaryConfirm = (item) => {
  if (item.isPrimary) return
  actionError.value = ''
  statusMessage.value = ''
  confirmState.value = {
    type: 'set-primary',
    item,
    title: '메인 퍼스널컬러 설정',
    message: '이 진단 결과를 메인 퍼스널컬러로 설정할까요?',
    confirmText: '설정하기',
    danger: false,
  }
}

const openUnsetPrimaryConfirm = (item) => {
  if (!item.isPrimary) return
  actionError.value = ''
  statusMessage.value = ''
  confirmState.value = {
    type: 'unset-primary',
    item,
    title: '메인 퍼스널컬러 설정 취소',
    message: '메인 퍼스널컬러 설정을 취소할까요? 취소하면 추천 기준으로 사용할 메인 결과가 없어집니다.',
    confirmText: '설정 취소',
    danger: false,
  }
}

const openDeleteConfirm = (item) => {
  actionError.value = ''
  statusMessage.value = ''
  confirmState.value = {
    type: 'delete',
    item,
    title: item.isPrimary ? '메인 진단 결과 삭제' : '진단 결과 삭제',
    message: item.isPrimary
      ? '현재 메인 퍼스널컬러로 설정된 결과입니다. 삭제하면 메인 퍼스널컬러가 없는 상태가 됩니다. 삭제할까요?'
      : '이 진단 결과를 삭제할까요?',
    confirmText: '삭제하기',
    danger: true,
  }
}

const closeConfirm = () => {
  if (isMutating.value) return
  confirmState.value = null
  actionError.value = ''
}

const confirmAction = async () => {
  if (!confirmState.value?.item?.id) {
    actionError.value = '처리할 진단 결과를 찾을 수 없습니다.'
    return
  }
  isMutating.value = true
  actionError.value = ''
  statusMessage.value = ''
  const action = confirmState.value
  const shouldMoveBack = action.type === 'delete' && items.value.length === 1 && pagination.value.page > 1

  try {
    if (action.type === 'set-primary') {
      await setPrimaryDiagnosis(action.item.id)
    } else if (action.type === 'unset-primary') {
      await unsetPrimaryDiagnosis(action.item.id)
    } else if (action.type === 'delete') {
      await deleteDiagnosisResult(action.item.id)
    }
    confirmState.value = null
    statusMessage.value = successMessage(action.type)
    await loadList(shouldMoveBack ? pagination.value.page - 1 : pagination.value.page)
  } catch (error) {
    console.error(`diagnosis ${action.type} failed:`, error)
    actionError.value = safeActionErrorMessage(action.type)
  } finally {
    isMutating.value = false
  }
}

const openItem = (item) => {
  if (item.type === 'diagnoses') {
    router.push(`/diagnosis/results/${item.id}`)
    return
  }
  if (item.type === 'liked-options') {
    if (!item.productId) {
      alert('상세 조회에 필요한 상품 ID가 없습니다.')
      return
    }
    router.push({
      name: 'product-color-matching',
      params: { id: item.productId },
      query: item.optionId ? { option: item.optionId } : {},
    })
    return
  }
  if (item.type === 'url-analyses') {
    router.push(`/analysis/result/${item.id}`)
    return
  }
  if (item.type === 'posts') {
    router.push(`/community/posts/${item.id}`)
  }
}

watch(currentType, () => loadList(1), { immediate: true })
</script>

<style scoped>
.list-page {
  max-width: 980px;
  min-height: 100vh;
  margin: 0 auto;
  padding: 40px 20px 72px;
  color: #333;
  background: #fdf8f6;
  font-family: 'Pretendard', sans-serif;
}

.list-header {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 24px;
}

.back-btn {
  border: 1px solid #ead6d9;
  border-radius: 8px;
  background: #fff;
  color: #8b3a4a;
  cursor: pointer;
  padding: 9px 13px;
  white-space: nowrap;
}

.eyebrow {
  margin: 0 0 4px;
  color: #b75a73;
  font-size: 0.78rem;
  font-weight: 800;
  text-transform: uppercase;
}

.list-header h1 {
  margin: 0;
  font-size: 1.8rem;
}

.subtitle {
  margin: 8px 0 0;
  color: #777;
}

.list-panel {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  padding: 18px;
}

.state-msg {
  padding: 64px 12px;
  color: #999;
  text-align: center;
}

.record-list {
  display: flex;
  flex-direction: column;
}

.record-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 4px;
  border-bottom: 1px solid #f3eceb;
  cursor: pointer;
}

.record-card:last-child {
  border-bottom: none;
}

.record-card:hover h2 {
  color: #8b3a4a;
}

.record-card.primary-card {
  margin: 8px 0;
  border: 1px solid #f1b7c3;
  border-radius: 12px;
  background: #fff6f7;
  padding: 16px;
}

.thumb-wrap {
  display: grid;
  place-items: center;
  width: 64px;
  height: 64px;
  flex: 0 0 64px;
  overflow: hidden;
  border-radius: 10px;
  background: #fff4f3;
  color: #8b3a4a;
  font-weight: 800;
}

.thumb-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.record-body {
  flex: 1;
  min-width: 0;
}

.record-topline {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.record-date {
  color: #999;
  font-size: 0.84rem;
}

.badge {
  border-radius: 999px;
  background: #fff0f1;
  color: #8b3a4a;
  font-size: 0.76rem;
  font-weight: 800;
  padding: 3px 8px;
}

.record-card h2 {
  margin: 0;
  overflow: hidden;
  color: #333;
  font-size: 1rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-card p {
  margin: 6px 0 0;
  overflow: hidden;
  color: #777;
  font-size: 0.9rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-card .primary-note {
  color: #b75a73;
  font-size: 0.82rem;
  font-weight: 800;
}

.swatches {
  display: flex;
  gap: 5px;
  margin-top: 10px;
}

.swatches span {
  width: 16px;
  height: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 50%;
}

.open-label {
  color: #b75a73;
  font-size: 0.86rem;
  font-weight: 800;
}

.record-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.set-primary-btn,
.unset-primary-btn,
.delete-record-btn,
.cancel-btn,
.confirm-btn {
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 800;
  padding: 8px 11px;
  white-space: nowrap;
}

.set-primary-btn {
  border: 1px solid #ead6d9;
  background: #fff;
  color: #8b3a4a;
}

.unset-primary-btn {
  border: 1px solid #ead6d9;
  background: #fff8f6;
  color: #6b4b52;
}

.set-primary-btn:disabled {
  cursor: default;
  opacity: 0.6;
}

.delete-record-btn,
.confirm-btn.danger {
  border: none;
  background: #b3261e;
  color: #fff;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.35);
  padding: 20px;
}

.confirm-modal {
  width: min(100%, 420px);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.2);
  padding: 24px;
}

.confirm-modal h3 {
  margin: 0 0 10px;
  color: #333;
  font-size: 1.1rem;
}

.confirm-modal p {
  margin: 0;
  color: #555;
  line-height: 1.6;
  white-space: normal;
}

.action-error {
  margin-top: 10px;
  color: #b3261e;
  font-size: 0.9rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 22px;
}

.cancel-btn {
  border: 1px solid #ddd;
  background: #fff;
  color: #444;
}

.confirm-btn {
  border: none;
  background: #8b3a4a;
  color: #fff;
}

.cancel-btn:disabled,
.confirm-btn:disabled,
.unset-primary-btn:disabled,
.delete-record-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.status-msg {
  margin: 16px 0 0;
  color: #8b3a4a;
  font-size: 0.92rem;
  font-weight: 800;
  text-align: center;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 14px;
  margin-top: 22px;
}

.pagination button {
  border: 1px solid #ead6d9;
  border-radius: 8px;
  background: #fff;
  color: #8b3a4a;
  cursor: pointer;
  padding: 8px 14px;
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

@media (max-width: 720px) {
  .list-header {
    flex-direction: column;
  }

  .record-card {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .record-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .open-label {
    display: none;
  }
}
</style>
