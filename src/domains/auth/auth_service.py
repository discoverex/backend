from uuid import UUID

from fastapi import HTTPException, status

from src.domains.auth.dtos.auth_dtos import UserCreateRequest, UserInfo
from src.domains.auth.utils.password_utils import PasswordUtils
from src.utils.load_sql import load_sql


from datetime import datetime, timedelta
from jose import jwt
from typing import Optional

from src.domains.auth.utils.session_manager import SessionManager

# JWT 설정 (설정 파일로 빼는 것이 좋으나 여기서는 예시로 상수로 둡니다)
SECRET_KEY = "your-secret-key-for-local-jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1일

class AuthService:
    """
    사용자 인증 및 가입을 담당하는 서비스 클래스입니다.
    """

    def __init__(self, cursor):
        self.cursor = cursor
        self.session_manager = SessionManager()

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """자체 JWT를 생성합니다."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def authenticate_user(self, email: str, password: str) -> str:
        """사용자를 인증하고 JWT 토큰을 반환하며 Redis에 세션을 저장합니다."""
        # 이메일로 사용자 조회
        query = load_sql("domains/auth", "get_user_by_email")
        self.cursor.execute(query, (email,))
        user_data = self.cursor.fetchone()
        
        if not user_data or not user_data.get("password"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자 정보를 찾을 수 없습니다.")

        # 비밀번호 검증
        if not PasswordUtils.verify_password(password, user_data.get("password")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비밀번호가 일치하지 않습니다.")

        # 토큰 발급
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        user_id = str(user_data.get("user_id"))
        token_payload = {"sub": user_data.get("email"), "uid": user_id}
        
        access_token = self.create_access_token(
            data=token_payload,
            expires_delta=access_token_expires
        )
        
        # Redis 세션 저장 (토큰별 & 사용자별 통합 세션 모두 갱신)
        session_data = {
            "user_id": user_id,
            "email": email,
            "provider": "local"
        }
        expire_seconds = int(access_token_expires.total_seconds())
        self.session_manager.set_session(access_token, session_data, expire_seconds)
        self.session_manager.set_user_session(user_id, session_data, expire_seconds)
        
        return access_token

    def logout(self, user_id: str, token: str = None) -> bool:
        """전체 로그아웃 처리 (DB에 로그아웃 시간 기록 및 Redis 세션 파기)"""

        # 1. DB에 마지막 로그아웃 시간 기록 (다른 앱 간 동기화 핵심)
        query_update_logout = load_sql("domains/auth", "update_last_logout")
        self.cursor.execute(query_update_logout, (user_id,))
        
        # 2. Redis 세션 삭제
        if token:
            self.session_manager.delete_session(token)
        return self.session_manager.delete_user_session(user_id)

    def register_with_password(self, request: UserCreateRequest) -> UserInfo:
        """
        비밀번호 기반 회원가입을 처리합니다.
        """
        # 이메일 중복 확인
        check_query = load_sql("domains/auth", "get_user_by_email")
        self.cursor.execute(check_query, (request.email,))
        if self.cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 가입된 이메일입니다."
            )

        # 비밀번호 해싱 후 저장
        hashed_pwd = PasswordUtils.hash_password(request.password)
        create_query = load_sql("domains/auth", "create_user_with_password")
        self.cursor.execute(create_query, (request.email, request.name, hashed_pwd))
        
        return UserInfo(**self.cursor.fetchone())

    def handle_login_or_register(self, email: str, name: str, sso_provider: str = "firebase", firebase_uid: str = None) -> UserInfo:
        """
        이메일로 사용자를 조회하고, 없으면 새로 가입 시킨 후 사용자 정보를 반환합니다.
        기존에 일반 가입('none') 사용자가 소셜로 접근 시 SSO 정보를 업데이트합니다.
        """
        # 1. 사용자 조회
        query_get = load_sql("domains/auth", "get_user_by_email")
        self.cursor.execute(query_get, (email,))
        user_data = self.cursor.fetchone()

        if user_data:
            # 기존 사용자가 일반 가입('none')인 상태에서 파이어베이스로 접근한 경우 자동 연동
            if user_data.get("sso_provider") == "none" and sso_provider == "firebase":
                update_query = load_sql("domains/auth", "update_user_sso")
                self.cursor.execute(update_query, (sso_provider, email))
                user_data = self.cursor.fetchone()

            user_id_str = str(user_data.get("user_id"))
            
            # Redis 통합 세션 생성/갱신
            self.session_manager.set_user_session(
                user_id=user_id_str,
                session_data={"user_id": user_id_str, "email": email, "provider": sso_provider}
            )

            # Firebase UID와 DB UUID 매핑 저장 (verify_user에서 사용)
            if firebase_uid:
                self.session_manager.set_uid_mapping(f_uid=firebase_uid, db_uuid=user_id_str)
            
            return UserInfo(**user_data)

        # 2. 신규 사용자 가입 (자동 가입)
        query_create = load_sql("domains/auth", "create_user")
        self.cursor.execute(query_create, (email, name, sso_provider))
        new_user_data = self.cursor.fetchone()

        user_id_str = str(new_user_data.get("user_id"))
        
        # Redis 통합 세션 생성
        self.session_manager.set_user_session(
            user_id=user_id_str,
            session_data={"user_id": user_id_str, "email": email, "provider": sso_provider}
        )
        
        # Firebase UID와 DB UUID 매핑 저장
        if firebase_uid:
            self.session_manager.set_uid_mapping(f_uid=firebase_uid, db_uuid=user_id_str)

        return UserInfo(**new_user_data)

    def update_user_name(self, user_id: UUID, name: str) -> UserInfo:
        """사용자의 이름을 업데이트합니다."""
        query = load_sql("domains/auth", "update_user_name")
        self.cursor.execute(query, (name, user_id))
        user_data = self.cursor.fetchone()
        if not user_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
        return UserInfo(**user_data)

    def change_password(self, user_id: UUID, old_password: str, new_password: str):
        """사용자의 비밀번호를 변경합니다."""
        # 1. 기존 비밀번호 조회
        query_get_pwd = load_sql("domains/auth", "get_user_password")
        self.cursor.execute(query_get_pwd, (user_id,))
        row = self.cursor.fetchone()
        
        if not row or not row.get("password"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="일반 가입된 사용자가 아닙니다.")

        # 2. 기존 비밀번호 검증
        if not PasswordUtils.verify_password(old_password, row.get("password")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="기존 비밀번호가 일치하지 않습니다.")

        # 3. 새 비밀번호 해싱 후 업데이트
        hashed_new_pwd = PasswordUtils.hash_password(new_password)
        query_update_pwd = load_sql("domains/auth", "update_user_password")
        self.cursor.execute(query_update_pwd, (hashed_new_pwd, user_id))
