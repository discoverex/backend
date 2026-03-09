import json
import httpx
import firebase_admin
from firebase_admin import credentials

# from configs.database import check_db_connection
from src.configs.http_client import http_holder
# from configs.redis_conn import check_redis_connection
from src.configs.setting import APP_PORT, FIREBASE_SERVICE_ACCOUNT_JSON
from src.utils.logger import info, error


def _initialize_http_client():
    info("HTTP 클라이언트를 구성합니다...")
    http_holder.client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0), limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
    )


def _initialize_firebase():
    """
    Firebase SDK를 초기화합니다.
    환경변수 FIREBASE_SERVICE_ACCOUNT_JSON에 저장된 서비스 계정 키를 사용합니다.
    """
    if not firebase_admin._apps:
        info("Firebase SDK를 초기화 중...")
        try:
            if not FIREBASE_SERVICE_ACCOUNT_JSON:
                raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON 환경변수가 설정되지 않았습니다.")
            
            cred_dict = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            info("Firebase SDK가 성공적으로 초기화되었습니다.")
        except Exception as e:
            error(f"Firebase 초기화 실패: {str(e)}")
            # 애플리케이션 시작을 중단시키려면 raise를 사용합니다. 
            # 여기서는 선택에 따라 처리할 수 있으나, 인증 기능이 필수적이므로 raise 하는 것이 안전합니다.
            raise RuntimeError(f"Firebase 초기화 실패: {str(e)}")
    else:
        info("Firebase 앱이 이미 초기화되어 있습니다.")


def _print_startup_message():
    print("\n" + "⭐" * 40)
    print(f"  Swagger UI: http://127.0.0.1:{APP_PORT}/docs")
    print(f"  ReDoc:      http://127.0.0.1:{APP_PORT}/redoc")
    print("⭐" * 40 + "\n")


def startup_event_handler():
    # check_db_connection()
    # check_redis_connection()
    _initialize_http_client()
    _initialize_firebase()
    _print_startup_message()


async def shutdown_event_handler():
    await http_holder.client.aclose()
    info("HTTP 클라이언트 종료 중...")
    info("Backend Service 종료 중...")
