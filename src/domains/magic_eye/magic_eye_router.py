from fastapi import APIRouter, Depends

from src.domains.magic_eye.dtos.magic_eye_dtos import MagicEyeMetadataQuery
from src.domains.magic_eye.services.magic_eye_service import MagicEyeService

magic_eye_router = APIRouter(prefix="/magic-eye", tags=["매직아이"])

# 서비스 인스턴스
magic_eye_service = MagicEyeService()

@magic_eye_router.get("/")
async def get_magic_eye():
    """매직아이 엔드포인트의 기본 골격입니다."""
    return {"message": "Magic Eye skeleton is ready."}

@magic_eye_router.get("/metadata")
async def get_magic_eye_metadata(query: MagicEyeMetadataQuery = Depends()):
    """
    로컬에 저장된 매직아이 메타데이터를 조회합니다.
    asset_id, file_number를 통한 필터링 검색이 가능합니다.
    """
    return await magic_eye_service.get_magic_eye_metadata(query)
