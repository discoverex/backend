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
