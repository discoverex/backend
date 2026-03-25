import bcrypt

class PasswordUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호를 해싱합니다 (bcrypt 직접 사용)."""
        # bcrypt는 bytes 타입을 입력받아야 합니다.
        password_bytes = password.encode('utf-8')
        # Salt 생성 및 해싱 (기본 cost는 12입니다)
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """평문 비밀번호와 해싱된 비밀번호를 비교합니다."""
        try:
            if not hashed_password:
                return False
            # 비교할 때도 두 인자 모두 bytes 타입이어야 합니다.
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            print(f"비밀번호 검증 중 오류 발생: {e}")
            return False

    @staticmethod
    def print_hashed_sample(password: str):
        """DB 수동 업데이트용 해시값 출력 메서드"""
        hashed = PasswordUtils.hash_password(password)
        print("\n" + "="*60)
        print(f"입력 비밀번호: {password}")
        print(f"DB에 넣을 해시값: {hashed}")
        print("="*60 + "\n")
        return hashed

# if __name__ == "__main__":
    # 1. DB에 넣을 해시값을 생성합니다.
    # 실행 명령어: uv run src/domains/auth/utils/password_utils.py
    # PasswordUtils.print_hashed_sample("test_password_1234")