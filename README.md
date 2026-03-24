# Vision AI Game Hub - Backend

Vision AI Game Hub는 "렉스를 찾아라!" 메인 게임과 "매직아이 퀴즈" 등 다양한 AI 기반 게임 서비스를 제공하는 FastAPI 백엔드 애플리케이션입니다.

## 🚀 최근 업데이트 및 주요 기능

### 1. 공통 응답 구조 (WrappedResponse)
*   모든 API 응답은 `WrappedResponse` 모델로 감싸져 일관된 데이터 구조를 보장합니다.
*   성공 여부(`status`), 데이터(`data`), 그리고 서버 메시지(`message`)를 포함합니다.

### 2. 매직아이(Magic Eye) 퀴즈 서비스 개선
*   **동적 퀴즈 후보 설정**: 프론트엔드에서 퀴즈 후보 개수를 파라미터(`count`)로 조절할 수 있습니다 (5~50개). 범위를 벗어날 경우 서버에서 자동으로 조정하며 안내 메시지를 제공합니다.
*   **LLM 기반 '목격자 증언' 생성**: 
    *   LangChain과 OpenAI(GPT-4o-mini)를 활용하여 정답 이미지에 대한 신비로운 목격담을 실시간으로 생성합니다.
    *   이미지 생성 프롬프트(Description)에서 불필요한 기술적 상용구를 제거하고, 정답을 유추할 수 없도록 객체명을 치환하여 보안을 강화했습니다.
    *   프롬프트는 외부 Markdown 파일(`witness_testimony.md`)로 관리되어 유연한 스타일 수정이 가능합니다.
*   **토큰 최적화**: 오직 정답(`correct_answer`)에 대해서만 증언을 생성하여 API 호출 비용을 최소화했습니다.

### 3. CI/CD 및 배포 자동화
*   **GitHub Actions**: `main` 브랜치 푸시 시 Google Cloud Run으로 자동 배포됩니다.
*   **안정적인 인증**: `gcloud` 도구 대신 `access_token`을 사용한 직접적인 Docker 로그인 방식을 적용하여 CI 환경에서의 배포 안정성을 확보했습니다.
*   **수동 배포 지원**: `workflow_dispatch`를 통해 필요 시 GitHub Actions 탭에서 수동으로 재배포 버튼을 실행할 수 있습니다.

## 🛠 기술 스택
*   **Framework**: FastAPI
*   **AI/LLM**: LangChain, OpenAI API (GPT-4o-mini)
*   **Storage**: Google Cloud Storage (Signed URL 제공)
*   **Database**: PostgreSQL, Redis
*   **Deployment**: Docker, Google Cloud Run, GitHub Actions
*   **Linter**: Ruff (Strict linting & formatting)

## 📁 프로젝트 구조 (핵심)
*   `src/domains/`: 도메인별 비즈니스 로직 (Auth, Magic Eye, Score 등)
*   `src/common/`: 공통 DTO (`WrappedResponse` 등) 및 유틸리티
*   `src/configs/`: 데이터베이스, LLM, GCS 관련 설정
*   `src/domains/magic_eye/prompts/`: LLM용 프롬프트 파일 관리

## ⚙️ 설정 및 실행
자세한 실행 방법과 개발 규칙은 [GEMINI.md](./GEMINI.md)를 참고하세요.
