from fastapi import APIRouter, Depends

from src.common.dtos.wrapped_response import WrappedResponse
from src.configs.database import get_db_cursor
from src.domains.auth.auth_service import AuthService
from src.domains.auth.dtos.auth_dtos import UserInfo
from src.domains.auth.utils.verify_firebase_token import verify_firebase_token

auth_router = APIRouter(prefix="/auth", tags=["인증"])

def get_auth_service(cursor=Depends(get_db_cursor)) -> AuthService:
    """
    AuthService 인스턴스를 생성하여 반환합니다.
    """
    return AuthService(cursor)

@auth_router.get(
    "/users/me",
    response_model=WrappedResponse[UserInfo],
    summary="로그인 및 자동 가입",
    description="파이어베이스로부터 JWT를 받아 사용자 정보를 확인합니다. DB에 없는 신규 사용자라면 자동으로 회원가입을 진행합니다.",
)
async def get_my_profile(
    user_info: dict = Depends(verify_firebase_token),
    auth_service: AuthService = Depends(get_auth_service)
):
    email = user_info.get("email")
    # Firebase 토큰에서 이름을 가져옵니다. 없을 경우 이메일의 앞부분을 이름으로 사용합니다.
    name = user_info.get("name") or email.split("@")[0]

    # DB 조회 및 자동 가입 로직 수행
    user_data = auth_service.handle_login_or_register(
        email=email,
        name=name,
        sso_provider="firebase"
    )

    return WrappedResponse(
        data=user_data,
        message="로그인 성공"
    )
