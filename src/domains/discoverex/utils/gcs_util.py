from src.configs import setting
from src.configs.gcs import gcs_holder
from src.utils.logger import logger


class GCSFolderUtil:
    """
    GCP Cloud Storage에서 폴더(Prefix) 목록을 조회하기 위한 유틸리티 클래스입니다.
    """

    def __init__(self):
        self.bucket_name = setting.IMAGE_BUCKET_NAME
        self._client = gcs_holder.client
        self._bucket = self._client.bucket(self.bucket_name)

    def list_subfolders(self, prefix: str) -> list[str]:
        """
        특정 접두사(폴더 경로) 바로 아래에 있는 하위 폴더 목록을 반환합니다.
        GCS에서는 '/' 구분자를 사용하여 가상의 디렉토리 구조를 표현합니다.
        """
        try:
            # prefix는 항상 '/'로 끝나야 정확한 하위 폴더를 찾을 수 있습니다.
            if prefix and not prefix.endswith("/"):
                prefix += "/"
            
            # delimiter를 설정하면 blobs.prefixes에 하위 폴더(prefix)가 담깁니다.
            blobs = self._client.list_blobs(self.bucket_name, prefix=prefix, delimiter="/")
            
            # next(blobs, None) 호출로 이터레이터를 한 번 실행해야 prefixes가 채워집니다.
            list(blobs)
            
            # 반환된 prefixes에서 요청한 prefix를 제외하고 폴더 이름만 추출합니다.
            subfolders = []
            for p in blobs.prefixes:
                # p는 'hide-and-seek/theme1/' 형태이므로 끝의 '/'와 앞의 prefix를 제거
                folder_name = p[len(prefix):].rstrip("/")
                if folder_name:
                    subfolders.append(folder_name)
            
            return sorted(subfolders)
        except Exception as e:
            logger.error(f"GCS 하위 폴더 목록 조회 실패 (prefix={prefix}): {str(e)}")
            return []

_gcs_folder_util = None

def get_gcs_folder_util() -> GCSFolderUtil:
    """
    GCSFolderUtil 인스턴스를 반환합니다. (싱글톤 패턴)
    """
    global _gcs_folder_util
    if _gcs_folder_util is None:
        _gcs_folder_util = GCSFolderUtil()
    return _gcs_folder_util
