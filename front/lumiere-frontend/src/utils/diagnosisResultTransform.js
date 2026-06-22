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
  name: color?.nameKo || color?.name || `컬러 ${order + 1}`,
  hex: color?.hex || '#E7D8D7',
  description: color?.description || color?.reason || '',
  usage: color?.usage || '',
  order: color?.order ?? order,
})

const normalizeColorGroup = (items) => asArray(items).map(normalizeColorChip)

const getToneKey = (raw) => {
  return (
    raw?.toneKey ||
    raw?.tone_key ||
    raw?.diagnosis_json?.toneKey ||
    raw?.palette?.toneKey ||
    raw?.palette_snapshot?.toneKey ||
    raw?.type ||
    raw?.personal_color_code ||
    raw?.personal_color?.tone_key ||
    raw?.personal_color?.code ||
    ''
  )
}

const getFixedPalette = (raw) => raw.palette || raw.palette_snapshot || null

const normalizeFixedPaletteGroups = (palette, raw) => {
  if (!palette) {
    return {
      best: normalizeColorGroup(raw.palettes?.best || raw.color_palettes?.best),
      neutral: normalizeColorGroup(raw.palettes?.neutral || raw.color_palettes?.neutral),
      accent: normalizeColorGroup(raw.palettes?.accent || raw.color_palettes?.accent),
      try: normalizeColorGroup(raw.palettes?.try || raw.color_palettes?.try),
      worst: normalizeColorGroup(raw.palettes?.worst || raw.color_palettes?.worst),
    }
  }

  const groups = palette.palettes || {}
  return {
    best: normalizeColorGroup(groups.best || palette.bestColors || palette.best_colors),
    neutral: normalizeColorGroup(groups.neutral || palette.neutralColors || palette.neutral_colors),
    accent: normalizeColorGroup(groups.accent || palette.accentColors || palette.accent_colors),
    try: normalizeColorGroup(groups.try || palette.tryColors || palette.try_colors),
    worst: normalizeColorGroup(groups.worst || palette.worstColors || palette.worst_colors),
  }
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

const normalizeMakeupGuide = (raw, fixedPalette) => {
  const guide = raw.makeupColorGuide || raw.makeup_color_guide || fixedPalette?.makeupColorGuide || {}
  const eye = guide.eye || {}
  const roles = eye.roles || {}
  const roleColors = (key, fallback) => normalizeColorGroup(fallback || (roles[key] ? [roles[key]] : []))
  const lip = guide.lip || {}
  const blush = guide.blush || guide.cheek || {}

  return {
    base: {
      title: guide.base?.title || '베이스 컬러 가이드',
      description: guide.base?.description || guide.base?.guide || '',
      shadeRange: asArray(guide.base?.shadeRange || guide.base?.shade_range || guide.base?.recommended),
      chips: normalizeColorGroup(guide.base?.chips),
      avoid: asArray(guide.base?.avoid),
    },
    eye: {
      description: eye.description || eye.guide || '',
      highlighter: roleColors('highlighter', eye.highlighter),
      base: roleColors('base', eye.base),
      shading: roleColors('shading', eye.shading),
      point: roleColors('point', eye.point),
    },
    lip: {
      title: lip.title || '립 컬러 가이드',
      description: lip.description || lip.guide || '',
      chips: normalizeColorGroup(lip.chips),
      avoid: asArray(lip.avoid),
    },
    blush: {
      title: blush.title || '블러셔 컬러 가이드',
      description: blush.description || blush.guide || '',
      chips: normalizeColorGroup(blush.chips),
      avoid: asArray(blush.avoid),
    },
  }
}

const normalizeStyleGuide = (raw, fixedPalette) => {
  const source = raw.styleGuide || raw.style_guide || fixedPalette?.styleGuide || {}

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
  const personalColorCode = String(toneKey || '')
  const fixedPalette = getFixedPalette(raw)
  const colorPalettes = normalizeFixedPaletteGroups(fixedPalette, raw)
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
      korean_name: fixedPalette?.toneName || raw.titleKo || raw.korean_name,
      english_name: raw.titleEn || raw.english_name,
    },
    tone_key: personalColorCode,
    korean_name: fixedPalette?.toneName || raw.titleKo || raw.korean_name || raw.personal_color?.korean_name || '퍼스널 컬러',
    english_name: raw.titleEn || raw.english_name || raw.personal_color?.english_name || '',
    confidence: clampPercent(raw.confidence ?? raw.confidence_score),
    confidence_score: clampPercent(raw.confidence_score ?? raw.confidence),
    diagnosed_at: normalizeDate(raw.diagnosedAt || raw.diagnosed_at || raw.created_at),
    summary: raw.summary || fixedPalette?.summary || raw.description || '',
    keywords: asArray(raw.keywords?.length ? raw.keywords : fixedPalette?.keywords),
    profile_image_url: profileImageUrl,
    uploaded_image_url: raw.uploaded_image_url || raw.uploadedImageUrl || '',
    generated_makeup_image_url: raw.genAiImageUrl || raw.generated_makeup_image_url || '',
    image_features: normalizeImageFeatures(raw.imageFeatures || raw.image_features || fixedPalette?.imageFeatures),
    representative_colors: fixedPalette
      ? normalizeColorGroup(fixedPalette.representativeColors || fixedPalette.bestColors || fixedPalette.best_colors).slice(0, 6)
      : normalizeColorGroup(raw.representativeColors || raw.representative_colors),
    color_palettes: colorPalettes,
    skin_metrics: metrics,
    radar_chart: normalizeRadarChart(raw, metrics),
    makeover_styles: normalizeMakeoverStyles(raw),
    makeup_color_guide: normalizeMakeupGuide(raw, fixedPalette),
    style_guide: normalizeStyleGuide(raw, fixedPalette),
    recommended_products: asArray(raw.recommended_products),
    recommended_lenses: asArray(raw.recommended_lenses),
    palette: fixedPalette,
    palette_status: raw.palette_status || (fixedPalette?.isPlaceholder ? 'preparing' : ''),
    analysis: raw.analysis || raw.diagnosis_json?.analysis || null,
    evidence: raw.evidence || raw.diagnosis_json?.evidence || null,
    cautions: asArray(raw.cautions || raw.diagnosis_json?.cautions),
    makeup_generation_status: raw.makeup_generation_status || (raw.generated_makeup_image_url ? 'complete' : 'none'),
    styling_keywords: asArray(fixedPalette?.stylingKeywords || fixedPalette?.styling_keywords),
    recommended_product_tone_range:
      fixedPalette?.recommendedProductToneRange || fixedPalette?.recommended_product_tone_range || {},
    tip: raw.tip || fixedPalette?.resultTip || '',
    is_demo: Boolean(raw.is_demo || raw.id?.startsWith?.('mock-')),
    is_mock: Boolean(raw.is_mock || raw.id?.startsWith?.('mock-')),
  }
}

export const getDiagnosisProfileImageUrl = (diagnosis) => {
  if (!diagnosis) return null
  return diagnosis.profile_image_url || diagnosis.profileImageUrl || getLatestDiagnosisToneImageUrl(diagnosis)
}
