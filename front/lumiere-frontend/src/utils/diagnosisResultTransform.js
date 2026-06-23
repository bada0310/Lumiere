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

const normalizeColorChip = (color, order = 0) => {
  if (typeof color === 'string') {
    return {
      name: color,
      hex: '#E7D8D7',
      description: '',
      usage: '',
      order,
    }
  }

  return {
    name: color?.nameKo || color?.name || `컬러 ${order + 1}`,
    hex: color?.hex || '#E7D8D7',
    description: color?.description || color?.reason || '',
    usage: color?.usage || '',
    order: color?.order ?? order,
  }
}

const normalizeColorGroup = (items) => asArray(items).filter(Boolean).map(normalizeColorChip)

const getToneKey = (raw) =>
  raw?.toneKey ||
  raw?.tone_key ||
  raw?.diagnosis_json?.toneKey ||
  raw?.diagnosis_json?.tone_key ||
  raw?.palette?.toneKey ||
  raw?.palette_snapshot?.toneKey ||
  raw?.type ||
  raw?.personal_color_code ||
  raw?.personal_color?.tone_key ||
  raw?.personal_color?.code ||
  ''

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
  if (/^\d{4}\.\d{2}\.\d{2}$/.test(String(value))) return String(value).replaceAll('.', '-')
  return value
}

const normalizeImageFeatures = (features) =>
  asArray(features).map((feature, index) => ({
    key: feature.key || feature.label || feature.title || `feature-${index}`,
    title: feature.title || feature.label || `특징 ${index + 1}`,
    description: feature.description || '',
    icon: feature.icon || '',
  }))

const defaultMakeoverStyles = () => [
  {
    key: 'natural_daily',
    name: '내추럴 데일리룩',
    description: '피부결과 혈색을 자연스럽게 살린 데일리 메이크업',
    image_url: '',
    status: 'none',
    error_message: '',
    order: 1,
    is_default: true,
  },
  {
    key: 'pure_daily',
    name: '청순 데일리룩',
    description: '맑고 부드러운 눈매와 은은한 립을 중심으로 한 룩',
    image_url: '',
    status: 'none',
    error_message: '',
    order: 2,
    is_default: false,
  },
  {
    key: 'romantic',
    name: '로맨틱 룩',
    description: '톤에 맞는 립과 블러셔로 분위기를 더한 룩',
    image_url: '',
    status: 'none',
    error_message: '',
    order: 3,
    is_default: false,
  },
  {
    key: 'chic',
    name: '시크 룩',
    description: '정돈된 음영과 선명한 포인트를 살린 룩',
    image_url: '',
    status: 'none',
    error_message: '',
    order: 4,
    is_default: false,
  },
  {
    key: 'smoky',
    name: '스모키 룩',
    description: '톤에 맞는 깊은 음영으로 눈매를 또렷하게 만든 룩',
    image_url: '',
    status: 'none',
    error_message: '',
    order: 5,
    is_default: false,
  },
]

const normalizeMakeoverStyles = (raw) => {
  const mockItems = asArray(raw.makeoverImages).map((item, index) => ({
    key: item.id || item.key || `style-${index}`,
    name: item.styleName || item.name || `스타일 ${index + 1}`,
    description: item.description || '',
    image_url: item.imageUrl || item.image_url || '',
    status: item.status || (item.imageUrl || item.image_url ? 'complete' : 'none'),
    error_message: item.error_message || item.error || '',
    order: item.order ?? index + 1,
    is_default: Boolean(item.is_default || index === 0),
  }))
  if (mockItems.length) return mockItems

  return asArray(raw.makeover_styles || raw.ai_makeover?.styles).map((item, index) => ({
    key: item.key || item.id || `style-${index}`,
    name: item.name || item.styleName || `스타일 ${index + 1}`,
    description: item.description || '',
    image_url: item.image_url || item.image || '',
    status: item.status || (item.image_url || item.image ? 'complete' : 'none'),
    error_message: item.error_message || item.error || '',
    order: item.order ?? index + 1,
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
  const base = guide.base || {}
  const eye = guide.eye || {}
  const roles = eye.roles || {}
  const lip = guide.lip || {}
  const blush = guide.blush || guide.cheek || {}
  const roleColors = (key, fallback) => normalizeColorGroup(fallback || (roles[key] ? [roles[key]] : []))

  return {
    base: {
      title: base.title || '베이스 컬러 가이드',
      description: base.description || base.guide || '',
      shadeRange: asArray(base.shadeRange || base.shade_range || base.recommended),
      chips: normalizeColorGroup(base.chips),
      avoid: asArray(base.avoid),
    },
    eye: {
      title: eye.title || '아이 메이크업',
      description: eye.description || eye.guide || '',
      highlighter: roleColors('highlighter', eye.highlighter),
      base: roleColors('base', eye.base),
      shading: roleColors('shading', eye.shading),
      point: roleColors('point', eye.point),
      aegyosal: roleColors('aegyosal', eye.aegyosal),
      eyeliner: roleColors('eyeliner', eye.eyeliner),
      avoid: asArray(eye.avoid),
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

const normalizeAccessory = (items) =>
  asArray(items).map((item) =>
    typeof item === 'string'
      ? item
      : {
          name: item.name || item.title || item.description || '',
          description: item.description || item.tone || item.material || '',
        },
  )

const normalizeStyleGuide = (raw, fixedPalette) => {
  const source = raw.styleGuide || raw.style_guide || fixedPalette?.styleGuide || {}
  const outfit = source.outfit || source.fashion_guide || {}
  const outfitColors = outfit.colors || source.outfit_colors || source.fashion || source.recommended_styles

  return {
    lens: normalizeColorGroup(source.lens || source.lenses || source.lens_colors),
    hair: normalizeColorGroup(source.hair || source.hair_colors),
    accessory: normalizeAccessory(source.accessory || source.accessories),
    outfit: {
      description: outfit.description || source.fashion_description || '',
      colors: normalizeColorGroup(outfitColors),
    },
    fashion: normalizeColorGroup(source.fashion || source.recommended_styles),
  }
}

const normalizeAiMakeover = (raw, styles) => {
  const source = raw.ai_makeover || raw.makeover || {}
  const normalizedStyles = styles.length ? styles : defaultMakeoverStyles()
  const status =
    source.status ||
    raw.makeover_generation_status ||
    raw.makeup_generation_status ||
    (normalizedStyles.some((style) => style.image_url) ? 'complete' : 'none')

  return {
    status,
    styles: normalizedStyles,
    error: source.error || raw.makeup_generation_error || '',
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
  const makeoverStyles = normalizeMakeoverStyles(raw)
  const aiMakeover = normalizeAiMakeover(raw, makeoverStyles)

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
    processed_image_url: raw.processed_image_url || raw.processedImageUrl || '',
    generated_makeup_image_url: raw.genAiImageUrl || raw.generated_makeup_image_url || '',
    image_features: normalizeImageFeatures(raw.imageFeatures || raw.image_features || fixedPalette?.imageFeatures),
    representative_colors: fixedPalette
      ? normalizeColorGroup(fixedPalette.representativeColors || fixedPalette.bestColors || fixedPalette.best_colors).slice(0, 6)
      : normalizeColorGroup(raw.representativeColors || raw.representative_colors),
    color_palettes: colorPalettes,
    skin_metrics: metrics,
    radar_chart: normalizeRadarChart(raw, metrics),
    makeover_styles: makeoverStyles,
    ai_makeover: aiMakeover,
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
    styling_keywords: asArray(fixedPalette?.stylingKeywords || fixedPalette?.styling_keywords || raw.style_guide?.styling_keywords),
    recommended_product_tone_range:
      fixedPalette?.recommendedProductToneRange ||
      fixedPalette?.recommended_product_tone_range ||
      raw.style_guide?.recommended_product_tone_range ||
      {},
    tip: raw.tip || fixedPalette?.resultTip || '',
    is_primary: Boolean(raw.is_primary),
    is_demo: Boolean(raw.is_demo || raw.id?.startsWith?.('mock-')),
    is_mock: Boolean(raw.is_mock || raw.id?.startsWith?.('mock-')),
  }
}

export const getDiagnosisProfileImageUrl = (diagnosis) => {
  if (!diagnosis) return null
  return diagnosis.profile_image_url || diagnosis.profileImageUrl || getLatestDiagnosisToneImageUrl(diagnosis)
}
