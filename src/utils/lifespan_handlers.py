import csv
import io
import json
import httpx
import firebase_admin
from firebase_admin import credentials

from configs.database import check_db_connection
from configs.redis_conn import check_redis_connection
from src.configs.http_client import http_holder
from src.configs.gcs import initialize_gcs_client
from src.configs import setting
from src.configs.setting import APP_PORT, FIREBASE_SERVICE_ACCOUNT_JSON
from src.domains.magic_eye.utils.gcs_image_loader import get_gcs_image_loader
from src.utils.logger import info, error


def _initialize_http_client():
    info("HTTP 클라이언트를 구성합니다...")
    http_holder.client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0), limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
    )


def _initialize_gcs():
    """
    전역 GCS 클라이언트를 초기화합니다.
    """
    initialize_gcs_client()


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
            info("✅ Firebase SDK가 성공적으로 초기화되었습니다.")
        except Exception as e:
            error(f"Firebase 초기화 실패: {str(e)}")
            # 애플리케이션 시작을 중단시키려면 raise를 사용합니다. 
            # 여기서는 선택에 따라 처리할 수 있으나, 인증 기능이 필수적이므로 raise 하는 것이 안전합니다.
            raise RuntimeError(f"Firebase 초기화 실패: {str(e)}")
    else:
        info("Firebase 앱이 이미 초기화되어 있습니다.")


def _fetch_and_save_magic_eye_metadata():
    """
    GCS에서 매직아이 메타데이터(CSV)를 가져와 "split": "test"인 정보만 JSON으로 저장합니다.
    최신 버전이 있을 때만 새로 내려받아 덮어쓰기합니다.
    """
    bucket_name = "discoverex-image-storage"
    blob_name = "magic-eye/metadata.csv"

    # 저장될 폴더 및 파일 경로 (BASE_DIR/src/domains/magic_eye/consts/)
    metadata_dir = setting.BASE_DIR / "src" / "domains" / "magic_eye" / "consts"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    json_file_path = metadata_dir / "magic_eye_metadata.json"
    etag_file_path = metadata_dir / "magic_eye_metadata.etag"

    try:
        gcs_loader = get_gcs_image_loader()
        
        # 1. GCS에서 최신 ETag 가져오기
        remote_etag = gcs_loader.get_blob_etag(blob_name, bucket_name=bucket_name)
        if remote_etag is None:
            error(f"GCS에서 파일을 찾을 수 없습니다: {blob_name}")
            return

        # 2. 로컬 ETag 확인 (파일이 없거나 내용이 다르면 업데이트 대상)
        local_etag = ""
        if etag_file_path.exists():
            with open(etag_file_path, "r", encoding="utf-8") as f:
                local_etag = f.read().strip()

        if json_file_path.exists() and local_etag == remote_etag:
            info("매직아이 메타데이터가 최신 상태입니다. (변경 사항 없음)")
            return

        info(f"매직아이 메타데이터 업데이트 중... (ETag: {remote_etag})")

        # 3. 데이터 다운로드 및 처리
        csv_bytes = gcs_loader.download_image_as_bytes(blob_name, bucket_name=bucket_name)
        if csv_bytes is None:
            return

        csv_text = csv_bytes.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(csv_text))

        # "split": "test" 필터링 및 숫자 변환
        test_metadata = []
        for row in csv_reader:
            if row.get("split") == "test":
                for key in ["file_number", "file_no"]:
                    if key in row and row[key]:
                        try:
                            row[key] = int(row[key])
                        except (ValueError, TypeError):
                            pass
                test_metadata.append(row)

        # 4. JSON 및 ETag 저장
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(test_metadata, f, ensure_ascii=False, indent=4)
        
        with open(etag_file_path, "w", encoding="utf-8") as f:
            f.write(remote_etag)

        info(f"매직아이 메타데이터 저장 완료: {len(test_metadata)} 건 (split='test')")

    except Exception as e:
        error(f"매직아이 메타데이터 fetch/save 실패: {str(e)}")


def _print_startup_message():
    print("\n" + "⭐" * 40)
    print(f"  Swagger UI: http://127.0.0.1:{APP_PORT}/docs")
    print(f"  ReDoc:      http://127.0.0.1:{APP_PORT}/redoc")
    print("⭐" * 40 + "\n")


def startup_event_handler():
    check_db_connection()
    check_redis_connection()
    _initialize_http_client()
    _initialize_gcs()
    _initialize_firebase()
    _fetch_and_save_magic_eye_metadata()
    _print_startup_message()


async def shutdown_event_handler():
    await http_holder.client.aclose()
    info("HTTP 클라이언트 종료 중...")
    info("Backend Service 종료 중...")
