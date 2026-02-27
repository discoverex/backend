import firebase_admin
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import credentials, auth

from src.configs.setting import FIREBASE_SERVICE_ACCOUNT_PATH

# 서비스 계정 키 로드 (JSON 파일 경로) → 파이어베이스 콘솔에서 제공 / .gitignore 항목 추가
print(FIREBASE_SERVICE_ACCOUNT_PATH)
cred = credentials.Certificate(str(FIREBASE_SERVICE_ACCOUNT_PATH))
firebase_admin.initialize_app(cred)

security = HTTPBearer()


async def verify_firebase_token(res: HTTPAuthorizationCredentials = Depends(security)):
    """
    프론트엔드에서 보낸 Bearer 토큰을 검증하는 함수
    """
    token = res.credentials
    try:
        # Firebase 서버와 통신하여 토큰의 유효성(만료 여부, 변조 여부) 확인
        decoded_token = auth.verify_id_token(token)
        # 검증 성공 시 유저 정보(uid, email 등) 반환
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"인증 실패: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )