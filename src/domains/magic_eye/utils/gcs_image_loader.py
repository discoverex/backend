import json
from datetime import timedelta

from google.cloud import storage
from google.oauth2 import service_account

from src.configs import setting
from src.utils.logger import logger


class GCSImageLoader:
    """
    GCP Cloud Storage에서 이미지를 조회하기 위한 유틸리티 클래스입니다.
    """

    def __init__(self):
        self.bucket_name = setting.IMAGE_BUCKET_NAME
        self.credentials_info = setting.GCP_SERVICE_ACCOUNT_JSON
        self._client = self._init_client()
        self._bucket = self._client.bucket(self.bucket_name)

    def _init_client(self) -> storage.Client:
        """
        GCP 서비스 계정 정보를 사용하여 Storage 클라이언트를 초기화합니다.
        """
        try:
            # GCP_SERVICE_ACCOUNT_JSON이 JSON 문자열인 경우와 파일 경로인 경우를 모두 대응
            if self.credentials_info.startswith("{"):
                info = json.loads(self.credentials_info)
                credentials = service_account.Credentials.from_service_account_info(info)
                return storage.Client(credentials=credentials)
            else:
                # 파일 경로인 경우
                return storage.Client.from_service_account_json(self.credentials_info)
        except Exception as e:
            logger.error(f"GCS 클라이언트 초기화 실패: {str(e)}")
            raise e

    def list_blobs(self, prefix: str = "", bucket_name: str = None) -> list[str]:
        """
        특정 접두사(폴더 경로) 내의 모든 파일(blob) 이름을 반환합니다.
        """
        try:
            target_bucket_name = bucket_name or self.bucket_name
            blobs = self._client.list_blobs(target_bucket_name, prefix=prefix)
            return [blob.name for blob in blobs if not blob.name.endswith("/")]
        except Exception as e:
            logger.error(f"GCS 파일 목록 조회 실패 (bucket={bucket_name or self.bucket_name}, prefix={prefix}): {str(e)}")
            return []

    def download_image_as_bytes(self, blob_name: str, bucket_name: str = None) -> bytes | None:
        """
        단일 이미지 파일을 바이트 형식으로 다운로드합니다.
        """
        try:
            target_bucket = self._client.bucket(bucket_name) if bucket_name else self._bucket
            blob = target_bucket.blob(blob_name)
            if not blob.exists():
                logger.warning(f"GCS 파일을 찾을 수 없음: {blob_name} (bucket={bucket_name or self.bucket_name})")
                return None
            return blob.download_as_bytes()
        except Exception as e:
            logger.error(f"GCS 이미지 다운로드 실패 ({blob_name}, bucket={bucket_name or self.bucket_name}): {str(e)}")
            return None

    def get_blob_etag(self, blob_name: str, bucket_name: str = None) -> str | None:
        """
        GCS 파일의 ETag를 가져옵니다. (변경 사항 감지용)
        """
        try:
            target_bucket = self._client.bucket(bucket_name) if bucket_name else self._bucket
            blob = target_bucket.get_blob(blob_name)
            return blob.etag if blob else None
        except Exception as e:
            logger.error(f"GCS ETag 조회 실패 ({blob_name}, bucket={bucket_name or self.bucket_name}): {str(e)}")
            return None

    def download_multiple_images_as_bytes(self, blob_names: list[str]) -> list[tuple[str, bytes]]:
        """
        여러 이미지 파일을 한 번에 조회하여 (이름, 바이트) 리스트로 반환합니다.
        """
        results = []
        for name in blob_names:
            img_bytes = self.download_image_as_bytes(name)
            if img_bytes:
                results.append((name, img_bytes))
        return results

    def get_images_in_folder(self, prefix: str) -> list[tuple[str, bytes]]:
        """
        특정 폴더(prefix) 내의 모든 이미지를 조회합니다.
        """
        blob_names = self.list_blobs(prefix)
        return self.download_multiple_images_as_bytes(blob_names)

    def generate_signed_url(self, blob_name: str, bucket_name: str = None, expiration_minutes: int = 60) -> str | None:
        """
        프론트엔드에서 직접 접근 가능한 서명된 URL을 생성합니다.
        """
        try:
            target_bucket = self._client.bucket(bucket_name) if bucket_name else self._bucket
            blob = target_bucket.blob(blob_name)
            # expiration에 정수 대신 timedelta 객체를 전달하세요.
            return blob.generate_signed_url(
                version="v4",  # 최신 v4 서명 방식 권장
                expiration=timedelta(minutes=expiration_minutes),
                method="GET"
            )
        except Exception as e:
            logger.error(f"GCS 서명된 URL 생성 실패 ({blob_name}, bucket={bucket_name or self.bucket_name}): {str(e)}")
            return None

_gcs_image_loader = None

def get_gcs_image_loader() -> GCSImageLoader:
    """
    GCSImageLoader 인스턴스를 반환합니다. (싱글톤 패턴)
    """
    global _gcs_image_loader
    if _gcs_image_loader is None:
        _gcs_image_loader = GCSImageLoader()
    return _gcs_image_loader
