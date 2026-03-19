import json
from google.cloud import storage
from google.oauth2 import service_account

from src.configs import setting
from src.utils.logger import logger, info, error


class GCSHolder:
    """
    GCS 클라이언트를 전역적으로 관리하기 위한 홀더 클래스입니다.
    """
    def __init__(self):
        self._client: storage.Client | None = None

    @property
    def client(self) -> storage.Client:
        if self._client is None:
            # 예외적으로 초기화되지 않은 상태에서 접근 시 시도 (권장되지 않음)
            self._client = initialize_gcs_client()
        return self._client

    @client.setter
    def client(self, value: storage.Client):
        self._client = value


gcs_holder = GCSHolder()


def initialize_gcs_client() -> storage.Client:
    """
    GCP 서비스 계정 정보를 사용하여 전역 GCS 클라이언트를 초기화합니다.
    """
    info("GCS 클라이언트를 초기화 중...")
    credentials_info = setting.GCP_SERVICE_ACCOUNT_JSON
    
    try:
        if not credentials_info:
            raise ValueError("GCP_SERVICE_ACCOUNT_JSON 환경변수가 설정되지 않았습니다.")

        if credentials_info.startswith("{"):
            info_dict = json.loads(credentials_info)
            credentials = service_account.Credentials.from_service_account_info(info_dict)
            client = storage.Client(credentials=credentials)
        else:
            client = storage.Client.from_service_account_json(credentials_info)
        
        gcs_holder.client = client
        info("GCS 클라이언트가 성공적으로 초기화되었습니다.")
        return client
    except Exception as e:
        error(f"GCS 클라이언트 초기화 실패: {str(e)}")
        raise RuntimeError(f"GCS 클라이언트 초기화 실패: {str(e)}")
