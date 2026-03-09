from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ScoreCreateRequest(BaseModel):
    game_id: UUID = Field(..., description="게임/맵 고유 ID")
    game_type: str = Field(..., description="게임 유형 (discoverex 또는 magic-eye)")
    score: int = Field(..., description="획득 점수")

class ScoreResponse(BaseModel):
    user_id: UUID
    game_id: UUID
    game_type: str
    last_score: int
    updated_at: datetime

    class Config:
        from_attributes = True
