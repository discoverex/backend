from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ThemeListResponse(BaseModel):
    """
    게임 테마 목록 응답 DTO
    """
    themes: List[str]

class LayerImage(BaseModel):
    """
    레이어 이미지 정보 DTO
    """
    name: str
    url: str

class SceneRef(BaseModel):
    """
    manifest 내 scene_ref 정보
    """
    scene_id: str
    version_id: str

class DeliveryBundle(BaseModel):
    """
    manifest 내 delivery_bundle 정보 중 선별된 필드들
    """
    scene_ref: SceneRef
    playable: Dict[str, Any]
    answer_key: Dict[str, Any]

class ThemeLayersResponse(BaseModel):
    """
    테마별 레이어 이미지 목록 응답 DTO
    """
    theme: str
    layers: List[LayerImage]
    manifest: Optional[DeliveryBundle] = None
    lottie: Optional[str] = None
