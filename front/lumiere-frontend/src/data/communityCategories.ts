export interface CommunityCategory {
  key: string
  apiValue: string
  label: string
  icon: string
  visible: boolean
  boardType?: 'post-category' | 'popular-tags' | 'popular-posts' | 'notices' | 'recommended-lounges'
}

export const COMMUNITY_CATEGORIES: CommunityCategory[] = [
  {
    key: 'life-item',
    apiValue: 'LIFE_ITEM',
    label: '인생템 공유',
    icon: '🛍️',
    visible: true,
    boardType: 'post-category',
  },
  {
    key: 'swatch-review',
    apiValue: 'COLOR_REVIEW',
    label: '발색 리뷰',
    icon: '✨',
    visible: true,
    boardType: 'post-category',
  },
  {
    key: 'makeup-question',
    apiValue: 'QUESTION',
    label: '메이크업 질문',
    icon: '💬',
    visible: true,
    boardType: 'post-category',
  },
  {
    key: 'product-recommendation',
    apiValue: 'PRODUCT_RECOMMENDATION',
    label: '제품 추천',
    icon: '🎁',
    visible: true,
    boardType: 'post-category',
  },
  {
    key: 'free-community',
    apiValue: 'FREE',
    label: '자유 커뮤니티',
    icon: '☕',
    visible: false,
    boardType: 'post-category',
  },
  {
    key: 'popular-product-tags',
    apiValue: 'POPULAR_PRODUCT_TAGS',
    label: '인기 제품 태그',
    icon: '#',
    visible: false,
    boardType: 'popular-tags',
  },
  {
    key: 'weekly-popular-posts',
    apiValue: 'WEEKLY_POPULAR_POSTS',
    label: '이번 주 인기 글',
    icon: '↗',
    visible: false,
    boardType: 'popular-posts',
  },
  {
    key: 'lounge-notices',
    apiValue: 'LOUNGE_NOTICES',
    label: '라운지 공지사항',
    icon: '!',
    visible: false,
    boardType: 'notices',
  },
  {
    key: 'recommended-lounges',
    apiValue: 'RECOMMENDED_LOUNGES',
    label: '맞춤 라운지 추천',
    icon: '◎',
    visible: false,
    boardType: 'recommended-lounges',
  },
]

export const DEFAULT_COMMUNITY_CATEGORY = 'life-item'

export const getCommunityCategoryByKey = (key?: string | null) =>
  COMMUNITY_CATEGORIES.find((category) => category.key === key) ||
  COMMUNITY_CATEGORIES.find((category) => category.key === DEFAULT_COMMUNITY_CATEGORY)!

export const getCommunityCategoryByApiValue = (apiValue?: string | null) =>
  COMMUNITY_CATEGORIES.find((category) => category.apiValue === apiValue)
