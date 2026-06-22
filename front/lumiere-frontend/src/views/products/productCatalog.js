const NOISE_PATTERNS = [
  /\[[^\]]*\]/g,
  /\([^)]*출고[^)]*\)/g,
  /\b\d+(?:\.\d+)?\s*(?:ml|g)\b/gi,
  /\b\d+\s*(?:개입|개|ml|g|매|호)\b/gi,
  /[xX]\s*\d+\s*개?/g,
  /\bBNS\b/gi,
  /\b정품\b/g,
  /\b무료배송\b/g,
]

const GROUP_STOPWORDS = new Set([
  '화장품',
  '정품',
  '기획',
  '세트',
  '단품',
  '본품',
  '리필',
  '증정',
  '쿨톤',
  '웜톤',
  '봄웜',
  '여름쿨',
  '가을웜',
  '겨울쿨',
  '봄',
  '여름',
  '가을',
  '겨울',
])

export const compactSpaces = (value) => {
  return String(value || '').replace(/\s+/g, ' ').trim()
}

export const normalizeCatalogText = (value) => {
  return String(value || '').toLowerCase().replace(/\s/g, '')
}

export const cleanProductName = (value, brand = '') => {
  let text = String(value || '')
    .replace(/<.*?>/g, '')
    .replace(/[’]/g, "'")
    .replace(/[“”]/g, '"')

  if (brand && !['브랜드 미상', 'UNKNOWN'].includes(brand)) {
    text = text.replace(new RegExp(escapeRegExp(brand), 'gi'), ' ')
  }

  NOISE_PATTERNS.forEach((pattern) => {
    text = text.replace(pattern, ' ')
  })

  return compactSpaces(text.replace(/[+/_]/g, ' '))
}

export const extractOptionParts = (cleanedName) => {
  const patterns = [
    /\b(?:NO|No|no)\.?\s*(?<code>\d{1,3})\s*(?<shade>[가-힣A-Za-z0-9' -]{1,28})/,
    /\b(?<code>[A-Z]{1,4}\s?\d{2,4})\s*(?<shade>[가-힣A-Za-z0-9' -]{1,28})/,
    /\b(?<code>\d{1,3})\s*호\s*(?<shade>[가-힣A-Za-z0-9' -]{1,28})/,
    /(?<shade>[가-힣A-Za-z0-9' -]{1,24})\s*(?<code>\d{1,3})\s*호/,
  ]

  for (const pattern of patterns) {
    const match = cleanedName.match(pattern)
    if (!match?.groups) continue

    const code = compactSpaces(match.groups.code || '')
    const shade = compactSpaces(match.groups.shade || '')
      .replace(/(?:쿨톤|웜톤|기준|화장품).*$/g, '')
      .replace(/[xX]\s*\d+\s*개?.*$/g, '')
      .trim()

    const optionName = compactSpaces(`${code} ${shade}`) || code || shade
    const groupName = compactSpaces(
      `${cleanedName.slice(0, match.index)} ${cleanedName.slice(match.index + match[0].length)}`,
    )

    return {
      optionCode: code,
      optionShade: shade,
      optionName,
      groupName: cleanGroupDisplay(groupName || cleanedName),
    }
  }

  return {
    optionCode: '',
    optionShade: '',
    optionName: cleanedName,
    groupName: cleanGroupDisplay(cleanedName),
  }
}

export const getGroupTokenKey = (value) => {
  const tokens = String(value || '')
    .toLowerCase()
    .match(/[가-힣A-Za-z0-9]+/g)

  if (!tokens) return ''

  return [...new Set(tokens)]
    .filter((token) => !GROUP_STOPWORDS.has(token))
    .filter((token) => !/^\d+$/.test(token))
    .sort()
    .join('-')
}

export const makeProductGroups = (products) => {
  const buckets = new Map()

  products.forEach((product) => {
    const cleanedName = cleanProductName(product.name, product.brand)
    const optionParts = extractOptionParts(cleanedName)
    const groupName = optionParts.groupName || product.name
    const tokenKey = getGroupTokenKey(groupName || product.texture || product.name)
    const groupKey = [
      product.brand,
      product.categoryKey,
      tokenKey || normalizeCatalogText(product.name),
    ].join('|')

    const option = {
      ...product,
      optionCode: optionParts.optionCode,
      optionShade: optionParts.optionShade,
      option: optionParts.optionName || product.option,
      groupName,
      groupKey,
    }

    if (!buckets.has(groupKey)) {
      buckets.set(groupKey, {
        id: groupKey,
        groupKey,
        brand: product.brand,
        name: groupName || product.name,
        productName: groupName || product.name,
        categoryKey: product.categoryKey,
        categoryLabel: product.categoryLabel,
        texture: product.texture,
        finish: product.finish,
        filterKeys: new Set(product.filterKeys || []),
        options: [],
        liked: false,
      })
    }

    const group = buckets.get(groupKey)
    group.options.push(option)
    group.filterKeys = new Set([...group.filterKeys, ...(product.filterKeys || [])])
  })

  return [...buckets.values()].map((group) => {
    const options = group.options.sort((a, b) => {
      return String(a.option || '').localeCompare(String(b.option || ''), 'ko')
    })
    const representative = [...options].sort((a, b) => b.score - a.score)[0]
    const colors = [...new Set(options.map((option) => option.hex).filter(Boolean))].slice(0, 8)
    const tags = [...new Set(options.flatMap((option) => option.tags || []))].slice(0, 6)

    return {
      ...group,
      ...representative,
      id: group.groupKey,
      optionId: representative.id,
      name: group.productName,
      option: representative.option,
      optionCount: options.length,
      options,
      colors: colors.length ? colors : representative.colors,
      tags,
      filterKeys: [...group.filterKeys],
      score: Math.round(
        options.reduce((sum, option) => sum + option.score, 0) / Math.max(options.length, 1),
      ),
      bestScore: representative.score,
      popularityScore: options.reduce((sum, option) => sum + option.popularityScore, 0),
      desc: `${group.categoryLabel} ${group.texture || ''} 제품의 ${options.length}개 옵션을 색상 기준으로 묶었어요.`,
      representative,
    }
  })
}

export const makeDetailPayload = (group, option = group?.representative) => {
  if (!group || !option) return null

  return {
    ...option,
    groupKey: group.groupKey,
    groupName: group.productName || group.name,
    groupOptions: group.options || [],
    optionCount: group.optionCount || group.options?.length || 1,
  }
}

const cleanGroupDisplay = (value) => {
  return compactSpaces(
    String(value || '')
      .replace(/(?:쿨톤|웜톤|봄웜|여름쿨|가을웜|겨울쿨)/g, ' ')
      .replace(/\s*[-_/]\s*$/g, ''),
  )
}

const escapeRegExp = (value) => {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
