from fastapi import Depends, APIRouter

from src.common.dtos.wrapped_response import WrappedResponse
from src.domains.auth.utils.verify_firebase_token import verify_firebase_token
from src.domains.auth.dtos.auth_dtos import UserInfo

auth_router = APIRouter(prefix="/auth", tags=["인증"])

@auth_router.get(
    "/users/me",
    response_model=WrappedResponse[UserInfo],
    summary="로그인",
    description="파이어베이스로부터 JWT를 받아 사용자 정보를 조회합니다.",
)
async def get_my_profile(user_info: dict = Depends(verify_firebase_token)):
    uid = user_info.get("uid")
    email = user_info.get("email")
    # DB(PostgreSQL 등)를 조회하여 추가 정보를 가져올 수 있습니다.
    # 예: user_data = db.query(User).filter(User.firebase_uid == uid).first()

    return WrappedResponse(
        data=UserInfo(uid=uid, email=email),
        message="인증 성공!"
    )