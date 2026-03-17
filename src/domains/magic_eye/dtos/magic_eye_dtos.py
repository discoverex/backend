
from typing import Optional

from pydantic import BaseModel, Field


class MagicEyeMetadataRecord(BaseModel):
    """매직아이 메타데이터 개별 레코드 모델"""

    asset_id: str = Field(..., description="에셋 아이디")
    file_number: int = Field(..., description="파일 번호")
    split: str = Field(..., description="데이터 분할 (train/test)")
    # CSV의 다른 컬럼들이 있다면 여기에 추가될 수 있습니다.
    # 현재는 사용자가 언급한 asset_id, file_number를 필수로 포함합니다.

    class Config:
        extra = "allow"  # CSV의 다른 모든 필드를 허용


class MagicEyeMetadataQuery(BaseModel):
    """매직아이 메타데이터 검색 쿼리 파라미터"""

    asset_id: Optional[str] = Field(None, description="필터링할 에셋 아이디")
    file_number: Optional[int] = Field(None, description="필터링할 파일 번호")


class MagicEyeQuizQuery(BaseModel):
    """매직아이 퀴즈 생성 쿼리 파라미터"""

    count: int = Field(5, description="추출할 퀴즈 후보 개수 (5~50, 범위를 벗어나면 최소/최대값으로 자동 조정됨)")


class MagicEyeCandidate(BaseModel):
    """매직아이 퀴즈 정답 후보 모델"""
    id: int = Field(..., description="후보 식별 ID")
    asset_id: str = Field(..., description="에셋 아이디")
    display_name: str = Field(..., description="표시 이름")
    problem_url: str = Field(..., description="문제 이미지 URL (서명됨)")
    answer_url: str = Field(..., description="정답 이미지 URL (서명됨)")

class MagicEyeCorrectAnswer(BaseModel):
    """매직아이 퀴즈 정답 정보 모델"""
    id: int = Field(..., description="정답인 후보의 식별 ID")
    asset_id: str = Field(..., description="정답 에셋 아이디")
    description: str = Field(..., description="정답 상세 설명 (프롬프트/목격자 증언)")

class MagicEyeQuizResponse(BaseModel):
    """매직아이 퀴즈 응답 모델"""
    total_count: int = Field(..., description="전체 퀴즈 후보 개수")
    candidates: list[MagicEyeCandidate] = Field(..., description="퀴즈 후보 리스트")
    correct_answer: MagicEyeCorrectAnswer = Field(..., description="정답 정보")

class MagicEyeFinderQuery(BaseModel):
    model_filename: str = Field(
        ...,
        description="조회할 ONNX 모델의 전체 파일명",
        examples=["ai_lv5.onnx"],
        min_length=5,
        pattern=r".*\.onnx$"
    )

class MagicEyeFinderResponse(BaseModel):
    model_name: str = Field(..., description="요청한 모델명", examples=["ai_lv5.onnx"])
    singed_url: str = Field(..., description="서명된 모델 주소(15분 유효)", examples=["https://storage.googleapis.com/discoverex-magic-eye-models/models/onnx/ai_lv5.onnx?..."])