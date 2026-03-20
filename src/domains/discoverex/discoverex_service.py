from src.domains.discoverex.dtos.play_log_dto import PlayLogCreateRequest
from src.domains.discoverex.dtos.theme_dto import ThemeLayersResponse, LayerImage, DeliveryBundle, SceneRef
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
        특정 테마의 레이어 이미지, manifest JSON, lottie 파일 정보를 반환합니다.
        """
        try:
            output_prefix = f"hide-and-seek/{theme_name}/outputs/"
            layer_prefix = f"{output_prefix}layers/"
            
            # 1. 레이어 이미지 목록 조회 (Signed URL)
            blob_names = self.gcs_util.list_blobs(layer_prefix)
            layers = []
            for blob_name in blob_names:
                signed_url = self.gcs_util.generate_signed_url(blob_name)
                if signed_url:
                    display_name = blob_name.split("/")[-1]
                    layers.append(LayerImage(name=display_name, url=signed_url))
            
            # 2. manifest.json 파일 내용 읽기 및 필터링
            manifest_json = self.gcs_util.read_json_blob(f"{output_prefix}manifest.json")
            
            delivery_bundle = None
            if manifest_json:
                # "manifest" 키가 있으면 그 안에서 찾고, 없으면 전체 데이터에서 찾습니다.
                base_data = manifest_json.get("manifest", manifest_json)
                raw_bundle = base_data.get("delivery_bundle", {})
                
                if raw_bundle:
                    scene_ref_data = raw_bundle.get("scene_ref", {})
                    delivery_bundle = DeliveryBundle(
                        scene_ref=SceneRef(
                            scene_id=scene_ref_data.get("scene_id", ""),
                            version_id=scene_ref_data.get("version_id", "")
                        ),
                        playable=raw_bundle.get("playable", {}),
                        answer_key=raw_bundle.get("answer_key", {})
                    )
            
            # 3. .lottie 파일 조회 (Signed URL)
            # outputs/ 경로의 파일 중 .lottie로 끝나는 첫 번째 파일을 찾습니다.
            output_blobs = self.gcs_util.list_blobs(output_prefix)
            lottie_url = None
            for b in output_blobs:
                if b.endswith(".lottie"):
                    lottie_url = self.gcs_util.generate_signed_url(b)
                    break
            
            return ThemeLayersResponse(
                theme=theme_name,
                layers=layers,
                manifest=delivery_bundle,
                lottie=lottie_url
            )
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
