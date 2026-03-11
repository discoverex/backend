import json

from fastapi import HTTPException, status

from src.configs import setting
from src.domains.magic_eye.dtos.magic_eye_dtos import MagicEyeMetadataQuery
from src.utils.gcs_image_loader import GCSImageLoader, get_gcs_image_loader
from src.utils.logger import logger


class MagicEyeService:
    def __init__(self, gcs_loader: GCSImageLoader = None):
        """매직아이 서비스의 기본 골격입니다."""
        self.gcs_loader = gcs_loader or get_gcs_image_loader()
        self.metadata_path = setting.BASE_DIR / "metadata" / "magic_eye_metadata.json"

    async def get_magic_eye_metadata(self, query: MagicEyeMetadataQuery = None) -> list[dict]:
        """
        로컬 JSON 파일에서 매직아이 메타데이터를 읽어오고 필터링하여 반환합니다.
        """
        try:
            if not self.metadata_path.exists():
                logger.error(f"메타데이터 파일이 존재하지 않습니다: {self.metadata_path}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="매직아이 메타데이터 파일을 찾을 수 없습니다. (먼저 fetch_metadata.py를 실행하세요)"
                )

            with open(self.metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # 필터링 적용
            if query:
                if query.asset_id:
                    metadata = [row for row in metadata if row.get("asset_id") == query.asset_id]
                if query.file_number is not None:
                    metadata = [row for row in metadata if row.get("file_number") == query.file_number]

            return metadata

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"매직아이 메타데이터 조회 중 오류 발생: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"메타데이터 조회 중 오류가 발생했습니다: {str(e)}"
            )

    async def example_method(self):
        """예시 메서드입니다."""
        return {"status": "ok"}
