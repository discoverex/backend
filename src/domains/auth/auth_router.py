from fastapi import APIRouter, Depends, status
from src.common.dtos.wrapped_response import WrappedResponse
from src.configs.database import get_db_cursor
from src.domains.auth.auth_service import AuthService
from src.domains.auth.dtos.auth_dtos import UserInfo, UserCreateRequest, UserUpdateRequest, PasswordChangeRequest, UserLoginRequest
from src.domains.auth.utils.verify_token import verify_user

auth_router = APIRouter(prefix="/auth", tags=["인증"])

def get_auth_service(cursor=Depends(get_db_cursor)) -> AuthService:
    """
    AuthService 인스턴스를 생성하여 반환합니다.
    """
    return AuthService(cursor)

@auth_router.post(
    "/register",
    response_model=WrappedResponse[UserInfo],
    status_code=status.HTTP_201_CREATED,
    summary="일반 회원가입",
    description="이메일과 비밀번호를 사용하여 회원가입을 진행합니다."
)
async def register_user(
    request: UserCreateRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    일반 이메일/비밀번호 회원가입
    """
    user_data = auth_service.register_with_password(request)
    return WrappedResponse(
        data=user_data,
        message="회원가입이 완료되었습니다."
    )

@auth_router.post(
    "/login",
    response_model=WrappedResponse[str],
    summary="일반 로그인",
    description="이메일과 비밀번호로 로그인하여 자체 JWT 토큰을 발급받습니다."
)
async def login_user(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    이메일/비밀번호 로그인 (JWT 발급)
    """
    token = auth_service.authenticate_user(request.email, request.password)
    return WrappedResponse(
        data=token,
        message="로그인 성공"
    )

@auth_router.post(
    "/logout",
    response_model=WrappedResponse[bool],
    summary="로그아웃",
    description="현재 세션을 파기하고 로그아웃합니다. (Redis에서 세션 삭제)"
)
async def logout_user(
    user_info: dict = Depends(verify_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    로그아웃 (모든 앱 세션 삭제)
    """
    user_id = user_info.get("uid")
    token = user_info.get("token")
    
    if user_id:
        auth_service.logout(user_id=user_id, token=token)
    
    return WrappedResponse(
        data=True,
        message="로그아웃되었습니다."
    )

@auth_router.get(
    "/users/me",
    response_model=WrappedResponse[UserInfo],
    summary="로그인 및 자동 가입",
    description="토큰(Firebase 또는 자체 JWT)을 받아 사용자 정보를 확인합니다. DB에 없는 신규 사용자라면 자동으로 회원가입을 진행합니다.",
)
async def get_my_profile(
    user_info: dict = Depends(verify_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    email = user_info.get("email")
    provider = user_info.get("provider", "firebase")
    fuid = user_info.get("sub") if provider == "firebase" else None
    
    # Firebase 토큰인 경우 이름을 가져오고, 로컬 JWT인 경우 이름 정보는 DB에서 조회되므로 최소값 전달
    photoURL = user_info.get("picture") or user_info.get("photoURL")
    name = user_info.get("name") or email.split("@")[0]

    # DB 조회 및 (필요 시) 자동 가입/SSO 연동 로직 수행
    user_data = auth_service.handle_login_or_register(
        email=email,
        name=name,
        sso_provider=provider,
        firebase_uid=fuid,
        photoURL=photoURL
    )

    return WrappedResponse(
        data=user_data,
        message="인증 성공"
    )

@auth_router.patch(
    "/users/me/name",
    response_model=WrappedResponse[UserInfo],
    summary="사용자 이름 수정",
    description="로그인된 사용자의 이름을 수정합니다."
)
async def update_my_name(
    request: UserUpdateRequest,
    user_info: dict = Depends(verify_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    # 1. 토큰의 이메일로 사용자 UUID 확보
    email = user_info.get("email")
    fuid = user_info.get("sub") if user_info.get("provider") == "firebase" else None
    user_data = auth_service.handle_login_or_register(email=email, name="", firebase_uid=fuid)
    
    # 2. 이름 업데이트
    updated_user = auth_service.update_user_name(user_id=user_data.user_id, name=request.name)
    
    return WrappedResponse(
        data=updated_user,
        message="사용자 이름이 성공적으로 변경되었습니다."
    )

@auth_router.post(
    "/users/me/change-password",
    response_model=WrappedResponse[bool],
    summary="비밀번호 변경",
    description="로그인된 사용자의 비밀번호를 변경합니다. 일반 가입자만 가능합니다."
)
async def change_my_password(
    request: PasswordChangeRequest,
    user_info: dict = Depends(verify_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    # 1. 토큰의 이메일로 사용자 UUID 확보
    email = user_info.get("email")
    user_data = auth_service.handle_login_or_register(email=email, name="")
    
    # 2. 비밀번호 변경
    auth_service.change_password(
        user_id=user_data.user_id, 
        old_password=request.old_password, 
        new_password=request.new_password
    )
    
    return WrappedResponse(
        data=True,
        message="비밀번호가 성공적으로 변경되었습니다."
    )
