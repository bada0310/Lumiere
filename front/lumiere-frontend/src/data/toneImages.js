export const FALLBACK_TONE_IMAGE = '/images/tones/summer_cool_light.png'

const TONE_IMAGE_FILE_MAP = {
  'spring-warm-bright': 'spring_warm_bright',
  'spring-warm-light': 'spring_warm_light',
  'spring-warm-mute': 'spring_warm_mute',
  'spring-warm-deep': 'spring_warm_deep',
  'spring-cool-bright': 'spring_cool_bright',
  'spring-cool-light': 'spring_cool_light',
  'spring-cool-mute': 'spring_cool_mute',
  'spring-cool-deep': 'spring_cool_deep',

  'summer-warm-bright': 'summer_warm_bright',
  'summer-warm-light': 'summer_warm_ligth',
  'summer-warm-mute': 'summer_warm_mute',
  'summer-warm-deep': 'summer_warm_deep',
  'summer-cool-bright': 'summer_cool_bright',
  'summer-cool-light': 'summer_cool_light',
  'summer-cool-mute': 'summer_cool_mute',
  'summer-cool-deep': 'summer_cool_deep',

  'autumn-warm-bright': 'fall_warm_bright',
  'autumn-warm-light': 'fall_warm_light',
  'autumn-warm-mute': 'fall_warm_mute',
  'autumn-warm-deep': 'fall_warm_deep',
  'autumn-cool-bright': 'fall_cool_bright',
  'autumn-cool-light': 'fall_cool_light',
  'autumn-cool-mute': 'fall_cool_mute',
  'autumn-cool-deep': 'fall_cool_deep',
  'fall-warm-bright': 'fall_warm_bright',
  'fall-warm-light': 'fall_warm_light',
  'fall-warm-mute': 'fall_warm_mute',
  'fall-warm-deep': 'fall_warm_deep',
  'fall-cool-bright': 'fall_cool_bright',
  'fall-cool-light': 'fall_cool_light',
  'fall-cool-mute': 'fall_cool_mute',
  'fall-cool-deep': 'fall_cool_deep',

  'winter-warm-bright': 'winter_warm_bright',
  'winter-warm-light': 'winter_warm_light',
  'winter-warm-mute': 'winter_warm_mute',
  'winter-warm-deep': 'winter_warm_deep',
  'winter-cool-bright': 'winter_cool_bright',
  'winter-cool-light': 'winter_cool_light',
  'winter-cool-mute': 'winter_cool_mute',
  'winter-cool-deep': 'winter_cool_deep',
}

const TONE_ALIASES = {
  clear: 'bright',
  vivid: 'bright',
  muted: 'mute',
  soft: 'mute',
  dark: 'deep',
}

const SEASON_ALIASES = {
  autumn: 'fall',
}

const normalizeSeason = (season) => {
  const value = String(season || '').trim().toLowerCase()
  return SEASON_ALIASES[value] || value
}

const normalizeTone = (tone) => {
  const value = String(tone || '').trim().toLowerCase()
  return TONE_ALIASES[value] || value
}

const normalizeToneKey = (value) => {
  const raw = String(value || '').trim().toLowerCase()
  if (!raw) return null

  const parts = raw
    .replace(/_/g, '-')
    .replace(/\s+/g, '-')
    .split('-')
    .filter(Boolean)

  if (parts.length < 3) return null

  const [season, temperature, tone] = parts
  const key = `${normalizeSeason(season)}-${temperature}-${normalizeTone(tone)}`

  return TONE_IMAGE_FILE_MAP[key] ? key : null
}

const getToneKeyFromEnglishName = (englishName) => {
  const parts = String(englishName || '').trim().toLowerCase().split(/\s+/)
  if (parts.length < 3) return null

  const [season, temperature, tone] = parts
  return normalizeToneKey(`${season}-${temperature}-${tone}`)
}

export const getToneKeyFromPersonalColor = (personalColor) => {
  if (!personalColor) return null

  if (typeof personalColor === 'string') {
    return normalizeToneKey(personalColor)
  }

  const directCode = normalizeToneKey(
    personalColor.toneKey ||
      personalColor.tone_key ||
      personalColor.code ||
      personalColor.personal_color_code ||
      personalColor.type,
  )
  if (directCode) return directCode

  const englishNameKey = getToneKeyFromEnglishName(personalColor.english_name || personalColor.titleEn)
  if (englishNameKey) return englishNameKey

  const season = normalizeSeason(personalColor.season)
  const temperature = String(personalColor.temperature || personalColor.base_temperature || '').trim().toLowerCase()
  const tone = normalizeTone(personalColor.tone_code || personalColor.tone)

  if (!season || !temperature || !tone) return null
  return normalizeToneKey(`${season}-${temperature}-${tone}`)
}

export const getToneImageUrl = (personalColor) => {
  const toneKey = getToneKeyFromPersonalColor(personalColor)
  const fileName = TONE_IMAGE_FILE_MAP[toneKey]
  return fileName ? `/images/tones/${fileName}.png` : FALLBACK_TONE_IMAGE
}

export const getLatestDiagnosisToneImageUrl = (diagnosis) => {
  if (!diagnosis) return FALLBACK_TONE_IMAGE

  return getToneImageUrl(
    diagnosis.personal_color ||
      diagnosis.personal_color_code ||
      diagnosis.toneKey ||
      diagnosis.tone_key ||
      diagnosis.type,
  )
}
