import os
import json
import time
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth
from jose import jwt, JWTError
from src.configs import setting
from src.utils.logger import logger

# JWT 설정 (자체 발급용)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-local-jwt")
ALGORITHM = "HS256"

security = HTTPBearer()

async def verify_user(res: HTTPAuthorizationCredentials = Depends(security)):
    """
    파이어베이스 토큰 또는 자체 발급 JWT를 검증하여 사용자 정보를 반환합니다.
    """
    token = res.credentials
    
    # 1. 자체 발급 JWT 검증 시도
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email:
            # 자체 발급 토큰인 경우
            return {"email": email, "provider": "local", "uid": payload.get("uid")}
    except JWTError:
        # 자체 발급 토큰이 아니면 파이어베이스 검증으로 넘어감
        pass

    # 2. 파이어베이스 토큰 검증 시도
    # (verify_firebase_token.py의 로직을 그대로 활용)
    for i in range(2):
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            decoded_token["provider"] = "firebase"
            return decoded_token
        except Exception as e:
            if "Token used too early" in str(e) and i == 0:
                time.sleep(1)
                continue
            
            # 둘 다 실패한 경우에만 401 에러
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return None
