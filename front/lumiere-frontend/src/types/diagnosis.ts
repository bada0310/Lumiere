export type Season = 'spring' | 'summer' | 'autumn' | 'fall' | 'winter'
export type Temperature = 'warm' | 'cool'
export type Tone = 'BRIGHT' | 'LIGHT' | 'MUTE' | 'DEEP' | 'bright' | 'light' | 'muted' | 'deep'
export type PaletteGroup = 'best' | 'neutral' | 'accent' | 'try' | 'worst'

export interface DiagnosisColorItem {
  name: string
  hex: string
  order: number
  group?: PaletteGroup
  description?: string
  usage?: string
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
  status: 'none' | 'queued' | 'running' | 'complete' | 'failed' | 'skipped'
  error_message: string
  order: number
  is_default: boolean
}

export interface DiagnosisMakeupColorGuide {
  base: {
    title: string
    description: string
    shadeRange: string[]
    chips: DiagnosisColorItem[]
    avoid: string[]
  }
  eye: {
    title: string
    description: string
    highlighter: DiagnosisColorItem[]
    base: DiagnosisColorItem[]
    shading: DiagnosisColorItem[]
    point: DiagnosisColorItem[]
    aegyosal: DiagnosisColorItem[]
    eyeliner: DiagnosisColorItem[]
    avoid: string[]
  }
  lip: {
    title: string
    description: string
    chips: DiagnosisColorItem[]
    avoid: string[]
  }
  blush: {
    title: string
    description: string
    chips: DiagnosisColorItem[]
    avoid: string[]
  }
}

export interface DiagnosisAiMakeover {
  status: 'none' | 'queued' | 'running' | 'partial' | 'complete' | 'failed' | 'skipped'
  styles: DiagnosisMakeoverStyle[]
  error: string
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
  ai_makeover: DiagnosisAiMakeover
  color_palettes: Record<PaletteGroup, DiagnosisColorItem[]>
  makeup_color_guide: DiagnosisMakeupColorGuide
  recommended_products: DiagnosisRecommendedProduct[]
  recommended_lenses: DiagnosisRecommendedLens[]
  style_guide: Record<string, unknown>
  uploaded_image_url: string | null
  processed_image_url: string | null
  generated_makeup_image_url: string | null
  makeup_generation_status: string
  is_primary: boolean
  is_demo: boolean
}
