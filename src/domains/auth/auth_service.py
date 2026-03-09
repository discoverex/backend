from src.domains.auth.dtos.auth_dtos import UserInfo
from src.utils.load_sql import load_sql


class AuthService:
    """
    사용자 인증 및 가입을 담당하는 서비스 클래스입니다.
    """

    def __init__(self, cursor):
        self.cursor = cursor

    def handle_login_or_register(self, email: str, name: str, sso_provider: str = "firebase") -> UserInfo:
        """
        이메일로 사용자를 조회하고, 없으면 새로 가입 시킨 후 사용자 정보를 반환합니다.
        """
        # 1. 사용자 조회
        query_get = load_sql("domains/auth", "get_user_by_email")
        self.cursor.execute(query_get, (email,))
        user_data = self.cursor.fetchone()

        if user_data:
            # 기존 사용자 정보 반환
            return UserInfo(**user_data)

        # 2. 신규 사용자 가입 (자동 가입)
        query_create = load_sql("domains/auth", "create_user")
        self.cursor.execute(query_create, (email, name, sso_provider))
        new_user_data = self.cursor.fetchone()

        return UserInfo(**new_user_data)
