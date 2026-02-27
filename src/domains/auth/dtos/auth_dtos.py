from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    message: str = Field(..., description="기타 메시지"),
    firebase_uid: str = Field(..., description="파이어베이스 유저 고유 아이디"),
    email: str = Field(..., description="사용자 이메일")