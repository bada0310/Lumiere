# Lumiere DB 분류표

작성일: 2026-06-24  
기준 코드: Django Model 기준  
개발 DB: `back/db.sqlite3`

## 1. 전체 DB 구성 요약

Lumiere의 데이터베이스는 크게 5개 업무 영역으로 분류된다.

| 분류 | Django App | 주요 역할 | 대표 테이블 |
| --- | --- | --- | --- |
| 회원/인증 | accounts | 사용자 계정, 프로필, 권한 | `accounts_user` |
| 퍼스널컬러 진단 | diagnosis | AI 진단 결과, 팔레트, 메이크오버 이미지 생성 작업 | `diagnosis_diagnosisresult` |
| 상품/추천 | products | 화장품 상품, 옵션, 가격, 색상 분석, 리뷰 | `products_product` |
| 커뮤니티 | community | 게시글, 댓글, 좋아요 | `community_post` |
| 참여/저장 | engagements | 상품 찜, URL 분석 기록 | `engagements_likedproductoption` |

## 2. 테이블 성격별 분류

| 성격 | 설명 | 테이블 |
| --- | --- | --- |
| 사용자 마스터 | 서비스 사용자 계정과 프로필 | `accounts_user` |
| 기준 마스터 | 퍼스널컬러 타입, 고정 팔레트, 상품 카탈로그 | `diagnosis_personalcolor`, `diagnosis_personalcolorpalette`, `products_product` |
| 진단 결과 | 사용자별 AI 진단 결과와 분석 데이터 | `diagnosis_diagnosisresult` |
| 진단 상세 | 대표 컬러, 팔레트, 추천 상품, 렌즈, 메이크오버 스타일 | `diagnosis_diagnosisrepresentativecolor`, `diagnosis_diagnosiscolorpalette`, `diagnosis_diagnosisrecommendedproduct`, `diagnosis_diagnosisrecommendedlens`, `diagnosis_diagnosismakeoverstyle` |
| AI 작업 큐 | 메이크오버 이미지 생성 비동기 작업 | `diagnosis_makeupgenerationjob` |
| 상품 상세 | 상품 옵션, 판매처, 옵션별 톤 점수 | `products_productoption`, `products_productoffer`, `products_productoptiontonescore` |
| 사용자 콘텐츠 | 리뷰, 커뮤니티 게시글, 댓글 | `products_review`, `community_post`, `community_comment` |
| 반응/관계 | 좋아요, 찜, 게시글-상품 연결 | `community_postlike`, `community_commentlike`, `community_post_products`, `engagements_likedproductoption` |
| 분석 기록 | 상품 URL 분석 결과 저장 | `engagements_urlanalysisrecord` |
| Django 시스템 | 권한, 세션, 마이그레이션, 관리자 로그 | `auth_*`, `django_*`, `accounts_user_groups`, `accounts_user_user_permissions` |

## 3. Accounts DB

### 3.1 accounts_user

사용자 계정과 프로필 정보를 저장한다. Django `AbstractUser`를 확장한 커스텀 유저 테이블이다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `accounts_user` |
| 모델 | `accounts.User` |
| PK | `id` |
| 주요 FK | 없음 |
| 주요 제약 | `username` unique, `nickname` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| username | 로그인 아이디 |
| password | 비밀번호 해시 |
| email | 이메일 |
| nickname | 서비스 닉네임 |
| social_id | 소셜 로그인 ID |
| social_provider | 소셜 로그인 제공자 |
| role | USER, MANAGER, ADMIN |
| profile_image | 사용자 프로필 이미지 |
| is_active | 계정 활성 상태 |
| is_staff | 관리자 사이트 접근 여부 |
| is_superuser | 슈퍼유저 여부 |
| deleted_at | 탈퇴 처리 시각 |
| last_login | 마지막 로그인 시각 |
| date_joined | 가입 시각 |

### 3.2 accounts_user_groups

Django 권한 시스템에서 사용자와 그룹을 연결하는 자동 생성 M:N 테이블이다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `accounts_user_groups` |
| 성격 | Django 자동 생성 관계 테이블 |
| 관계 | `accounts_user` N:M `auth_group` |

### 3.3 accounts_user_user_permissions

Django 권한 시스템에서 사용자와 개별 권한을 연결하는 자동 생성 M:N 테이블이다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `accounts_user_user_permissions` |
| 성격 | Django 자동 생성 관계 테이블 |
| 관계 | `accounts_user` N:M `auth_permission` |

## 4. Diagnosis DB

### 4.1 diagnosis_personalcolor

퍼스널컬러 타입의 기준 정보를 저장하는 마스터 테이블이다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `diagnosis_personalcolor` |
| 모델 | `diagnosis.PersonalColor` |
| PK | `id` |
| 주요 제약 | `type_name` unique, `tone_key` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| type_name | 퍼스널컬러 한글명 |
| tone_key | 시스템에서 사용하는 toneKey |
| base_temperature | warm, cool |
| season | spring, summer, fall, winter |
| tone | BRIGHT, LIGHT, MUTE, DEEP |
| description | 타입 설명 |
| temperature_degree | 온도감 수치 |
| brightness_degree | 명도 수치 |
| saturation_degree | 채도 수치 |
| turbidity_degree | 탁도 수치 |
| glossiness_degree | 광택감 수치 |
| contrast_degree | 대비감 수치 |
| best_pccs | 베스트 PCCS 코드 JSON |
| sub_pccs | 서브 PCCS 코드 JSON |

### 4.2 diagnosis_colorrecommendation

퍼스널컬러별 추천/비추천 메이크업 컬러를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `diagnosis_colorrecommendation` |
| 모델 | `diagnosis.ColorRecommendation` |
| PK | `id` |
| FK | `personal_color_id` → `diagnosis_personalcolor.id` |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| recommendation_type | REP, BEST, WORST |
| makeup_part | LIP, BASE, EYE |
| color_name | 색상명 |
| color_hex | HEX 색상 코드 |
| description | 추천 설명 |

### 4.3 diagnosis_diagnosisresult

사용자의 AI 퍼스널컬러 진단 결과를 저장하는 핵심 테이블이다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `diagnosis_diagnosisresult` |
| 모델 | `diagnosis.DiagnosisResult` |
| PK | `id` |
| FK | `user_id` → `accounts_user.id`, `personal_color_id` → `diagnosis_personalcolor.id` |
| 주요 제약 | 사용자별 `is_primary=True` 결과는 1개만 허용 |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| user_id | 진단을 받은 사용자 |
| personal_color_id | 진단된 퍼스널컬러 기준 타입 |
| confidence_score | AI 진단 신뢰도 |
| status | completed, low_confidence, failed |
| tone_key | 진단 toneKey |
| personal_color_code | 퍼스널컬러 코드 |
| korean_name | 결과 한글명 |
| english_name | 결과 영문명 |
| summary | 결과 요약 |
| diagnosis_json | AI 원본 진단 JSON |
| palette_snapshot | 진단 시점의 고정 팔레트 JSON |
| palette_status | ready, preparing, missing |
| keywords | 스타일 키워드 JSON |
| image_features | 이미지 분석 포인트 JSON |
| skin_metrics | 피부 지표 JSON |
| radar_chart | 레이더 차트 지표 JSON |
| style_guide | 스타일 가이드 JSON |
| is_primary | 메인 퍼스널컬러 여부 |
| is_demo | 데모 결과 여부 |
| diagnosed_at | 진단일 |
| uploaded_image | 업로드 원본 이미지 |
| processed_image | 처리된 이미지 |
| generated_makeup_image | 단일 메이크업 생성 이미지 |
| makeup_generation_status | none, queued, running, complete, failed, skipped |
| makeup_generation_error | 메이크오버 생성 오류 메시지 |
| created_at | 생성 시각 |

### 4.4 diagnosis_diagnosisrepresentativecolor

진단 결과 화면에 표시할 대표 컬러를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `diagnosis_diagnosisrepresentativecolor` |
| 모델 | `diagnosis.DiagnosisRepresentativeColor` |
| PK | `id` |
| FK | `diagnosis_id` → `diagnosis_diagnosisresult.id` |
| 주요 제약 | `diagnosis_id`, `order` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| name | 색상명 |
| hex | HEX 색상 코드 |
| order | 표시 순서 |

### 4.5 diagnosis_diagnosiscolorpalette

진단 결과별 BEST, NEUTRAL, ACCENT, TRY, WORST 팔레트를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `diagnosis_diagnosiscolorpalette` |
| 모델 | `diagnosis.DiagnosisColorPalette` |
| PK | `id` |
| FK | `diagnosis_id` → `diagnosis_diagnosisresult.id` |
| 주요 제약 | `diagnosis_id`, `group`, `order` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| group | best, neutral, accent, try, worst |
| name | 색상명 |
| hex | HEX 색상 코드 |
| order | 그룹 내 표시 순서 |

### 4.6 diagnosis_diagnosismakeoverstyle

AI 메이크오버 스타일별 생성 상태와 결과 이미지를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `diagnosis_diagnosismakeoverstyle` |
| 모델 | `diagnosis.DiagnosisMakeoverStyle` |
| PK | `id` |
| FK | `diagnosis_id` → `diagnosis_diagnosisresult.id` |
| 주요 제약 | `diagnosis_id`, `key` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| key | natural_daily, pure_daily, romantic, chic, smoky |
| name | 화면 표시명 |
| description | 스타일 설명 |
| image | 생성 이미지 저장 경로 |
| status | none, queued, running, complete, failed, skipped |
| error_message | 실패 사유 |
| order | 표시 순서 |
| is_default | 기본 선택 스타일 여부 |

### 4.7 diagnosis_diagnosisrecommendedproduct

진단 결과별 추천 화장품 정보를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `diagnosis_diagnosisrecommendedproduct` |
| 모델 | `diagnosis.DiagnosisRecommendedProduct` |
| PK | `id` |
| FK | `diagnosis_id` → `diagnosis_diagnosisresult.id`, `product_id` → `products_product.id` |
| 주요 제약 | `diagnosis_id`, `category` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| category | 추천 카테고리 |
| category_name | 카테고리 표시명 |
| tone_label | 톤 설명 |
| brand | 브랜드 |
| product_name | 상품명 |
| shade | 색상/호수 |
| description | 추천 설명 |
| image | 이미지 경로 |
| product_url | 상품 URL |
| order | 표시 순서 |

### 4.8 diagnosis_diagnosisrecommendedlens

진단 결과별 추천 렌즈 정보를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `diagnosis_diagnosisrecommendedlens` |
| 모델 | `diagnosis.DiagnosisRecommendedLens` |
| PK | `id` |
| FK | `diagnosis_id` → `diagnosis_diagnosisresult.id` |
| 주요 제약 | `diagnosis_id`, `order` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| rank | 추천 등급 |
| brand | 브랜드 |
| product_name | 렌즈명 |
| color | 렌즈 컬러 |
| description | 추천 설명 |
| image | 이미지 경로 |
| order | 표시 순서 |

### 4.9 diagnosis_personalcolorpalette

퍼스널컬러 toneKey별 고정 팔레트를 저장하는 마스터 테이블이다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `diagnosis_personalcolorpalette` |
| 모델 | `diagnosis.PersonalColorPalette` |
| PK | `id` |
| FK | `personal_color_id` → `diagnosis_personalcolor.id` |
| 주요 제약 | `tone_key` unique, `personal_color_id` OneToOne |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| tone_key | 팔레트 toneKey |
| data | 전체 팔레트 JSON |
| tone_name | 톤 이름 |
| season | 시즌 |
| temperature | 온도감 |
| brightness | 명도 |
| chroma | 채도 |
| contrast | 대비 |
| description | 설명 |
| keywords | 키워드 JSON |
| best_colors | 베스트 컬러 JSON |
| worst_colors | 워스트 컬러 JSON |
| makeup_palette | 메이크업 팔레트 JSON |
| base_makeup_guide | 베이스 가이드 |
| lip_guide | 립 가이드 |
| cheek_guide | 치크 가이드 |
| eye_guide | 아이 가이드 |
| styling_keywords | 스타일링 키워드 JSON |
| recommended_product_tone_range | 추천 제품 색상 범위 JSON |
| is_placeholder | 임시 팔레트 여부 |
| created_at | 생성 시각 |
| updated_at | 수정 시각 |

### 4.10 diagnosis_makeupgenerationjob

AI 메이크오버 이미지 생성 작업을 큐 형태로 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `diagnosis_makeupgenerationjob` |
| 모델 | `diagnosis.MakeupGenerationJob` |
| PK | `id` |
| FK | `diagnosis_id` → `diagnosis_diagnosisresult.id` |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| style_key | 생성할 메이크오버 스타일 key |
| status | queued, running, complete, failed |
| prompt | 이미지 생성 프롬프트 |
| error_message | 실패 사유 |
| created_at | 작업 생성 시각 |
| updated_at | 작업 수정 시각 |

## 5. Products DB

### 5.1 products_product

화장품 상품의 기본 정보와 색상 분석 결과를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `products_product` |
| 모델 | `products.Product` |
| PK | `id` |
| 주요 제약 | `canonical_key` 조건부 unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| brand | 브랜드 |
| name | 상품명 |
| canonical_key | 상품 통합 식별 키 |
| category | LIP, EYE, CHEEK, BASE, LENS, ETC |
| image_url | 상품 이미지 URL |
| representative_image_url | 대표 이미지 URL |
| product_url | 상품 상세 URL |
| description | 상품 설명 |
| price | 대표 가격 |
| mall_name | 판매처 |
| naver_product_id | 네이버 상품 ID |
| source_query | 수집 검색어 |
| naver_category1~4 | 네이버 카테고리 |
| texture | 제형/상품 타입 |
| finish | MATTE, GLOSSY, VELVET, SHIMMER, NATURAL, UNKNOWN |
| tone_tag | 퍼스널컬러 추천 태그 |
| color_family | PINK, ROSE, CORAL 등 |
| hex_code | 대표 색상 HEX |
| rgb_r, rgb_g, rgb_b | 대표 색상 RGB |
| brightness | 명도 |
| saturation | 채도 |
| coolness | 쿨 점수 |
| warmth | 웜 점수 |
| depth | 딥한 정도 |
| softness | 부드러움/탁도 |
| contrast | 대비감 |
| match_score | 추천 점수 |
| reason | 추천 사유 |
| created_at | 생성 시각 |
| updated_at | 수정 시각 |

### 5.2 products_productoption

상품의 색상 옵션 또는 호수 정보를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `products_productoption` |
| 모델 | `products.ProductOption` |
| PK | `id` |
| FK | `product_id` → `products_product.id` |
| 주요 제약 | `product_id`, `option_key` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| option_no | 옵션 번호 |
| option_name | 옵션명 |
| option_key | 옵션 식별 키 |
| image_url | 옵션 이미지 URL |
| color_family | 색상 계열 |
| analyzed_tone_tag | 분석된 tone tag |
| hex_code | 옵션 대표 색상 HEX |
| rgb_r, rgb_g, rgb_b | 옵션 색상 RGB |
| brightness | 명도 |
| saturation | 채도 |
| coolness | 쿨 점수 |
| warmth | 웜 점수 |
| depth | 딥한 정도 |
| softness | 부드러움/탁도 |
| contrast | 대비감 |
| created_at | 생성 시각 |
| updated_at | 수정 시각 |

### 5.3 products_productoffer

상품 옵션별 판매처와 가격 정보를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `products_productoffer` |
| 모델 | `products.ProductOffer` |
| PK | `id` |
| FK | `option_id` → `products_productoption.id` |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| mall_name | 판매처 |
| price | 가격 |
| product_url | 구매 URL |
| naver_product_id | 네이버 상품 ID |
| is_representative | 대표 판매처 여부 |
| created_at | 생성 시각 |

### 5.4 products_productoptiontonescore

상품 옵션이 특정 퍼스널컬러 tone에 얼마나 잘 맞는지 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `products_productoptiontonescore` |
| 모델 | `products.ProductOptionToneScore` |
| PK | `id` |
| FK | `option_id` → `products_productoption.id` |
| 주요 제약 | `option_id`, `target_tone` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| target_tone | 대상 toneKey |
| match_score | 매칭 점수 |
| grade | BEST, GOOD, OK, CAUTION |
| reason | 점수 사유 |
| created_at | 생성 시각 |
| updated_at | 수정 시각 |

### 5.5 products_review

사용자가 상품에 작성한 리뷰를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `products_review` |
| 모델 | `products.Review` |
| PK | `id` |
| FK | `product_id` → `products_product.id`, `author_id` → `accounts_user.id` |
| 주요 제약 | `product_id`, `author_id` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| rating | 평점, 1~5 |
| content | 리뷰 내용 |
| image_url | 리뷰 이미지 URL |
| created_at | 생성 시각 |
| updated_at | 수정 시각 |

## 6. Community DB

### 6.1 community_post

커뮤니티 게시글을 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `community_post` |
| 모델 | `community.Post` |
| PK | `id` |
| FK | `author_id` → `accounts_user.id` |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| title | 게시글 제목 |
| content | 게시글 내용 |
| category | LIFE_ITEM, COLOR_REVIEW, QUESTION, PRODUCT_RECOMMENDATION, ROUTINE, FREE |
| image_url | 첨부 이미지 URL |
| view_count | 조회수 |
| created_at | 생성 시각 |
| updated_at | 수정 시각 |

### 6.2 community_post_products

게시글과 상품을 연결하는 자동 생성 M:N 테이블이다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `community_post_products` |
| 성격 | Django ManyToMany 자동 생성 테이블 |
| 관계 | `community_post` N:M `products_product` |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| id | PK |
| post_id | 게시글 ID |
| product_id | 상품 ID |

### 6.3 community_comment

게시글 댓글과 대댓글을 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `community_comment` |
| 모델 | `community.Comment` |
| PK | `id` |
| FK | `post_id` → `community_post.id`, `author_id` → `accounts_user.id`, `parent_id` → `community_comment.id` |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| content | 댓글 내용 |
| parent_id | 대댓글의 부모 댓글 |
| created_at | 생성 시각 |
| updated_at | 수정 시각 |

### 6.4 community_postlike

게시글 좋아요 정보를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `community_postlike` |
| 모델 | `community.PostLike` |
| PK | `id` |
| FK | `post_id` → `community_post.id`, `user_id` → `accounts_user.id` |
| 주요 제약 | `post_id`, `user_id` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| created_at | 좋아요 생성 시각 |

### 6.5 community_commentlike

댓글 좋아요 정보를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `community_commentlike` |
| 모델 | `community.CommentLike` |
| PK | `id` |
| FK | `comment_id` → `community_comment.id`, `user_id` → `accounts_user.id` |
| 주요 제약 | `comment_id`, `user_id` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| created_at | 좋아요 생성 시각 |

## 7. Engagements DB

### 7.1 engagements_likedproductoption

사용자가 찜한 상품 또는 상품 옵션을 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `engagements_likedproductoption` |
| 모델 | `engagements.LikedProductOption` |
| PK | `id` |
| FK | `user_id` → `accounts_user.id`, `product_id` → `products_product.id`, `product_option_id` → `products_productoption.id` |
| 주요 제약 | `user_id`, `product_id`, `option_id` unique |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| option_id | 프론트/외부 옵션 식별자 |
| group_key | 화면 그룹 키 |
| brand | 찜 당시 브랜드 스냅샷 |
| name | 찜 당시 상품명 스냅샷 |
| option | 찜 당시 옵션명 스냅샷 |
| image_url | 찜 당시 이미지 URL |
| product_url | 찜 당시 상품 URL |
| snapshot | 추가 스냅샷 JSON |
| created_at | 생성 시각 |
| updated_at | 수정 시각 |

### 7.2 engagements_urlanalysisrecord

사용자가 분석한 상품 URL 결과를 저장한다.

| 항목 | 내용 |
| --- | --- |
| 테이블명 | `engagements_urlanalysisrecord` |
| 모델 | `engagements.UrlAnalysisRecord` |
| PK | `id` |
| FK | `user_id` → `accounts_user.id` |

주요 컬럼:

| 컬럼 | 설명 |
| --- | --- |
| source_url | 분석 요청 URL |
| title | 분석 결과 제목 |
| brand | 브랜드 |
| product_name | 상품명 |
| image_url | 상품 이미지 URL |
| colors | 추출 색상 JSON |
| result_payload | 전체 분석 결과 JSON |
| created_at | 생성 시각 |
| updated_at | 수정 시각 |

## 8. 주요 관계 요약

### 회원 중심 관계

| 관계 | 설명 |
| --- | --- |
| `accounts_user` 1:N `diagnosis_diagnosisresult` | 한 사용자는 여러 진단 결과를 가질 수 있다. |
| `accounts_user` 1:N `products_review` | 한 사용자는 여러 상품 리뷰를 작성할 수 있다. |
| `accounts_user` 1:N `community_post` | 한 사용자는 여러 커뮤니티 게시글을 작성할 수 있다. |
| `accounts_user` 1:N `community_comment` | 한 사용자는 여러 댓글을 작성할 수 있다. |
| `accounts_user` 1:N `engagements_likedproductoption` | 한 사용자는 여러 상품 옵션을 찜할 수 있다. |
| `accounts_user` 1:N `engagements_urlanalysisrecord` | 한 사용자는 여러 URL 분석 기록을 저장할 수 있다. |

### 진단 중심 관계

| 관계 | 설명 |
| --- | --- |
| `diagnosis_personalcolor` 1:N `diagnosis_diagnosisresult` | 하나의 퍼스널컬러 타입은 여러 사용자 진단 결과에 연결된다. |
| `diagnosis_diagnosisresult` 1:N `diagnosis_diagnosisrepresentativecolor` | 진단 결과별 대표 컬러 목록 |
| `diagnosis_diagnosisresult` 1:N `diagnosis_diagnosiscolorpalette` | 진단 결과별 팔레트 그룹 |
| `diagnosis_diagnosisresult` 1:N `diagnosis_diagnosismakeoverstyle` | 진단 결과별 5개 메이크오버 스타일 |
| `diagnosis_diagnosisresult` 1:N `diagnosis_makeupgenerationjob` | 진단 결과별 이미지 생성 작업 큐 |
| `diagnosis_diagnosisresult` 1:N `diagnosis_diagnosisrecommendedproduct` | 진단 결과별 추천 상품 |
| `diagnosis_diagnosisresult` 1:N `diagnosis_diagnosisrecommendedlens` | 진단 결과별 추천 렌즈 |

### 상품 중심 관계

| 관계 | 설명 |
| --- | --- |
| `products_product` 1:N `products_productoption` | 하나의 상품은 여러 옵션을 가진다. |
| `products_productoption` 1:N `products_productoffer` | 하나의 옵션은 여러 판매처/가격 정보를 가진다. |
| `products_productoption` 1:N `products_productoptiontonescore` | 하나의 옵션은 toneKey별 매칭 점수를 가진다. |
| `products_product` 1:N `products_review` | 하나의 상품은 여러 리뷰를 가진다. |
| `products_product` N:M `community_post` | 게시글에서 여러 상품을 언급할 수 있다. |

### 커뮤니티 중심 관계

| 관계 | 설명 |
| --- | --- |
| `community_post` 1:N `community_comment` | 하나의 게시글은 여러 댓글을 가진다. |
| `community_comment` 1:N `community_comment` | 댓글은 대댓글을 가질 수 있다. |
| `community_post` 1:N `community_postlike` | 게시글 좋아요 |
| `community_comment` 1:N `community_commentlike` | 댓글 좋아요 |

## 9. 주요 제약 조건 요약

| 테이블 | 제약 조건 | 목적 |
| --- | --- | --- |
| `accounts_user` | `nickname` unique | 닉네임 중복 방지 |
| `diagnosis_personalcolor` | `type_name` unique, `tone_key` unique | 퍼스널컬러 기준값 중복 방지 |
| `diagnosis_diagnosisresult` | user별 `is_primary=True` 1개 | 메인 퍼스널컬러 단일화 |
| `diagnosis_diagnosisrepresentativecolor` | `diagnosis_id`, `order` unique | 대표 컬러 순서 중복 방지 |
| `diagnosis_diagnosiscolorpalette` | `diagnosis_id`, `group`, `order` unique | 팔레트 그룹 내 순서 중복 방지 |
| `diagnosis_diagnosismakeoverstyle` | `diagnosis_id`, `key` unique | 같은 스타일 중복 생성 방지 |
| `diagnosis_diagnosisrecommendedproduct` | `diagnosis_id`, `category` unique | 카테고리별 추천 상품 중복 방지 |
| `diagnosis_diagnosisrecommendedlens` | `diagnosis_id`, `order` unique | 추천 렌즈 순서 중복 방지 |
| `diagnosis_personalcolorpalette` | `tone_key` unique | toneKey별 고정 팔레트 단일화 |
| `products_product` | `canonical_key` 조건부 unique | 같은 상품 통합 식별 |
| `products_productoption` | `product_id`, `option_key` unique | 상품 내 옵션 중복 방지 |
| `products_productoptiontonescore` | `option_id`, `target_tone` unique | 옵션-tone 점수 중복 방지 |
| `products_review` | `product_id`, `author_id` unique | 사용자당 상품 리뷰 1개 제한 |
| `community_postlike` | `post_id`, `user_id` unique | 게시글 좋아요 중복 방지 |
| `community_commentlike` | `comment_id`, `user_id` unique | 댓글 좋아요 중복 방지 |
| `engagements_likedproductoption` | `user_id`, `product_id`, `option_id` unique | 상품 옵션 찜 중복 방지 |

## 10. Django 시스템 테이블

아래 테이블은 서비스 도메인 데이터가 아니라 Django Framework 운영을 위해 생성된다.

| 테이블 | 역할 |
| --- | --- |
| `django_migrations` | 마이그레이션 적용 이력 |
| `django_content_type` | Django 모델 메타 정보 |
| `django_session` | 세션 로그인 데이터 |
| `django_admin_log` | 관리자 페이지 작업 로그 |
| `auth_group` | 권한 그룹 |
| `auth_permission` | 모델별 권한 |
| `accounts_user_groups` | 사용자-그룹 관계 |
| `accounts_user_user_permissions` | 사용자-권한 관계 |

## 11. 데이터 흐름 기준 요약

### 퍼스널컬러 진단 흐름

1. 사용자가 이미지 업로드
2. `diagnosis_diagnosisresult` 생성
3. 고정 팔레트를 기반으로 `diagnosis_diagnosiscolorpalette`, `diagnosis_diagnosisrepresentativecolor` 생성
4. 메이크오버 요청 시 `diagnosis_diagnosismakeoverstyle`와 `diagnosis_makeupgenerationjob` 생성
5. AI 이미지 생성 완료 후 `diagnosis_diagnosismakeoverstyle.image` 저장

### 상품 추천 흐름

1. `products_product`에 상품 기본 정보 저장
2. 옵션이 있으면 `products_productoption`에 색상 옵션 저장
3. 판매처/가격은 `products_productoffer`에 저장
4. toneKey별 매칭 점수는 `products_productoptiontonescore`에 저장
5. 사용자 진단 결과의 toneKey와 상품 색상 정보를 매칭하여 추천 화면에 표시

### 커뮤니티 흐름

1. 사용자가 `community_post` 작성
2. 게시글에 상품을 연결하면 `community_post_products`에 관계 저장
3. 댓글은 `community_comment`에 저장
4. 좋아요는 `community_postlike`, `community_commentlike`에 저장

### 찜/분석 기록 흐름

1. 사용자가 상품 옵션을 찜하면 `engagements_likedproductoption` 생성
2. 사용자가 외부 상품 URL을 분석하면 `engagements_urlanalysisrecord`에 결과 저장

