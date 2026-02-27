# GEMINI.md (한국어)

이 문서는 프로젝트의 목적, 기술, 빌드, 실행 및 개발 지침을 포함하여 프로젝트에 대한 포괄적인 개요를 제공합니다.

## 프로젝트 개요

이 프로젝트는 "Vision AI Game Hub"라는 이름의 Python 기반 백엔드 서비스입니다. **FastAPI** 프레임워크를 사용하여 구축되었습니다. 이 서비스의 주요 목적은 "Vision AI Game Hub"와 메인 게임인 "렉스를 찾아라!"를 위한 API를 제공하는 것입니다.

### 주요 기술

- **프레임워크:** FastAPI
- **언어:** Python 3.11+
- **서버:** Uvicorn
- **의존성:**
    - `fastapi`: API 빌드를 위한 웹 프레임워크.
    - `uvicorn`: 애플리케이션 실행을 위한 ASGI 서버.
    - `python-dotenv`: 환경 변수 관리를 위한 라이브러리.
    - `httpx`: Python용 차세대 HTTP 클라이언트.

### 아키텍처

이 프로젝트는 표준 FastAPI 애플리케이션 구조를 따릅니다:

- `src/main.py`: 애플리케이션의 메인 진입점. FastAPI 앱, 미들웨어 및 라우터를 초기화합니다.
- `src/configs/`: 설정, API 라우터, 로깅 및 CORS 출처에 대한 구성 파일이 포함된 디렉토리입니다.
- `src/utils/`: 유틸리티 함수 및 예외 핸들러가 포함된 디렉토리입니다.
- `src/common/`: DTO 및 유틸리티 함수와 같은 공통 모듈이 포함된 디렉토리입니다.
- `pyproject.toml`: 프로젝트 메타데이터와 의존성을 정의합니다.

## 빌드 및 실행

### 사전 요구 사항

- Python 3.11 이상
- `uv` 패키지 관리자 (또는 `pip`)

### 설정

1. **리포지토리를 복제합니다.**
2. **가상 환경을 만듭니다:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **의존성을 설치합니다:**
   ```bash
   uv pip install -r requirements.txt
   ```
   *참고: `requirements.txt`가 존재하지 않는 경우, `pyproject.toml`에서 생성하거나 `uv pip install -e .`를 사용하여 직접 의존성을 설치할 수 있습니다.*

### 환경 변수

이 프로젝트는 `.env` 파일을 사용하여 환경 변수를 관리합니다. 루트 디렉토리에 `.env` 파일을 만들고 다음 변수를 추가하십시오:

```
# .env

# 애플리케이션 설정
APP_HOST=127.0.0.1
APP_PORT=8000
APP_ENV=local

# 원격 호스트
REMOTE_HOST=localhost

# 데이터베이스 (PostgreSQL)
DB_USER=user
DB_PASSWORD=password
DB_NAME=dbname
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_PASSWORD=password
REDIS_HOST=localhost
REDIS_PORT=6379

# 프론트엔드
WEB_HOST=localhost
WEB_PORT=3000
```

### 애플리케이션 실행

개발 환경에서 애플리케이션을 실행하려면 다음 명령을 사용하십시오:

```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

이렇게 하면 Uvicorn 서버가 시작되고 코드가 변경될 때 자동으로 다시 로드됩니다.

`http://127.0.0.1:8000/docs`에서 API 문서에 접근할 수 있습니다.

## 개발 규칙

### 코드 스타일

이 프로젝트에는 아직 엄격한 코드 스타일 가이드가 정의되어 있지 않습니다. 그러나 Python 코드에 대해 **PEP 8** 스타일 가이드를 따르는 것이 좋습니다.

### API 개발

- API 라우터는 `src/routers/` 디렉토리에 정의됩니다 (이 디렉토리는 현재 없으며 `src/configs/api_routers.py`의 `API_ROUTERS`는 비어 있습니다).
- 새로운 관련 엔드포인트 세트를 추가할 때, 새 라우터를 만들고 `src/configs/api_routers.py`의 `API_ROUTERS` 목록에 추가하십시오.
- 요청 및 응답 모델에는 `src/common/dtos/` 디렉토리의 DTO (Data Transfer Objects)를 사용하십시오.

### 테스트

TODO: 테스트 실행 방법에 대한 지침을 추가해야 합니다.

### 기여 지침

TODO: 기여 지침을 추가해야 합니다.