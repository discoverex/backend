from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class GameResponse(BaseModel):
    game_id: UUID = Field(..., description="게임 고유 ID")
    user_id: UUID = Field(..., description="사용자 ID")
    game_type: str = Field(..., description="게임 유형 (discoverex, magic-eye 등)")
    created_at: datetime = Field(..., description="생성 일시")

    class Config:
        from_attributes = True
