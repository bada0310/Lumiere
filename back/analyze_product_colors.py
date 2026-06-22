import colorsys
import os
import re
import sys
from collections import defaultdict
from io import BytesIO
from urllib.request import Request, urlopen

from PIL import Image


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Lumiere.settings")

import django  # noqa: E402

django.setup()

from products.models import Product  # noqa: E402


def clamp(value, min_value=0, max_value=100):
    return max(min_value, min(max_value, int(round(value))))


KEYWORD_COLORS = [
    (("라벤더", "라일락", "퍼플", "보라", "쿨블렌딩"), "#b99ac9", "LAVENDER", 88, 12),
    (("모브", "뮤트핑크", "말린장미"), "#b7798f", "ROSE", 78, 22),
    (("베리", "푸시아", "버건디", "플럼"), "#b84d72", "BERRY", 84, 16),
    (("로즈", "로지", "장미"), "#c45b75", "ROSE", 74, 26),
    (("핑크", "핑크소다", "리본핑크"), "#df8fa5", "PINK", 70, 30),
    (("코랄",), "#e57966", "CORAL", 25, 75),
    (("피치", "복숭아"), "#f0a080", "CORAL", 20, 80),
    (("오렌지",), "#e06f45", "CORAL", 12, 88),
    (("브라운", "초코", "카카오"), "#8f5d48", "BROWN", 24, 76),
    (("베이지", "누드", "바닐라", "아이보리", "샌드"), "#e8c7ad", "BEIGE", 40, 60),
    (("그레이", "애쉬", "회색"), "#9f9aa3", "GRAY", 62, 38),
    (("레드", "빨강"), "#c83f4f", "RED", 55, 45),
]

COOL_WORDS = ("쿨톤", "여름쿨", "겨울쿨", "쿨 ")
WARM_WORDS = ("웜톤", "봄웜", "가을웜", "웜 ")
MUTE_WORDS = ("뮤트", "블러", "소프트", "차분", "말린")
BRIGHT_WORDS = ("브라이트", "비비드", "선명", "맑은")
LIGHT_WORDS = ("라이트", "밀크", "베어", "누드", "아이보리", "21호", "17호")
DEEP_WORDS = ("딥", "다크", "버건디", "브라운", "초코")


COLOR_FAMILY_BY_HUE = [
    ((330, 360), "PINK"),
    ((0, 12), "RED"),
    ((12, 28), "CORAL"),
    ((28, 48), "CORAL"),
    ((48, 70), "BEIGE"),
    ((250, 290), "LAVENDER"),
    ((290, 330), "BERRY"),
]


def normalize_text(value):
    return re.sub(r"\s+", "", str(value or "").lower())


def hex_to_rgb(hex_code):
    value = hex_code.strip().lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*[clamp(v, 0, 255) for v in rgb])


def blend_rgb(a, b, image_weight=0.65):
    return tuple(
        int(round((a[i] * image_weight) + (b[i] * (1 - image_weight))))
        for i in range(3)
    )


def get_keyword_hint(product):
    text = normalize_text(f"{product.brand} {product.name} {product.description}")

    for keywords, hex_code, family, coolness, warmth in KEYWORD_COLORS:
        if any(normalize_text(keyword) in text for keyword in keywords):
            return {
                "hex": hex_code,
                "rgb": hex_to_rgb(hex_code),
                "family": family,
                "coolness": coolness,
                "warmth": warmth,
            }

    return None


def download_image(url, timeout=8):
    if not url:
        return None

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
            )
        },
    )

    with urlopen(request, timeout=timeout) as response:
        return response.read()


def is_useful_pixel(r, g, b, category):
    h, lightness, saturation = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    hue = h * 360

    if lightness >= 0.92:
        return False
    if lightness <= 0.08:
        return False

    if category == "BASE":
        if saturation < 0.04:
            return False
        return 5 <= hue <= 70 and 0.35 <= lightness <= 0.88

    if category == "LENS":
        return 0.18 <= lightness <= 0.82 and saturation >= 0.04

    if saturation < 0.10:
        return False

    cosmetic_hue = (
        hue <= 70
        or hue >= 285
        or 230 <= hue <= 285
    )
    return cosmetic_hue


def extract_representative_rgb(image_bytes, category):
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image.thumbnail((180, 180))

    buckets = defaultdict(lambda: [0, 0, 0, 0, 0.0])

    for r, g, b in image.getdata():
        if not is_useful_pixel(r, g, b, category):
            continue

        h, lightness, saturation = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        key = (r // 16, g // 16, b // 16)

        lightness_bonus = 1.0 - min(abs(lightness - 0.58), 0.45)
        saturation_bonus = 0.45 + saturation
        score = saturation_bonus * lightness_bonus

        buckets[key][0] += r
        buckets[key][1] += g
        buckets[key][2] += b
        buckets[key][3] += 1
        buckets[key][4] += score

    if not buckets:
        return None

    best = max(buckets.values(), key=lambda item: item[4])
    pixel_count = max(best[3], 1)

    rgb = (
        clamp(best[0] / pixel_count, 0, 255),
        clamp(best[1] / pixel_count, 0, 255),
        clamp(best[2] / pixel_count, 0, 255),
    )

    return rgb


def color_family_from_hue(hue):
    for (start, end), family in COLOR_FAMILY_BY_HUE:
        if start <= hue < end:
            return family
    if 70 <= hue < 165:
        return "BEIGE"
    if 165 <= hue < 250:
        return "GRAY"
    return "ETC"


def get_temperature_scores(family, hue, text, keyword_hint):
    if keyword_hint:
        coolness = keyword_hint["coolness"]
        warmth = keyword_hint["warmth"]
    elif family in ("PINK", "ROSE", "BERRY", "LAVENDER", "GRAY"):
        coolness, warmth = 72, 28
    elif family in ("CORAL", "BROWN", "BEIGE", "IVORY"):
        coolness, warmth = 28, 72
    elif hue >= 285 or hue <= 8:
        coolness, warmth = 60, 40
    elif 8 < hue <= 70:
        coolness, warmth = 35, 65
    else:
        coolness, warmth = 50, 50

    if any(word in text for word in COOL_WORDS):
        coolness += 18
        warmth -= 10

    if any(word in text for word in WARM_WORDS):
        warmth += 18
        coolness -= 10

    coolness = clamp(coolness)
    warmth = clamp(warmth)

    total = max(coolness + warmth, 1)
    coolness = clamp((coolness / total) * 100)
    warmth = clamp(100 - coolness)

    return coolness, warmth


def get_tone_tag(brightness, saturation, coolness, warmth, softness, text):
    is_cool = coolness >= warmth
    is_light = brightness >= 66 or any(word in text for word in LIGHT_WORDS)
    is_deep = brightness <= 42 or any(word in text for word in DEEP_WORDS)
    is_bright = saturation >= 58 or any(word in text for word in BRIGHT_WORDS)
    is_mute = softness >= 52 or any(word in text for word in MUTE_WORDS)

    if is_cool:
        if is_deep:
            return Product.ToneTag.WINTER_DEEP
        if is_bright:
            return Product.ToneTag.WINTER_BRIGHT
        if is_mute:
            return Product.ToneTag.SUMMER_MUTE
        return Product.ToneTag.SUMMER_LIGHT

    if is_deep:
        return Product.ToneTag.AUTUMN_DEEP
    if is_mute:
        return Product.ToneTag.AUTUMN_MUTE
    if is_bright:
        return Product.ToneTag.SPRING_BRIGHT
    return Product.ToneTag.SPRING_LIGHT


def get_finish(product):
    text = normalize_text(f"{product.name} {product.description} {product.texture}")

    if "매트" in text:
        return Product.Finish.MATTE
    if "벨벳" in text or "블러" in text:
        return Product.Finish.VELVET
    if "글로" in text or "광" in text or "촉촉" in text or "워터" in text:
        return Product.Finish.GLOSSY
    if "쉬머" in text or "글리터" in text or "펄" in text:
        return Product.Finish.SHIMMER
    return product.finish or Product.Finish.UNKNOWN


def analyze_product(product):
    text = normalize_text(f"{product.brand} {product.name} {product.description}")
    keyword_hint = get_keyword_hint(product)
    image_rgb = None

    try:
        image_bytes = download_image(product.image_url)
        image_rgb = extract_representative_rgb(image_bytes, product.category)
    except Exception:
        image_rgb = None

    if image_rgb and keyword_hint:
        rgb = blend_rgb(image_rgb, keyword_hint["rgb"], image_weight=0.65)
    elif image_rgb:
        rgb = image_rgb
    elif keyword_hint:
        rgb = keyword_hint["rgb"]
    else:
        fallback = {
            "LIP": "#c45b75",
            "EYE": "#b99ac9",
            "CHEEK": "#e89aac",
            "BASE": "#e8c7ad",
            "LENS": "#9f9ab0",
        }.get(product.category, "#c45b75")
        rgb = hex_to_rgb(fallback)

    r, g, b = rgb
    hue_raw, lightness_raw, saturation_raw = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    hue = hue_raw * 360
    brightness = clamp(lightness_raw * 100)
    saturation = clamp(saturation_raw * 100)
    depth = clamp(100 - brightness)
    softness = clamp((100 - saturation) * 0.72 + max(0, 58 - brightness) * 0.18)
    contrast = clamp(abs(brightness - 72) * 0.65 + saturation * 0.35)

    family = keyword_hint["family"] if keyword_hint else color_family_from_hue(hue)
    coolness, warmth = get_temperature_scores(family, hue, text, keyword_hint)
    tone_tag = get_tone_tag(brightness, saturation, coolness, warmth, softness, text)

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
        "color_family": family if family in Product.ColorFamily.values else Product.ColorFamily.ETC,
        "tone_tag": tone_tag,
        "finish": get_finish(product),
    }


def main():
    products = Product.objects.exclude(image_url="").order_by("id")
    total = products.count()
    updated = 0
    failed = 0

    print(f"색상 분석 시작: {total}개")

    for index, product in enumerate(products, start=1):
        try:
            result = analyze_product(product)

            for field, value in result.items():
                setattr(product, field, value)

            product.reason = (
                f"대표 색상 {result['hex_code']} 기준으로 명도 {result['brightness']}, "
                f"채도 {result['saturation']}, 쿨 {result['coolness']}/웜 {result['warmth']} "
                "방향성을 분석했어요."
            )
            product.save(update_fields=[*result.keys(), "reason", "updated_at"])
            updated += 1

            print(
                f"[{index}/{total}] OK {product.id} {product.brand} "
                f"{result['hex_code']} 명도 {result['brightness']} 채도 {result['saturation']}"
            )
        except Exception as error:
            failed += 1
            print(f"[{index}/{total}] FAIL {product.id} {product.name}: {error}")

    print("")
    print("색상 분석 완료")
    print(f"업데이트: {updated}개")
    print(f"실패: {failed}개")


if __name__ == "__main__":
    main()
