from rest_framework.decorators import api_view
from rest_framework.response import Response
## 일단 DB없이 가짜 상품 2개 보내주는 api

@api_view(['GET'])
def product_list(request):
    products = [
        {
            "id": 1,
            "brand": "롬앤",
            "name": "쥬시 래스팅 틴트",
            "category": "립틴트",
            "match_score": 92,
            "image": "https://image.oliveyoung.co.kr/uploads/images/goods/10/0000/0018/A00000018056701ko.jpg"
        },
        {
            "id": 2,
            "brand": "페리페라",
            "name": "잉크 무드 글로이 틴트",
            "category": "립틴트",
            "match_score": 88,
            "image": "https://image.oliveyoung.co.kr/uploads/images/goods/10/0000/0019/A00000019723101ko.jpg"
        },
    ]

    return Response(products)