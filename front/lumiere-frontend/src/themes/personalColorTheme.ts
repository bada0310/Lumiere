export type PersonalColorSeason = 'spring' | 'summer' | 'autumn' | 'winter'
export type PersonalColorTemperature = 'warm' | 'cool'
export type PersonalColorTone = 'bright' | 'light' | 'muted' | 'deep'

export type PersonalColorProfile = {
  season?: string | null
  temperature?: string | null
  tone?: string | null
}

export type PersonalColorThemeKey =
  `${PersonalColorSeason}-${PersonalColorTemperature}-${PersonalColorTone}`

export const DEFAULT_LOUNGE_COLOR = '#963D50'

export const PERSONAL_COLOR_THEME: Record<PersonalColorThemeKey, string> = {
  'spring-warm-bright': '#C85F45',
  'spring-warm-light': '#A86F63',
  'spring-warm-muted': '#95695E',
  'spring-warm-deep': '#75483E',

  'spring-cool-bright': '#C94F78',
  'spring-cool-light': '#A76D85',
  'spring-cool-muted': '#8B6677',
  'spring-cool-deep': '#704255',

  'summer-warm-bright': '#BF6872',
  'summer-warm-light': '#A47878',
  'summer-warm-muted': '#896A70',
  'summer-warm-deep': '#704F5A',

  'summer-cool-bright': '#4E82C2',
  'summer-cool-light': '#657CAF',
  'summer-cool-muted': '#586D8E',
  'summer-cool-deep': '#40587A',

  'autumn-warm-bright': '#B85D2D',
  'autumn-warm-light': '#98704F',
  'autumn-warm-muted': '#80614F',
  'autumn-warm-deep': '#65432F',

  'autumn-cool-bright': '#A84C63',
  'autumn-cool-light': '#866473',
  'autumn-cool-muted': '#725965',
  'autumn-cool-deep': '#523B45',

  'winter-warm-bright': '#B93D43',
  'winter-warm-light': '#98706E',
  'winter-warm-muted': '#805F61',
  'winter-warm-deep': '#573A3D',

  'winter-cool-bright': '#2E67BD',
  'winter-cool-light': '#6075AD',
  'winter-cool-muted': '#51658D',
  'winter-cool-deep': '#294475',
}

const VALID_SEASONS = new Set(['spring', 'summer', 'autumn', 'winter'])
const VALID_TEMPERATURES = new Set(['warm', 'cool'])
const VALID_TONES = new Set(['bright', 'light', 'muted', 'deep'])
const MIN_WHITE_TEXT_CONTRAST = 4.5

const normalizeTone = (value: string | null | undefined) => {
  const normalized = String(value || '').trim().toLowerCase()
  if (normalized === 'mute') return 'muted'
  return normalized
}

export const getPersonalColorThemeKey = (
  personalColor?: PersonalColorProfile | null,
): PersonalColorThemeKey | null => {
  const season = String(personalColor?.season || '').trim().toLowerCase()
  const temperature = String(personalColor?.temperature || '').trim().toLowerCase()
  const tone = normalizeTone(personalColor?.tone)

  if (
    !VALID_SEASONS.has(season) ||
    !VALID_TEMPERATURES.has(temperature) ||
    !VALID_TONES.has(tone)
  ) {
    return null
  }

  return `${season}-${temperature}-${tone}` as PersonalColorThemeKey
}

const hexToRgb = (hex: string) => {
  const normalized = hex.replace('#', '')
  return {
    r: Number.parseInt(normalized.slice(0, 2), 16),
    g: Number.parseInt(normalized.slice(2, 4), 16),
    b: Number.parseInt(normalized.slice(4, 6), 16),
  }
}

const rgbToHex = ({ r, g, b }: { r: number; g: number; b: number }) =>
  `#${[r, g, b]
    .map((channel) => Math.max(0, Math.min(255, Math.round(channel))))
    .map((channel) => channel.toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase()}`

const relativeLuminance = ({ r, g, b }: { r: number; g: number; b: number }) => {
  const channels = [r, g, b].map((channel) => {
    const value = channel / 255
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
  })

  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722
}

const contrastWithWhite = (hex: string) => {
  const colorLuminance = relativeLuminance(hexToRgb(hex))
  return 1.05 / (colorLuminance + 0.05)
}

const darkenColor = (hex: string, amount = 0.08) => {
  const rgb = hexToRgb(hex)
  return rgbToHex({
    r: rgb.r * (1 - amount),
    g: rgb.g * (1 - amount),
    b: rgb.b * (1 - amount),
  })
}

export const ensureReadableOnWhiteText = (hex: string) => {
  let readableColor = hex
  let guard = 0

  while (contrastWithWhite(readableColor) < MIN_WHITE_TEXT_CONTRAST && guard < 20) {
    readableColor = darkenColor(readableColor)
    guard += 1
  }

  return readableColor
}

export const getPersonalColorLoungeColor = (
  personalColor?: PersonalColorProfile | null,
) => {
  const themeKey = getPersonalColorThemeKey(personalColor)
  const themeColor = themeKey ? PERSONAL_COLOR_THEME[themeKey] : DEFAULT_LOUNGE_COLOR
  return ensureReadableOnWhiteText(themeColor || DEFAULT_LOUNGE_COLOR)
}
