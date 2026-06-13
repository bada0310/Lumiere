# 프로젝트 기여 가이드 (Contributing Guidelines)

본 문서는 프로젝트에 코드를 기여하고 협업하기 위한 핵심 규칙을 정의합니다. 복잡한 절차는 줄이고, 팀원 간의 코드 일관성과 인프라/시스템의 보수적인 안정성을 유지하는 데 집중합니다.

---

## 1. 🌱 브랜치 전략 (Branch Rules)
- **원칙:** `main` 브랜치는 항상 안정적으로 배포 가능한 상태여야 합니다.
- **작업:** 최신 `main`에서 용도에 맞는 짧은 수명의 브랜치를 생성하고, 병합 후에는 삭제합니다.
- **네이밍 형식:** `<유형>/<도메인>-<짧은이름>` (소문자와 하이픈 사용)
  - `feat/auth-login`
  - `fix/board-pagination`
  - `docs/api-conventions`
  - `refactor/user-serializer`

---

## 2. 📝 커밋 메시지 규칙 (Commit Message)
팀원들이 히스토리만 읽어도 **왜 필요한 변경인지** 바로 이해할 수 있도록 **한글**로 작성합니다. 

**형식:** `<아이콘> <타입>(<범위>): <한글 요약>`

### 🔹 주요 커밋 타입 (Type)
| 아이콘 | 타입 | 설명 | 예시 |
| :---: | :--- | :--- | :--- |
| ✨ | **`feat`** | 새로운 기능 추가 | `✨ feat(auth): JWT 기반 로그인 API 구현` |
| 🐛 | **`fix`** | 버그 수정 | `🐛 fix(vue): 데이터 파싱 시 발생하는 예외 처리 추가` |
| 📝 | **`docs`** | 문서 수정 (README, API 명세 등) | `📝 docs(api): API 명세서에 실시간 알림 엔드포인트 추가` |
| 🎨 | **`style`** | 코드 포맷팅, 세미콜론 누락 등 | `🎨 style(django): 코드 인덴트 및 Lint 스타일 수정` |
| ♻️ | **`refactor`** | 코드 리팩토링 (기능 변화 없음) | `♻️ refactor(django): 데이터 전처리 로직 가독성 개선 및 함수 분리` |
| 🧪 | **`test`** | 테스트 코드 추가 및 수정 | `🧪 test(api): 모델 추론 파이프라인 유닛 테스트 추가` |
| 🔧 | **`chore`** | 인프라 설정, 빌드 업무, 패키지 수정 | `🔧 chore(infra): 운영 배포를 위한 Dockerfile 환경변수 업데이트` |
| 🚀 | **`deploy`** | 배포 관련 설정 및 환경 변경 | `🚀 deploy(infra): 운영 서버 프로비저닝 및 보안 그룹 설정` |

---

## 3. 🏷️ 네이밍 컨벤션 (Naming Conventions)
Django(Python)와 Vue(JavaScript/TypeScript)의 언어적 특성을 존중하여 명명합니다.

| 대상 | 환경 | 규칙 | 예시 |
| :--- | :--- | :--- | :--- |
| Python 클래스/모델 | Django | `PascalCase` | `UserProfile`, `BoardViewSet` |
| Python 함수/변수 | Django | `snake_case` | `get_user_data`, `user_list` |
| DB 테이블/컬럼 | Django (ORM) | `snake_case` | `user_profile`, `created_at` |
| Vue 컴포넌트 파일 | Vue | `PascalCase.vue`| `UserProfileCard.vue` |
| JS 함수/변수 | Vue | `camelCase` | `fetchUserData`, `isLoggedIn` |
| Pinia 스토어 | Vue | `<domain>Store` | `useAuthStore` |

---

## 4. 🏗️ 아키텍처 및 코드 규칙 (Architecture)

**Backend (Django):**
- **Views/ViewSets:** 요청을 받고 응답을 반환하는 역할에 집중합니다. 복잡한 비즈니스 로직은 모델(Model) 메서드나 별도의 서비스 레이어로 분리합니다.
- **Serializers:** 입출력 데이터의 엄격한 검증을 담당합니다.
- ⚠️ **트랜잭션과 안정성:** 데이터베이스 스키마 변경(`makemigrations`/`migrate`)이 포함된 작업은 반드시 팀원과 공유합니다. 핵심 데이터 저장은 부가적인 외부 연동 실패로 인해 롤백되지 않도록 철저히 격리하여 보수적인 안정성을 최우선으로 확보합니다.

**Frontend (Vue):**
- **Pages (Views):** 라우팅과 연결되는 최상위 컴포넌트로, 세부 피처(Feature) 컴포넌트들을 조합합니다.
- **Components:** 재사용 가능한 UI 요소를 작성합니다.
- **API 호출:** 컴포넌트 내부에 API URL을 하드코딩하지 않고, 별도의 `api/` 디렉토리나 스토어에서 관리합니다.

---

## 5. ✅ Pull Request 템플릿 및 리뷰 규칙
모든 PR은 아래의 양식을 본문에 포함하여 작성합니다. 리뷰어가 코드를 보지 않고도 변경 의도와 시스템 영향을 한눈에 파악할 수 있도록 합니다.

> 💡 **Tip:** 이 양식을 `.github/PULL_REQUEST_TEMPLATE.md` 파일로 저장해두면 PR 작성 시 자동으로 적용됩니다.

### 📋 PR 본문 템플릿
```markdown
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
```