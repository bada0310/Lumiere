# 모든 알림 읽음 처리

Method: POST
URL: /api/notifications/mark-all-read/
param: -
사용자: 회원
설명: 로그인 사용자의 모든 알림을 읽음 처리합니다.
순서: 68
인증필요여부: 로그인 필요
카테고리: 알림 4

### Request Syntax

```jsx
POST /api/notifications/mark-all-read/
```

### Parameters

없음.

### Request Header

| Header | 필수 | 설명 | 예시 |
| --- | --- | --- | --- |
| Authorization | O | JWT access token | Bearer {access_token} |
| Content-Type | O | JSON 요청 | application/json |

### Request Body

요청 바디 없음.

### Response

응답 형식은 해당 API의 Serializer 또는 View 반환값 기준으로 확인합니다.

```json
{
  "message": "확인 필요"
}
```

### Status

| status | response content |
| --- | --- |
| 201 또는 200 | 처리 성공 |
| 400 | 잘못된 요청 |
| 401 | 인증 실패 |
| 404 | 대상 없음 |
| 500 | 서버 내부 오류 |

### Example

```json
{
  "message": "확인 필요"
}
```