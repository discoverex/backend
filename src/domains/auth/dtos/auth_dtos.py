from datetime import datetime
from typing import Any, List
from uuid import UUID

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    user_id: UUID = Field(..., description="사용자 고유 UUID")
    email: str = Field(..., description="사용자 이메일")
    name: str = Field(..., description="사용자 이름")
    sso_provider: str = Field(default="none", description="SSO 제공자 (예: firebase)")
    badges: List[Any] = Field(default=[], description="사용자 뱃지 목록")
    level: int = Field(default=1, description="사용자 레벨")
    exp: int = Field(default=0, description="사용자 경험치")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    class Config:
        from_attributes = True

class UserCreateRequest(BaseModel):
    email: str = Field(..., description="사용자 이메일")
    name: str = Field(..., description="사용자 이름")
    password: str = Field(..., description="비밀번호")

class UserUpdateRequest(BaseModel):
    name: str = Field(..., description="변경할 사용자 이름")

class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., description="새 비밀번호")

class UserLoginRequest(BaseModel):
    email: str = Field(..., description="사용자 이메일")
    password: str = Field(..., description="비밀번호")
