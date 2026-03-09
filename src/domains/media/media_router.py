from fastapi import APIRouter, Depends, Response, Query
from src.domains.media.media_service import MediaService
from src.common.dtos.wrapped_response import WrappedResponse

media_router = APIRouter(prefix="/media", tags=["미디어"])

def get_media_service() -> MediaService:
    """
    MediaService 인스턴스를 생성하여 반환합니다.
    """
    return MediaService()

@media_router.get(
    "/images/{blob_name:path}",
    summary="이미지 조회 (Binary)",
    description="GCS 스토리지의 이미지 경로를 전달받아 이미지 데이터를 직접 반환합니다."
)
async def get_image(
    blob_name: str,
    media_service: MediaService = Depends(get_media_service)
):
    """
    이미지 바이트 데이터를 Response로 반환합니다.
    (브라우저에서 직접 <img src="/media/images/path/to/img.png" /> 형태로 사용 가능)
    """
    image_bytes = media_service.get_image_content(blob_name)

    # 파일 확장자에 따른 Content-Type을 유추하여 반환 (기본값 image/png)
    content_type = "image/png"
    if blob_name.lower().endswith(".jpg") or blob_name.lower().endswith(".jpeg"):
        content_type = "image/jpeg"
    elif blob_name.lower().endswith(".gif"):
        content_type = "image/gif"
    elif blob_name.lower().endswith(".webp"):
        content_type = "image/webp"

    return Response(content=image_bytes, media_type=content_type)

@media_router.get(
    "/images-list",
    response_model=WrappedResponse[list[dict]],
    summary="이미지 목록 조회 (Signed URL)",
    description="특정 경로(prefix) 내의 모든 이미지에 대해 접근 가능한 서명된 URL 목록을 반환합니다."
)
async def get_images_list(
    prefix: str = Query(
        default="", 
        description="조회할 GCS 버킷 내의 폴더 경로 (예: 'games/rex/')",
        examples=["games/rex/", "magic_eye/results/"]
    ),
    media_service: MediaService = Depends(get_media_service)
):
    """
    특정 폴더 내의 이미지 목록을 서명된 URL 형태로 반환합니다.
    """
    # GCSImageLoader를 직접 써서 목록을 가져올 수도 있습니다.
    blob_names = media_service.gcs_loader.list_blobs(prefix)
    image_urls = media_service.get_multiple_images(blob_names)

    return WrappedResponse(
        data=image_urls,
        message="이미지 목록 조회 성공"
    )
