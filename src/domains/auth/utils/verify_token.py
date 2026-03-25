from typing import Optional

from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from src.configs.setting import ALGORITHM, AUTH_COOKIE_ENABLED, ENFORCE_REDIS_SESSIONS, SECRET_KEY
from src.domains.auth.utils.verify_firebase_token import _verify_firebase_core
from src.configs.database import get_db_cursor
from src.utils.load_sql import load_sql

from src.domains.auth.utils.session_manager import SessionManager

security = HTTPBearer(auto_error=False)
session_manager = SessionManager()

async def verify_user(
    request: Request, 
    res: Optional[HTTPAuthorizationCredentials] = Depends(security),
    cursor = Depends(get_db_cursor)
):
    """
    자체 발급 JWT 또는 파이어베이스 토큰을 검증하여 사용자 정보를 반환합니다.
    헤더(Authorization) 또는 쿠키(access_token)에서 토큰을 추출하여 Next.js SSR을 지원합니다.
    """
    # 1. 헤더 또는 쿠키에서 토큰 확인
    token = None
    if res and res.credentials:
        token = res.credentials.strip()
    elif AUTH_COOKIE_ENABLED:
        # 헤더에 없으면 쿠키에서 확인 (Next.js SSR 지원)
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보가 유효하지 않거나 토큰이 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    path = request.url.path
    is_logout_path = path.endswith("/auth/logout")

    # 1. 자체 발급 JWT 검증 시도
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        uid: str = payload.get("uid")
        if email and uid:
            if not is_logout_path and not session_manager.is_active(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="로그아웃되었거나 만료된 토큰입니다."
                )
            if ENFORCE_REDIS_SESSIONS and not is_logout_path and not session_manager.is_user_session_active(uid):
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
            if not is_logout_path:
                # 로그아웃 시간 비교
                if last_logout_at and auth_time and auth_time < last_logout_at.timestamp():
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="로그아웃된 세션입니다. 다시 로그인해 주세요."
                    )
                # Redis 세션 체크
                if ENFORCE_REDIS_SESSIONS and not session_manager.is_user_session_active(db_uuid):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="만료되거나 다른 기기에서 로그아웃된 세션입니다."
                    )
            
            firebase_payload["uid"] = db_uuid
        else:
            firebase_payload["uid"] = f_uid
        
        firebase_payload["token"] = token
        return firebase_payload

    # 모든 인증 수단 실패 시
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않거나 토큰이 만료되었습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
