from fastapi import APIRouter, Depends, status

from src.common.dtos.wrapped_response import WrappedResponse
from src.configs.database import get_db_cursor
from src.domains.discoverex.discoverex_service import DiscoverexService
from src.domains.discoverex.dtos.play_log_dto import PlayLogCreateRequest
from src.domains.auth.utils.verify_token import verify_user

discoverex_router = APIRouter(prefix="/discoverex", tags=["Discoverex"])

def get_discoverex_service(cursor=Depends(get_db_cursor)) -> DiscoverexService:
    return DiscoverexService(cursor)

@discoverex_router.get(
    "/jobs",
    response_model=WrappedResponse[list[str]],
    summary="작업 폴더 목록 조회",
    description="MinIO 버킷의 jobs/ 경로 아래에 있는 폴더(작업) 목록을 조회합니다. (인증 필요)"
)
async def get_job_list(
    # user_info: dict = Depends(verify_user),
    service: DiscoverexService = Depends(get_discoverex_service)
):
    """
    MinIO에서 작업 폴더 목록을 가져옵니다.
    """
    job_folders = service.get_job_list()
    
    return WrappedResponse(
        data=job_folders,
        message="작업 목록을 성공적으로 조회했습니다."
    )


@discoverex_router.post(
    "/logs",
    status_code=status.HTTP_201_CREATED,
    response_model=WrappedResponse[bool],
    summary="게임 플레이 로그 저장",
    description="로그인된 사용자의 게임 플레이 중 발생하는 클릭 이벤트 로그를 저장합니다. (인증 필요)"
)
async def post_play_logs(
    request: PlayLogCreateRequest,
    user_info: dict = Depends(verify_user),
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
