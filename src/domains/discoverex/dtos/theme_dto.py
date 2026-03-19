from pydantic import BaseModel
from typing import List

class ThemeListResponse(BaseModel):
    """
    게임 테마 목록 응답 DTO
    """
    themes: List[str]

class LayerImage(BaseModel):
    """
    레이어 이미지 정보 DTO
    """
    name: str
    url: str

class ThemeLayersResponse(BaseModel):
    """
    테마별 레이어 이미지 목록 응답 DTO
    """
    theme: str
    layers: List[LayerImage]
