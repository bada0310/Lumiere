from copy import deepcopy

from diagnosis.domain.tone_keys import CANONICAL_TONE_KEYS, build_tone_name, split_tone_key


ROLE_KEYS = ('highlighter', 'base', 'shading', 'point')

SEASON_META = {
    'spring': {
        'ko': '봄',
        'mood': '맑고 생기 있는',
        'profile': '밝고 산뜻한 인상을 살릴 때 조화가 좋습니다.',
        'style': ['fresh', 'clear', 'lively'],
    },
    'summer': {
        'ko': '여름',
        'mood': '부드럽고 차분한',
        'profile': '강한 대비보다 은은한 균형에서 얼굴선이 편안해 보입니다.',
        'style': ['soft', 'calm', 'elegant'],
    },
    'autumn': {
        'ko': '가을',
        'mood': '깊고 차분한',
        'profile': '자연스럽고 밀도 있는 색에서 분위기가 안정됩니다.',
        'style': ['natural', 'rich', 'grounded'],
    },
    'winter': {
        'ko': '겨울',
        'mood': '선명하고 또렷한',
        'profile': '명확한 대비와 정돈된 색감에서 인상이 또렷해집니다.',
        'style': ['defined', 'modern', 'crisp'],
    },
}

TEMPERATURE_META = {
    'warm': {
        'ko': '웜',
        'axis': 'warm',
        'undertone': '노란기, 복숭아기, 골드 베이스가 자연스럽게 연결되는 웜 경향',
        'base_tone': 'yellow_or_neutral_base',
        'base_guide': '붉거나 회색기 강한 베이스보다 옐로우 또는 뉴트럴 베이스를 얇게 사용합니다.',
        'avoid_base': ['pink gray base', 'blue pearl base'],
        'lens': [('Honey Brown', '허니 브라운', '#8C6239'), ('Olive Brown', '올리브 브라운', '#6F6A3F')],
        'hair': [('Warm Brown', '웜 브라운', '#6B3F2A'), ('Chestnut', '체스트넛', '#8A4B2D')],
        'accessory': ['골드 또는 샴페인 골드 금속', '아이보리 진주', '따뜻한 베이지 가죽'],
        'hues': ['peach', 'coral', 'apricot', 'camel', 'olive'],
    },
    'cool': {
        'ko': '쿨',
        'axis': 'cool',
        'undertone': '붉은기, 핑크기, 블루 베이스가 자연스럽게 연결되는 쿨 경향',
        'base_tone': 'pink_or_neutral_base',
        'base_guide': '노란기가 강한 베이스보다 핑크 또는 뉴트럴 베이스를 얇게 사용합니다.',
        'avoid_base': ['orange beige base', 'yellow gold base'],
        'lens': [('Soft Gray', '소프트 그레이', '#7C828C'), ('Rose Brown', '로즈 브라운', '#7B565F')],
        'hair': [('Ash Brown', '애쉬 브라운', '#5F5656'), ('Cool Black', '쿨 블랙', '#202229')],
        'accessory': ['실버 또는 화이트 골드 금속', '화이트 진주', '차가운 그레이 가죽'],
        'hues': ['pink', 'rose', 'mauve', 'berry', 'blue'],
    },
}

TONE_META = {
    'bright': {
        'ko': '브라이트',
        'brightness': 'medium_high',
        'chroma': 'high',
        'contrast': 'medium_high',
        'intensity': 'clear',
        'summary': '맑고 선명한 색이 얼굴의 생기와 이목구비 대비를 살립니다.',
        'keywords': ['clear', 'bright', 'vivid'],
        'avoid': '탁하거나 회색기가 많은 색은 인상이 흐려질 수 있습니다.',
    },
    'light': {
        'ko': '라이트',
        'brightness': 'high',
        'chroma': 'low_to_medium',
        'contrast': 'low',
        'intensity': 'airy',
        'summary': '밝고 가벼운 색이 피부를 맑고 투명하게 보이게 합니다.',
        'keywords': ['light', 'airy', 'delicate'],
        'avoid': '무겁고 어두운 색은 얼굴에 그림자가 질 수 있습니다.',
    },
    'mute': {
        'ko': '뮤트',
        'brightness': 'medium',
        'chroma': 'low_to_medium',
        'contrast': 'low',
        'intensity': 'soft',
        'summary': '부드럽고 낮은 채도의 색이 자연스러운 조화를 만듭니다.',
        'keywords': ['muted', 'soft', 'calm'],
        'avoid': '형광기와 고채도 색은 얼굴색과 분리되어 보일 수 있습니다.',
    },
    'deep': {
        'ko': '딥',
        'brightness': 'low_to_medium',
        'chroma': 'medium_high',
        'contrast': 'high',
        'intensity': 'rich',
        'summary': '깊이감 있는 색과 또렷한 음영이 인상을 안정적으로 잡아줍니다.',
        'keywords': ['deep', 'rich', 'defined'],
        'avoid': '너무 옅고 흐린 색은 얼굴의 윤곽을 약하게 만들 수 있습니다.',
    },
}


def _chip(name, name_ko, hex_value, usage, description):
    return {
        'name': name,
        'nameKo': name_ko,
        'hex': hex_value,
        'usage': usage,
        'description': description,
    }


def _avoid(name, name_ko, hex_value, reason):
    return {
        'name': name,
        'nameKo': name_ko,
        'hex': hex_value,
        'usage': 'avoid',
        'reason': reason,
    }


BASE_SWATCHES = {
    'warm': {
        'bright': {
            'best': [
                _chip('Clear Coral', '클리어 코랄', '#FF6F61', 'lip_cheek', '맑은 코랄기가 생기와 혈색을 선명하게 살립니다.'),
                _chip('Fresh Apricot', '프레시 애프리콧', '#FFA26B', 'lip', '가벼운 오렌지 피치가 입술에 활기를 줍니다.'),
                _chip('Sunlit Yellow', '선릿 옐로', '#F7D35C', 'fashion', '따뜻하고 밝은 노란빛이 얼굴 주변을 환하게 합니다.'),
                _chip('Green Apple', '그린 애플', '#8CCB5E', 'eye_base', '맑은 연두기가 브라이트 타입의 경쾌함과 잘 맞습니다.'),
            ],
            'neutral': [
                _chip('Warm Ivory', '웜 아이보리', '#F7E4C2', 'base', '노란기가 은은한 밝은 베이스 컬러입니다.'),
                _chip('Cream Pearl', '크림 펄', '#FBEEDB', 'eye_highlighter', '눈 앞머리와 하이라이트에 쓰기 좋은 크림 톤입니다.'),
            ],
            'accent': [
                _chip('Turquoise Mint', '터쿼이즈 민트', '#34C6B4', 'eye_point', '맑은 포인트 컬러로 눈매를 산뜻하게 만듭니다.'),
                _chip('Poppy Red', '파피 레드', '#F04444', 'lip', '명확한 포인트 립이 브라이트한 인상을 강화합니다.'),
            ],
            'try': [
                _chip('Salmon Pink', '살몬 핑크', '#FF8D8D', 'try', '코랄과 핑크 사이의 안전한 시도 컬러입니다.'),
                _chip('Fresh Peach', '프레시 피치', '#FFC38B', 'try', '가벼운 피치 톤으로 데일리 활용도가 높습니다.'),
            ],
            'worst': [
                _avoid('Blue Gray', '블루 그레이', '#73849C', '회색기와 차가운 기운이 생기를 낮출 수 있습니다.'),
                _avoid('Dusty Plum', '더스티 플럼', '#76566C', '탁한 보랏빛이 얼굴을 무겁게 보이게 할 수 있습니다.'),
                _avoid('Blackened Navy', '블랙 네이비', '#111827', '지나치게 어두워 밝은 웜 브라이트의 경쾌함을 누릅니다.'),
            ],
        },
        'light': {
            'best': [
                _chip('Peach Pink', '피치 핑크', '#F8B7A7', 'lip_cheek', '밝은 피치 핑크가 피부를 부드럽게 밝혀줍니다.'),
                _chip('Apricot Cream', '애프리콧 크림', '#FFD1A6', 'lip', '연한 살구빛이 입술에 자연스러운 온기를 더합니다.'),
                _chip('Butter Yellow', '버터 옐로', '#F6E6A8', 'fashion', '가볍고 따뜻한 노랑이 라이트 톤의 투명감과 맞습니다.'),
                _chip('Light Camel', '라이트 카멜', '#D9B586', 'eye_base', '옅은 카멜이 눈가에 따뜻한 깊이를 줍니다.'),
            ],
            'neutral': [
                _chip('Milky Ivory', '밀키 아이보리', '#FAEBD2', 'base', '밝고 부드러운 베이스 컬러입니다.'),
                _chip('Champagne Pearl', '샴페인 펄', '#F4DFC1', 'eye_highlighter', '과하지 않은 샴페인 빛으로 눈가를 밝힙니다.'),
            ],
            'accent': [
                _chip('Light Melon', '라이트 멜론', '#F5C98A', 'eye_point', '연한 멜론빛이 산뜻한 포인트가 됩니다.'),
                _chip('Sweet Coral', '스위트 코랄', '#F58F82', 'lip', '밝은 코랄 립이 생기를 보완합니다.'),
            ],
            'try': [
                _chip('Cream Peach', '크림 피치', '#FAD2BE', 'try', '채도를 낮춘 피치로 안정적인 시도가 가능합니다.'),
                _chip('Pale Apricot', '페일 애프리콧', '#FFE0B8', 'try', '밝은 피부 표현과 잘 이어지는 컬러입니다.'),
            ],
            'worst': [
                _avoid('Charcoal', '차콜', '#34343A', '명도가 너무 낮아 얼굴을 무겁게 만들 수 있습니다.'),
                _avoid('Burgundy', '버건디', '#6F1D32', '깊고 차가운 붉은색은 라이트 톤에 부담스럽습니다.'),
                _avoid('Neon Orange', '네온 오렌지', '#FF6A00', '채도가 과해 얼굴색과 분리될 수 있습니다.'),
            ],
        },
        'mute': {
            'best': [
                _chip('Dusty Peach', '더스티 피치', '#D49A82', 'lip_cheek', '탁도를 머금은 피치가 차분한 혈색을 줍니다.'),
                _chip('Soft Terracotta', '소프트 테라코타', '#B87458', 'lip', '부드러운 흙빛 코랄이 입술을 자연스럽게 잡아줍니다.'),
                _chip('Sage', '세이지', '#9AA77B', 'fashion', '저채도 그린이 웜 뮤트의 자연스러운 분위기와 맞습니다.'),
                _chip('Warm Taupe', '웜 토프', '#9A7A67', 'eye_base', '부드러운 브라운 음영을 만들기 좋습니다.'),
            ],
            'neutral': [
                _chip('Oat Beige', '오트 베이지', '#D7C2A3', 'base', '회색기 없이 차분한 베이지 베이스입니다.'),
                _chip('Muted Champagne', '뮤트 샴페인', '#DCC8A4', 'eye_highlighter', '은은한 하이라이트로 부드럽게 빛납니다.'),
            ],
            'accent': [
                _chip('Moss Khaki', '모스 카키', '#7A7B4F', 'eye_point', '차분한 포인트로 음영감을 줍니다.'),
                _chip('Clay Rose', '클레이 로즈', '#B56F62', 'lip', '흙빛 로즈가 과하지 않은 포인트가 됩니다.'),
            ],
            'try': [
                _chip('Muted Apricot', '뮤트 애프리콧', '#D8A078', 'try', '피치가 부담스러울 때 선택하기 좋은 중간 톤입니다.'),
                _chip('Soft Olive', '소프트 올리브', '#8F9167', 'try', '의상 컬러로 활용하기 좋은 저채도 올리브입니다.'),
            ],
            'worst': [
                _avoid('Icy Pink', '아이시 핑크', '#F2C7D8', '차갑고 밝은 핑크가 피부를 떠 보이게 할 수 있습니다.'),
                _avoid('Electric Blue', '일렉트릭 블루', '#005DFF', '고채도 블루는 웜 뮤트의 차분함과 충돌합니다.'),
                _avoid('Pure White', '퓨어 화이트', '#FFFFFF', '명도 대비가 강해 얼굴색이 탁해 보일 수 있습니다.'),
            ],
        },
        'deep': {
            'best': [
                _chip('Brick Red', '브릭 레드', '#9E3F2F', 'lip_cheek', '깊은 벽돌빛이 얼굴의 밀도를 안정적으로 잡아줍니다.'),
                _chip('Burnt Orange', '번트 오렌지', '#B85B2A', 'lip', '따뜻한 딥 립으로 세련된 포인트를 만듭니다.'),
                _chip('Olive', '올리브', '#606B38', 'fashion', '어두운 올리브가 깊이 있는 분위기를 줍니다.'),
                _chip('Espresso', '에스프레소', '#4B2E24', 'eye_shading', '진한 브라운 음영으로 눈매를 또렷하게 합니다.'),
            ],
            'neutral': [
                _chip('Deep Beige', '딥 베이지', '#B08A68', 'base', '깊은 웜톤과 이어지는 베이스 컬러입니다.'),
                _chip('Antique Gold', '앤틱 골드', '#B99655', 'eye_highlighter', '번쩍임보다 깊은 골드 포인트에 적합합니다.'),
            ],
            'accent': [
                _chip('Deep Teal', '딥 틸', '#0F5B5B', 'eye_point', '깊은 청록 포인트가 웜 딥의 세련미를 살립니다.'),
                _chip('Tomato Red', '토마토 레드', '#B8332A', 'lip', '따뜻하고 선명한 레드 포인트입니다.'),
            ],
            'try': [
                _chip('Cinnamon', '시나몬', '#9C5A35', 'try', '웜 딥의 데일리 음영으로 활용하기 좋습니다.'),
                _chip('Dark Olive', '다크 올리브', '#4E5730', 'try', '검정보다 부드러운 깊이를 줍니다.'),
            ],
            'worst': [
                _avoid('Pastel Lavender', '파스텔 라벤더', '#D9C6F0', '명도와 온도가 맞지 않아 얼굴이 흐려질 수 있습니다.'),
                _avoid('Cool Mint', '쿨 민트', '#BDEFEA', '차갑고 밝아 깊은 웜톤의 안정감을 깨뜨립니다.'),
                _avoid('Neon Pink', '네온 핑크', '#FF2FA0', '형광기가 강해 피부색과 분리되어 보일 수 있습니다.'),
            ],
        },
    },
    'cool': {
        'bright': {
            'best': [
                _chip('Fuchsia Pink', '푸시아 핑크', '#D91E6A', 'lip_cheek', '선명한 블루 핑크가 얼굴의 또렷함을 살립니다.'),
                _chip('Blue Red', '블루 레드', '#C9152E', 'lip', '푸른 기가 도는 레드가 치아와 피부를 깨끗하게 보입니다.'),
                _chip('Cobalt Blue', '코발트 블루', '#1E4DD8', 'fashion', '강한 쿨 포인트로 대비감을 줍니다.'),
                _chip('Clear Violet', '클리어 바이올렛', '#7B3FE4', 'eye_base', '맑은 보라기가 쿨 브라이트의 선명함과 맞습니다.'),
            ],
            'neutral': [
                _chip('Clean White', '클린 화이트', '#F7F8FA', 'base', '노란기 없이 깨끗한 밝은 베이스입니다.'),
                _chip('Icy Pearl', '아이시 펄', '#EAF0FA', 'eye_highlighter', '차갑고 깨끗한 하이라이트를 만듭니다.'),
            ],
            'accent': [
                _chip('Icy Aqua', '아이시 아쿠아', '#7DE2E8', 'eye_point', '차갑고 맑은 포인트로 눈매를 밝혀줍니다.'),
                _chip('Raspberry Pop', '라즈베리 팝', '#D81B60', 'lip', '선명한 베리 포인트 립입니다.'),
            ],
            'try': [
                _chip('Clear Rose', '클리어 로즈', '#E24D83', 'try', '푸시아보다 부드럽지만 선명함은 유지합니다.'),
                _chip('Royal Blue', '로열 블루', '#2647C7', 'try', '의상 포인트로 쓰기 좋은 쿨 블루입니다.'),
            ],
            'worst': [
                _avoid('Mustard', '머스터드', '#B88918', '노란기가 강해 얼굴이 칙칙해 보일 수 있습니다.'),
                _avoid('Rust Orange', '러스트 오렌지', '#B4572A', '따뜻하고 탁한 색이 쿨 브라이트의 선명함과 맞지 않습니다.'),
                _avoid('Dusty Beige', '더스티 베이지', '#B6A08B', '회색기와 노란기가 함께 있어 생기를 낮출 수 있습니다.'),
            ],
        },
        'light': {
            'best': [
                _chip('Baby Pink', '베이비 핑크', '#F3B6CD', 'lip_cheek', '밝고 차가운 핑크가 투명한 혈색을 줍니다.'),
                _chip('Powder Lavender', '파우더 라벤더', '#CFC3EE', 'lip', '연한 라벤더 핑크가 쿨 라이트의 맑음을 살립니다.'),
                _chip('Mist Blue', '미스트 블루', '#BFD7F2', 'fashion', '흐리지 않은 밝은 블루가 얼굴 주변을 정리합니다.'),
                _chip('Pearl Rose', '펄 로즈', '#E7C5D3', 'eye_base', '은은한 로즈기가 눈가를 부드럽게 밝혀줍니다.'),
            ],
            'neutral': [
                _chip('Pink Ivory', '핑크 아이보리', '#F7E8EA', 'base', '노란기를 줄인 밝은 핑크 베이스입니다.'),
                _chip('Cool Pearl', '쿨 펄', '#EEF0F8', 'eye_highlighter', '맑은 펄감으로 눈가를 화사하게 합니다.'),
            ],
            'accent': [
                _chip('Cool Mint', '쿨 민트', '#BFE8E3', 'eye_point', '가벼운 민트 포인트가 답답함을 줄입니다.'),
                _chip('Soft Berry Pink', '소프트 베리 핑크', '#D87FA5', 'lip', '라이트 톤에서도 부담 없는 베리 핑크입니다.'),
            ],
            'try': [
                _chip('Pale Lilac', '페일 라일락', '#DCCEF4', 'try', '라벤더가 부담스러울 때 쓰기 좋은 밝은 컬러입니다.'),
                _chip('Cloud Blue', '클라우드 블루', '#D6E5F7', 'try', '의상과 네일에 활용하기 좋은 밝은 블루입니다.'),
            ],
            'worst': [
                _avoid('Dark Brown', '다크 브라운', '#3B2419', '어둡고 따뜻해 라이트 타입의 투명감을 누릅니다.'),
                _avoid('Pumpkin Orange', '펌킨 오렌지', '#D36B22', '오렌지기가 강해 얼굴이 노랗게 보일 수 있습니다.'),
                _avoid('Black', '블랙', '#050505', '대비가 너무 강해 이목구비보다 색이 먼저 보일 수 있습니다.'),
            ],
        },
        'mute': {
            'best': [
                _chip('Dusty Rose', '더스티 로즈', '#C98FA0', 'lip_cheek', '차분한 장밋빛이 부드러운 쿨 무드를 살립니다.'),
                _chip('Mauve Pink', '모브 핑크', '#B9829A', 'lip', '탁도가 있는 핑크가 입술에 자연스럽게 연결됩니다.'),
                _chip('Soft Lavender', '소프트 라벤더', '#B8A7D6', 'cheek', '붉은기를 과하게 올리지 않고 쿨한 분위기를 만듭니다.'),
                _chip('Taupe Brown', '토프 브라운', '#8E7A7D', 'eye_base', '붉은기가 적은 브라운으로 부드러운 음영을 만듭니다.'),
            ],
            'neutral': [
                _chip('Neutral Pink Beige', '뉴트럴 핑크 베이지', '#D9C8C9', 'base', '핑크와 베이지가 균형 잡힌 베이스 컬러입니다.'),
                _chip('Soft Gray Pearl', '소프트 그레이 펄', '#CBC9D3', 'eye_highlighter', '회색기가 은은해 튀지 않는 하이라이트입니다.'),
            ],
            'accent': [
                _chip('Mauve Brown', '모브 브라운', '#7E6571', 'eye_shading', '눈매를 부드럽게 잡아주는 쿨 음영입니다.'),
                _chip('Muted Berry', '뮤트 베리', '#9D5D75', 'lip', '채도를 낮춘 베리 포인트입니다.'),
            ],
            'try': [
                _chip('Rose Taupe', '로즈 토프', '#B5939B', 'try', '로즈와 그레이가 섞인 안정적인 시도 컬러입니다.'),
                _chip('Smoky Lilac', '스모키 라일락', '#A99BC8', 'try', '의상 포인트로 쓰기 좋은 저채도 라일락입니다.'),
            ],
            'worst': [
                _avoid('Neon Orange', '네온 오렌지', '#FF6A00', '채도와 온도가 강해 얼굴색이 뜨거나 노랗게 보일 수 있습니다.'),
                _avoid('Golden Yellow', '골든 옐로', '#E4B431', '따뜻한 온도가 강해 은은한 쿨 무드를 깨뜨릴 수 있습니다.'),
                _avoid('Warm Brick', '웜 브릭', '#A7472A', '붉은 갈색의 온기가 피부를 답답하게 보이게 할 수 있습니다.'),
            ],
        },
        'deep': {
            'best': [
                _chip('Burgundy', '버건디', '#7B1839', 'lip_cheek', '푸른 기가 있는 깊은 레드가 얼굴을 선명하게 합니다.'),
                _chip('Deep Plum', '딥 플럼', '#4E234F', 'lip', '깊은 보라기가 고급스러운 포인트를 만듭니다.'),
                _chip('Midnight Navy', '미드나잇 네이비', '#16213E', 'fashion', '블랙보다 세련된 깊이를 주는 쿨 네이비입니다.'),
                _chip('Charcoal Teal', '차콜 틸', '#204B4F', 'eye_shading', '차갑고 깊은 음영으로 눈매를 또렷하게 합니다.'),
            ],
            'neutral': [
                _chip('Cool Beige', '쿨 베이지', '#B8AAA8', 'base', '노란기를 낮춘 깊은 베이스 컬러입니다.'),
                _chip('Pewter Pearl', '퓨터 펄', '#9EA0AA', 'eye_highlighter', '은은한 메탈릭 그레이 하이라이트입니다.'),
            ],
            'accent': [
                _chip('Sapphire', '사파이어', '#123E8A', 'eye_point', '깊은 블루 포인트가 대비감을 높입니다.'),
                _chip('Wine Rose', '와인 로즈', '#8E2F55', 'lip', '딥 타입에 잘 맞는 차가운 와인 립입니다.'),
            ],
            'try': [
                _chip('Smoky Navy', '스모키 네이비', '#27324D', 'try', '블랙 대신 쓰기 좋은 깊은 쿨 컬러입니다.'),
                _chip('Black Cherry', '블랙 체리', '#5D1630', 'try', '강한 립 포인트를 원할 때 안정적입니다.'),
            ],
            'worst': [
                _avoid('Pastel Peach', '파스텔 피치', '#F6C5B0', '밝고 따뜻해 얼굴의 깊이와 대비를 약하게 만듭니다.'),
                _avoid('Camel', '카멜', '#B9854D', '노란 갈색이 쿨 딥의 선명함을 흐릴 수 있습니다.'),
                _avoid('Light Mint', '라이트 민트', '#C8F1DD', '너무 옅어 얼굴 윤곽이 약해 보일 수 있습니다.'),
            ],
        },
    },
}

SIGNATURE_SWATCHES = {
    ('spring', 'warm'): _chip('Fresh Coral', '프레시 코랄', '#FF7F6E', 'lip_cheek', '봄 웜 특유의 밝고 생기 있는 혈색을 줍니다.'),
    ('spring', 'cool'): _chip('Clear Rose', '클리어 로즈', '#EA6F9A', 'lip_cheek', '봄의 맑음과 쿨한 장밋빛을 함께 살립니다.'),
    ('summer', 'warm'): _chip('Soft Peach Beige', '소프트 피치 베이지', '#E7B39A', 'cheek', '여름의 부드러움에 따뜻한 피치기를 더합니다.'),
    ('summer', 'cool'): _chip('Blue Pink', '블루 핑크', '#DFA1B8', 'lip_cheek', '여름 쿨의 은은한 핑크 혈색을 만듭니다.'),
    ('autumn', 'warm'): _chip('Cinnamon Brown', '시나몬 브라운', '#9F5A35', 'eye_shading', '가을 웜의 깊고 자연스러운 음영을 살립니다.'),
    ('autumn', 'cool'): _chip('Smoky Rosewood', '스모키 로즈우드', '#9A6672', 'lip_cheek', '가을의 차분함에 쿨 로즈 기운을 더합니다.'),
    ('winter', 'warm'): _chip('Scarlet Tomato', '스칼렛 토마토', '#C93B2E', 'lip', '겨울의 선명함에 따뜻한 레드 포인트를 줍니다.'),
    ('winter', 'cool'): _chip('Icy Raspberry', '아이시 라즈베리', '#C91565', 'lip', '겨울 쿨의 선명하고 차가운 포인트 컬러입니다.'),
}


def _unique(items):
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def _first_by_usage(items, usages, fallback):
    for item in items:
        if item.get('usage') in usages:
            return item
    return fallback


def _chip_names(items):
    return [item.get('name') for item in items if item.get('name')]


def _legacy_makeup_palette(makeup_guide):
    eye_roles = makeup_guide['eye']['roles']
    return {
        'base': {
            'tone': makeup_guide['base']['tone'],
            'guide': makeup_guide['base']['guide'],
            'recommended': makeup_guide['base']['recommended'],
            'avoid': makeup_guide['base']['avoid'],
        },
        'lip': {
            'recommended': makeup_guide['lip']['recommended'],
            'avoid': makeup_guide['lip']['avoid'],
        },
        'cheek': {
            'recommended': makeup_guide['blush']['recommended'],
            'avoid': makeup_guide['blush']['avoid'],
        },
        'eye': {
            'recommended': _chip_names([eye_roles[key] for key in ROLE_KEYS]),
            'avoid': makeup_guide['eye']['avoid'],
        },
    }


def _build_style_guide(temp_meta, palettes):
    lens = [_chip(name, name_ko, hex_value, 'lens', f'{name_ko} 렌즈는 톤의 온도감과 자연스럽게 이어집니다.') for name, name_ko, hex_value in temp_meta['lens']]
    hair = [_chip(name, name_ko, hex_value, 'hair', f'{name_ko} 헤어 컬러는 얼굴 주변 대비를 안정적으로 잡아줍니다.') for name, name_ko, hex_value in temp_meta['hair']]
    return {
        'lens': lens,
        'hair': hair,
        'accessory': temp_meta['accessory'],
        'fashion': palettes['best'][:2] + palettes['accent'][:2],
    }


def _build_payload(tone_key):
    season, temperature, tone = split_tone_key(tone_key)
    season_meta = SEASON_META[season]
    temp_meta = TEMPERATURE_META[temperature]
    tone_meta = TONE_META[tone]
    swatches = deepcopy(BASE_SWATCHES[temperature][tone])
    signature = deepcopy(SIGNATURE_SWATCHES[(season, temperature)])
    label = build_tone_name(tone_key)

    best = [signature] + swatches['best']
    palettes = {
        'best': best,
        'neutral': swatches['neutral'],
        'accent': swatches['accent'],
        'try': swatches['try'],
        'worst': swatches['worst'],
    }

    highlighter = _first_by_usage(palettes['neutral'], {'eye_highlighter'}, palettes['neutral'][0])
    eye_base = _first_by_usage(best, {'eye_base'}, palettes['neutral'][0])
    shading = _first_by_usage(best + palettes['accent'], {'eye_shading'}, palettes['accent'][0])
    point = _first_by_usage(palettes['accent'], {'eye_point'}, palettes['accent'][0])
    lip_chips = [item for item in best + palettes['accent'] if item.get('usage') in {'lip', 'lip_cheek'}][:4]
    blush_chips = [item for item in best if item.get('usage') in {'cheek', 'lip_cheek'}][:3]
    if not blush_chips:
        blush_chips = lip_chips[:2]

    makeup_guide = {
        'base': {
            'title': '베이스',
            'tone': temp_meta['base_tone'],
            'guide': temp_meta['base_guide'],
            'recommended': [palettes['neutral'][0]['name'], palettes['neutral'][0]['nameKo']],
            'avoid': temp_meta['avoid_base'],
            'chips': [palettes['neutral'][0]],
        },
        'eye': {
            'title': '아이',
            'guide': f"{label}는 {tone_meta['intensity']} 강도의 아이 컬러를 얇게 쌓는 방식이 좋습니다.",
            'paletteLayout': list(ROLE_KEYS),
            'roles': {
                'highlighter': highlighter,
                'base': eye_base,
                'shading': shading,
                'point': point,
            },
            'avoid': _chip_names(palettes['worst'][:2]),
        },
        'lip': {
            'title': '립',
            'guide': f"{label} 립은 {tone_meta['summary']}",
            'recommended': _chip_names(lip_chips),
            'avoid': _chip_names(palettes['worst']),
            'chips': lip_chips,
        },
        'blush': {
            'title': '치크',
            'guide': f"{label} 치크는 넓고 연하게 올려 피부 톤과 연결합니다.",
            'recommended': _chip_names(blush_chips),
            'avoid': _chip_names(palettes['worst'][:2]),
            'chips': blush_chips,
        },
    }

    axes = {
        'season': season,
        'temperature': temp_meta['axis'],
        'brightness': tone_meta['brightness'],
        'chroma': tone_meta['chroma'],
        'contrast': tone_meta['contrast'],
    }
    keywords = _unique(season_meta['style'] + tone_meta['keywords'] + [temperature, season])
    style_guide = _build_style_guide(temp_meta, palettes)
    close_to = [
        candidate
        for candidate in (
            f'{season}_{temperature}_light',
            f'{season}_{temperature}_mute',
            f'{season}_{temperature}_bright',
            f'{season}_{temperature}_deep',
            f"{season}_{'cool' if temperature == 'warm' else 'warm'}_{tone}",
        )
        if candidate in CANONICAL_TONE_KEYS and candidate != tone_key
    ][:3]

    payload = {
        'toneKey': tone_key,
        'label': label,
        'toneName': label,
        'season': season,
        'temperature': temperature,
        'brightness': tone_meta['brightness'],
        'chroma': tone_meta['chroma'],
        'contrast': tone_meta['contrast'],
        'description': f"{label}는 {season_meta['mood']} 인상과 {temp_meta['undertone']}을 기준으로, {tone_meta['summary']}",
        'summary': f"{season_meta['ko']} 계절감의 {temp_meta['ko']}톤 안에서 {tone_meta['ko']} 특성이 강한 타입입니다. {tone_meta['summary']}",
        'keywords': keywords,
        'axes': axes,
        'imageFeatures': [
            {'key': 'temperature', 'title': '온도감', 'description': temp_meta['undertone'], 'icon': 'sparkle'},
            {'key': 'brightness', 'title': '명도', 'description': f"{tone_meta['brightness']} 범위의 명도가 안정적입니다.", 'icon': 'sun'},
            {'key': 'chroma', 'title': '채도', 'description': f"{tone_meta['chroma']} 채도에서 얼굴색과 조화됩니다.", 'icon': 'flower'},
            {'key': 'contrast', 'title': '대비', 'description': f"{tone_meta['contrast']} 대비를 기준으로 스타일링합니다.", 'icon': 'diamond'},
        ],
        'profile': {
            'season': season,
            'temperature': temperature,
            'tone': tone,
            'persona': season_meta['profile'],
            'recommendedIntensity': tone_meta['intensity'],
            'avoidMood': tone_meta['avoid'],
        },
        'representativeColors': best[:4] + palettes['neutral'][:2],
        'palettes': palettes,
        'makeupColorGuide': makeup_guide,
        'makeupPalette': _legacy_makeup_palette(makeup_guide),
        'baseMakeupGuide': makeup_guide['base']['guide'],
        'lipGuide': makeup_guide['lip']['guide'],
        'cheekGuide': makeup_guide['blush']['guide'],
        'eyeGuide': makeup_guide['eye']['guide'],
        'styleGuide': style_guide,
        'stylingKeywords': keywords[:5],
        'recommendedProductToneRange': {
            'hue': temp_meta['hues'],
            'brightness': [tone_meta['brightness']],
            'chroma': [tone_meta['chroma']],
            'temperature': temperature,
        },
        'boundary': {
            'closeTo': close_to,
            'notToConfuseWith': f"{'cool' if temperature == 'warm' else 'warm'} 계열 또는 {tone_meta['avoid']}",
            'decisionRule': '온도감, 명도, 채도, 대비가 모두 같은 방향으로 맞을 때만 확정합니다.',
        },
        'recommendationTags': _unique([tone_key, season, temperature, tone] + temp_meta['hues'] + tone_meta['keywords']),
        'genAiPromptSeed': {
            'base': makeup_guide['base']['guide'],
            'lip': makeup_guide['lip']['recommended'],
            'cheek': makeup_guide['blush']['recommended'],
            'eye': _chip_names([makeup_guide['eye']['roles'][key] for key in ROLE_KEYS]),
            'avoid': _chip_names(palettes['worst']),
            'styleKeywords': keywords,
        },
        'ui': {
            'themeHex': best[0]['hex'],
            'gradient': [best[0]['hex'], palettes['neutral'][0]['hex']],
            'profileImageKey': tone_key,
        },
        'resultTip': f"{label}는 {palettes['best'][0]['nameKo']}처럼 기준 축에 맞는 컬러를 얼굴 가까이에 두면 진단 장점이 가장 잘 보입니다.",
        'is_placeholder': False,
        'isPlaceholder': False,
    }
    return payload


PALETTE_SEED_DATA = {tone_key: _build_payload(tone_key) for tone_key in CANONICAL_TONE_KEYS}


def validate_palette_payload(tone_key, payload):
    errors = []
    required_top_level = [
        'label',
        'description',
        'summary',
        'keywords',
        'axes',
        'imageFeatures',
        'profile',
        'representativeColors',
        'palettes',
        'makeupColorGuide',
        'styleGuide',
        'boundary',
        'recommendationTags',
        'genAiPromptSeed',
        'ui',
        'resultTip',
    ]
    for key in required_top_level:
        if not payload.get(key):
            errors.append(f'{tone_key}: {key} is required')

    if payload.get('is_placeholder') is not False:
        errors.append(f'{tone_key}: is_placeholder must be False')

    palettes = payload.get('palettes') or {}
    for group in ['best', 'neutral', 'accent', 'try', 'worst']:
        items = palettes.get(group)
        if not items:
            errors.append(f'{tone_key}: palettes.{group} must not be empty')
            continue
        for index, item in enumerate(items):
            for key in ['name', 'nameKo', 'hex', 'usage']:
                if not item.get(key):
                    errors.append(f'{tone_key}: palettes.{group}[{index}].{key} is required')
            if not item.get('description') and not item.get('reason'):
                errors.append(f'{tone_key}: palettes.{group}[{index}] needs description or reason')

    eye = (payload.get('makeupColorGuide') or {}).get('eye') or {}
    roles = eye.get('roles') or {}
    missing_roles = [key for key in ROLE_KEYS if not roles.get(key)]
    if missing_roles:
        errors.append(f"{tone_key}: makeupColorGuide.eye.roles missing {', '.join(missing_roles)}")
    if not eye.get('paletteLayout'):
        errors.append(f'{tone_key}: makeupColorGuide.eye.paletteLayout is required')

    for section in ['base', 'lip', 'blush']:
        if not (payload.get('makeupColorGuide') or {}).get(section):
            errors.append(f'{tone_key}: makeupColorGuide.{section} is required')

    for section in ['lens', 'hair', 'accessory', 'fashion']:
        if not (payload.get('styleGuide') or {}).get(section):
            errors.append(f'{tone_key}: styleGuide.{section} is required')

    return errors


def validate_palette_seed_data(seed_data):
    errors = []
    keys = set(seed_data.keys())
    canonical = set(CANONICAL_TONE_KEYS)
    missing = sorted(canonical - keys)
    extra = sorted(keys - canonical)
    if missing:
        errors.append(f'Missing tone keys: {", ".join(missing)}')
    if extra:
        errors.append(f'Unknown tone keys: {", ".join(extra)}')

    for tone_key in CANONICAL_TONE_KEYS:
        payload = seed_data.get(tone_key)
        if not payload:
            continue
        errors.extend(validate_palette_payload(tone_key, payload))
    return errors
