from pydantic import BaseModel
from typing import List

class ThemeListResponse(BaseModel):
    """
    게임 테마 목록 응답 DTO
    """
    themes: List[str]
