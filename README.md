# 🎨 Lumière (루미에르)
> **AI 기반 퍼스널 컬러 진단 및 맞춤형 화장품 추천 서비스**

## 1. 프로젝트 소개
Lumière(루미에르)는 사용자의 이미지를 분석하여 퍼스널 컬러를 정확하게 진단하고, 진단된 톤에 가장 매칭되는 화장품을 추천 및 비교해 주는 웹 서비스입니다. 단순한 설문 분석을 넘어 이미지 분석 기술을 활용해 진단의 객관성을 높였으며, 개인 맞춤형 뷰티 정보와 유저 간 소통을 위한 커뮤니티 환경을 제공합니다.

## 2. 프로젝트 목표 및 주요 구현 성과
- **정확한 퍼스널 컬러 추출:** 사용자 안면 이미지를 분석하여 봄/여름/가을/겨울 및 세부 톤을 정확히 진단합니다.
- **컴포넌트 기반 시각화:** 진단 결과를 유저가 직관적으로 이해할 수 있도록 퍼스널 컬러 요약 화면 및 톤 포지션 차트 기능 등을 구현했습니다.
- **화장품 데이터 매칭 및 상세 비교:** 진단 톤에 매칭되는 화장품들의 상세 스펙을 한눈에 비교할 수 있는 기능을 제공합니다.
- **보수적인 시스템 안정성:** Django 백엔드와 Vue 프론트엔드를 독립적으로 분리하여, 예외 상황이나 트래픽 변화에도 핵심 기능이 안전하게 동작하도록 구축했습니다.

## 3. 핵심 사용자 흐름 (Core User Flow)
1. **인증 (Accounts):** 서비스 이용을 위한 회원가입 및 JWT 기반 로그인
2. **진단 (Diagnosis):** 개인 안면 이미지 업로드 및 AI 퍼스널 컬러 분석 프로세스 진행
3. **결과 확인 (Analysis):** 퍼스널 컬러 진단 결과 요약 및 상세 톤 포지션 차트 확인
4. **상품 탐색 및 비교 (Products):** 추천된 화장품 리스트 확인 및 상세 비교 분석
5. **커뮤니티 우회 (Engagements):** 진단 결과와 뷰티 팁을 공유하는 게시글 및 댓글 소통

## 4. 주요 기능 (구현 기능 목록)
- **accounts:** 유저 인증, 회원 정보 관리 및 세션 유지
- **diagnosis:** 이미지 업로드 및 AI 기반 퍼스널 컬러 진단 로직 제어
- **products & product:** 카테고리별 화장품 데이터 관리 및 진단 톤별 맞춤형 상품 매칭
- **engagements:** 사용자 간 게시글, 댓글, 좋아요 등의 커뮤니티 상호작용 기능

## 5. 시스템 구성도 (System Architecture)
전체 프로젝트 레이아웃은 서비스 안정성과 독립성을 위해 백엔드, 프론트엔드, 산출물 문서 영역으로 명확히 구분되어 관리됩니다.

```text
📦 LUMIERE
 ┣ 📂 back/                  # Django REST Framework 기반 API 백엔드 서버
 ┣ 📂 docs/                  # 프로젝트 기획 및 설계 산출물 문서
 ┗ 📂 front/lumiere-frontend/# Vue 3 & Vite 기반 프론트엔드 클라이언트
 ```

 ## 6. 기술 스택 (Tech Stack)

| 구분 | 기술 스택 |
|---|---|
| **Frontend** | Vue 3, Vite, Pinia, Vue Router, JavaScript, HTML5, CSS3 |
| **Backend** | Python, Django, Django REST Framework (DRF) |
| **Database** | SQLite |
| **Tools** | VS Code, ERDCloud (vuerd) |

## 7. 저장소 구조 (Repository Structure)

### 🔹 Backend (Django)

| 디렉토리/파일명 | 역할 및 포함 내용 |
|---|---|
| `back/accounts/` | 회원가입, 로그인 등 사용자 관리 앱 |
| `back/diagnosis/` | 이미지 분석 및 퍼스널 컬러 진단 처리 앱 |
| `back/engagements/` | 게시글, 댓글 등 커뮤니티 활성화 앱 |
| `back/products/`<br>`back/product/` | 화장품 정보 적재 및 맞춤형 상품 매칭 앱 |
| `back/manage.py` | Django 프로젝트 관리 스크립트 |
| `back/requirements.txt` | 백엔드 의존성 패키지 명세 리스트 |

### 🔹 Frontend (Vue 3)

| 디렉토리/파일명 | 역할 및 포함 내용 |
|---|---|
| `src/views/` | accounts, Analysis, community, diagnosis, Home, products 페이지 컴포넌트 |
| `src/components/` | `PersonalColorSummary.vue`, `TonePositionChart.vue` 등 재사용 UI 요소 |
| `src/stores/` | Pinia 전역 상태 관리 모듈 (사용자 인증 및 진단 상태 등) |
| `src/router/` | 서비스 내 라우팅 구조 정의 |
| `vite.config.js` | Vite 빌드 및 개발 서버 환경 설정 파일 |

## 8. 문서 (Documentation)

| 구분 | 파일명 | 설명 |
|---|---|---|
| **요구사항** | `00_요구사항_명세서초안.pdf` | 프로젝트 필수 및 선택 기능 제약사항 정의서 |
| **기획서** | `01_대전1반_4조_Lumière.docx` | 화면 와이어프레임 및 서비스 전반 기능 기획서 |
| **데이터베이스** | `02_ERD.png`<br>`back/erd.vuerd.json` | 시스템 데이터베이스 테이블 구조 및 관계도 |
| **프로세스** | `03_Flow Chart.png` | 서비스 내 핵심 사용자 비즈니스 로직 흐름도 |
| **사용자 도메인** | `04_USD.png` | 시스템 유스케이스 다이어그램 (Usecase Diagram) |
| **일정 관리** | `05_Lumière_간트차트_템플릿.xlsx` | 2인 협업 체계 기반 마일스톤 및 개발 진행 일정표 |