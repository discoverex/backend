from fastapi import Depends, APIRouter

from src.common.dtos.wrapped_response import WrappedResponse
from src.domains.auth.utils.verify_firebase_token import verify_firebase_token
from src.domains.auth.dtos.auth_dtos import UserInfo

auth_router = APIRouter(prefix="/auth", tags=["인증"])

@auth_router.get(
    "/users/me",
    response_model=WrappedResponse[UserInfo],
    summary="로그인",
    description="2d6 주사위를 굴려 플레이어의 능력치를 더한 후, 설정된 난이도와 비교해 성공 여부를 판정합니다.",
)
async def get_my_profile(user_info: dict = Depends(verify_firebase_token)):
    # DB(PostgreSQL 등)를 조회하여 추가 정보를 가져올 수 있습니다.
    # 예: user_data = db.query(User).filter(User.firebase_uid == uid).first()

    return WrappedResponse(
            data=UserInfo(**user_info),
            message="인증 성공!"
        )