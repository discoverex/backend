from fastapi import HTTPException, status

from src.domains.magic_eye.utils.gcs_image_loader import GCSImageLoader, get_gcs_image_loader
from src.utils.logger import logger


class MediaService:
    """
    미디어 리소스(이미지 등)를 처리하는 비즈니스 로직 클래스입니다.
    """

    def __init__(self, gcs_loader: GCSImageLoader = None):
        # 의존성 주입을 통해 GCSImageLoader를 가져옵니다.
        self.gcs_loader = gcs_loader or get_gcs_image_loader()

    def get_image_content(self, blob_name: str) -> bytes:
        """
        GCS에서 이미지 바이트 데이터를 가져옵니다.
        """
        image_bytes = self.gcs_loader.download_image_as_bytes(blob_name)
        
        if image_bytes is None:
            logger.warning(f"이미지를 찾을 수 없음: {blob_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="요청하신 이미지를 찾을 수 없습니다."
            )
            
        return image_bytes

    def get_multiple_images(self, blob_names: list[str]) -> list[dict]:
        """
        여러 이미지의 정보를 조회합니다. (필요 시 바이트 또는 서명된 URL 반환)
        """
        results = []
        for name in blob_names:
            # 여기서는 예시로 서명된 URL을 반환하도록 구성할 수 있습니다.
            url = self.gcs_loader.generate_signed_url(name)
            if url:
                results.append({"name": name, "url": url})
        
        return results
