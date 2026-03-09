from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Request, status
from starlette.middleware.cors import CORSMiddleware

from common.dtos.common_response import CustomJSONResponse
from configs.api_routers import API_ROUTERS
from configs.database import check_db_connection
from configs.logging_config import LOGGING_CONFIG
from configs.origins import origins
from configs.setting import APP_ENV, APP_PORT, REMOTE_HOST
from utils.exceptions import init_exception_handlers
from utils.lifespan_handlers import shutdown_event_handler, startup_event_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 시작될 때 실행
    startup_event_handler()
    yield  # 서버가 동작하는 지점
    # 서버가 종료될 때 실행
    await shutdown_event_handler()


app = FastAPI(
    title="Vision AI Game Hub",
    description="비전 AI 숨은그림찾기 '렉스를 찾아라!'입니다.",
    version="1.0.0",
    default_response_class=CustomJSONResponse,
    servers=[
        {"url": "/", "description": "Auto (Current Host)"},
        {"url": f"http://localhost:{APP_PORT}", "description": "Local env"},
        {"url": f"http://{REMOTE_HOST}:{APP_PORT}", "description": "Dev env"},
    ],
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True}
)


@app.middleware("http")
async def error_logging_middleware(request: Request, call_next):
    # 이제 에러 로그는 핸들러가 담당하므로 미들웨어는 통과만 시킵니다.
    response = await call_next(request)
    return response


# 커스덤 에러 핸들러 초기화
init_exception_handlers(app)

try:
    if APP_ENV == "local":
        allow_origins = ["*"]
    else:
        # origins 리스트가 비어있거나 None이 포함되어 있는지 검증
        allow_origins = [o for o in origins if o]
except Exception as e:
    print(f"CORS origins loading error: {e}")
    allow_origins = ["*"] # 실패 시 fallback

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,  # 허용할 출처(CORS) 목록
    allow_credentials=True,  # 쿠키 등 자격 증명 허용 여부
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

def register_routers(app: FastAPI):
    for router in API_ROUTERS:
        app.include_router(router)


register_routers(app)


@app.get("/", description="서버 연결 확인", summary="테스트 - 서버 연결을 확인합니다.")
def read_root():
    return {"message": "반갑습니다. 비전 게임 허브입니다!"}


# health check
@app.get("/health")
def health_check() -> Dict[str, str]:
    health_status = {"status": "ok", "db": "connected"}
    try:
        check_db_connection()
        return health_status
    except Exception as e:
        # 하나라도 실패하면 503 에러 반환
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"status": "error", "message": str(e)}
        ) from e


if __name__ == "__main__":
    import os
    import uvicorn

    # 1. Cloud Run은 시스템 환경변수 'PORT'를 통해 포트 지정
    # 우선순위: 시스템 PORT > 설정 파일의 APP_PORT > 기본값 8080
    env_port = os.environ.get("PORT")

    if APP_ENV == "local":
        effective_port = APP_PORT
        effective_host = "127.0.0.1"
    else:
        # 프로덕션에서는 Cloud Run이 주입하는 PORT를 최우선으로, 없으면 8080
        effective_port = int(os.environ.get("PORT", 8080))
        effective_host = "0.0.0.0"

    LOGGING_CONFIG["handlers"]["default"]["stream"] = "ext://sys.stdout"
    LOGGING_CONFIG["handlers"]["access"]["stream"] = "ext://sys.stdout"

    uvicorn.run(
        "main:app",
        host=effective_host,
        port=effective_port,
        reload=(APP_ENV == "local"),
        log_config=LOGGING_CONFIG,
    )
