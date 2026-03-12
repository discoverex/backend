from fastapi import APIRouter, Depends

from src.common.dtos.wrapped_response import WrappedResponse
from src.domains.magic_eye.dtos.magic_eye_dtos import (
    MagicEyeMetadataQuery,
    MagicEyeQuizQuery,
    MagicEyeQuizResponse,
)
from src.domains.magic_eye.services.magic_eye_service import MagicEyeService

magic_eye_router = APIRouter(prefix="/magic-eye", tags=["매직아이"])

# 서비스 인스턴스
magic_eye_service = MagicEyeService()

@magic_eye_router.get("/quiz", response_model=WrappedResponse[MagicEyeQuizResponse])
async def get_magic_eye_quiz(query: MagicEyeQuizQuery = Depends()):
    """
    객관식 매직아이 퀴즈를 생성하여 반환합니다.
    요청한 개수(기본 5개)의 랜덤 후보군(이미지 URL 포함)과 정답 정보를 포함합니다.
    """
    data, message = await magic_eye_service.get_magic_eye_quiz(query.count)
    return WrappedResponse(data=data, message=message)

@magic_eye_router.get("/metadata", response_model=WrappedResponse[list[dict]])
async def get_magic_eye_metadata(query: MagicEyeMetadataQuery = Depends()):

    """
    로컬에 저장된 매직아이 메타데이터를 조회합니다.
    asset_id, file_number를 통한 필터링 검색이 가능합니다.
    """
    data = await magic_eye_service.get_magic_eye_metadata(query)
    return WrappedResponse(data=data)
