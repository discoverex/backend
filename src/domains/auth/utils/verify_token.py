import os

from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from src.domains.auth.utils.verify_firebase_token import _verify_firebase_core
from src.configs.database import get_db_cursor
from src.utils.load_sql import load_sql

# JWT 설정 (자체 발급용)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-local-jwt")
ALGORITHM = "HS256"

from src.domains.auth.utils.session_manager import SessionManager

security = HTTPBearer()
session_manager = SessionManager()

async def verify_user(
    request: Request, 
    res: HTTPAuthorizationCredentials = Depends(security),
    cursor = Depends(get_db_cursor)
):
    """
    자체 발급 JWT 또는 파이어베이스 토큰을 검증하여 사용자 정보를 반환합니다.
    /auth/users/me 또는 /auth/logout 경로인 경우 세션 상태와 상관없이 토큰만 유효하면 통과시킵니다.
    """
    token = res.credentials.strip()
    path = request.url.path
    # 세션 체크 및 로그아웃 시간 비교 예외 경로
    skip_session_check = path.endswith("/auth/users/me") or path.endswith("/auth/logout")

    # 1. 자체 발급 JWT 검증 시도
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        uid: str = payload.get("uid")
        if email and uid:
            # 예외 경로가 아닌 경우에만 Redis 세션 활성 여부 체크
            if not skip_session_check and not session_manager.is_user_session_active(uid):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="만료되거나 다른 기기에서 로그아웃된 세션입니다."
                )
            return {"email": email, "provider": "local", "uid": uid, "token": token}
    except JWTError:
        pass

    # 2. 파이어베이스 토큰 검증 시도
    firebase_payload = _verify_firebase_core(token)
    if firebase_payload:
        f_uid = firebase_payload.get("sub")
        email = firebase_payload.get("email")
        auth_time = firebase_payload.get("auth_time")

        db_uuid = session_manager.get_uuid_from_fuid(f_uid)
        last_logout_at = None

        if not db_uuid and email:
            query = load_sql("domains/auth", "get_user_by_email")
            cursor.execute(query, (email,))
            user_data = cursor.fetchone()
            if user_data:
                db_uuid = str(user_data.get("user_id"))
                last_logout_at = user_data.get("last_logout_at")
                session_manager.set_uid_mapping(f_uid, db_uuid)

        if db_uuid and not last_logout_at:
            query = load_sql("domains/auth", "get_user_by_email")
            cursor.execute(query, (email,))
            user_data = cursor.fetchone()
            if user_data:
                last_logout_at = user_data.get("last_logout_at")

        if db_uuid:
            # [핵심] skip_session_check가 아닐 때만 로그아웃 시간 및 Redis 세션 체크 수행
            if not skip_session_check:
                # 로그아웃 시간 비교
                if last_logout_at and auth_time and auth_time < last_logout_at.timestamp():
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="로그아웃된 세션입니다. 다시 로그인해 주세요."
                    )
                # Redis 세션 체크
                if not session_manager.is_user_session_active(db_uuid):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="만료되거나 다른 기기에서 로그아웃된 세션입니다."
                    )
            
            firebase_payload["uid"] = db_uuid
        else:
            firebase_payload["uid"] = f_uid

        return firebase_payload

    # 모든 인증 수단 실패 시
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않거나 토큰이 만료되었습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
