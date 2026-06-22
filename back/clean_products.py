import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Lumiere.settings")
django.setup()

from products.models import Product


# 1. 상품명이 이런 단어를 포함하면 화장품 본품이 아니라 도구/잡화일 가능성이 높아서 삭제
BAD_KEYWORDS = [
    "스파츌라", "스패출러", "스패츌러",
    "브러시", "브러쉬", "더스트 브러시",
    "네일", "아크릴", "먼지", "청소",
    "마사지기", "마사지 기",
    "샴푸", "바디워시", "바디 워시",
    "핸드크림", "풋크림", "헤어",
    "인형", "방석", "베개", "필로우", "침구", "쿠션솜",
    "케이스", "차량", "강아지", "고양이",
]


# 2. 브랜드 미상인데 상품명에 브랜드명이 들어있는 경우 보정
BRAND_MAP = {
    "3CE": "3CE",
    "롬앤": "롬앤",
    "rom&nd": "롬앤",
    "페리페라": "페리페라",
    "peripera": "페리페라",
    "클리오": "클리오",
    "clio": "클리오",
    "데이지크": "데이지크",
    "dasique": "데이지크",
    "삐아": "삐아",
    "bbia": "삐아",
    "에뛰드": "에뛰드",
    "etude": "에뛰드",
    "웨이크메이크": "웨이크메이크",
    "wakemake": "웨이크메이크",
    "힌스": "힌스",
    "hince": "힌스",
    "어뮤즈": "어뮤즈",
    "amuse": "어뮤즈",
    "라카": "라카",
    "laka": "라카",
    "정샘물": "정샘물",
    "헤라": "헤라",
    "hera": "헤라",
    "에스쁘아": "에스쁘아",
    "espoir": "에스쁘아",
    "라네즈": "라네즈",
    "laneige": "라네즈",
    "투쿨포스쿨": "투쿨포스쿨",
    "too cool for school": "투쿨포스쿨",
    "맥": "맥",
    "MAC": "맥",
    "나스": "나스",
    "NARS": "나스",
    "크리니크": "크리니크",
    "clinique": "크리니크",
    "컬러그램": "컬러그램",
    "colorgram": "컬러그램",
    "오렌즈": "오렌즈",
    "OLENS": "오렌즈",
    "하파크리스틴": "하파크리스틴",
    "hapa kristin": "하파크리스틴",
    "렌즈미": "렌즈미",
    "lensme": "렌즈미",
    "플라워노즈": "플라워노즈",
    "flower knows": "플라워노즈",
    "피치씨": "피치씨",
    "peach c": "피치씨",
    "머지": "머지",
    "merzy": "머지",
    "입큰": "입큰",
    "ipkn": "입큰",
    "바비브라운": "바비브라운",
    "bobbi brown": "바비브라운",
}


def normalize(text):
    return str(text or "").lower().replace(" ", "")


def infer_brand(name):
    normalized_name = normalize(name)

    for keyword, brand in BRAND_MAP.items():
        if normalize(keyword) in normalized_name:
            return brand

    return ""


def main():
    print("정리 전 전체 상품 수:", Product.objects.count())
    print("정리 전 브랜드 미상 수:", Product.objects.filter(brand="브랜드 미상").count())

    deleted_count = 0
    updated_count = 0

    # 1. 이상한 상품 삭제
    for product in list(Product.objects.all()):
        normalized_name = normalize(product.name)

        if any(normalize(word) in normalized_name for word in BAD_KEYWORDS):
            print("삭제:", product.id, product.brand, product.name)
            product.delete()
            deleted_count += 1

    # 2. 브랜드 미상 보정
    for product in Product.objects.filter(brand="브랜드 미상"):
        guessed_brand = infer_brand(product.name)

        if guessed_brand:
            print("브랜드 보정:", product.id, product.name, "=>", guessed_brand)
            product.brand = guessed_brand[:80]
            product.save()
            updated_count += 1

    print()
    print("정리 완료")
    print("삭제한 상품 수:", deleted_count)
    print("브랜드 보정 수:", updated_count)
    print("정리 후 전체 상품 수:", Product.objects.count())
    print("정리 후 브랜드 미상 수:", Product.objects.filter(brand="브랜드 미상").count())


if __name__ == "__main__":
    main()