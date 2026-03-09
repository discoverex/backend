import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=False)


# 공통 설정
REMOTE_HOST = os.getenv("REMOTE_HOST")

# RDB 설정
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST", REMOTE_HOST)
DB_PORT = int(os.getenv("DB_PORT"))

# LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# 원격 서버
APP_HOST = os.getenv("APP_HOST")  # 운영 환경에서는 '0.0.0.0' 주입
APP_PORT = int(os.getenv("APP_PORT"))
APP_ENV = os.getenv("APP_ENV")  # local, dev, prod 등

# services
BUCKET_NAME = os.getenv("BUCKET_NAME")
GCP_SERVICE_ACCOUNT_JSON = os.getenv("GCP_SERVICE_ACCOUNT_JSON")

# 프론트엔드
GAME_HUB_PORT = os.getenv("GAME_HUB_PORT")
DISCOVEREX_PORT = os.getenv("DISCOVEREX_PORT")
MAGIC_EYE_PORT = os.getenv("MAGIC_EYE_PORT")
# WEB_URL = f"http://{WEB_HOST}:{WEB_PORT}"
GAME_HUB_URL = os.getenv("GAME_HUB_URL")
DISCOVEREX_URL = os.getenv("DISCOVEREX_URL")
MAGIC_EYE_URL = os.getenv("MAGIC_EYE_URL")

# 허깅페이스
HF_TOKEN = os.getenv("HF_TOKEN")

# 인증
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7일 동안 유효
REFRESH_TOKEN_EXPIRE_SECONDS = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 7일 만료 (초단위)
