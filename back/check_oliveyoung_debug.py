import requests
from bs4 import BeautifulSoup

url = input("올리브영 상품 URL을 붙여넣고 Enter 누르세요: ").strip()

if not url.startswith("http"):
    print("URL이 잘못됐어요. https:// 로 시작하는 올리브영 상품 URL을 넣어야 해요.")
    exit()

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.oliveyoung.co.kr/",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

res = requests.get(url, headers=headers, timeout=10)

print("상태코드:", res.status_code)
print("최종 URL:", res.url)
print("HTML 길이:", len(res.text))
print("앞부분 500자:")
print(res.text[:500])

soup = BeautifulSoup(res.text, "html.parser")

print("title:", soup.title.get_text(strip=True) if soup.title else "title 없음")

check_words = ["상품", "브랜드", "goodsNm", "brandNm", "option", "옵션", "price", "goodsNo"]

for word in check_words:
    print(word, "포함 여부:", word in res.text)

with open("debug_oliveyoung.html", "w", encoding="utf-8") as f:
    f.write(res.text)

print("debug_oliveyoung.html 저장 완료")