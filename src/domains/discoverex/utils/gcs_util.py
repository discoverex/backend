import json
from datetime import timedelta
from src.configs import setting
from src.configs.gcs import gcs_holder
from src.utils.logger import logger


class GCSUtil:
    """
    GCP Cloud Storage 작업을 위한 공통 유틸리티 클래스입니다.
    """

    def __init__(self):
        self.bucket_name = setting.IMAGE_BUCKET_NAME
        self._client = gcs_holder.client
        self._bucket = self._client.bucket(self.bucket_name)

    def read_json_blob(self, blob_name: str) -> dict | None:
        """
        GCS에서 JSON 파일을 읽어 딕셔너리로 반환합니다.
        """
        try:
            blob = self._bucket.blob(blob_name)
            if not blob.exists():
                return None
            content = blob.download_as_text()
            return json.loads(content)
        except Exception as e:
            logger.error(f"GCS JSON 파일 읽기 실패 ({blob_name}): {str(e)}")
            return None

    def list_subfolders(self, prefix: str) -> list[str]:
        """
        특정 접두사(폴더 경로) 바로 아래에 있는 하위 폴더 목록을 반환합니다.
        """
        try:
            if prefix and not prefix.endswith("/"):
                prefix += "/"
            
            blobs = self._client.list_blobs(self.bucket_name, prefix=prefix, delimiter="/")
            list(blobs)
            
            subfolders = []
            for p in blobs.prefixes:
                folder_name = p[len(prefix):].rstrip("/")
                if folder_name:
                    subfolders.append(folder_name)
            
            return sorted(subfolders)
        except Exception as e:
            logger.error(f"GCS 하위 폴더 목록 조회 실패 (prefix={prefix}): {str(e)}")
            return []

    def list_blobs(self, prefix: str) -> list[str]:
        """
        특정 접두사(폴더 경로) 내의 모든 파일(blob) 이름을 반환합니다.
        """
        try:
            blobs = self._client.list_blobs(self.bucket_name, prefix=prefix)
            # 폴더 자체를 제외한 파일만 필터링하여 반환
            return [blob.name for blob in blobs if not blob.name.endswith("/")]
        except Exception as e:
            logger.error(f"GCS 파일 목록 조회 실패 (prefix={prefix}): {str(e)}")
            return []

    def generate_signed_url(self, blob_name: str, expiration_minutes: int = 60) -> str | None:
        """
        프론트엔드에서 직접 접근 가능한 서명된 URL을 생성합니다.
        """
        try:
            blob = self._bucket.blob(blob_name)
            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET"
            )
        except Exception as e:
            logger.error(f"GCS 서명된 URL 생성 실패 ({blob_name}): {str(e)}")
            return None

_gcs_util = None

def get_gcs_util() -> GCSUtil:
    """
    GCSUtil 인스턴스를 반환합니다. (싱글톤 패턴)
    """
    global _gcs_util
    if _gcs_util is None:
        _gcs_util = GCSUtil()
    return _gcs_util
