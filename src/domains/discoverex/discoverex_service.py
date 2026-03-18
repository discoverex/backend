from fastapi import HTTPException, status
from src.domains.discoverex.dtos.play_log_dto import PlayLogCreateRequest
from src.domains.discoverex.utils.minio_utils import get_job_folders
from src.utils.load_sql import load_sql
from src.utils.logger import logger


class DiscoverexService:
    """
    Discoverex 게임 데이터를 처리하는 서비스 클래스입니다.
    """

    def __init__(self, cursor):
        self.cursor = cursor

    def get_job_list(self) -> list[str]:
        """
        MinIO에서 작업 폴더 목록을 조회합니다.
        """
        try:
            return get_job_folders()
        except Exception as e:
            # 403 에러가 포함되어 있다면 명시적으로 권한 부족 오류를 발생시킵니다.
            if "403" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"MinIO 접근 권한이 거부되었습니다 (Cloudflare/MinIO 403 Forbidden). 상세 에러: {str(e)}"
                )
            # 그 외의 경우 500 에러를 발생시킵니다.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MinIO 서버 통신 중 오류가 발생했습니다: {str(e)}"
            )

    def save_play_logs(self, request_data: PlayLogCreateRequest) -> bool:
        """
        사용자의 플레이 로그들을 DB에 저장합니다.
        """
        try:
            insert_query = load_sql("domains/discoverex", "insert_play_log")
            
            # 각 플레이 로그 항목을 별도의 행으로 저장
            for log in request_data.play_logs:
                # Pydantic 모델을 JSON 직렬화 가능한 딕셔너리로 변환 후 JSON 문자열화
                event_data = log.model_dump_json()
                
                self.cursor.execute(
                    insert_query,
                    (
                        str(request_data.user_id),
                        str(request_data.game_id),
                        event_data
                    )
                )
            
            return True
        except Exception as e:
            logger.error(f"플레이 로그 저장 중 오류 발생: {str(e)}")
            raise e
