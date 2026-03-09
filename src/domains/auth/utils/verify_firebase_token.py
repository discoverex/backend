import time
import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth
from src.utils.logger import error

security = HTTPBearer()

def _verify_firebase_core(token: str):
    """
    Firebase ID 토큰을 검증하는 핵심 비즈니스 로직.
    다른 유틸리티(예: verify_token.py)에서 재사용 가능하도록 분리됨.
    """
    if not firebase_admin._apps:
        error("Firebase SDK가 초기화되지 않았습니다.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase SDK가 초기화되지 않았습니다."
        )

    # 최대 3번 시도 (시간 오차 대비)
    for i in range(3):
        try:
            # ID 토큰 검증
            decoded_token = auth.verify_id_token(token, check_revoked=False)
            decoded_token["provider"] = "firebase"
            return decoded_token
        except Exception as e:
            error_msg = str(e)
            if "Token used too early" in error_msg and i < 2:
                time.sleep(1.5)  # 1.5초 대기 후 재시도
                continue

            error(f"DEBUG - Firebase Error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"인증 실패: {error_msg}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return None

async def verify_firebase_token(res: HTTPAuthorizationCredentials = Depends(security)):
    """
    FastAPI 의존성 주입용 함수. Firebase 전 전용 검증 시 사용.
    """
    return _verify_firebase_core(res.credentials.strip())
