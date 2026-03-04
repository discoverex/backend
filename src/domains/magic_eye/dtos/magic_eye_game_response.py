from typing import List

from pydantic import BaseModel, Field


class MagicEyeGameResponse(BaseModel):
    problem: str = Field(..., description="Base64로 인코딩된 매직아이 문제 이미지 (data:image/png;base64,...)")
    answer: str = Field(..., description="Base64로 인코딩된 정답 깊이 맵 이미지")
    answer_key: str = Field(..., description="화면에 표시될 정답 이름 (예: 고래)")
    acceptable_words: List[str] = Field(..., description="정답으로 인정되는 유사어 리스트")

    class Config:
        json_schema_extra = {
            "example": {
                "problem": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...",
                "answer": "data:image/png;base64,m0KGgoAAAANSUhEUgAAAA...",
                "answer_key": "고래",
                "acceptable_words": ["고래", "흰수염고래", "whale"]
            }
        }