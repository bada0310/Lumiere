# 내 정보 조회

Method: GET
URL: /accounts/user/
param: -
사용자: 회원
설명: 로그인한 사용자의 프로필 정보를 조회합니다.
순서: 6
인증필요여부: 로그인 필요
카테고리: 계정 11

### Request Syntax

```jsx
GET /accounts/user/
```

### Parameters

없음.

### Request Header

| Header | 필수 | 설명 | 예시 |
| --- | --- | --- | --- |
| Authorization | O | JWT access token | Bearer {access_token} |

### Request Body

요청 바디 없음.

### Response

| key | 설명 | value 타입 | 옵션 | Nullable | 예시 |
| --- | --- | --- | --- | --- | --- |
| id | 사용자 ID | Number |  | X | 1 |
| username | 아이디 | String |  | X | "user01" |
| nickname | 닉네임 | String |  | X | "루미에르_1234" |
| email | 이메일 | String |  | O | "user01@example.com" |
| profile_image_url | 프로필 이미지 URL | String |  | O | "http://127.0.0.1:8000/media/..." |
| requires_password_confirmation | 비밀번호 확인 필요 여부 | Boolean |  | X | true |

### Status

| status | response content |
| --- | --- |
| 200 | 조회 성공 |
| 401 | 인증 실패 |
| 500 | 서버 내부 오류 |

### Example

```jsx
{
  "id": 1,
  "username": "user01",
  "nickname": "루미에르_1234",
  "email": "user01@example.com",
  "profile_image_url": "http://127.0.0.1:8000/media/profiles/uploads/profile.png",
  "requires_password_confirmation": true
}
```