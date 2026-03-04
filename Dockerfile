# 1. Python 공식 이미지를 베이스로 사용 (쉘이 포함되어 있음)
FROM python:3.11-slim AS builder

# uv 설치 (가장 확실한 방법)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvbin/uv
ENV PATH="/uvbin:${PATH}"

WORKDIR /app

# 의존성 파일 복사
COPY pyproject.toml uv.lock ./

# 시스템에 직접 설치 (Cloud Run은 컨테이너 자체가 독립된 환경이라 --system이 효율적입니다)
RUN uv pip install --system --no-cache -r pyproject.toml

# 2. 실행 스테이지
FROM python:3.11-slim
WORKDIR /app

# 빌드 스테이지에서 설치된 패키지 및 소스 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

# Cloud Run에서 설정한 3333 포트 사용
ENV PORT 3333
EXPOSE 3333

# 서버 실행 (main.py가 루트에 있다고 가정)
CMD ["python", "main.py", "--port", "3333"]