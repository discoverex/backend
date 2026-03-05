from configs.setting import APP_ENV
from src.domains.auth.auth_router import auth_router

API_ROUTERS = [auth_router]

if APP_ENV == "local":
    try:
        from src.domains.magic_eye.magic_eye_router import magic_eye_router
        API_ROUTERS.append(magic_eye_router)
        print("✅ MagicEye Router loaded in local environment.")
    except ImportError as e:
        print(f"❌ Failed to load MagicEye Router: {e}")
