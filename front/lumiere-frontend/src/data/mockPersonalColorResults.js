import { getToneImageUrl } from '@/data/toneImages'

const makeProfileImageUrl = (toneKey) => getToneImageUrl(toneKey)

const summerCoolLight = {
  id: 'mock-summer-cool-light',
  userId: 'dev-user',
  type: 'summer_cool_light',
  toneKey: 'summer_cool_light',
  titleKo: '여름 쿨 라이트',
  titleEn: 'Summer Cool Light',
  description: '맑고 부드러운 쿨톤 컬러가 당신의 매력을 가장 빛나게 해요.',
  confidence: 93,
  diagnosedAt: '2024.05.20',
  keywords: ['맑은 톤', '부드러운 대비', '쿨 핑크 베이스', '저채도', '라이트 톤'],
  profileImageUrl: makeProfileImageUrl('summer_cool_light'),
  skinAnalysis: {
    brightness: 65,
    saturation: 30,
    clarity: 85,
    contrast: 35,
    coolWarm: -65,
    softness: 78,
  },
  imageFeatures: [
    { label: '맑음', description: '깨끗하고 투명한 인상', icon: 'sparkle' },
    { label: '부드러움', description: '은은하고 부드러운 톤', icon: 'cloud' },
    { label: '세련됨', description: '차분하고 도시적인 분위기', icon: 'diamond' },
    { label: '우아함', description: '차분하고 우아한 무드', icon: 'flower' },
  ],
  representativeColors: [
    { name: '라이트 핑크', hex: '#F3B8C8' },
    { name: '라벤더 핑크', hex: '#D8B7DA' },
    { name: '쿨 로즈', hex: '#C989A4' },
    { name: '소프트 라일락', hex: '#C7C3E6' },
    { name: '블루 그레이', hex: '#A9B8C9' },
  ],
  palettes: {
    best: [
      { name: '로지 핑크', hex: '#EFA6B8', description: '얼굴빛을 맑게 살리는 메인 컬러' },
      { name: '쿨 핑크', hex: '#E7A4C2' },
      { name: '라벤더 핑크', hex: '#D8B7DA' },
      { name: '소프트 라일락', hex: '#C7C3E6' },
      { name: '페일 블루', hex: '#B8CBE8' },
    ],
    neutral: [
      { name: '쿨 베이지', hex: '#D8D1CE' },
      { name: '라이트 그레이', hex: '#C9CCD3' },
      { name: '블루 그레이', hex: '#A9B8C9' },
      { name: '소프트 네이비', hex: '#67748A' },
    ],
    accent: [
      { name: '모브 로즈', hex: '#B86F8A' },
      { name: '베리 핑크', hex: '#C15D82' },
      { name: '플럼 모브', hex: '#8D6A93' },
      { name: '더스티 블루', hex: '#6F83B7' },
    ],
    worst: [
      { name: '오렌지 코랄', hex: '#F09A5A' },
      { name: '브릭 오렌지', hex: '#D9784F' },
      { name: '머스타드', hex: '#D6B84A' },
      { name: '카키 올리브', hex: '#8B9462' },
    ],
  },
  makeupColorGuide: {
    base: {
      title: '밝은 핑크 베이지',
      description: '피부 톤에 자연스럽게 어우러지는 밝고 맑은 베이스를 선택하세요.',
      shadeRange: ['A00', 'N01', 'N02', 'A02'],
      chips: [
        { name: '페일 로지 베이지', hex: '#EED7D1' },
        { name: '뉴트럴 쿨 베이지', hex: '#DED3D2' },
        { name: '라이트 핑크 베이지', hex: '#F0D1D5' },
      ],
      avoid: ['노란기 강한 베이스', '너무 어두운 베이스', '채도가 높은 코랄 베이스'],
    },
    eye: {
      highlighter: [
        { name: '실버 핑크', hex: '#F3D7E5' },
        { name: '라일락 펄', hex: '#DCD4F3' },
        { name: '페일 샴페인 핑크', hex: '#F1DFDD' },
      ],
      base: [
        { name: '페일 핑크', hex: '#F4CAD5' },
        { name: '로지 베이지', hex: '#DAB6BA' },
        { name: '라이트 모브', hex: '#CBB1CE' },
      ],
      shading: [
        { name: '소프트 모브 브라운', hex: '#9B7C84' },
        { name: '쿨 브라운', hex: '#8A7477' },
        { name: '그레이시 브라운', hex: '#827A80' },
      ],
      point: [
        { name: '쿨 로즈', hex: '#C989A4' },
        { name: '플럼 모브', hex: '#8D6A93' },
        { name: '더스티 라벤더', hex: '#A9A1C9' },
      ],
      description: '눈두덩은 옅고 맑게, 음영은 회기 도는 모브 브라운으로 낮게 쌓아주세요.',
    },
    lip: {
      title: '맑은 쿨 핑크 립',
      description: '맑고 푸른 기가 도는 핑크 계열이 생기를 살려줘요.',
      chips: [
        { name: '로지 핑크', hex: '#EFA6B8' },
        { name: '쿨 핑크', hex: '#E7A4C2' },
        { name: '모브 핑크', hex: '#C889A8' },
        { name: '라벤더 핑크', hex: '#D8B7DA' },
        { name: '베리 핑크', hex: '#C15D82' },
        { name: '소프트 플럼', hex: '#9B6B8E' },
      ],
      avoid: ['오렌지 레드', '브릭 코랄', '강한 웜 브라운'],
    },
    blush: {
      title: '은은한 쿨 핑크 블러셔',
      description: '은은하고 부드러운 핑크 계열이 자연스럽게 혈색을 살려줍니다.',
      chips: [
        { name: '라이트 핑크', hex: '#F3B8C8' },
        { name: '쿨 로즈', hex: '#C989A4' },
        { name: '라벤더 핑크', hex: '#D8B7DA' },
        { name: '모브 핑크', hex: '#C889A8' },
        { name: '소프트 플럼', hex: '#9B6B8E' },
      ],
      avoid: ['오렌지 코랄', '브라운 베이지', '강한 피치 컬러'],
    },
  },
  styleGuide: {
    lens: [
      { name: '실버 그레이', hex: '#B7BDC8' },
      { name: '라이트 브라운 그레이', hex: '#A69B95' },
    ],
    hair: [
      { name: '애쉬 브라운', hex: '#7C6F6A' },
      { name: '쿨 다크 브라운', hex: '#4E4244' },
      { name: '소프트 블랙', hex: '#2E2D32' },
    ],
    accessory: ['실버', '화이트 골드', '쿨톤 진주'],
    fashion: [
      { name: '라벤더', hex: '#C7C3E6' },
      { name: '소프트 블루', hex: '#B8CBE8' },
      { name: '쿨 핑크', hex: '#E7A4C2' },
      { name: '라이트 그레이', hex: '#C9CCD3' },
    ],
  },
  makeoverImages: [
    {
      id: 'natural',
      styleName: '내추럴',
      description: '자연스럽고 깨끗한 데일리 톤',
      imageUrl: '',
    },
    {
      id: 'daily',
      styleName: '데일리',
      description: '생기 있는 쿨 핑크 톤',
      imageUrl: '',
    },
    {
      id: 'romantic',
      styleName: '로맨틱',
      description: '사랑스러운 핑크 룩',
      imageUrl: '',
    },
  ],
  tip: '노란기와 채도가 강한 컬러는 얼굴이 탁해 보일 수 있어요. 맑고 부드러운 쿨 핑크, 라벤더, 소프트 블루 계열을 선택하면 피부가 더 깨끗해 보여요.',
}

const makeVariant = ({
  id,
  type,
  toneKey,
  titleKo,
  titleEn,
  description,
  confidence,
  keywords,
  skinAnalysis,
  best,
  neutral,
  accent,
  worst,
  tip,
}) => ({
  ...summerCoolLight,
  id,
  type: type || toneKey,
  toneKey,
  titleKo,
  titleEn,
  description,
  confidence,
  diagnosedAt: '2024.05.20',
  keywords,
  profileImageUrl: makeProfileImageUrl(toneKey),
  skinAnalysis,
  representativeColors: best.slice(0, 5),
  palettes: { best, neutral, accent, worst },
  tip,
})

export const MOCK_PERSONAL_COLOR_RESULTS = [
  summerCoolLight,
  makeVariant({
    id: 'mock-summer-cool-mute',
    toneKey: 'summer_cool_mute',
    titleKo: '여름 쿨 뮤트',
    titleEn: 'Summer Cool Mute',
    description: '부드럽고 차분한 쿨 컬러가 분위기를 가장 안정적으로 살려줘요.',
    confidence: 89,
    keywords: ['소프트 톤', '회기 있는 컬러', '차분함', '쿨 베이스'],
    skinAnalysis: { brightness: 58, saturation: 26, clarity: 68, contrast: 32, coolWarm: -58, softness: 88 },
    best: [
      { name: '더스티 핑크', hex: '#D8A5B2' },
      { name: '모브 베이지', hex: '#BFA5AD' },
      { name: '라벤더 그레이', hex: '#BFB8D4' },
      { name: '스모키 블루', hex: '#8EA1B7' },
    ],
    neutral: [
      { name: '쿨 그레이지', hex: '#C8C1BF' },
      { name: '소프트 그레이', hex: '#B7BAC0' },
      { name: '차콜 네이비', hex: '#5A6271' },
    ],
    accent: [
      { name: '뮤트 로즈', hex: '#AF6F80' },
      { name: '플럼 브라운', hex: '#795D68' },
      { name: '더스티 퍼플', hex: '#837197' },
    ],
    worst: [
      { name: '네온 핑크', hex: '#FF4AA2' },
      { name: '선명한 오렌지', hex: '#F48332' },
      { name: '골든 옐로', hex: '#E7B72F' },
    ],
    tip: '선명도보다 부드러운 회기와 낮은 채도가 잘 어울려요. 과하게 쨍한 색은 얼굴선을 거칠게 보이게 할 수 있어요.',
  }),
  makeVariant({
    id: 'mock-winter-cool-clear',
    type: 'winter_cool_clear',
    toneKey: 'winter_cool_bright',
    titleKo: '겨울 쿨 클리어',
    titleEn: 'Winter Cool Clear',
    description: '선명하고 투명한 쿨 컬러가 또렷한 인상을 만들어줘요.',
    confidence: 91,
    keywords: ['선명함', '높은 대비', '클리어 톤', '쿨 레드'],
    skinAnalysis: { brightness: 54, saturation: 62, clarity: 90, contrast: 82, coolWarm: -72, softness: 28 },
    best: [
      { name: '퓨어 화이트', hex: '#F8F8F7' },
      { name: '쿨 레드', hex: '#C83255' },
      { name: '푸시아 핑크', hex: '#D6428D' },
      { name: '로열 블루', hex: '#315CA8' },
      { name: '블랙', hex: '#1D1D24' },
    ],
    neutral: [
      { name: '쿨 그레이', hex: '#B6BCC8' },
      { name: '네이비', hex: '#273A64' },
      { name: '차콜', hex: '#34343B' },
    ],
    accent: [
      { name: '체리 핑크', hex: '#CE3E68' },
      { name: '바이올렛', hex: '#6847A3' },
      { name: '아이스 블루', hex: '#B9D8F2' },
    ],
    worst: [
      { name: '머스타드', hex: '#D6B84A' },
      { name: '카멜', hex: '#B77946' },
      { name: '살몬 코랄', hex: '#EF8C72' },
    ],
    tip: '탁한 중간색보다 맑고 또렷한 색을 선택하세요. 대비가 살아야 얼굴 윤곽이 선명해 보여요.',
  }),
  makeVariant({
    id: 'mock-spring-warm-light',
    toneKey: 'spring_warm_light',
    titleKo: '봄 웜 라이트',
    titleEn: 'Spring Warm Light',
    description: '밝고 생기 있는 웜 컬러가 얼굴을 화사하게 밝혀줘요.',
    confidence: 87,
    keywords: ['화사함', '웜 베이스', '라이트 톤', '맑은 코랄'],
    skinAnalysis: { brightness: 76, saturation: 48, clarity: 82, contrast: 38, coolWarm: 62, softness: 61 },
    best: [
      { name: '피치 핑크', hex: '#F5B6A3' },
      { name: '라이트 코랄', hex: '#F39B86' },
      { name: '크림 아이보리', hex: '#F6E5C5' },
      { name: '애플 그린', hex: '#B9D88D' },
      { name: '스카이 민트', hex: '#A7DCD0' },
    ],
    neutral: [
      { name: '웜 아이보리', hex: '#EFE0C6' },
      { name: '라이트 베이지', hex: '#E5CFB3' },
      { name: '허니 브라운', hex: '#A77852' },
    ],
    accent: [
      { name: '살몬 코랄', hex: '#F08575' },
      { name: '멜론', hex: '#F2C46B' },
      { name: '클리어 민트', hex: '#7FCBBE' },
    ],
    worst: [
      { name: '블루 그레이', hex: '#8795A8' },
      { name: '플럼', hex: '#7B4A74' },
      { name: '차콜', hex: '#414047' },
    ],
    tip: '밝고 따뜻한 코랄, 피치, 아이보리 계열이 잘 맞아요. 차갑고 탁한 색은 생기를 줄일 수 있어요.',
  }),
  makeVariant({
    id: 'mock-autumn-warm-deep',
    toneKey: 'autumn_warm_deep',
    titleKo: '가을 웜 딥',
    titleEn: 'Autumn Warm Deep',
    description: '깊고 고급스러운 웜 컬러가 분위기를 또렷하게 잡아줘요.',
    confidence: 90,
    keywords: ['딥 톤', '웜 브라운', '고급스러움', '낮은 명도'],
    skinAnalysis: { brightness: 42, saturation: 58, clarity: 52, contrast: 76, coolWarm: 74, softness: 42 },
    best: [
      { name: '딥 브릭', hex: '#9B4F3E' },
      { name: '테라코타', hex: '#B76343' },
      { name: '올리브 카키', hex: '#697349' },
      { name: '초콜릿 브라운', hex: '#513329' },
      { name: '웜 버건디', hex: '#6E2E35' },
    ],
    neutral: [
      { name: '카멜', hex: '#B77A48' },
      { name: '웜 베이지', hex: '#C8A982' },
      { name: '에스프레소', hex: '#3F2A23' },
    ],
    accent: [
      { name: '머스터드', hex: '#C89C33' },
      { name: '러스티 레드', hex: '#95453B' },
      { name: '포레스트 그린', hex: '#3F5D46' },
    ],
    worst: [
      { name: '아이스 핑크', hex: '#F4CDE0' },
      { name: '라벤더', hex: '#C7C3E6' },
      { name: '실버 블루', hex: '#B8CBE8' },
    ],
    tip: '깊고 따뜻한 브라운, 브릭, 올리브 계열이 잘 맞아요. 너무 밝고 차가운 파스텔은 얼굴을 떠 보이게 할 수 있어요.',
  }),
]

export const DEFAULT_MOCK_TONE_KEY = 'summer_cool_light'

export const isMockPersonalColorResultKey = (toneKey) => {
  const normalizedKey = String(toneKey || '').replace(/-/g, '_')
  return MOCK_PERSONAL_COLOR_RESULTS.some((result) => result.toneKey === normalizedKey || result.type === normalizedKey)
}

export const getMockPersonalColorResult = (toneKey = DEFAULT_MOCK_TONE_KEY) => {
  const normalizedKey = String(toneKey || DEFAULT_MOCK_TONE_KEY).replace(/-/g, '_')
  return (
    MOCK_PERSONAL_COLOR_RESULTS.find((result) => result.toneKey === normalizedKey || result.type === normalizedKey) ||
    MOCK_PERSONAL_COLOR_RESULTS[0]
  )
}
