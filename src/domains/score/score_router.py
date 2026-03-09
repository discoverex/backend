from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.common.dtos.wrapped_response import WrappedResponse
from src.configs.database import get_db_cursor
from src.domains.auth.auth_service import AuthService
from src.domains.auth.utils.verify_firebase_token import verify_firebase_token
from src.domains.score.dtos.score_dto import ScoreCreateRequest, ScoreResponse
from src.domains.score.score_service import ScoreService

score_router = APIRouter(prefix="/scores", tags=["점수 관리"])

def get_score_service(cursor=Depends(get_db_cursor)) -> ScoreService:
    return ScoreService(cursor)

def get_auth_service(cursor=Depends(get_db_cursor)) -> AuthService:
    return AuthService(cursor)

@score_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=WrappedResponse[ScoreResponse],
    summary="사용자 점수 등록",
    description="로그인된 사용자의 게임 점수를 등록합니다."
)
async def post_score(
    request: ScoreCreateRequest,
    user_info: dict = Depends(verify_firebase_token),
    score_service: ScoreService = Depends(get_score_service),
    auth_service: AuthService = Depends(get_auth_service)
):
    # 1. 토큰에서 추출한 이메일로 DB 상의 사용자 정보를 확인
    email = user_info.get("email")
    name = user_info.get("name") or email.split("@")[0]
    
    # 2. handle_login_or_register를 통해 UUID를 포함한 사용자 정보 객체(UserInfo) 획득
    user_data = auth_service.handle_login_or_register(email=email, name=name)
    
    # 3. 점수 기록
    result = score_service.register_score(user_id=user_data.user_id, request=request)
    
    return WrappedResponse(
        data=result,
        message="점수가 성공적으로 기록되었습니다."
    )

@score_router.get(
    "/",
    response_model=WrappedResponse[List[ScoreResponse]],
    summary="점수 목록 조회",
    description="최고 득점 순으로 점수 목록을 조회합니다. 사용자별, 게임 유형별, 기간별 필터링이 가능합니다."
)
async def get_scores(
    user_id: Optional[UUID] = Query(None, description="특정 사용자의 점수만 조회할 경우"),
    game_type: Optional[str] = Query(None, description="특정 게임 유형(discoverex, magic-eye)만 조회할 경우"),
    start_date: Optional[datetime] = Query(None, description="조회 시작 기간 (ISO 형식)"),
    end_date: Optional[datetime] = Query(None, description="조회 종료 기간 (ISO 형식)"),
    # 인증 필수
    _: dict = Depends(verify_firebase_token),
    score_service: ScoreService = Depends(get_score_service)
):
    results = score_service.get_user_scores(
        user_id=user_id,
        game_type=game_type,
        start_date=start_date,
        end_date=end_date
    )
    
    return WrappedResponse(
        data=results,
        message="점수 목록 조회 성공"
    )
