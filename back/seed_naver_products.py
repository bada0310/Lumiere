import os
import re
import math
import colorsys
from io import BytesIO
from collections import defaultdict

import django
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Lumiere.settings")
django.setup()

from products.models import Product


CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError(".env 파일에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET을 넣어주세요.")

NAVER_URL = "https://openapi.naver.com/v1/search/shop.json"

HEADERS = {
    "X-Naver-Client-Id": CLIENT_ID,
    "X-Naver-Client-Secret": CLIENT_SECRET,
}

IMAGE_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# 기존 DB 상품을 지우고 새로 넣을지 여부
RESET_DB = True

# 퍼스널컬러 x 카테고리 조합마다 몇 개까지 저장할지
# 8톤 x 5카테고리 x 4개 = 최대 160개
MAX_SAVE_PER_TARGET = 12

# 네이버 API 한 번 호출할 때 가져올 후보 개수
DISPLAY_COUNT = 100

START_POSITIONS = [1, 101, 201]

TONE_TARGETS = [
    (Product.ToneTag.SPRING_LIGHT, "봄웜 라이트"),
    (Product.ToneTag.SPRING_BRIGHT, "봄웜 브라이트"),
    (Product.ToneTag.SUMMER_LIGHT, "여름쿨 라이트"),
    (Product.ToneTag.SUMMER_MUTE, "여름쿨 뮤트"),
    (Product.ToneTag.AUTUMN_MUTE, "가을웜 뮤트"),
    (Product.ToneTag.AUTUMN_DEEP, "가을웜 딥"),
    (Product.ToneTag.WINTER_BRIGHT, "겨울쿨 브라이트"),
    (Product.ToneTag.WINTER_DEEP, "겨울쿨 딥"),
]

CATEGORY_TARGETS = [
    # 립
    (Product.Category.LIP, "립틴트 화장품"),
    (Product.Category.LIP, "립글로스 화장품"),
    (Product.Category.LIP, "립스틱 화장품"),

    # 아이
    (Product.Category.EYE, "아이팔레트 화장품"),
    (Product.Category.EYE, "아이섀도우 화장품"),
    (Product.Category.EYE, "마스카라 화장품"),
    (Product.Category.EYE, "아이라이너 화장품"),

    # 치크
    (Product.Category.CHEEK, "블러셔 화장품"),
    (Product.Category.CHEEK, "치크 화장품"),
    (Product.Category.CHEEK, "볼터치 화장품"),

    # 베이스
    (Product.Category.BASE, "쿠션 파운데이션 화장품"),
    (Product.Category.BASE, "파운데이션 화장품"),
    (Product.Category.BASE, "컨실러 화장품"),
    (Product.Category.BASE, "톤업 베이스 화장품"),

    # 렌즈
    (Product.Category.LENS, "컬러렌즈"),
    (Product.Category.LENS, "원데이 컬러렌즈"),
    (Product.Category.LENS, "그레이 렌즈"),
    (Product.Category.LENS, "브라운 렌즈"),
]


INCLUDE_KEYWORDS = {
    Product.Category.LIP: [
        "립", "틴트", "글로스", "립스틱", "라커", "벨벳"
    ],
    Product.Category.EYE: [
        "아이", "팔레트", "섀도우", "쉐도우", "마스카라", "아이라이너"
    ],
    Product.Category.CHEEK: [
        "치크", "블러셔", "블러쉬", "볼터치"
    ],
    Product.Category.BASE: [
        "쿠션", "파운데이션", "컨실러", "비비", "BB", "씨씨", "CC", "베이스", "톤업"
    ],
    Product.Category.LENS: [
        "렌즈", "컬러렌즈", "그레이", "브라운", "원데이", "애쉬"
    ],
}

EXCLUDE_KEYWORDS = [
    "바디필로우", "필로우", "베개", "방석", "쿠션솜", "침구", "이불",
    "매트리스", "패드", "인형", "커버", "시트", "냉감바디", "냉감 바디",
    "샤워", "바디워시", "바디 로션", "핸드크림", "풋크림", "헤어", "샴푸",
    "강아지", "고양이", "차량", "자동차", "스마트폰", "케이스"
]


TONE_PROFILES = {
    Product.ToneTag.SPRING_LIGHT: {
        "brightness": 82,
        "saturation": 45,
        "warmth": 75,
        "coolness": 25,
        "depth": 18,
        "softness": 35,
        "contrast": 35,
    },
    Product.ToneTag.SPRING_BRIGHT: {
        "brightness": 76,
        "saturation": 70,
        "warmth": 70,
        "coolness": 30,
        "depth": 22,
        "softness": 18,
        "contrast": 68,
    },
    Product.ToneTag.SUMMER_LIGHT: {
        "brightness": 80,
        "saturation": 35,
        "warmth": 20,
        "coolness": 82,
        "depth": 18,
        "softness": 45,
        "contrast": 28,
    },
    Product.ToneTag.SUMMER_MUTE: {
        "brightness": 65,
        "saturation": 28,
        "warmth": 30,
        "coolness": 72,
        "depth": 35,
        "softness": 65,
        "contrast": 25,
    },
    Product.ToneTag.AUTUMN_MUTE: {
        "brightness": 55,
        "saturation": 35,
        "warmth": 78,
        "coolness": 25,
        "depth": 45,
        "softness": 65,
        "contrast": 35,
    },
    Product.ToneTag.AUTUMN_DEEP: {
        "brightness": 42,
        "saturation": 50,
        "warmth": 78,
        "coolness": 25,
        "depth": 72,
        "softness": 35,
        "contrast": 55,
    },
    Product.ToneTag.WINTER_BRIGHT: {
        "brightness": 66,
        "saturation": 75,
        "warmth": 20,
        "coolness": 82,
        "depth": 42,
        "softness": 12,
        "contrast": 82,
    },
    Product.ToneTag.WINTER_DEEP: {
        "brightness": 38,
        "saturation": 62,
        "warmth": 25,
        "coolness": 78,
        "depth": 82,
        "softness": 20,
        "contrast": 75,
    },
}


def clean_html(text):
    return re.sub("<.*?>", "", text or "")


def normalize_text(text):
    return str(text or "").lower().replace(" ", "")


def clamp(value, min_value=0, max_value=100):
    return max(min_value, min(max_value, value))


def rgb_to_hex(rgb):
    r, g, b = rgb
    return f"#{r:02X}{g:02X}{b:02X}"


def hue_distance(h1, h2):
    diff = abs(h1 - h2) % 360
    return min(diff, 360 - diff)


def score_by_hue(hue, centers, scale=1.0):
    min_distance = min(hue_distance(hue, center) for center in centers)
    return clamp(100 - min_distance * scale)


def get_dominant_rgb(image_url):
    """
    상품 이미지에서 대표 RGB를 뽑는다.
    흰 배경, 검정 배경, 투명 영역은 최대한 제외한다.
    """
    if not image_url:
        return (200, 150, 170)

    try:
        response = requests.get(image_url, headers=IMAGE_HEADERS, timeout=10)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content)).convert("RGBA")
        image.thumbnail((160, 160))

        pixels = []

        for r, g, b, a in image.getdata():
            if a < 128:
                continue

            # 흰 배경 제거
            if r > 238 and g > 238 and b > 238:
                continue

            # 검정 배경 제거
            if r < 25 and g < 25 and b < 25:
                continue

            # 너무 밝은 회색 배경 제거
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if s < 0.08 and v > 0.75:
                continue

            pixels.append((r, g, b))

        # 너무 많이 제거되었으면 전체 픽셀 사용
        if len(pixels) < 50:
            pixels = [
                (r, g, b)
                for r, g, b, a in image.getdata()
                if a >= 128
            ]

        if not pixels:
            return (200, 150, 170)

        palette_image = Image.new("RGB", (len(pixels), 1))
        palette_image.putdata(pixels)

        quantized = palette_image.quantize(colors=6)
        colors = quantized.getcolors()
        palette = quantized.getpalette()

        dominant_index = max(colors, key=lambda item: item[0])[1]

        r = palette[dominant_index * 3]
        g = palette[dominant_index * 3 + 1]
        b = palette[dominant_index * 3 + 2]

        return (r, g, b)

    except Exception as error:
        print("이미지 분석 실패:", error)
        return (200, 150, 170)


def analyze_rgb(rgb):
    r, g, b = rgb

    r_ratio = r / 255
    g_ratio = g / 255
    b_ratio = b / 255

    h, s, v = colorsys.rgb_to_hsv(r_ratio, g_ratio, b_ratio)
    hue = h * 360

    max_c = max(r_ratio, g_ratio, b_ratio)
    min_c = min(r_ratio, g_ratio, b_ratio)
    lightness = (max_c + min_c) / 2

    brightness = round(lightness * 100)
    saturation = round(s * 100)

    # 쿨 중심: 블루, 바이올렛, 핑크, 마젠타
    coolness = round(score_by_hue(hue, [210, 250, 290, 320, 340], scale=0.75))

    # 웜 중심: 레드오렌지, 오렌지, 옐로우, 브라운 계열
    warmth = round(score_by_hue(hue, [15, 30, 45, 60], scale=0.9))

    depth = round(clamp(100 - brightness))

    # 채도가 낮으면 부드럽고 탁하다고 판단
    softness = round(clamp((100 - saturation) * 0.65))

    # 대비감: 채도와 명도 차이를 함께 사용
    contrast = round(clamp(abs(brightness - 50) * 0.8 + saturation * 0.35))

    return {
        "hex_code": rgb_to_hex(rgb),
        "rgb_r": r,
        "rgb_g": g,
        "rgb_b": b,
        "brightness": brightness,
        "saturation": saturation,
        "coolness": coolness,
        "warmth": warmth,
        "depth": depth,
        "softness": softness,
        "contrast": contrast,
    }


def calculate_match_score(metrics, tone_tag):
    profile = TONE_PROFILES.get(tone_tag)

    if not profile:
        return 80

    diff = 0
    diff += abs(metrics["brightness"] - profile["brightness"]) * 0.18
    diff += abs(metrics["saturation"] - profile["saturation"]) * 0.16
    diff += abs(metrics["coolness"] - profile["coolness"]) * 0.22
    diff += abs(metrics["warmth"] - profile["warmth"]) * 0.16
    diff += abs(metrics["depth"] - profile["depth"]) * 0.12
    diff += abs(metrics["softness"] - profile["softness"]) * 0.08
    diff += abs(metrics["contrast"] - profile["contrast"]) * 0.08

    score = 100 - diff

    return round(clamp(score, 0, 100))


def infer_texture(category, text):
    search_text = normalize_text(text)

    if category == Product.Category.LIP:
        if "글로스" in search_text or "글로우" in search_text:
            return "립글로스"
        if "립스틱" in search_text:
            return "립스틱"
        return "립틴트"

    if category == Product.Category.EYE:
        if "마스카라" in search_text:
            return "마스카라"
        if "아이라이너" in search_text:
            return "아이라이너"
        return "아이팔레트"

    if category == Product.Category.CHEEK:
        return "블러셔"

    if category == Product.Category.BASE:
        if "파운데이션" in search_text:
            return "파운데이션"
        if "컨실러" in search_text:
            return "컨실러"
        return "쿠션"

    if category == Product.Category.LENS:
        return "컬러렌즈"

    return "기타"


def infer_finish(category, text):
    search_text = normalize_text(text)

    if any(word in search_text for word in ["매트", "matte"]):
        return Product.Finish.MATTE

    if any(word in search_text for word in ["벨벳", "velvet", "블러"]):
        return Product.Finish.VELVET

    if any(word in search_text for word in ["글로스", "글로시", "글로우", "촉촉", "워터", "glow", "gloss"]):
        return Product.Finish.GLOSSY

    if any(word in search_text for word in ["펄", "쉬머", "글리터", "shimmer", "glitter"]):
        return Product.Finish.SHIMMER

    if category in [Product.Category.BASE, Product.Category.LENS]:
        return Product.Finish.NATURAL

    return Product.Finish.UNKNOWN


def infer_color_family(text, hue, category):
    search_text = normalize_text(text)

    keyword_map = [
        (Product.ColorFamily.LAVENDER, ["라벤더", "모브", "퍼플", "바이올렛", "lavender", "mauve", "purple"]),
        (Product.ColorFamily.BERRY, ["베리", "플럼", "자두", "berry", "plum"]),
        (Product.ColorFamily.PINK, ["핑크", "pink"]),
        (Product.ColorFamily.ROSE, ["로즈", "rose"]),
        (Product.ColorFamily.CORAL, ["코랄", "피치", "살구", "coral", "peach"]),
        (Product.ColorFamily.RED, ["레드", "red"]),
        (Product.ColorFamily.BEIGE, ["베이지", "누드", "nude", "beige"]),
        (Product.ColorFamily.BROWN, ["브라운", "초코", "brown", "choco"]),
        (Product.ColorFamily.GRAY, ["그레이", "애쉬", "gray", "grey", "ash"]),
        (Product.ColorFamily.IVORY, ["아이보리", "포슬린", "바닐라", "ivory", "porcelain", "vanilla"]),
    ]

    for family, keywords in keyword_map:
        if any(keyword in search_text for keyword in keywords):
            return family

    if category == Product.Category.BASE:
        return Product.ColorFamily.IVORY

    if category == Product.Category.LENS:
        if 180 <= hue <= 260:
            return Product.ColorFamily.GRAY
        return Product.ColorFamily.BROWN

    if 300 <= hue <= 350:
        return Product.ColorFamily.PINK

    if 250 <= hue < 300:
        return Product.ColorFamily.LAVENDER

    if 350 <= hue or hue <= 10:
        return Product.ColorFamily.RED

    if 10 < hue <= 40:
        return Product.ColorFamily.CORAL

    if 40 < hue <= 80:
        return Product.ColorFamily.BEIGE

    return Product.ColorFamily.ETC


def make_reason(tone_label, category, metrics):
    if metrics["coolness"] >= 70:
        temp_text = "쿨한 색감이 강한 편"
    elif metrics["warmth"] >= 70:
        temp_text = "따뜻한 색감이 강한 편"
    else:
        temp_text = "웜/쿨 균형이 비교적 부드러운 편"

    if metrics["brightness"] >= 70:
        light_text = "밝은 명도"
    elif metrics["depth"] >= 65:
        light_text = "딥한 명도"
    else:
        light_text = "중간 명도"

    if metrics["saturation"] >= 60:
        chroma_text = "선명한 채도"
    elif metrics["saturation"] <= 35:
        chroma_text = "낮은 채도"
    else:
        chroma_text = "중간 채도"

    return f"{tone_label} 기준으로 {light_text}, {chroma_text}, {temp_text}이라 추천 후보로 분류했어요."


def is_valid_product(item, category):
    title = clean_html(item.get("title", ""))
    category1 = item.get("category1", "")
    category2 = item.get("category2", "")
    category3 = item.get("category3", "")
    category4 = item.get("category4", "")

    full_text = f"{title} {category1} {category2} {category3} {category4}"
    normalized = normalize_text(full_text)

    # 렌즈가 아닌 경우에는 화장품/미용 카테고리만 허용
    if category != Product.Category.LENS:
        if category1 != "화장품/미용":
            return False

    for word in EXCLUDE_KEYWORDS:
        if normalize_text(word) in normalized:
            return False

    include_words = INCLUDE_KEYWORDS.get(category, [])
    has_include_keyword = any(normalize_text(word) in normalized for word in include_words)

    return has_include_keyword

import time

def fetch_products(query):
    all_items = []

    for start in START_POSITIONS:
        params = {
            "query": query,
            "display": DISPLAY_COUNT,
            "start": start,
            "sort": "sim",
            "exclude": "used:rental:cbshop",
        }

        response = requests.get(NAVER_URL, headers=HEADERS, params=params)

        print("\n검색어:", query, "| start:", start)
        print("상태코드:", response.status_code)

        if response.status_code != 200:
            print("에러:", response.text)
            continue

        items = response.json().get("items", [])
        all_items.extend(items)

        # 너무 빠르게 요청하지 않기
        time.sleep(0.2)

    return all_items


def main():
    if RESET_DB:
        Product.objects.all().delete()
        print("기존 Product 데이터 삭제 완료")

    total_saved = 0
    seen_keys = set()
    category_count = defaultdict(int)

    for tone_tag, tone_label in TONE_TARGETS:
        for category, category_query in CATEGORY_TARGETS:
            query = f"{tone_label} {category_query}"
            items = fetch_products(query)

            saved_for_target = 0

            for item in items:
                if saved_for_target >= MAX_SAVE_PER_TARGET:
                    break

                title = clean_html(item.get("title", ""))
                brand = item.get("brand") or item.get("maker") or "브랜드 미상"
                image_url = item.get("image", "")
                product_url = item.get("link", "")
                naver_product_id = item.get("productId", "")

                unique_key = naver_product_id or product_url or title

                if unique_key in seen_keys:
                    print("중복 제외:", title)
                    continue

                if not is_valid_product(item, category):
                    print("제외:", title, "|", item.get("category1"), item.get("category2"))
                    continue

                rgb = get_dominant_rgb(image_url)
                metrics = analyze_rgb(rgb)

                r_ratio = rgb[0] / 255
                g_ratio = rgb[1] / 255
                b_ratio = rgb[2] / 255
                hue = colorsys.rgb_to_hsv(r_ratio, g_ratio, b_ratio)[0] * 360

                full_text = f"{brand} {title} {query}"
                texture = infer_texture(category, full_text)
                finish = infer_finish(category, full_text)
                color_family = infer_color_family(full_text, hue, category)

                match_score = calculate_match_score(metrics, tone_tag)
                reason = make_reason(tone_label, category, metrics)

                Product.objects.create(
                    brand=brand[:80],
                    name=title[:300],
                    category=category,

                    image_url=image_url,
                    product_url=product_url,
                    description=reason,

                    price=int(item.get("lprice") or 0),
                    mall_name=item.get("mallName", "")[:100],
                    naver_product_id=naver_product_id[:100],
                    source_query=query[:200],

                    naver_category1=item.get("category1", "")[:100],
                    naver_category2=item.get("category2", "")[:100],
                    naver_category3=item.get("category3", "")[:100],
                    naver_category4=item.get("category4", "")[:100],

                    texture=texture[:100],
                    finish=finish,
                    tone_tag=tone_tag,
                    color_family=color_family,

                    hex_code=metrics["hex_code"],
                    rgb_r=metrics["rgb_r"],
                    rgb_g=metrics["rgb_g"],
                    rgb_b=metrics["rgb_b"],

                    brightness=metrics["brightness"],
                    saturation=metrics["saturation"],
                    coolness=metrics["coolness"],
                    warmth=metrics["warmth"],
                    depth=metrics["depth"],
                    softness=metrics["softness"],
                    contrast=metrics["contrast"],

                    match_score=match_score,
                    reason=reason,
                )

                seen_keys.add(unique_key)
                saved_for_target += 1
                total_saved += 1
                category_count[category] += 1

                print(
                    "저장:",
                    tone_label,
                    category,
                    brand,
                    title[:35],
                    metrics["hex_code"],
                    f"{match_score}점",
                )

    print("\n완료!")
    print("총 저장 개수:", total_saved)
    print("카테고리별 개수:")

    for category, count in category_count.items():
        print(category, count)


if __name__ == "__main__":
    main()
