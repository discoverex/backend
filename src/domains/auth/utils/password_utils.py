from passlib.context import CryptContext

# bcrypt 알고리즘을 사용한 암호화 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호를 해싱합니다."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """평문 비밀번호와 해싱된 비밀번호를 비교합니다."""
        return pwd_context.verify(plain_password, hashed_password)
