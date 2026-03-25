# Auth Recovery Handheld

## 현재 주요 문제 상황

Cloud Run 배포 후 로그인 흐름이 다음 형태로 무너지고 있었다.

- 로그인 화면에서 무한 로딩이 발생한다.
- 로그인 서비스에서 다른 게임 서비스로 이동하면 인증 상태가 풀린다.
- 서비스 이동 후 인증이 꼬여 무한 리다이렉션이 발생한다.
- 어떤 경우에는 로그인 직후 다음 API 호출에서 바로 401이 난다.
- 로그아웃 후에도 일부 세션은 남아 있거나, 반대로 정상 세션이 중간에 끊긴다.

이 문제는 단일 버그가 아니라, 현재 인증 구조가 Cloud Run `run.app` 멀티 서비스 배포 방식과 맞지 않는 데서 시작됐다.

## 원인 분석

### 1. Cloud Run `run.app` 간 쿠키 공유 전제 자체가 깨져 있었다

현재 서비스들은 예를 들어 아래처럼 서로 다른 Cloud Run 기본 도메인을 쓰고 있다.

- `discoverex-game-hub-329947062450.asia-northeast3.run.app`
- `discoverex-magic-eye-329947062450.asia-northeast3.run.app`

이 구조에서는 서비스 간 쿠키 공유 기반 SSO를 기대하면 안 된다.  
즉 한 서비스에서 심은 쿠키를 다른 서비스에서 자연스럽게 이어받는 구조가 아니다.

그런데 서버는 운영 환경에서도 `access_token` 쿠키를 주요 인증 매체처럼 다루고 있었고, 이 전제가 무너지면서 서비스 이동 시 인증 소실과 루프가 발생했다.

### 2. JWT 발급 키와 검증 키가 서로 달라질 수 있었다

기존 코드에서는:

- `src/domains/auth/auth_service.py` 가 로컬 하드코딩 `SECRET_KEY` 로 JWT를 발급
- `src/domains/auth/utils/verify_token.py` 가 환경변수 `SECRET_KEY` 로 JWT를 검증

이 상태에서 Cloud Run 환경에 `SECRET_KEY` 가 주입돼 있으면, 로그인 직후 발급한 JWT를 다음 요청에서 서버가 자기 손으로 검증 실패시킬 수 있었다.

이건 로그인 성공 직후 다시 로그인 화면으로 튕기거나, `/auth/users/me` 가 401을 내는 직접 원인이 된다.

### 3. Firebase 토큰과 백엔드 쿠키를 혼용하고 있었다

기존 `/auth/users/me` 는 들어온 토큰을 기반으로 인증한 뒤, 다시 `access_token` 쿠키를 심고 있었다.

- Firebase 토큰도 쿠키에 다시 저장될 수 있었음
- 이후 요청은 헤더 기반일 수도 있고 쿠키 기반일 수도 있었음
- 서비스마다 인증 소스가 달라지면서 상태가 꼬이기 쉬웠음

결과적으로 인증 기준이 하나가 아니라 둘 이상이었고, 브라우저/서비스 이동/SSR 상황에 따라 동작이 달라졌다.

### 4. Redis 세션 검사가 Firebase 흐름까지 과도하게 강제되고 있었다

기존 로직은 Firebase 토큰이 유효해도 Redis 상의 사용자 세션이 없으면 401을 낼 수 있었다.

멀티 서비스 이동, 첫 진입, 세션 동기화 타이밍 차이 같은 상황에서 이 조건은 지나치게 빡빡했고, 정상 사용자를 오인 차단해서 재로그인 루프를 만들 수 있었다.

### 5. Firebase 로그아웃 시 세션 정리가 누락될 수 있었다

기존 `/auth/logout` 은 자체 JWT는 잘 처리해도 Firebase 토큰 경로에서는 DB 사용자 UUID를 안정적으로 찾지 못해 세션 정리가 빠질 여지가 있었다.

이 경우 로그아웃 후 세션이 남거나, 반대로 상태가 어중간하게 꼬일 수 있다.

## 이번에 적용한 서버 수정

### 1. JWT 키 소스를 단일화했다

다음 파일들을 수정했다.

- [`src/configs/setting.py`](/home/esillileu/backend/src/configs/setting.py)
- [`src/domains/auth/auth_service.py`](/home/esillileu/backend/src/domains/auth/auth_service.py)
- [`src/domains/auth/utils/verify_token.py`](/home/esillileu/backend/src/domains/auth/utils/verify_token.py)

변경 내용:

- `SECRET_KEY` 를 설정 파일에서 환경변수 기반으로 통일
- `ALGORITHM` 도 설정 파일 기준으로 통일
- JWT 발급과 검증이 같은 키를 쓰도록 정리

효과:

- 로그인 성공 후 바로 401 나는 치명적인 불일치 제거
- Cloud Run 환경에서 키 주입 여부 때문에 동작이 갈리는 문제 완화

### 2. 운영 환경 기본값에서 교차 서비스 쿠키 의존을 껐다

`src/configs/setting.py` 에 다음 플래그를 추가했다.

- `AUTH_COOKIE_ENABLED`
- `ENFORCE_REDIS_SESSIONS`

기본값:

- `local` 에서는 둘 다 `true`
- 그 외 환경에서는 둘 다 `false`

의도:

- 로컬 개발에서는 기존 쿠키/세션 흐름을 최대한 유지
- Cloud Run 운영에서는 쿠키 기반 서비스 간 인증 전파를 기본적으로 기대하지 않음

### 3. `/auth/users/me` 가 Firebase 토큰을 쿠키로 다시 굽지 않도록 바꿨다

수정 파일:

- [`src/domains/auth/auth_router.py`](/home/esillileu/backend/src/domains/auth/auth_router.py)

기존 문제:

- 인증 성공 후 서버가 다시 `access_token` 쿠키를 심음
- Firebase 토큰과 자체 JWT 경계가 흐려짐

변경 후:

- 쿠키 기능이 켜져 있어도 `local` 자체 JWT 사용자에게만 쿠키 재설정
- Firebase 기반 운영 흐름에서는 헤더 기반 인증을 우선

효과:

- 서비스 이동 시 쿠키 상태 꼬임 감소
- 인증 기준을 `Authorization` 헤더 쪽으로 정리

### 4. Firebase 경로의 Redis 세션 강제 검사를 완화했다

수정 파일:

- [`src/domains/auth/utils/verify_token.py`](/home/esillileu/backend/src/domains/auth/utils/verify_token.py)

변경 내용:

- Redis 세션 체크를 `ENFORCE_REDIS_SESSIONS` 플래그 뒤로 이동
- 운영 환경 기본값은 강제하지 않도록 조정

효과:

- Firebase 토큰이 유효한데도 Redis 타이밍 문제로 401 나던 흐름 완화
- 서비스 첫 진입/이동 시 로그인 루프 감소 기대

### 5. 로그아웃 경로에서 Firebase 사용자도 안정적으로 세션 정리되게 했다

수정 파일:

- [`src/domains/auth/auth_router.py`](/home/esillileu/backend/src/domains/auth/auth_router.py)

변경 내용:

- 자체 JWT 디코드 실패 시 Firebase 토큰 검증으로 fallback
- payload 에 `uid` 가 없으면 `email` 로 DB 사용자를 조회해서 UUID 확보
- 확보된 UUID 기준으로 `auth_service.logout(...)` 실행

효과:

- Firebase 기반 로그아웃에서도 사용자 세션 정리 누락 가능성 축소

## 지금 상태에서 기대되는 개선

서버 기준으로는 다음 문제가 완화되거나 제거됐다.

- 로그인 직후 바로 401 나는 문제
- 서비스 이동 후 쿠키 기반 인증 꼬임
- Firebase 토큰이 유효한데 Redis 세션 때문에 튕기는 문제
- Firebase 로그아웃 세션 정리 누락

즉, 서버는 이제 Cloud Run `run.app` 멀티 서비스 환경에서 "쿠키 공유 SSO" 를 전제로 하지 않도록 방향을 바꿨다.

## 프론트까지 반영한 현재 상태

서버 수정만으로는 충분하지 않았고, 프론트도 같은 전제로 정리해야 했다.

현재 프론트 기준 핵심 원칙은 아래와 같다.

- 운영에서 인증의 기준은 쿠키가 아니라 `Authorization` 헤더다.
- 토큰 소스 우선순위는 `명시 전달 토큰 -> Firebase ID token -> sessionStorage.sso_token` 이다.
- 서비스 간 이동 시 `sso_token` 은 1회 부트스트랩 용도이고, 대상 앱은 동기화 후 URL 에서 즉시 제거한다.
- 운영 환경의 SSR 은 다른 `run.app` 서비스 쿠키를 신뢰하지 않는다. 보호 페이지의 최종 인증 판단은 클라이언트 부팅 후 `/auth/users/me` 재동기화 결과를 기준으로 한다.
- 로컬 개발만 `access_token` 쿠키 기반 SSR 보조 경로를 유지한다.

### 이번 프론트 정리에서 반영한 내용

- 공용 API 클라이언트의 기본 인증을 `Authorization` 헤더 주입 방식으로 통일
- `AuthProvider` 의 세션 갱신 로직을 단일 토큰 해석 함수 기준으로 통합
- 백엔드 응답의 사용자 식별자를 `user_id` 기준으로 읽도록 수정
- `server-auth` 는 로컬 API URL 에서만 쿠키 SSR 복구를 시도하고, 운영에서는 즉시 `null` 반환
- 허브/글로벌 네비게이션/로그인 리다이렉트 모두 동일한 `sso_token` 부트스트랩 규칙 사용
- `vision_ai_logout_signal` 쿠키 기반 글로벌 로그아웃 전제를 제거하고, 백엔드 로그아웃 + 로컬 상태 정리로 단순화

### 여전히 남는 구조적 한계

Cloud Run 기본 `run.app` 를 여러 서비스에 그대로 쓰는 한, 교차 서비스 SSR 쿠키 공유는 계속 불가능하다.

장기적으로 가장 안정적인 방향은 아래 둘 중 하나다.

- 하나의 상위 커스텀 도메인 아래 서브도메인/경로 체계로 재배치
- 하나의 프론트에서 여러 게임을 path 기반으로 통합

## 변경 파일 요약

- [`src/configs/setting.py`](/home/esillileu/backend/src/configs/setting.py)
- [`src/domains/auth/auth_service.py`](/home/esillileu/backend/src/domains/auth/auth_service.py)
- [`src/domains/auth/auth_router.py`](/home/esillileu/backend/src/domains/auth/auth_router.py)
- [`src/domains/auth/utils/verify_token.py`](/home/esillileu/backend/src/domains/auth/utils/verify_token.py)

## 간단 검증 결과

- 서버 인증 관련 수정 파일은 기존 문서 기준 문법 검증 통과 상태
- 현재 작업 환경에서는 `backend` 의 `uv run pytest` 가 `pytest` 실행 파일 부재로 실패
- 현재 작업 환경에서는 `web` 의 타입체크가 `pnpm` 실행 파일 부재로 실패

## 운영자가 바로 확인할 것

배포 후 아래를 우선 확인하면 된다.

1. 로그인 직후 `/auth/users/me` 가 200인지 확인
2. 다른 게임 서비스로 이동한 뒤 첫 보호 API가 200인지 확인
3. 브라우저 네트워크 탭에서 요청이 쿠키가 아니라 `Authorization` 헤더 기준으로 가는지 확인
4. 401이 나면 서버 로그에서 JWT decode 실패인지, Firebase 검증 실패인지, Redis 세션 체크 때문인지 구분해서 확인

## 운영자가 바로 확인할 프론트 포인트

1. Game Hub 로그인 후 다른 게임으로 이동했을 때 URL 의 `sso_token` 이 즉시 사라지는지 확인
2. 이동 직후 첫 `/auth/users/me` 요청이 `Authorization` 헤더 포함 200으로 끝나는지 확인
3. 운영 배포에서 SSR 시점 `initialUser` 가 없어도 클라이언트 복구 후 무한 로딩이나 로그인 루프가 없는지 확인
4. 로그아웃 후 다른 게임 URL 직접 진입 시 이전 사용자 UI 가 남지 않는지 확인

1. Firebase 초기화 완료 대기
2. `auth.currentUser` 확인
3. 사용자가 있으면 `getIdToken()` 호출
4. 해당 토큰으로 `/auth/users/me` 호출
5. 200이면 앱 내부 사용자 상태 확정
6. 401이면 로그인 화면 또는 재인증 흐름으로 이동

즉, "다른 서비스에서 이미 로그인했으니 여기서도 쿠키로 자동 인식되겠지" 라는 기대를 버려야 한다.

#### 3. 로그인 완료 판단 기준을 쿠키에서 Firebase 세션으로 옮기기

기존에 아래 같은 판단이 있으면 바꾸는 것이 좋다.

- 쿠키 존재 여부로 로그인 상태 판단
- 특정 API가 쿠키를 자동 첨부해줄 것이라는 전제
- 서비스 이동 후 로컬 스토리지/쿠키 값만 보고 로그인 완료로 간주

권장 기준:

- Firebase `onAuthStateChanged`
- `auth.currentUser`
- `getIdToken()` 성공 여부
- `/auth/users/me` 성공 여부

#### 4. 로그인 화면 무한 로딩 방지 가드 추가

무한 로딩은 보통 아래 상황에서 생긴다.

- Firebase 초기화 대기 중
- 토큰 재발급 대기 중
- `/auth/users/me` 호출이 반복 실패
- 실패했는데도 상태 머신이 종료되지 않음

프론트에서는 인증 부트스트랩 상태를 최소한 아래처럼 나눠야 한다.

- `loading`
- `authenticated`
- `unauthenticated`
- `error`

특히 `loading -> loading -> loading` 으로 돌아가는 루프를 막아야 한다.

예시:

```ts
type AuthBootState =
  | 'loading'
  | 'authenticated'
  | 'unauthenticated'
  | 'error';
```

그리고 `/auth/users/me` 가 401이면 무조건 재시도 루프에 넣지 말고, 횟수 제한 후 로그인 화면으로 보내야 한다.

#### 5. 서비스 이동 시 토큰 재사용 전략 정리

Game Hub에서 Magic Eye나 다른 게임으로 넘어갈 때는 다음 원칙을 지킨다.

- 이동 전에 별도 쿠키 동기화를 기대하지 않는다.
- 이동 후 도착한 서비스가 자기 Firebase 세션에서 `getIdToken()` 을 다시 꺼낸다.
- 그 토큰으로 자기 API 초기화를 수행한다.

즉 "공유 쿠키 전달" 이 아니라 "공유 Firebase 로그인 상태를 각 서비스가 재해석" 하는 구조다.

### 프론트 구현 체크리스트

서비스별로 아래를 점검하면 된다.

1. 보호 API 호출 공통 함수가 있는지 확인
2. 그 공통 함수가 항상 `Authorization` 헤더를 붙이는지 확인
3. `credentials: 'include'` 에 로그인 유지가 의존하는지 확인
4. 앱 최초 진입 시 `/auth/users/me` 동기화가 있는지 확인
5. 401 응답 시 무한 재시도하지 않는지 확인
6. 로그인 성공 후 다른 서비스로 이동할 때 별도 쿠키 기대 로직이 있는지 확인
7. 로그아웃 시 Firebase 로그아웃과 백엔드 `/auth/logout` 호출 순서를 명확히 정했는지 확인

### 권장 로그인 부트스트랩 흐름

가장 단순한 권장 흐름은 아래다.

1. 앱 시작
2. Firebase auth 상태 확인
3. 유저 없음: 비로그인 상태로 전환
4. 유저 있음: `getIdToken()` 호출
5. `/auth/users/me` 호출
6. 성공: 사용자 상태 저장 후 앱 렌더링
7. 실패: 에러 기록 후 로그인 화면 또는 재로그인 유도

이 흐름을 서비스마다 동일하게 맞추면 서비스 이동 시 인증 꼬임이 크게 줄어든다.

### 로그아웃 권장 흐름

로그아웃도 일관되게 맞춰야 한다.

권장 순서:

1. Firebase `signOut()`
2. 백엔드 `/auth/logout` 호출
3. 프론트 로컬 사용자 상태 초기화
4. 로그인 화면 이동

중요한 건, 로그아웃 완료 판단을 쿠키 삭제 성공 여부에 두지 않는 것이다.

### 프론트에서 바로 찾을 냄새나는 코드

아래 패턴이 있으면 지금 장애와 직접 연결될 가능성이 높다.

- `document.cookie` 또는 쿠키 값으로 로그인 상태 판단
- `credentials: 'include'` 만 있고 `Authorization` 헤더는 없음
- 401 응답 시 무조건 동일 요청 재호출
- `/auth/users/me` 실패 시 상태 종료 없이 다시 로딩 시작
- 서비스 이동 시 토큰 갱신 없이 라우팅만 수행
- Firebase user 존재 여부와 백엔드 사용자 상태를 분리해서 관리하지 않음

### 프론트 작업 우선순위

가장 빠른 복구 순서는 아래가 좋다.

1. 공통 API 클라이언트에서 `Authorization` 헤더 주입
2. 서비스 최초 진입 시 `/auth/users/me` 동기화 추가
3. 로그인 로딩 상태 머신 정리
4. 401 재시도 루프 제거
5. 로그아웃 순서 통일

### 프론트 예시 구현 스케치

```ts
export async function getAuthHeaders() {
  const user = auth.currentUser;
  if (!user) return {};

  const token = await user.getIdToken();
  return {
    Authorization: `Bearer ${token}`,
  };
}

export async function fetchMe() {
  const headers = await getAuthHeaders();
  return fetch(`${API_BASE_URL}/auth/users/me`, {
    method: 'GET',
    headers,
  });
}
```

이 패턴을 모든 게임 서비스에 공통으로 두는 게 가장 안전하다.

## 프론트까지 포함한 최종 결론

이번 장애의 본질은 "Cloud Run 멀티 `run.app` 환경에서 쿠키 기반 인증 공유를 기대한 구조" 에 있다.

백엔드는 이미 다음 방향으로 정리했다.

- JWT 키 통일
- 운영 환경 쿠키 의존도 축소
- Firebase 경로 세션 검증 완화
- 로그아웃 정리 보강

프론트는 다음 방향으로 맞추면 된다.

- Firebase 로그인 상태를 신뢰
- 매 요청 또는 보호 API 호출 시 `Authorization` 헤더 사용
- 각 서비스가 자기 첫 진입 시 `/auth/users/me` 로 사용자 상태 동기화
- 쿠키 기반 로그인 유지 전제 제거

이렇게 맞추면 지금 보고 있는 무한 로딩, 인증 초기화, 무한 리다이렉션 문제는 구조적으로 정리된다.

## 한 줄 결론

이번 정상화는 "Cloud Run 멀티 `run.app` 환경에서 쿠키 기반 인증 공유를 버리고, 헤더 기반 인증으로 정리" 하는 방향의 1차 복구다.  
서버 쪽 급한 불은 껐고, 완전한 안정화는 프론트가 같은 기준으로 맞춰질 때 완료된다.
