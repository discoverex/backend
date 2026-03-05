# 1. 빌드 스테이지
FROM python:3.11-slim AS builder

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvbin/uv
ENV PATH="/uvbin:${PATH}"

WORKDIR /app

# 의존성 파일 복사 및 설치
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

# 2. 실행 스테이지
FROM python:3.11-slim
WORKDIR /app

# [추가] 로그가 즉시 출력되도록 설정 (Cloud Run 디버깅용)
ENV PYTHONUNBUFFERED=1

# 빌드 스테이지에서 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages

# [수정] 소스 코드 전체 복사 (패키지 외에 main.py 등 포함)
COPY . .

# [중요] 포트 환경변수 기본값 설정 (혹시 모를 에러 방지용)
ENV APP_PORT=3333

# 서버 실행 (Shell form 사용으로 $APP_PORT 치환 허용)
CMD python main.py --port $APP_PORT