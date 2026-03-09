import os

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from src.domains.auth.utils.verify_firebase_token import _verify_firebase_core

# JWT 설정 (자체 발급용)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-local-jwt")
ALGORITHM = "HS256"

security = HTTPBearer()

async def verify_user(res: HTTPAuthorizationCredentials = Depends(security)):
    """
    자체 발급 JWT 또는 파이어베이스 토큰을 검증하여 사용자 정보를 반환합니다.
    """
    token = res.credentials.strip()
    
    # 1. 자체 발급 JWT 검증 시도
    try:
        # 우선 자체 토큰인지 확인 (빠른 거절을 위해 시도)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email:
            # 자체 발급 토큰인 경우
            return {"email": email, "provider": "local", "uid": payload.get("uid")}
    except JWTError:
        # 자체 발급 토큰이 아니면 파이어베이스 검증 단계로 넘어감
        pass

    # 2. 파이어베이스 토큰 검증 시도 (공통 유틸리티 호출)
    return _verify_firebase_core(token)
