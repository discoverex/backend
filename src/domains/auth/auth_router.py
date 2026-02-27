from fastapi import Depends, APIRouter

from src.common.dtos.wrapped_response import WrappedResponse
from src.domains.auth.utils.verify_firebase_token import verify_firebase_token
from src.domains.auth.dtos.auth_dtos import UserInfo

auth_router = APIRouter(prefix="/auth", tags=["인증"])

@auth_router.get(
    "/users/me",
    response_model=WrappedResponse[UserInfo],
    summary="주사위 판정 실행",
    description="2d6 주사위를 굴려 플레이어의 능력치를 더한 후, 설정된 난이도와 비교해 성공 여부를 판정합니다.",
)
async def get_my_profile(user_info: dict = Depends(verify_firebase_token)):
    # user_info에는 Firebase에서 추출한 'uid', 'email' 등이 들어있습니다.
    uid = user_info.get("uid")
    email = user_info.get("email")

    # 여기서 우리 DB(PostgreSQL 등)를 조회하여 추가 정보를 가져올 수 있습니다.
    # 예: user_data = db.query(User).filter(User.firebase_uid == uid).first()

    return {
        "message": "인증 성공!",
        "firebase_uid": uid,
        "email": email
    }