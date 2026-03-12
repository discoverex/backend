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
   uv sync
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
uvicorn src.main:app --reload --host 127.0.0.1 --port 8080
```
```bash
(실행 오류 시) PYTHONPATH=src uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

이렇게 하면 Uvicorn 서버가 시작되고 코드가 변경될 때 자동으로 다시 로드됩니다.

`http://127.0.0.1:8000/docs`에서 API 문서에 접근할 수 있습니다.

## 개발 규칙

## 🚀 Core Modules

1. src/common: 여러 도메인에서 공통으로 재사용되는 코드를 관리합니다. 도메인 간의 경계를 넘나드는 유틸리티나 공통 데이터 구조가 여기에 위치합니다.

    - dtos/: 전역적으로 사용되는 데이터 전송 객체
    - utils/: 범용 유틸리티 함수

2. src/configs: 애플리케이션의 런타임 환경을 제어하는 설정 파일들의 집합입니다.

- **setting.py**: 환경 변수(`load_dotenv`)를 로드하고 프로젝트 전역에서 사용하는 상수를 정의합니다.
    - `BASE_DIR`: 프로젝트 루트 경로 (`Path(__file__).resolve().parent.parent.parent`)
    - `DB_*`: 데이터베이스 연결 정보 (Host, Port, User, Password, Name)
    - `APP_*`: 애플리케이션 실행 환경 (Host, Port, Env)
    - `BUCKET_NAME`, `GCP_SERVICE_ACCOUNT_JSON`: GCP 클라우드 스토리지 설정
    - `GAME_HUB_*`, `DISCOVEREX_*`, `MAGIC_EYE_*`: 프론트엔드 서비스별 포트 및 URL 정보
    - `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `HF_TOKEN`: 외부 API 키
- **database.py**: PostgreSQL 연결 및 커서 관리를 담당합니다.
    - `get_db_connection()`: `psycopg2`를 사용한 DB 연결 생성
    - `get_db_cursor()`: FastAPI 의존성 주입(`Depends`)용 커서 생성기 (트랜잭션 관리 포함)
    - `check_db_connection()`: DB 상태 확인용 Health Check 함수
- **api_routers.py**: 애플리케이션의 모든 도메인 라우터를 하나로 모으는 역할을 합니다.
    - `API_ROUTERS`: `main.py`에서 등록할 라우터 객체들의 리스트
- **origins.py**: CORS 설정을 위한 허용 출처(Origin) 리스트를 관리합니다.
    - `origins`: 로컬 개발 및 운영 환경의 프론트엔드 URL 리스트
- **logging_config.py**: 애플리케이션의 로그 출력 형식을 제어합니다.
- **http_client.py**: 비동기 HTTP 요청을 위한 `httpx.AsyncClient` 설정을 관리합니다.

3. src/domains: 실제 비즈니스 로직이 수행되는 핵심 계층입니다. Swagger 문서상에서도 이 도메인 단위를 기준으로 API 태그가 분류됩니다.

   | 폴더/파일             | 역할 설명                                                   |
         |:------------------|:--------------------------------------------------------|
   | **dtos/**         | Pydantic 모델을 정의합니다. (Request/Response 스키마)              |
   | **prompts/**      | LLM 서비스를 위한 .md 프롬프트 파일 또는 동적 프롬프트 생성 파이썬 함수            |
   | **queries/**      | PostgreSQL 기반의 템플릿 .sql 파일. Service 계층에서 이를 호출하여 사용합니다. |
   | **utils/**        | 해당 도메인 내 반복 로직, 추상 클래스, 팩토리 메서드 등 리팩터링 공간               |
   | **\*_router.py**  | API 엔드포인트를 정의하고 요청을 서비스 계층으로 전달합니다.                     |
   | **\*_service.py** | 핵심 비즈니스 로직 및 쿼리 실행을 담당합니다. 필요 시 파일 분리가 가능합니다.           |

---

## 🛠️ Development Principles & Rules
코드의 일관성과 유지보수성을 위해 아래 규칙을 반드시 준수합니다.

1. 객체지향 설계 (OOP)

- Class 기반 구현: Router와 Service 계층은 함수형이 아닌 클래스 선언을 원칙으로 합니다.
- 메서드 구현: 각 기능을 클래스 내부 메서드로 구현하여 응집도를 높이고 상태 관리를 명확히 합니다.

2. 코드 스타일 (Pythonic Code)

- 3항 연산자 활용: 단순한 조건식은 true_value if condition else false_value 형태의 파이썬 3항식을 사용하여 간결함을 유지합니다.
- 주석 작성: 코드를 제외한 모든 설명 주석은 한국어로 작성하여 팀 내 의사소통 효율을 높입니다.

3. 코드 품질 관리 (Linting)

- Ruff 사용: 프로젝트의 모든 코드는 Ruff를 통해 린팅 및 포맷팅을 수행합니다.
- Rule 준수: pyproject.toml에 선언된 규칙을 엄격히 따르며, 커밋 전 반드시 린트 체크를 권장합니다.

4. 데이터 흐름 (Data Flow)

- Router: 요청 접수 및 응답 반환 (로직 최소화)
- Service: 비즈니스 유효성 검사 및 데이터 가공 (핵심 로직)
- Repository (Queries): 데이터베이스와의 상호작용
- 참고
    - 서비스 계층에서는 /src/utils/load_sql.py에서 load_sql(domain: str, filename: str) 함수를 사용해 템플릿 SQL을 불러오면 편리합니다.

5. Type Hinting:

- 파이썬의 typing 모듈을 사용하여 모든 메서드의 인자와 반환값에 타입을 명시합니다.

6. Gemini 협업 및 응답 규칙

- 언어 설정: 제미나이(AI)와의 모든 대화 및 제미나이의 모든 응답은 한국어로 진행합니다.
- 코드 가이드: 제미나이는 코드를 제안할 때 본 문서에 명시된 OOP 구조와 Ruff 스타일을 반영해야 합니다.

---

## 💡 Tip: 서비스 확장 가이드

도메인 로직이 비대해질 경우, 단일 서비스 파일에 모든 것을 넣지 않고 auth_service.py, payment_service.py와 같이 기능 단위로 서비스를 분리하여 가독성을 확보하세요.
