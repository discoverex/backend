from typing import Optional, Any
import json
from src.configs.redis_conn import get_redis_client
from src.utils.logger import logger

class SessionManager:
    """
    Redis를 이용한 세션 관리 유틸리티 클래스입니다.
    """
    
    def __init__(self):
        self.redis = get_redis_client()
        self.token_prefix = "session:"      # 토큰별 세션 (기존)
        self.user_prefix = "user_session:"  # 사용자별 통합 세션 (신규)
        self.mapping_prefix = "fuid_mapping:" # Firebase UID -> DB UUID 매핑

    def set_uid_mapping(self, f_uid: str, db_uuid: str, expire_seconds: int = 86400) -> bool:
        """
        Firebase UID와 DB UUID 간의 매핑 정보를 저장합니다.
        """
        try:
            key = f"{self.mapping_prefix}{f_uid}"
            return self.redis.setex(key, expire_seconds, db_uuid)
        except Exception as e:
            logger.error(f"UID 매핑 저장 실패: {e}")
            return False

    def get_uuid_from_fuid(self, f_uid: str) -> Optional[str]:
        """
        Firebase UID에 대응하는 DB UUID를 가져옵니다.
        """
        try:
            key = f"{self.mapping_prefix}{f_uid}"
            return self.redis.get(key)
        except Exception as e:
            logger.error(f"UID 매핑 조회 실패: {e}")
            return None

    def set_user_session(self, user_id: str, session_data: dict, expire_seconds: int = 86400) -> bool:
        """
        사용자 ID를 키로 하여 세션 정보를 저장/갱신합니다. (여러 앱 간 공유 세션)
        """
        try:
            key = f"{self.user_prefix}{user_id}"
            self.redis.setex(
                key,
                expire_seconds,
                json.dumps(session_data)
            )
            return True
        except Exception as e:
            logger.error(f"Redis 사용자 세션 저장 실패: {e}")
            return False

    def is_user_session_active(self, user_id: str) -> bool:
        """
        사용자 ID 기반 세션이 활성화되어 있는지 확인합니다.
        """
        key = f"{self.user_prefix}{user_id}"
        return self.redis.exists(key) > 0

    def delete_user_session(self, user_id: str) -> bool:
        """
        사용자 ID 기반 세션을 삭제합니다. (전체 로그아웃)
        """
        try:
            key = f"{self.user_prefix}{user_id}"
            return self.redis.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis 사용자 세션 삭제 실패: {e}")
            return False

    def set_session(self, token: str, user_data: dict, expire_seconds: int) -> bool:
        """
        토큰을 키로 하여 사용자 세션 정보를 Redis에 저장합니다.
        """
        try:
            key = f"{self.prefix}{token}"
            self.redis.setex(
                key,
                expire_seconds,
                json.dumps(user_data)
            )
            return True
        except Exception as e:
            logger.error(f"Redis 세션 저장 실패: {e}")
            return False

    def get_session(self, token: str) -> Optional[dict]:
        """
        Redis에서 토큰에 해당하는 세션 정보를 가져옵니다.
        """
        try:
            key = f"{self.prefix}{token}"
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis 세션 조회 실패: {e}")
            return None

    def delete_session(self, token: str) -> bool:
        """
        Redis에서 해당 토큰의 세션을 삭제합니다. (로그아웃)
        """
        try:
            key = f"{self.prefix}{token}"
            return self.redis.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis 세션 삭제 실패: {e}")
            return False

    def is_active(self, token: str) -> bool:
        """
        해당 토큰의 세션이 Redis에 활성화되어 있는지 확인합니다.
        """
        key = f"{self.prefix}{token}"
        return self.redis.exists(key) > 0
