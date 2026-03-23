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

class BackgroundImage(BaseModel):
    image_id: str
    src: str
    prompt: str
    width: int
    height: int

class BBox(BaseModel):
    x: float
    y: float
    w: float
    h: float

class Answer(BaseModel):
    lottie_id: str
    name: str
    src: str
    bbox: BBox
    prompt: str
    order: int


class DeliveryBundle(BaseModel):
    """
    manifest 내 delivery_bundle 정보 중 선별된 필드들
    """
    scene_ref: SceneRef
    background_img: BackgroundImage
    answers: List[Answer]

class ThemeLayersResponse(BaseModel):
    """
    테마별 레이어 이미지 목록 응답 DTO
    """
    theme: str
    layers: List[LayerImage]
    manifest: Optional[DeliveryBundle] = None
