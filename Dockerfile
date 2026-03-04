# 빌드 스테이지
FROM ghcr.io/astral-sh/uv:latest AS builder
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

# 실행 스테이지
FROM python:3.11-slim
WORKDIR /app

# 빌드 스테이지에서 설치된 패키지 가져오기
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

# 컨테이너가 3333 포트를 사용함을 명시
EXPOSE 3333

# 서버 실행 시 3333 포트를 사용하도록 명령 (예: FastAPI/Uvicorn 기준)
# main.py 안에 app.run 또는 uvicorn 설정이 3333으로 되어 있어야 합니다.
CMD ["python", "main.py", "--port", "3333"]