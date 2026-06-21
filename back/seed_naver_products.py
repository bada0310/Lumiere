import os
import re
import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Lumiere.settings")
django.setup()

from products.models import Product


CLIENT_ID = ""
CLIENT_SECRET = ""

NAVER_URL = "https://openapi.naver.com/v1/search/shop.json"

HEADERS = {
    "X-Naver-Client-Id": CLIENT_ID,
    "X-Naver-Client-Secret": CLIENT_SECRET,
}


SEARCH_TARGETS = [
    ("여름쿨 립틴트 화장품", Product.Category.LIP),
    ("쿨톤 립글로스 화장품", Product.Category.LIP),

    ("여름쿨 아이팔레트 화장품", Product.Category.EYE),
    ("쿨톤 아이섀도우 팔레트 화장품", Product.Category.EYE),

    ("여름쿨 쿠션 파운데이션 화장품", Product.Category.BASE),
    ("쿨톤 베이스 메이크업 쿠션 화장품", Product.Category.BASE),
]


INCLUDE_KEYWORDS = {
    Product.Category.LIP: [
        "립", "틴트", "글로스", "립스틱", "라커", "벨벳"
    ],
    Product.Category.EYE: [
        "아이", "팔레트", "섀도우", "쉐도우", "마스카라", "아이라이너"
    ],
    Product.Category.BASE: [
        "쿠션", "파운데이션", "컨실러", "비비", "BB", "씨씨", "CC", "베이스", "톤업"
    ],
}


EXCLUDE_KEYWORDS = [
    "바디필로우", "필로우", "베개", "방석", "쿠션솜", "침구", "이불",
    "매트", "패드", "인형", "커버", "시트", "냉감바디", "냉감 바디",
    "샤워", "바디워시", "로션", "크림", "핸드", "풋", "헤어", "샴푸"
]


def clean_html(text):
    return re.sub("<.*?>", "", text or "")


def is_valid_product(item, category):
    title = clean_html(item.get("title", ""))
    category1 = item.get("category1", "")
    category2 = item.get("category2", "")
    category3 = item.get("category3", "")
    category4 = item.get("category4", "")

    full_text = f"{title} {category1} {category2} {category3} {category4}"

    # 1. 네이버 쇼핑 카테고리가 화장품/미용이 아니면 제외
    if category1 != "화장품/미용":
        return False

    # 2. 제목에 침구/바디필로우/방석 같은 단어가 있으면 제외
    for word in EXCLUDE_KEYWORDS:
        if word.lower() in full_text.lower():
            return False

    # 3. 립/아이/베이스별 필요한 키워드가 하나라도 있어야 저장
    include_words = INCLUDE_KEYWORDS.get(category, [])
    has_include_keyword = any(word.lower() in full_text.lower() for word in include_words)

    if not has_include_keyword:
        return False

    return True


def fetch_products(query):
    params = {
        "query": query,
        "display": 30,
        "start": 1,
        "sort": "sim",
        "exclude": "used:rental:cbshop",
    }

    res = requests.get(NAVER_URL, headers=HEADERS, params=params)

    print("\n검색어:", query)
    print("상태코드:", res.status_code)

    if res.status_code != 200:
        print(res.text)
        return []

    return res.json().get("items", [])


def main():
    Product.objects.all().delete()

    total = 0
    seen_links = set()

    for query, category in SEARCH_TARGETS:
        items = fetch_products(query)
        saved_count = 0

        for item in items:
            if saved_count >= 10:
                break

            title = clean_html(item.get("title", ""))
            brand = item.get("brand") or item.get("maker") or "브랜드 미상"
            image_url = item.get("image", "")
            product_url = item.get("link", "")

            if product_url in seen_links:
                print("중복 제외:", title)
                continue

            if not is_valid_product(item, category):
                print("제외:", title, "|", item.get("category1"), item.get("category2"))
                continue

            Product.objects.create(
                brand=brand[:80],
                name=title[:120],
                category=category,
                image_url=image_url,
                product_url=product_url,
                description=f"{query} 검색 결과 기반 추천 상품입니다.",
                match_score=90,
            )

            seen_links.add(product_url)
            saved_count += 1
            total += 1

            print("저장:", brand, title)

    print("\n완료! 저장 개수:", total)


if __name__ == "__main__":
    main()