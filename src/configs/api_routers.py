from src.domains.auth.auth_router import auth_router
from src.domains.magic_eye.magic_eye_router import magic_eye_router
from src.domains.media.media_router import media_router
from src.domains.discoverex.discoverex_router import discoverex_router

API_ROUTERS = [
    auth_router,
    magic_eye_router,
    media_router,
    discoverex_router
]
