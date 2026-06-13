# Lumiere

# 📂 Lumiere 프로젝트 구조 (Project Structure)

이 섹션은 Lumiere 프로젝트의 디렉토리 구성과 각 앱의 역할을 설명합니다.

```text
project01_26/                  # 전체 프로젝트 루트 (Root)
├── manage.py                  # Django 프로젝트 관리 실행 파일
├── .gitignore                 # Git 관리 제외 설정
├── requirements.txt           # 프로젝트 의존성 라이브러리 목록
├── README.md                  # 프로젝트 설명 문서
│
├── Lumiere/                   # [Project] 메인 설정 디렉토리
│   ├── settings.py            # 데이터베이스, 앱 등록 등 전역 설정
│   ├── urls.py                # 최상위 URL 라우팅
│   ├── asgi.py                # 비동기 서버 설정
│   └── wsgi.py                # 웹 서버 인터페이스 설정
│
├── accounts/                  # [App] 사용자 관리 (Auth)
│   ├── models.py              # 커스텀 User 모델 (프로필, 닉네임 등)
│   ├── views.py               # 로그인, 회원가입, 로그아웃 로직
│   └── migrations/            # DB 변경 이력 관리
│
├── personal_color/            # [App] 퍼스널 컬러 진단 및 관리
│   ├── models.py              # 진단 결과(봄/여름/가을/겨울), 진단 히스토리
│   ├── views.py               # AI 모델 연동 및 진단 처리 로직
│   ├── fixtures/              # 컬러 타입 기본 데이터 (Initial Data)
│   ├── templates/
│   │   └── personal_color/    # 진단 페이지, 결과 페이지 HTML
│   └── migrations/
│
├── product/                   # [App] 제품 추천 및 정보 관리
│   ├── models.py              # 화장품 정보, 컬러 타입과의 매핑 관계
│   ├── views.py               # 제품 목록 및 상세 페이지 로직
│   ├── fixtures/              # 초기 화장품 데이터 (Initial Data)
│   ├── templates/
│   │   └── product/
│   │       └── index.html     # 제품 추천 메인 페이지
│   └── migrations/
│
└── templates/                 # [Global] 공통 템플릿 (base.html 등)
```
---
### 🔹 주요 커밋 타입 (Type)

| 아이콘 | 타입 | 설명 | 예시 |
| :---: | :--- | :--- | :--- |
| ✨ | **`feat`** | 새로운 기능 추가 | `feat: FastAPI 기반 실시간 웹소켓 엔드포인트 구현` |
| 🐛 | **`fix`** | 버그 수정 | `fix: 크롤러 데이터 파싱 시 발생하는 예외 처리 추가` |
| 📝 | **`docs`** | 문서 수정 (README, API 명세 등) | `docs: API 명세서에 실시간 알림 엔드포인트 추가` |
| 🎨 | **`style`** | 코드 포맷팅, 세미콜론 누락 등 (코드 변경 없음) | `style: 코드 인덴트 및 세미콜론 스타일 수정` |
| ♻️ | **`refactor`** | 코드 리팩토링 (기능 변화 없음) | `refactor: 데이터 전처리 로직 가독성 개선 및 함수 분리` |
| 🧪 | **`test`** | 테스트 코드 추가 및 수정 | `test: 모델 추론 파이프라인 유닛 테스트 추가` |
| 🔧 | **`chore`** | 인프라 설정, 빌드 업무, 패키지 수정 | `chore: AWS ECS 배포를 위한 Dockerfile 환경변수 업데이트` |
| 🚀 | **`deploy`** | 배포 관련 설정 및 환경 변경 | `deploy: 운영 서버 인프라 프로비저닝 및 보안 그룹 설정` |

---

## 🎯 작업 목적 (Why)
- 이 PR이 왜 필요한지 간략하게 설명합니다.
- (예: 기존 로컬 파일에 적재되던 로그를 확장성을 위해 데이터베이스로 바로 적재하도록 변경합니다.)

## 📝 주요 변경 사항 (What)
- 어떤 파일에서 어떤 핵심 로직이 변경되었는지 요약합니다.
- (예: `routers/log.py` 내 로그 수집 엔드포인트 로직 수정)
- (예: 모델 추론 파이프라인의 VQA 입력 데이터 전처리 로직 분리)

## 🕵️‍♂️ 테스트 및 검증 결과 (How to Test)
- 코드가 정상적으로 동작하는지, 기존 시스템에 악영향은 없는지 어떻게 검증했는지 작성합니다. **(보수적인 안정성을 위해 가장 중요한 항목입니다.)**
- (예: 로컬 환경에서 테스트 더미 데이터를 100건 전송하여 누락 없이 저장되는 것 확인 완료)

## 🤔 리뷰어에게 부탁하는 점 (Review Point)
- 코드에서 특별히 고민했던 부분이나, 리뷰어가 집중적으로 봐주었으면 하는 부분을 명시합니다.
- (예: 대용량 트래픽이 몰릴 때 병목이 생길 여지가 있는지 아키텍처 관점에서 리뷰 부탁드립니다.)

## 🔗 관련 이슈 (Issue Tracker)
- Jira, Github Issues 등 관련 작업 번호를 링크합니다. (예: Close #12)