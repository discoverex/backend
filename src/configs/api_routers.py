from src.domains.auth.auth_router import auth_router
from src.domains.magic_eye.magic_eye_router import magic_eye_router

API_ROUTERS = [
    auth_router,
    magic_eye_router
]
