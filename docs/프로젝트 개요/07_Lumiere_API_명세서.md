# Lumiere API 명세서

작성일: 2026-06-24  
기준 코드: Django REST Framework 백엔드 라우팅 기준

## 1. 공통 정보

### Base URL

개발 서버 기준:

```text
http://127.0.0.1:8000
```

주요 API Prefix:

```text
/accounts/
/api/diagnosis/
/api/products/
/api/community/
/api/engagements/
```

### 인증 방식

JWT 인증:

```http
Authorization: Bearer {access_token}
```

세션 인증:

```text
sessionid 쿠키 기반 인증
```

### 공통 Header

JSON 요청:

```http
Content-Type: application/json
```

파일 업로드 요청:

```http
Content-Type: multipart/form-data
```

### 공통 목록 응답

일부 목록 API는 `limit`, `page`, `page_size`를 지원한다.

`limit`만 사용한 경우:

```json
[
  { "id": 1 }
]
```

`page` 또는 `page_size` 사용 시:

```json
{
  "count": 25,
  "page": 1,
  "page_size": 10,
  "total_pages": 3,
  "next": 2,
  "previous": null,
  "results": []
}
```

## 2. 계정 API

### 2.1 회원가입

```http
POST /accounts/signup/
```

인증: 불필요

Request Body:

```json
{
  "username": "user01",
  "password": "password1234",
  "email": "user01@example.com"
}
```

Response `201`:

```json
{
  "message": "회원가입이 완료되었습니다."
}
```

### 2.2 세션 로그인

```http
POST /accounts/session-login/
```

인증: 불필요

Request Body:

```json
{
  "username": "user01",
  "password": "password1234"
}
```

Response `200`:

```json
{
  "message": "user01님, 세션 로그인 성공!"
}
```

### 2.3 세션 로그아웃

```http
POST /accounts/session-logout/
```

인증: 불필요

Response `200`:

```json
{
  "message": "로그아웃 되었습니다."
}
```

### 2.4 JWT 로그인

```http
POST /accounts/jwt-login/
```

인증: 불필요

Request Body:

```json
{
  "username": "user01",
  "password": "password1234"
}
```

Response `200`:

```json
{
  "refresh": "refresh_token",
  "access": "access_token"
}
```

### 2.5 JWT 토큰 갱신

```http
POST /accounts/jwt-refresh/
```

인증: 불필요

Request Body:

```json
{
  "refresh": "refresh_token"
}
```

Response `200`:

```json
{
  "access": "new_access_token"
}
```

### 2.6 내 정보 조회

```http
GET /accounts/user/
```

인증: 필요

Response `200`:

```json
{
  "id": 1,
  "username": "user01",
  "nickname": "루미에르_1234",
  "email": "user01@example.com",
  "profile_image_url": "http://127.0.0.1:8000/media/profiles/uploads/...",
  "requires_password_confirmation": true
}
```

### 2.7 내 정보 수정

```http
PATCH /accounts/user/update/
```

인증: 필요  
Content-Type: `multipart/form-data`

Request Form Data:

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| nickname | string | 선택 | 변경할 닉네임 |
| email | string | 선택 | 변경할 이메일 |
| profile_image | file | 선택 | JPG, PNG, WEBP, 최대 5MB |

Response `200`: 내 정보 조회 응답과 동일

### 2.8 회원 탈퇴

```http
DELETE /accounts/user/delete/
```

인증: 필요

Request Body:

```json
{
  "confirmation": "탈퇴합니다",
  "password": "password1234"
}
```

Response `200`:

```json
{
  "message": "회원탈퇴가 완료되었습니다."
}
```

### 2.9 아이디 중복 확인

```http
POST /accounts/check-username/
```

인증: 불필요

Request Body:

```json
{
  "username": "user01"
}
```

Response `200`:

```json
{
  "is_available": true,
  "message": "사용 가능한 아이디입니다."
}
```

### 2.10 닉네임 중복 확인

```http
POST /accounts/check-nickname/
```

인증: 필요

Request Body:

```json
{
  "nickname": "새닉네임"
}
```

Response `200`:

```json
{
  "is_available": true,
  "message": "사용 가능한 닉네임입니다."
}
```

### 2.11 임시 비밀번호 발급

```http
POST /accounts/find-password/
```

인증: 불필요

Request Body:

```json
{
  "email": "user01@example.com"
}
```

Response `200`:

```json
{
  "message": "임시 비밀번호가 이메일로 발송되었습니다."
}
```

## 3. 퍼스널컬러 진단 API

### 3.1 AI 퍼스널컬러 진단 실행

```http
POST /api/diagnosis/analyze/
```

인증: 필요  
Content-Type: `multipart/form-data`

Request Form Data:

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| image | file | 필수 | 진단할 얼굴 이미지 |

Response `201`: DiagnosisResult 객체

주요 응답 필드:

```json
{
  "id": 1,
  "status": "completed",
  "tone_key": "summer_cool_mute",
  "tone_label": "여름 쿨 뮤트",
  "personal_color_code": "summer_cool_mute",
  "korean_name": "여름 쿨 뮤트",
  "english_name": "Summer Cool Mute",
  "confidence": 82,
  "diagnosed_at": "2026-06-24",
  "summary": "진단 요약",
  "uploaded_image_url": "http://127.0.0.1:8000/media/diagnosis/originals/...",
  "processed_image_url": null,
  "palette_status": "ready",
  "keywords": ["차분한", "부드러운"],
  "skin_metrics": {
    "brightness": 55,
    "saturation": 38,
    "clarity": 82,
    "contrast": 25,
    "cool_warm": 82,
    "softness": 85,
    "gloss": 50
  },
  "representative_colors": [],
  "color_palettes": {
    "best": [],
    "neutral": [],
    "accent": [],
    "try": [],
    "worst": []
  },
  "makeover_styles": [],
  "makeup_generation_status": "none",
  "is_primary": true
}
```

Error:

| Status | code | 설명 |
| --- | --- | --- |
| 400 | image_required | 이미지 파일 누락 |
| 400 | palette_missing | toneKey 팔레트 없음 |
| 400 | invalid_diagnosis | 진단 결과 검증 실패 |
| 502 | invalid_ai_response | AI 응답 파싱 실패 |
| 503 | ai_not_configured | AI 설정 누락 |

### 3.2 진단 결과 목록 조회

```http
GET /api/diagnosis/results/
```

인증: 필요

Query Parameters:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| limit | number | 상위 N개만 배열로 반환 |
| page | number | 페이지 번호 |
| page_size | number | 페이지 크기, 최대 50 |

Response `200`: DiagnosisResult 배열 또는 페이지 객체

### 3.3 진단 결과 수동 생성

```http
POST /api/diagnosis/results/
```

인증: 필요

비고: 일반 사용 흐름에서는 `/api/diagnosis/analyze/` 사용을 권장한다. 이 엔드포인트는 DRF serializer 기반 수동 생성용이다.

Request Body 예시:

```json
{
  "personal_color_id": 1,
  "status": "completed",
  "tone_key": "summer_cool_mute",
  "personal_color_code": "summer_cool_mute",
  "korean_name": "여름 쿨 뮤트",
  "english_name": "Summer Cool Mute",
  "confidence_score": 82,
  "summary": "진단 요약"
}
```

Response `201`: DiagnosisResult 객체

### 3.4 진단 결과 상세 조회

```http
GET /api/diagnosis/results/{result_id}/
```

인증: 필요

Response `200`: DiagnosisResult 객체

### 3.5 진단 결과 삭제

```http
DELETE /api/diagnosis/results/{result_id}/
```

인증: 필요

Response `200`:

```json
{
  "deleted_id": 1,
  "was_primary": true,
  "new_primary_id": null,
  "new_primary": null,
  "message": "진단 결과가 삭제되었습니다."
}
```

### 3.6 메인 퍼스널컬러 설정

```http
POST /api/diagnosis/results/{result_id}/set-primary/
```

인증: 필요

Response `200`: DiagnosisResult 객체 + message

```json
{
  "id": 1,
  "is_primary": true,
  "message": "메인 퍼스널컬러로 설정되었습니다."
}
```

### 3.7 메인 퍼스널컬러 설정 취소

```http
POST /api/diagnosis/results/{result_id}/unset-primary/
```

인증: 필요

Response `200`: DiagnosisResult 객체 + message

```json
{
  "id": 1,
  "is_primary": false,
  "message": "메인 퍼스널컬러 설정이 취소되었습니다."
}
```

### 3.8 최신 메인 진단 결과 조회

```http
GET /api/diagnosis/latest/
```

인증: 필요

Response `200`:

```json
{
  "id": 1,
  "tone_key": "summer_cool_mute",
  "is_primary": true
}
```

메인 진단 결과가 없으면 `null` 반환.

### 3.9 데모 진단 결과 조회

```http
GET /api/diagnosis/demo/
```

인증: 불필요

Response `200`: 데모 DiagnosisResult 객체

### 3.10 AI 메이크오버 상태 조회

```http
GET /api/diagnosis/results/{result_id}/makeovers/
```

인증: 필요

Response `200`:

```json
{
  "status": "queued",
  "styles": [
    {
      "key": "natural_daily",
      "name": "내추럴 데일리메이크업",
      "description": "피부결과 혈색을 은은하게 살린 자연스러운 메이크업",
      "image": "diagnosis/generated/makeovers/makeup-1-natural_daily.png",
      "image_url": "http://127.0.0.1:8000/media/diagnosis/generated/makeovers/makeup-1-natural_daily.png",
      "status": "complete",
      "error_message": "",
      "order": 1,
      "is_default": true
    }
  ],
  "error": ""
}
```

### 3.11 AI 메이크오버 생성 시작

```http
POST /api/diagnosis/results/{result_id}/makeovers/
```

인증: 필요

동작:

1. `DEFAULT_MAKEOVER_STYLES` 기준 5개 스타일 job 생성
2. 백그라운드 worker 시작
3. 각 job마다 이미지 생성 API 호출
4. 완료 시 `image_url`로 생성 이미지 제공

Response `202`: 메이크오버 상태 응답

Error:

| Status | 설명 |
| --- | --- |
| 400 | 완료된 진단 결과가 아님 |
| 400 | 고정 팔레트가 준비되지 않음 |
| 400 | 원본 이미지 없음 |

### 3.12 AI 메이크오버 개별 스타일 재생성

```http
POST /api/diagnosis/results/{result_id}/makeovers/{style_key}/retry/
```

인증: 필요

Path Parameters:

| 이름 | 예시 |
| --- | --- |
| style_key | natural_daily, pure_daily, romantic, chic, smoky |

Response `202`: 메이크오버 상태 응답

## 4. 상품 API

### 4.1 상품 목록 조회

```http
GET /api/products/
```

인증: 선택

Query Parameters:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| category | string | LIP, EYE, CHEEK, BASE, LENS, ETC |
| q | string | 상품명 또는 브랜드 검색어 |
| tone_key | string | 추천 정렬에 사용할 퍼스널컬러 toneKey |
| second_tone_key | string | 보조 toneKey |

Response `200`: Product 배열

Product 주요 필드:

```json
{
  "id": 1,
  "brand": "브랜드명",
  "name": "상품명",
  "category": "LIP",
  "image": "https://...",
  "image_url": "https://...",
  "product_url": "https://...",
  "price": 15000,
  "mall_name": "네이버쇼핑",
  "texture": "립틴트",
  "finish": "VELVET",
  "tone_tag": "SUMMER_MUTE",
  "color_family": "ROSE",
  "hex_code": "#C96A7B",
  "match_score": 87,
  "reason": "추천 사유",
  "min_price": 12000,
  "max_price": 18000,
  "best_option": {},
  "options": [],
  "review_count": 2,
  "average_rating": 4.5,
  "created_at": "2026-06-24T00:00:00Z",
  "updated_at": "2026-06-24T00:00:00Z"
}
```

### 4.2 상품 상세 조회

```http
GET /api/products/{product_id}/
```

인증: 선택

Query Parameters:

| 이름 | 설명 |
| --- | --- |
| tone_key | 추천 점수 계산 기준 toneKey |
| second_tone_key | 보조 toneKey |

Response `200`: Product 객체

### 4.3 상품 색상 분석 조회

```http
GET /api/products/{product_id}/color-analysis/
```

인증: 불필요

Response `200`: 상품 카탈로그 색상 분석 결과

### 4.4 상품 URL 색상 분석

```http
POST /api/products/color-analysis/
```

인증: 불필요

Request Body:

```json
{
  "product_url": "https://www.oliveyoung.co.kr/..."
}
```

Response `200`:

```json
{
  "success": true,
  "source_url": "https://www.oliveyoung.co.kr/...",
  "title": "상품명",
  "brand": "브랜드명",
  "product_name": "상품명",
  "image_url": "https://...",
  "colors": [],
  "result_payload": {}
}
```

Error `400`:

```json
{
  "success": false,
  "message": "상품 정보를 가져올 수 없습니다. URL을 다시 확인해주세요.",
  "detail": "상품 정보를 가져올 수 없습니다. URL을 다시 확인해주세요.",
  "code": "PRODUCT_URL_ANALYSIS_FAILED"
}
```

### 4.5 상품 URL 스크래핑

```http
POST /api/products/scrape/
```

인증: 불필요

Request Body:

```json
{
  "product_url": "https://www.oliveyoung.co.kr/..."
}
```

Response `200`: 스크래핑 결과

Error `400`:

```json
{
  "status": "fail",
  "message": "The URL is unsupported or temporarily inaccessible.",
  "code": "SCRAPE_FAILED"
}
```

### 4.6 상품 Router API

DRF router로 제공되는 상품 CRUD API다.

| Method | URL | 인증 | 설명 |
| --- | --- | --- | --- |
| GET | `/api/products/items/` | 선택 | 상품 목록 |
| POST | `/api/products/items/` | 필요 | 상품 생성 |
| GET | `/api/products/items/{id}/` | 선택 | 상품 상세 |
| PUT/PATCH | `/api/products/items/{id}/` | 필요 | 상품 수정 |
| DELETE | `/api/products/items/{id}/` | 필요 | 상품 삭제 |

### 4.7 리뷰 API

| Method | URL | 인증 | 설명 |
| --- | --- | --- | --- |
| GET | `/api/products/reviews/` | 선택 | 리뷰 목록 |
| POST | `/api/products/reviews/` | 필요 | 리뷰 작성 |
| GET | `/api/products/reviews/{id}/` | 선택 | 리뷰 상세 |
| PUT/PATCH | `/api/products/reviews/{id}/` | 작성자 | 리뷰 수정 |
| DELETE | `/api/products/reviews/{id}/` | 작성자 | 리뷰 삭제 |

리뷰 목록 Query Parameters:

| 이름 | 설명 |
| --- | --- |
| product | 특정 상품 ID로 필터링 |

리뷰 작성 Request Body:

```json
{
  "product": 1,
  "rating": 5,
  "content": "발색이 좋아요.",
  "image_url": "https://..."
}
```

Response:

```json
{
  "id": 1,
  "product": 1,
  "author_id": 1,
  "author_username": "user01",
  "author_nickname": "루미에르_1234",
  "rating": 5,
  "content": "발색이 좋아요.",
  "image_url": "https://...",
  "created_at": "2026-06-24T00:00:00Z",
  "updated_at": "2026-06-24T00:00:00Z"
}
```

## 5. 커뮤니티 API

### 5.1 게시글 목록 조회

```http
GET /api/community/posts/
```

인증: 선택

Query Parameters:

| 이름 | 설명 |
| --- | --- |
| category | LIFE_ITEM, COLOR_REVIEW, QUESTION, PRODUCT_RECOMMENDATION, ROUTINE, FREE |
| product | 상품 ID |
| author | 작성자 ID |
| q | 제목/내용 검색어 |
| limit | 상위 N개 |
| page | 페이지 번호 |
| page_size | 페이지 크기 |

Response `200`: Post 배열 또는 페이지 객체

### 5.2 게시글 작성

```http
POST /api/community/posts/
```

인증: 필요

Request Body:

```json
{
  "title": "여름쿨 추천템 공유",
  "content": "이 립 색이 잘 맞았어요.",
  "category": "LIFE_ITEM",
  "product_ids": [1, 2],
  "image_url": "https://..."
}
```

Response `201`:

```json
{
  "id": 1,
  "author_id": 1,
  "author_username": "user01",
  "author_nickname": "루미에르_1234",
  "title": "여름쿨 추천템 공유",
  "content": "이 립 색이 잘 맞았어요.",
  "category": "LIFE_ITEM",
  "products": [],
  "image_url": "https://...",
  "view_count": 0,
  "comment_count": 0,
  "like_count": 0,
  "is_liked": false,
  "created_at": "2026-06-24T00:00:00Z",
  "updated_at": "2026-06-24T00:00:00Z"
}
```

### 5.3 게시글 상세 조회

```http
GET /api/community/posts/{id}/
```

인증: 선택

비고: 상세 조회 시 `view_count`가 1 증가한다.

Response `200`: Post 객체

### 5.4 게시글 수정/삭제

```http
PATCH /api/community/posts/{id}/
DELETE /api/community/posts/{id}/
```

인증: 작성자만 가능

### 5.5 내 게시글 조회

```http
GET /api/community/posts/mine/
```

인증: 필요

Response `200`: Post 목록

### 5.6 게시글 좋아요 토글

```http
POST /api/community/posts/{id}/like/
```

인증: 필요

Response `201`:

```json
{
  "is_liked": true
}
```

이미 좋아요 상태에서 다시 호출하면 Response `200`:

```json
{
  "is_liked": false
}
```

### 5.7 게시글 댓글 목록/작성

```http
GET /api/community/posts/{id}/comments/
POST /api/community/posts/{id}/comments/
```

GET 인증: 선택  
POST 인증: 필요

댓글 작성 Request Body:

```json
{
  "content": "저도 써봤는데 좋았어요.",
  "parent": null
}
```

대댓글 작성 Request Body:

```json
{
  "content": "맞아요!",
  "parent": 10
}
```

Response `201`:

```json
{
  "id": 10,
  "post": 1,
  "author_id": 1,
  "author_username": "user01",
  "author_nickname": "루미에르_1234",
  "parent": null,
  "content": "저도 써봤는데 좋았어요.",
  "like_count": 0,
  "is_liked": false,
  "replies": [],
  "created_at": "2026-06-24T00:00:00Z",
  "updated_at": "2026-06-24T00:00:00Z"
}
```

### 5.8 댓글 Router API

| Method | URL | 인증 | 설명 |
| --- | --- | --- | --- |
| GET | `/api/community/comments/` | 선택 | 댓글 목록 |
| POST | `/api/community/comments/` | 필요 | 댓글 작성 |
| GET | `/api/community/comments/{id}/` | 선택 | 댓글 상세 |
| PUT/PATCH | `/api/community/comments/{id}/` | 작성자 | 댓글 수정 |
| DELETE | `/api/community/comments/{id}/` | 작성자 | 댓글 삭제 |

댓글 목록 Query Parameters:

| 이름 | 설명 |
| --- | --- |
| post | 게시글 ID |

### 5.9 댓글 좋아요 토글

```http
POST /api/community/comments/{id}/like/
```

인증: 필요

Response:

```json
{
  "is_liked": true
}
```

## 6. 참여/찜 API

### 6.1 찜한 상품 옵션 목록 조회

```http
GET /api/engagements/liked-options/
```

인증: 필요

Query Parameters:

| 이름 | 설명 |
| --- | --- |
| limit | 상위 N개 |
| page | 페이지 번호 |
| page_size | 페이지 크기 |

Response `200`: LikedProductOption 배열 또는 페이지 객체

### 6.2 상품 옵션 찜 생성

```http
POST /api/engagements/liked-options/
```

인증: 필요

Request Body:

```json
{
  "product_id": 1,
  "product_option_id": 3,
  "group_key": "LIP-1",
  "snapshot": {
    "brand": "브랜드명",
    "name": "상품명"
  }
}
```

`product_option_id`가 있으면 `product_id`는 옵션의 상품 ID로 자동 보완된다.

Response `201`:

```json
{
  "id": 1,
  "product": {},
  "product_option": {},
  "option_id": "3",
  "group_key": "LIP-1",
  "brand": "브랜드명",
  "name": "상품명",
  "option": "옵션명",
  "image_url": "https://...",
  "product_url": "https://...",
  "snapshot": {},
  "created_at": "2026-06-24T00:00:00Z",
  "updated_at": "2026-06-24T00:00:00Z"
}
```

### 6.3 상품 옵션 찜 토글

```http
POST /api/engagements/liked-options/toggle/
```

인증: 필요

Request Body:

```json
{
  "product_id": 1,
  "product_option_id": 3
}
```

Response `201`:

```json
{
  "is_liked": true,
  "item": {}
}
```

이미 찜한 상태에서 다시 호출하면 Response `200`:

```json
{
  "is_liked": false
}
```

### 6.4 상품 옵션 찜 상세/수정/삭제

| Method | URL | 인증 | 설명 |
| --- | --- | --- | --- |
| GET | `/api/engagements/liked-options/{id}/` | 필요 | 상세 조회 |
| PUT/PATCH | `/api/engagements/liked-options/{id}/` | 필요 | 수정 |
| DELETE | `/api/engagements/liked-options/{id}/` | 필요 | 삭제 |

### 6.5 URL 분석 기록 목록 조회

```http
GET /api/engagements/url-analyses/
```

인증: 필요

Response `200`: UrlAnalysisRecord 배열 또는 페이지 객체

### 6.6 URL 분석 기록 생성

```http
POST /api/engagements/url-analyses/
```

인증: 필요

Request Body:

```json
{
  "source_url": "https://www.oliveyoung.co.kr/...",
  "title": "상품 분석 결과",
  "brand": "브랜드명",
  "product_name": "상품명",
  "image_url": "https://...",
  "colors": [],
  "result_payload": {}
}
```

Response `201`:

```json
{
  "id": 1,
  "source_url": "https://www.oliveyoung.co.kr/...",
  "title": "상품 분석 결과",
  "brand": "브랜드명",
  "product_name": "상품명",
  "image_url": "https://...",
  "colors": [],
  "result_payload": {},
  "created_at": "2026-06-24T00:00:00Z",
  "updated_at": "2026-06-24T00:00:00Z"
}
```

### 6.7 URL 분석 기록 상세/수정/삭제

| Method | URL | 인증 | 설명 |
| --- | --- | --- | --- |
| GET | `/api/engagements/url-analyses/{id}/` | 필요 | 상세 조회 |
| PUT/PATCH | `/api/engagements/url-analyses/{id}/` | 필요 | 수정 |
| DELETE | `/api/engagements/url-analyses/{id}/` | 필요 | 삭제 |

## 7. 주요 Enum 정리

### Product.category

| 값 | 설명 |
| --- | --- |
| LIP | 립 |
| EYE | 아이 |
| CHEEK | 치크 |
| BASE | 베이스 |
| LENS | 렌즈 |
| ETC | 기타 |

### Product.tone_tag

| 값 | 설명 |
| --- | --- |
| SPRING_LIGHT | 봄 웜 라이트 |
| SPRING_BRIGHT | 봄 웜 브라이트 |
| SUMMER_LIGHT | 여름 쿨 라이트 |
| SUMMER_MUTE | 여름 쿨 뮤트 |
| AUTUMN_MUTE | 가을 웜 뮤트 |
| AUTUMN_DEEP | 가을 웜 딥 |
| WINTER_BRIGHT | 겨울 쿨 브라이트 |
| WINTER_DEEP | 겨울 쿨 딥 |
| UNKNOWN | 미분류 |

### Community Post.category

| 값 | 설명 |
| --- | --- |
| LIFE_ITEM | 인생템 공유 |
| COLOR_REVIEW | 발색 리뷰 |
| QUESTION | 질문 |
| PRODUCT_RECOMMENDATION | 제품 추천 |
| ROUTINE | 메이크업 루틴 |
| FREE | 자유 |

### DiagnosisResult.status

| 값 | 설명 |
| --- | --- |
| completed | 진단 완료 |
| low_confidence | 낮은 신뢰도 |
| failed | 진단 실패 |

### MakeupGeneration.status

| 값 | 설명 |
| --- | --- |
| none | 미생성 |
| queued | 대기 중 |
| running | 생성 중 |
| complete | 완료 |
| failed | 실패 |
| skipped | 보류 |

### Makeover style_key

| 값 | 화면 표시명 |
| --- | --- |
| natural_daily | 내추럴 데일리메이크업 |
| pure_daily | 청순 데일리메이크업 |
| romantic | 로맨틱 메이크업 |
| chic | 시크 메이크업 |
| smoky | 스모키 메이크업 |

## 8. 대표 인증 흐름

### JWT 기반 흐름

1. `POST /accounts/jwt-login/`
2. 응답의 `access` 토큰 저장
3. 이후 인증 필요 API 호출 시 Header 추가

```http
Authorization: Bearer {access_token}
```

4. access 만료 시 `POST /accounts/jwt-refresh/`

### 세션 기반 흐름

1. `POST /accounts/session-login/`
2. 브라우저가 `sessionid` 쿠키 저장
3. 이후 같은 도메인 요청에서 세션 인증 사용
4. 로그아웃 시 `POST /accounts/session-logout/`

