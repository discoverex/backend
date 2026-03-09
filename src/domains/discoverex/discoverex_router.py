from fastapi import APIRouter, Depends, status

from src.common.dtos.wrapped_response import WrappedResponse
from src.configs.database import get_db_cursor
from src.domains.discoverex.discoverex_service import DiscoverexService
from src.domains.discoverex.dtos.play_log_dto import PlayLogCreateRequest
from src.domains.auth.utils.verify_firebase_token import verify_firebase_token

discoverex_router = APIRouter(prefix="/discoverex", tags=["Discoverex"])

def get_discoverex_service(cursor=Depends(get_db_cursor)) -> DiscoverexService:
    return DiscoverexService(cursor)

@discoverex_router.post(
    "/logs",
    status_code=status.HTTP_201_CREATED,
    response_model=WrappedResponse[bool],
    summary="게임 플레이 로그 저장",
    description="로그인된 사용자의 게임 플레이 중 발생하는 클릭 이벤트 로그를 저장합니다. (Firebase 인증 필요)"
)
async def post_play_logs(
    request: PlayLogCreateRequest,
    user_info: dict = Depends(verify_firebase_token), # 초기화 과정에서 로그인 여부 먼저 검증
    service: DiscoverexService = Depends(get_discoverex_service)
):
    """
    게임 플레이 로그 리스트를 받아 DB에 저장합니다.
    """
    success = service.save_play_logs(request)
    
    return WrappedResponse(
        data=success,
        message="플레이 로그가 성공적으로 기록되었습니다."
    )
