from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.common.dtos.wrapped_response import WrappedResponse
from src.domains.magic_eye.dtos.magic_eye_dtos import (
    MagicEyeMetadataQuery,
    MagicEyeQuizQuery,
    MagicEyeQuizResponse, MagicEyeFinderQuery, MagicEyeFinderResponse,
)
from src.domains.magic_eye.services.magic_eye_service import MagicEyeService

magic_eye_router = APIRouter(prefix="/magic-eye", tags=["매직아이"])

# 서비스 인스턴스
magic_eye_service = MagicEyeService()

@magic_eye_router.get(
    "/quiz",
    response_model=WrappedResponse[MagicEyeQuizResponse],
    summary="매직아이 퀴즈 출제",
    description="객관식 매직아이 퀴즈를 생성하여 반환합니다."
)
async def get_magic_eye_quiz(query: MagicEyeQuizQuery = Depends()):
    """
    객관식 매직아이 퀴즈를 생성하여 반환합니다.
    요청한 개수(기본 5개)의 랜덤 후보군(이미지 URL 포함)과 정답 정보를 포함합니다.
    """
    data, message = await magic_eye_service.get_magic_eye_quiz(query.count)
    return WrappedResponse(data=data, message=message)

@magic_eye_router.get(
    "/model",
    response_model=WrappedResponse[MagicEyeFinderResponse],
    summary="매직아이 판별 모델 서명 URL 발급",
    description="비공개 버킷에 저장된 ONNX 모델에 접근할 수 있는 15분 유효 서명 URL을 생성합니다.",
)
async def get_magic_eye_finder(query: Annotated[MagicEyeFinderQuery, Depends()]):
    """
    프론트엔드 WebGPU 가속을 위해 비공개 버킷의 모델 접근용 서명된 URL을 발급해 반환합니다.
    """
    result = await magic_eye_service.get_model_download_url(model_filename=query.model_filename)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"모델 파일 '{query.model_filename}'을 찾을 수 없습니다."
        )

        # DTO 생성 시 값을 명시적으로 매핑
    return WrappedResponse(
        data=result,
        message=f"{query.model_filename} 접근 정보가 발급되었습니다."
    )

@magic_eye_router.get(
    "/metadata",
    summary="매직아이 메타데이터 조회",
    response_model=WrappedResponse[list[dict]],
    description="로컬에 저장된 매직아이 메타데이터를 조회합니다."
)
async def get_magic_eye_metadata(query: MagicEyeMetadataQuery = Depends()):
    """
    로컬에 저장된 매직아이 메타데이터를 조회합니다.
    asset_id, file_number를 통한 필터링 검색이 가능합니다.
    """
    data = await magic_eye_service.get_magic_eye_metadata(query)
    return WrappedResponse(data=data)
