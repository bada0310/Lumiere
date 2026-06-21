import { getLatestDiagnosisToneImageUrl, getToneImageUrl } from '@/data/toneImages'

const asArray = (value) => (Array.isArray(value) ? value : [])

const clampPercent = (value) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.min(100, Math.max(0, Math.round(number)))
}

const coolWarmToPercent = (value) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return 50
  return clampPercent((Math.max(-100, Math.min(100, number)) + 100) / 2)
}

const normalizeColorChip = (color, order = 0) => ({
  name: color?.name || `컬러 ${order + 1}`,
  hex: color?.hex || '#E7D8D7',
  description: color?.description || '',
  order: color?.order ?? order,
})

const normalizeColorGroup = (items) => asArray(items).map(normalizeColorChip)

const getToneKey = (raw) => {
  return raw?.toneKey || raw?.tone_key || raw?.type || raw?.personal_color_code || raw?.personal_color?.code || ''
}

const normalizeDate = (value) => {
  if (!value) return new Date().toISOString()

  if (/^\d{4}\.\d{2}\.\d{2}$/.test(String(value))) {
    return String(value).replaceAll('.', '-')
  }

  return value
}

const normalizeImageFeatures = (features) =>
  asArray(features).map((feature, index) => ({
    key: feature.key || feature.label || feature.title || `feature-${index}`,
    title: feature.title || feature.label || `특징 ${index + 1}`,
    description: feature.description || '',
    icon: feature.icon || '',
  }))

const normalizeMakeoverStyles = (raw) => {
  const mockItems = asArray(raw.makeoverImages).map((item, index) => ({
    key: item.id || `style-${index}`,
    name: item.styleName || item.name || `스타일 ${index + 1}`,
    description: item.description || '',
    image_url: item.imageUrl || item.image_url || '',
    order: index,
    is_default: index === 0,
  }))

  if (mockItems.length) return mockItems

  return asArray(raw.makeover_styles).map((item, index) => ({
    key: item.key || item.id || `style-${index}`,
    name: item.name || item.styleName || `스타일 ${index + 1}`,
    description: item.description || '',
    image_url: item.image_url || item.image || '',
    order: item.order ?? index,
    is_default: Boolean(item.is_default || index === 0),
  }))
}

const normalizeSkinMetrics = (raw) => {
  const source = raw.skinAnalysis || raw.skin_metrics || {}
  return {
    brightness: clampPercent(source.brightness),
    saturation: clampPercent(source.saturation),
    clarity: clampPercent(source.clarity),
    contrast: clampPercent(source.contrast),
    cool_warm: raw.skinAnalysis ? coolWarmToPercent(source.coolWarm) : clampPercent(source.cool_warm),
    softness: clampPercent(source.softness),
    gloss: clampPercent(source.gloss ?? source.clarity),
  }
}

const normalizeRadarChart = (raw, metrics) => {
  const chart = raw.radar_chart || {}
  return {
    brightness: clampPercent(chart.brightness ?? metrics.brightness),
    saturation: clampPercent(chart.saturation ?? metrics.saturation),
    clarity: clampPercent(chart.clarity ?? metrics.clarity),
    contrast: clampPercent(chart.contrast ?? metrics.contrast),
    softness: clampPercent(chart.softness ?? metrics.softness),
    coolness: clampPercent(chart.coolness ?? 100 - metrics.cool_warm),
  }
}

const normalizeMakeupGuide = (raw) => {
  const guide = raw.makeupColorGuide || raw.makeup_color_guide || {}
  const eye = guide.eye || {}

  return {
    base: {
      title: guide.base?.title || '베이스 컬러 가이드',
      description: guide.base?.description || '',
      shadeRange: asArray(guide.base?.shadeRange || guide.base?.shade_range),
      chips: normalizeColorGroup(guide.base?.chips),
      avoid: asArray(guide.base?.avoid),
    },
    eye: {
      description: eye.description || '',
      highlighter: normalizeColorGroup(eye.highlighter),
      base: normalizeColorGroup(eye.base),
      shading: normalizeColorGroup(eye.shading),
      point: normalizeColorGroup(eye.point),
    },
    lip: {
      title: guide.lip?.title || '립 컬러 가이드',
      description: guide.lip?.description || '',
      chips: normalizeColorGroup(guide.lip?.chips),
      avoid: asArray(guide.lip?.avoid),
    },
    blush: {
      title: guide.blush?.title || '블러셔 컬러 가이드',
      description: guide.blush?.description || '',
      chips: normalizeColorGroup(guide.blush?.chips),
      avoid: asArray(guide.blush?.avoid),
    },
  }
}

const normalizeStyleGuide = (raw) => {
  const source = raw.styleGuide || raw.style_guide || {}

  return {
    lens: normalizeColorGroup(source.lens || source.lenses || source.lens_colors),
    hair: normalizeColorGroup(source.hair || source.hair_colors),
    accessory: asArray(source.accessory || source.accessories).map((item) =>
      typeof item === 'string' ? item : item.description || item.name,
    ),
    fashion: normalizeColorGroup(source.fashion || source.recommended_styles),
  }
}

export const normalizeDiagnosisResult = (raw) => {
  if (!raw) return null

  const toneKey = getToneKey(raw)
  const personalColorCode = String(toneKey || '').replace(/_/g, '-')
  const profileImageUrl =
    raw.profileImageUrl ||
    raw.profile_image_url ||
    getToneImageUrl(toneKey || raw.personal_color || raw.personal_color_code)
  const metrics = normalizeSkinMetrics(raw)

  return {
    ...raw,
    id: raw.id || 'mock-diagnosis-result',
    personal_color_code: personalColorCode,
    personal_color: raw.personal_color || {
      code: personalColorCode,
      korean_name: raw.titleKo || raw.korean_name,
      english_name: raw.titleEn || raw.english_name,
    },
    korean_name: raw.titleKo || raw.korean_name || raw.personal_color?.korean_name || '퍼스널 컬러',
    english_name: raw.titleEn || raw.english_name || raw.personal_color?.english_name || '',
    confidence: clampPercent(raw.confidence ?? raw.confidence_score),
    confidence_score: clampPercent(raw.confidence_score ?? raw.confidence),
    diagnosed_at: normalizeDate(raw.diagnosedAt || raw.diagnosed_at || raw.created_at),
    summary: raw.description || raw.summary || '',
    keywords: asArray(raw.keywords),
    profile_image_url: profileImageUrl,
    uploaded_image_url: raw.uploaded_image_url || raw.uploadedImageUrl || '',
    generated_makeup_image_url: raw.genAiImageUrl || raw.generated_makeup_image_url || '',
    image_features: normalizeImageFeatures(raw.imageFeatures || raw.image_features),
    representative_colors: normalizeColorGroup(raw.representativeColors || raw.representative_colors),
    color_palettes: {
      best: normalizeColorGroup(raw.palettes?.best || raw.color_palettes?.best),
      neutral: normalizeColorGroup(raw.palettes?.neutral || raw.color_palettes?.neutral),
      accent: normalizeColorGroup(raw.palettes?.accent || raw.color_palettes?.accent),
      worst: normalizeColorGroup(raw.palettes?.worst || raw.color_palettes?.worst),
    },
    skin_metrics: metrics,
    radar_chart: normalizeRadarChart(raw, metrics),
    makeover_styles: normalizeMakeoverStyles(raw),
    makeup_color_guide: normalizeMakeupGuide(raw),
    style_guide: normalizeStyleGuide(raw),
    recommended_products: asArray(raw.recommended_products),
    recommended_lenses: asArray(raw.recommended_lenses),
    tip: raw.tip || '',
    is_demo: Boolean(raw.is_demo || raw.id?.startsWith?.('mock-')),
    is_mock: Boolean(raw.is_mock || raw.id?.startsWith?.('mock-')),
  }
}

export const getDiagnosisProfileImageUrl = (diagnosis) => {
  if (!diagnosis) return null
  return diagnosis.profile_image_url || diagnosis.profileImageUrl || getLatestDiagnosisToneImageUrl(diagnosis)
}
