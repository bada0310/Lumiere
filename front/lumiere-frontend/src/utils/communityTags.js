export const TAG_CATEGORY = {
  PRODUCT: 'PRODUCT',
  BRAND: 'BRAND',
  CONCERN: 'CONCERN',
  TREND: 'TREND',
  MAKEUP: 'MAKEUP',
}

export const TAG_STATUS = {
  HOT: 'HOT',
  NEW: 'NEW',
  NORMAL: 'NORMAL',
}

const VALID_CATEGORIES = new Set(Object.values(TAG_CATEGORY))
const VALID_STATUSES = new Set(Object.values(TAG_STATUS))

const BRAND_KEYWORDS = [
  '3ce',
  '롬앤',
  'rom&nd',
  'romand',
  '데이지크',
  'dasique',
  '에스쁘아',
  'espoir',
  '페리페라',
  'peripera',
  '클리오',
  'clio',
]

const CONCERN_KEYWORDS = ['수분', '톤업', '저채도', '고민', '마스크팩']
const TREND_KEYWORDS = ['여쿨', '맑은', '물먹', '립조합', '요즘']
const MAKEUP_KEYWORDS = ['메이크업', '블러셔', '섀도우', '새도우', '하이라이터', '누드립', '립밤', '립']

const TAG_MATCH_ALIASES = {
  여쿨립: ['여쿨', '립', '베어그레이프', '틴트'],
  맑은틴트: ['맑은', '틴트', '글로시'],
  '3ce새도우': ['3ce', '섀도우', '새도우', 'shadow'],
  '3ce섀도우': ['3ce', '섀도우', '새도우', 'shadow'],
  데이지크팔레트: ['데이지크', 'dasique', '팔레트', '모브베리'],
  비리비리블러셔: ['블러셔', '베리', '라벤더'],
  베리베리블러셔: ['블러셔', '베리', '라벤더'],
  물먹립: ['물먹', '립', '틴트', '글로시'],
  톤업크림: ['톤업', '베이스', '크림'],
  여쿨라메이크업: ['여쿨라', '여쿨', '메이크업'],
  수분마스크팩: ['수분', '마스크팩'],
  저채도메이크업: ['저채도', '메이크업', '모브'],
  에스쁘아: ['에스쁘아', 'espoir'],
  롬앤: ['롬앤', 'rom&nd', 'romand'],
  페리페라: ['페리페라', 'peripera'],
  하이라이터: ['하이라이터'],
  누드립: ['누드립', '립'],
  무드블러셔: ['무드', '블러셔'],
  립밤: ['립밤', '립'],
  여쿨섀도우: ['여쿨', '섀도우', '새도우', '라벤더'],
  립조합: ['립조합', '립', '조합'],
  블러셔추천: ['블러셔', '추천'],
}

export const normalizeTagDisplayName = (value) => {
  const raw = String(value || '')
    .trim()
    .replace(/^#+/, '')
    .replace(/\s+/g, ' ')

  return raw ? `#${raw}` : ''
}

export const getTagSearchKey = (value) =>
  String(value || '')
    .trim()
    .replace(/^#+/, '')
    .replace(/\s+/g, '')
    .toLowerCase()

const includesAny = (key, keywords) => keywords.some((keyword) => key.includes(getTagSearchKey(keyword)))

export const inferTagCategory = (tag) => {
  if (VALID_CATEGORIES.has(tag?.category)) return tag.category

  const key = getTagSearchKey(tag?.name || tag)
  if (includesAny(key, BRAND_KEYWORDS)) return TAG_CATEGORY.BRAND
  if (includesAny(key, TREND_KEYWORDS)) return TAG_CATEGORY.TREND
  if (includesAny(key, CONCERN_KEYWORDS)) return TAG_CATEGORY.CONCERN
  if (includesAny(key, MAKEUP_KEYWORDS)) return TAG_CATEGORY.MAKEUP
  return TAG_CATEGORY.PRODUCT
}

export const normalizeTagStatus = (tag, index = 0) => {
  if (VALID_STATUSES.has(tag?.status)) return tag.status
  if (tag?.isTrending) return TAG_STATUS.HOT
  if ((tag?.trendScore || 0) >= 80 || (tag?.growthRate || 0) >= 30) return TAG_STATUS.HOT
  if ((tag?.trendScore || 0) >= 60 || (tag?.growthRate || 0) >= 15) return TAG_STATUS.NEW
  if (index === 0 || index === 1) return TAG_STATUS.HOT
  if (index === 2) return TAG_STATUS.NEW
  return TAG_STATUS.NORMAL
}

export const normalizePopularTag = (tag, index = 0) => {
  const name = normalizeTagDisplayName(tag?.name || tag)
  const key = getTagSearchKey(name)

  return {
    ...tag,
    id: tag?.id ?? key,
    key,
    name,
    rawName: name.replace(/^#/, ''),
    category: inferTagCategory(tag),
    status: normalizeTagStatus(tag, index),
    postCount: tag?.postCount ?? 0,
    trendScore: tag?.trendScore ?? 0,
    growthRate: tag?.growthRate ?? 0,
    sortIndex: index,
  }
}

export const normalizePopularTags = (tags = []) => tags.map(normalizePopularTag).filter((tag) => tag.name)

export const dedupeTagNames = (tags = []) => {
  const seen = new Set()
  return tags
    .map(normalizeTagDisplayName)
    .filter(Boolean)
    .filter((tag) => {
      const key = getTagSearchKey(tag)
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
}

export const parseQueryTags = (value) => {
  if (!value) return []
  const joined = Array.isArray(value) ? value.join(',') : String(value)
  return dedupeTagNames(joined.split(',').map((tag) => tag.trim()))
}

export const serializeTagsForQuery = (tags = []) =>
  dedupeTagNames(tags)
    .map((tag) => tag.replace(/^#/, ''))
    .join(',')

export const getTagCategoryClass = (category) => `tag-chip--${String(category || TAG_CATEGORY.PRODUCT).toLowerCase()}`

const collectPostValues = (post) => {
  const values = [
    post?.title,
    post?.content,
    post?.category,
    post?.author,
    post?.userTone,
    ...(Array.isArray(post?.hashtags) ? post.hashtags : String(post?.hashtags || '').split(/[,\s]+/)),
  ]

  if (Array.isArray(post?.products)) {
    post.products.forEach((product) => {
      values.push(product?.brand, product?.name, product?.category, `${product?.brand || ''}${product?.name || ''}`)
    })
  }

  return values.filter(Boolean)
}

const getTagCandidateKeys = (tag) => {
  const key = getTagSearchKey(tag?.name || tag)
  const aliases = TAG_MATCH_ALIASES[key] || []
  return [key, ...aliases.map(getTagSearchKey)].filter(Boolean)
}

export const matchesPostByTag = (post, tag) => {
  const haystack = collectPostValues(post).map(getTagSearchKey).join(' ')
  return getTagCandidateKeys(tag).some((candidate) => haystack.includes(candidate))
}

export const matchesPostByTags = (post, tags = [], mode = 'or') => {
  const normalizedTags = dedupeTagNames(tags)
  if (!normalizedTags.length) return true

  if (mode === 'and') {
    return normalizedTags.every((tag) => matchesPostByTag(post, tag))
  }

  return normalizedTags.some((tag) => matchesPostByTag(post, tag))
}
