import {
  ensureReadableOnWhiteText,
  PERSONAL_COLOR_THEME,
} from '@/themes/personalColorTheme'

export type Season = 'spring' | 'summer' | 'autumn' | 'winter'
export type Temperature = 'warm' | 'cool'
export type Tone = 'bright' | 'light' | 'muted' | 'deep'

export interface LoungeTheme {
  key: `${Season}-${Temperature}-${Tone}`
  season: Season
  temperature: Temperature
  tone: Tone
  koreanName: string
  color: string
  description: string
  members: number
}

export const SEASON_LABELS: Record<Season, string> = {
  spring: '봄',
  summer: '여름',
  autumn: '가을',
  winter: '겨울',
}

export const TEMPERATURE_LABELS: Record<Temperature, string> = {
  warm: '웜',
  cool: '쿨',
}

export const TONE_LABELS: Record<Tone, string> = {
  bright: '브라이트',
  light: '라이트',
  muted: '뮤트',
  deep: '딥',
}

const DESCRIPTION_BY_SEASON: Record<Season, string> = {
  spring: '생기 있고 맑은 컬러가 얼굴을 화사하게 밝혀줘요.',
  summer: '맑고 부드러운 쿨톤 컬러가 잘 어울리는 톤이에요.',
  autumn: '차분하고 깊이 있는 컬러가 분위기를 살려줘요.',
  winter: '선명하고 또렷한 컬러가 인상을 깔끔하게 잡아줘요.',
}

const SEASONS: Season[] = ['spring', 'summer', 'autumn', 'winter']
const TEMPERATURES: Temperature[] = ['warm', 'cool']
const TONES: Tone[] = ['bright', 'light', 'muted', 'deep']

export const LOUNGE_THEMES: LoungeTheme[] = SEASONS.flatMap((season, seasonIndex) =>
  TEMPERATURES.flatMap((temperature, temperatureIndex) =>
    TONES.map((tone, toneIndex) => {
      const key = `${season}-${temperature}-${tone}` as LoungeTheme['key']
      return {
        key,
        season,
        temperature,
        tone,
        koreanName: `${SEASON_LABELS[season]} ${TEMPERATURE_LABELS[temperature]} ${TONE_LABELS[tone]}`,
        color: ensureReadableOnWhiteText(PERSONAL_COLOR_THEME[key]),
        description: DESCRIPTION_BY_SEASON[season],
        members: 2100 + seasonIndex * 520 + temperatureIndex * 180 + toneIndex * 47,
      }
    }),
  ),
)

export const DEFAULT_LOUNGE_KEY: LoungeTheme['key'] = 'summer-cool-light'

export const getLoungeThemeByKey = (key?: string | null) =>
  LOUNGE_THEMES.find((theme) => theme.key === key) ||
  LOUNGE_THEMES.find((theme) => theme.key === DEFAULT_LOUNGE_KEY)!

export const getLoungeThemeFromPersonalColor = (personalColor?: {
  season?: string | null
  temperature?: string | null
  tone?: string | null
} | null) => {
  const key = `${personalColor?.season || ''}-${personalColor?.temperature || ''}-${personalColor?.tone || ''}`
  return getLoungeThemeByKey(key)
}
