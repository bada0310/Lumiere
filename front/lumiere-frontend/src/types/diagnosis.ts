export type Season = 'spring' | 'summer' | 'autumn' | 'fall' | 'winter'
export type Temperature = 'warm' | 'cool'
export type Tone = 'BRIGHT' | 'LIGHT' | 'MUTE' | 'DEEP' | 'bright' | 'light' | 'muted' | 'deep'
export type PaletteGroup = 'best' | 'neutral' | 'accent' | 'try' | 'worst'

export interface DiagnosisColorItem {
  name: string
  hex: string
  order: number
  group?: PaletteGroup
}

export interface DiagnosisImageFeature {
  key: string
  title: string
  description: string
  icon: string
}

export interface DiagnosisMakeoverStyle {
  key: string
  name: string
  description: string
  image: string | null
  image_url: string | null
  order: number
  is_default: boolean
}

export interface DiagnosisRecommendedProduct {
  category: string
  category_name: string
  tone_label: string
  brand: string
  product_name: string
  shade: string
  description: string
  image: string | null
  image_url: string | null
  product_url: string | null
  order: number
}

export interface DiagnosisRecommendedLens {
  rank: string
  brand: string
  product_name: string
  color: string
  description: string
  image: string | null
  image_url: string | null
  order: number
}

export interface DiagnosisResult {
  id: number
  personal_color_code: string
  korean_name: string
  english_name: string
  confidence: number
  confidence_score: number
  diagnosed_at: string
  summary: string
  keywords: string[]
  image_features: DiagnosisImageFeature[]
  skin_metrics: Record<string, number>
  radar_chart: Record<string, number>
  representative_colors: DiagnosisColorItem[]
  makeover_styles: DiagnosisMakeoverStyle[]
  color_palettes: Record<PaletteGroup, DiagnosisColorItem[]>
  recommended_products: DiagnosisRecommendedProduct[]
  recommended_lenses: DiagnosisRecommendedLens[]
  style_guide: Record<string, unknown>
  uploaded_image_url: string | null
  generated_makeup_image_url: string | null
  is_demo: boolean
}
