from src.domains.discoverex.dtos.play_log_dto import PlayLogCreateRequest
from src.domains.discoverex.utils.gcs_util import get_gcs_folder_util
from src.utils.load_sql import load_sql
from src.utils.logger import logger


class DiscoverexService:
    """
    Discoverex 게임 데이터를 처리하는 서비스 클래스입니다.
    """

    def __init__(self, cursor):
        self.cursor = cursor
        self.gcs_util = get_gcs_folder_util()

    def get_theme_list(self) -> list[str]:
        """
        hide-and-seek/ 경로 하위의 테마(폴더) 목록을 조회합니다.
        """
        try:
            return self.gcs_util.list_subfolders("hide-and-seek/")
        except Exception as e:
            logger.error(f"테마 목록 조회 중 오류 발생: {str(e)}")
            return []

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
