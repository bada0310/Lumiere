const STORAGE_KEY = 'skinColorMetrics'

const clampPercent = (value, fallback = 0) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return fallback
  return Math.min(100, Math.max(0, Math.round(number)))
}

const normalizeToneKey = (value = '') => {
  return String(value)
    .trim()
    .toUpperCase()
    .replaceAll('-', '_')
}

export const TONE_PROFILE_PRESETS = {
  SPRING_LIGHT: {
    toneTag: 'SPRING_LIGHT',
    toneName: '봄 웜 라이트',
    brightness: 82,
    saturation: 46,
    coolness: 24,
    warmth: 76,
    softness: 42,
    contrast: 28,
  },
  SPRING_BRIGHT: {
    toneTag: 'SPRING_BRIGHT',
    toneName: '봄 웜 브라이트',
    brightness: 80,
    saturation: 78,
    coolness: 22,
    warmth: 78,
    softness: 24,
    contrast: 64,
  },
  SUMMER_LIGHT: {
    toneTag: 'SUMMER_LIGHT',
    toneName: '여름 쿨 라이트',
    brightness: 78,
    saturation: 34,
    coolness: 78,
    warmth: 22,
    softness: 58,
    contrast: 24,
  },
  SUMMER_MUTE: {
    toneTag: 'SUMMER_MUTE',
    toneName: '여름 쿨 뮤트',
    brightness: 68,
    saturation: 30,
    coolness: 74,
    warmth: 26,
    softness: 76,
    contrast: 20,
  },
  AUTUMN_MUTE: {
    toneTag: 'AUTUMN_MUTE',
    toneName: '가을 웜 뮤트',
    brightness: 58,
    saturation: 34,
    coolness: 24,
    warmth: 76,
    softness: 78,
    contrast: 34,
  },
  AUTUMN_DEEP: {
    toneTag: 'AUTUMN_DEEP',
    toneName: '가을 웜 딥',
    brightness: 38,
    saturation: 48,
    coolness: 18,
    warmth: 82,
    softness: 52,
    contrast: 68,
  },
  WINTER_BRIGHT: {
    toneTag: 'WINTER_BRIGHT',
    toneName: '겨울 쿨 브라이트',
    brightness: 85,
    saturation: 85,
    coolness: 86,
    warmth: 14,
    softness: 25,
    contrast: 85,
  },
  WINTER_DEEP: {
    toneTag: 'WINTER_DEEP',
    toneName: '겨울 쿨 딥',
    brightness: 32,
    saturation: 68,
    coolness: 82,
    warmth: 18,
    softness: 24,
    contrast: 88,
  },
}

const getPresetByDiagnosis = (diagnosis = {}) => {
  const rawKey =
    diagnosis.toneTag ||
    diagnosis.tone_tag ||
    diagnosis.personal_color_code ||
    diagnosis.personal_color?.code ||
    diagnosis.type ||
    ''

  const normalizedKey = normalizeToneKey(rawKey)
  return TONE_PROFILE_PRESETS[normalizedKey] || TONE_PROFILE_PRESETS.SUMMER_LIGHT
}

export const buildDiagnosisColorProfile = (diagnosis = {}) => {
  const preset = getPresetByDiagnosis(diagnosis)
  const skinMetrics = diagnosis.skin_metrics || {}
  const radarChart = diagnosis.radar_chart || {}

  const coolWarm = Number(skinMetrics.cool_warm)
  const hasCoolWarm = Number.isFinite(coolWarm)
  const coolness = hasCoolWarm ? clampPercent(coolWarm, preset.coolness) : preset.coolness
  const warmth = hasCoolWarm ? clampPercent(100 - coolWarm, preset.warmth) : preset.warmth

  return {
    source: diagnosis.is_mock ? 'mock-diagnosis' : 'ai-diagnosis',
    diagnosisId: diagnosis.id || '',
    toneTag: preset.toneTag,
    toneName: diagnosis.korean_name || diagnosis.personal_color?.korean_name || preset.toneName,
    englishName: diagnosis.english_name || diagnosis.personal_color?.english_name || '',
    confidence: clampPercent(diagnosis.confidence ?? diagnosis.confidence_score),
    brightness: clampPercent(skinMetrics.brightness ?? radarChart.brightness, preset.brightness),
    saturation: clampPercent(skinMetrics.saturation ?? radarChart.saturation, preset.saturation),
    coolness,
    warmth,
    softness: clampPercent(skinMetrics.softness ?? radarChart.softness, preset.softness),
    contrast: clampPercent(skinMetrics.contrast ?? radarChart.contrast, preset.contrast),
    clarity: clampPercent(skinMetrics.clarity ?? radarChart.clarity, 50),
    representativeColors: Array.isArray(diagnosis.representative_colors) ? diagnosis.representative_colors : [],
    diagnosedAt: diagnosis.diagnosed_at || diagnosis.created_at || new Date().toISOString(),
  }
}

export const saveDiagnosisColorProfile = (diagnosis) => {
  const profile = buildDiagnosisColorProfile(diagnosis)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(profile))
  localStorage.setItem('selectedReferenceTone', profile.toneTag)
  return profile
}

export const readUserColorProfile = () => {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    if (saved?.toneTag) return saved
  } catch (error) {
    console.warn('저장된 피부 색상 데이터를 읽지 못했어요:', error)
  }

  return {
    ...TONE_PROFILE_PRESETS.SUMMER_LIGHT,
    source: 'reference-tone',
    diagnosedAt: '',
  }
}

export const hasSavedUserColorProfile = () => {
  try {
    return Boolean(JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')?.toneTag)
  } catch {
    return false
  }
}

export const calculateProductMatchScore = (profile, product) => {
  const target = profile || TONE_PROFILE_PRESETS.SUMMER_LIGHT
  const distance =
    Math.abs(clampPercent(target.brightness) - clampPercent(product.brightness)) * 0.22 +
    Math.abs(clampPercent(target.saturation) - clampPercent(product.saturation)) * 0.18 +
    Math.abs(clampPercent(target.coolness) - clampPercent(product.coolness)) * 0.18 +
    Math.abs(clampPercent(target.warmth) - clampPercent(product.warmth)) * 0.18 +
    Math.abs(clampPercent(target.softness) - clampPercent(product.softness)) * 0.14 +
    Math.abs(clampPercent(target.contrast) - clampPercent(product.contrast)) * 0.10

  return clampPercent(100 - distance)
}

export const getWarmCoolPosition = (item) => {
  return clampPercent(((clampPercent(item.coolness) - clampPercent(item.warmth)) + 100) / 2)
}

export const getChartPoint = (item) => {
  return {
    x: getWarmCoolPosition(item),
    y: clampPercent(item.brightness),
    size: Math.max(9, Math.min(24, Math.round(clampPercent(item.saturation) / 5))),
    color: item.hexCode || item.hex_code || item.hex || '#c65367',
  }
}

export const getMetricLabels = (profile) => {
  const coolDiff = clampPercent(profile.coolness) - clampPercent(profile.warmth)
  const toneDirection = coolDiff >= 16 ? '쿨 방향' : coolDiff <= -16 ? '웜 방향' : '뉴트럴'

  return {
    brightness: clampPercent(profile.brightness) >= 70 ? '명도: 밝음' : clampPercent(profile.brightness) <= 42 ? '명도: 어두움' : '명도: 중간',
    saturation: clampPercent(profile.saturation) >= 60 ? '채도: 높음' : clampPercent(profile.saturation) <= 40 ? '채도: 낮음' : '채도: 중간',
    direction: toneDirection,
  }
}
