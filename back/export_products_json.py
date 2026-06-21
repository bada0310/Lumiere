import json
import requests

API_URL = "http://127.0.0.1:8000/api/products/"
OUTPUT_FILE = "products.json"

res = requests.get(API_URL, headers={"Accept": "application/json"})

print("상태코드:", res.status_code)

if res.status_code != 200:
    print("API 요청 실패")
    print(res.text)
    exit()

products = res.json()

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print(f"저장 완료: {OUTPUT_FILE}")
print(f"상품 개수: {len(products)}개")