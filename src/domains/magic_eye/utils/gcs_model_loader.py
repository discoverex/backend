from src.configs import setting
from src.domains.magic_eye.dtos.magic_eye_dtos import ModelMeta
from src.domains.magic_eye.utils.gcs_image_loader import GCSImageLoader
from src.utils.logger import error


class GCSModelLoader(GCSImageLoader):
    """
    GCP Cloud Storage에서 ONNX 모델 파일을 관리하기 위한 유틸리티 클래스입니다.
    """

    def __init__(self):
        super().__init__()
        # 이미지 버킷 대신 모델 전용 버킷을 기본으로 설정
        self.bucket_name = setting.MODEL_BUCKET_NAME
        self._bucket = self._client.bucket(self.bucket_name)

    def get_model_signed_url(self, model_name: str, expiration_minutes: int = 120) -> str | None:
        """
        ONNX 모델 파일에 접근 가능한 서명된 URL을 생성합니다.
        모델 파일은 용량이 클 수 있으므로 기본 만료 시간을 120분으로 넉넉하게 잡았습니다.
        """
        # .onnx 확장자가 누락된 경우 자동으로 추가 (선택 사항)
        blob_name = model_name if model_name.endswith(".onnx") else f"{model_name}.onnx"

        url = self.generate_signed_url(
            blob_name=blob_name,
            expiration_minutes=expiration_minutes
        )

        return url if url else None

    def check_model_exists(self, model_name: str) -> bool:
        """
        버킷 내에 해당 모델 파일이 존재하는지 확인합니다.
        """
        blob_name = model_name if model_name.endswith(".onnx") else f"{model_name}.onnx"
        blob = self._bucket.blob(blob_name)
        return blob.exists()

    def get_model_metadata(self, blob_name: str) -> ModelMeta | None:
        """
        GCS 오브젝트의 메타데이터를 조회하여 버전(updated) 정보를 반환합니다.
        """
        blob = self._bucket.get_blob(blob_name)
        if not blob:
            error(f"[ERROR] '{blob_name}'을 찾을 수 없습니다. 경로를 다시 확인하세요.")
            return None
        # updated(최종 수정 시간)나 etag를 버전으로 사용합니다.
        # 타임스탬프를 문자열로 변환하여 사용자가 알아보기 쉽게 합니다.
        return ModelMeta(version=str(blob.updated.timestamp()), size=blob.size)


# 싱글톤 인스턴스 관리
_gcs_model_loader = None


def get_gcs_model_loader() -> GCSModelLoader:
    """
    GCSModelLoader 인스턴스를 반환합니다. (싱글톤 패턴)
    """
    global _gcs_model_loader
    _gcs_model_loader = _gcs_model_loader if _gcs_model_loader else GCSModelLoader()
    return _gcs_model_loader