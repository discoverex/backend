from src.domains.discoverex.dtos.play_log_dto import PlayLogCreateRequest
from src.domains.discoverex.dtos.theme_dto import ThemeLayersResponse, LayerImage
from src.domains.discoverex.utils.gcs_util import get_gcs_util
from src.utils.load_sql import load_sql
from src.utils.logger import logger


class DiscoverexService:
    """
    Discoverex 게임 데이터를 처리하는 서비스 클래스입니다.
    """

    def __init__(self, cursor):
        self.cursor = cursor
        self.gcs_util = get_gcs_util()

    def get_theme_list(self) -> list[str]:
        """
        hide-and-seek/ 경로 하위의 테마(폴더) 목록을 조회합니다.
        """
        try:
            return self.gcs_util.list_subfolders("hide-and-seek/")
        except Exception as e:
            logger.error(f"테마 목록 조회 중 오류 발생: {str(e)}")
            return []

    def get_theme_layers(self, theme_name: str) -> ThemeLayersResponse:
        """
        특정 테마의 레이어 이미지(hide-and-seek/[theme_name]/outputs/layers/) 목록과 서명된 URL을 반환합니다.
        """
        try:
            prefix = f"hide-and-seek/{theme_name}/outputs/layers/"
            blob_names = self.gcs_util.list_blobs(prefix)
            
            layers = []
            for blob_name in blob_names:
                signed_url = self.gcs_util.generate_signed_url(blob_name)
                if signed_url:
                    # 파일명만 추출 (예: '.../layer1.png' -> 'layer1.png')
                    display_name = blob_name.split("/")[-1]
                    layers.append(LayerImage(name=display_name, url=signed_url))
            
            return ThemeLayersResponse(theme=theme_name, layers=layers)
        except Exception as e:
            logger.error(f"테마 레이어 조회 중 오류 발생 (theme={theme_name}): {str(e)}")
            return ThemeLayersResponse(theme=theme_name, layers=[])

    def save_play_logs(self, request_data: PlayLogCreateRequest) -> bool:
        """
        사용자의 플레이 로그들을 DB에 저장합니다.
        """
        try:
            insert_query = load_sql("domains/discoverex", "insert_play_log")
            
            for log in request_data.play_logs:
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
