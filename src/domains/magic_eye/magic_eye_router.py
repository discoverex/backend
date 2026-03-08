from fastapi import APIRouter
from src.domains.magic_eye.services.magic_eye_service import MagicEyeService

magic_eye_router = APIRouter(prefix="/magic-eye", tags=["매직아이"])

# 서비스 인스턴스
magic_eye_service = MagicEyeService()

@magic_eye_router.get("/")
async def get_magic_eye():
    """매직아이 엔드포인트의 기본 골격입니다."""
    return {"message": "Magic Eye skeleton is ready."}
