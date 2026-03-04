import time

import firebase_admin
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import credentials, auth

from src.configs.setting import FIREBASE_SERVICE_ACCOUNT_PATH

# 서비스 계정 키 로드 (JSON 파일 경로) → 파이어베이스 콘솔에서 제공 / .gitignore 항목 추가
cred = credentials.Certificate(str(FIREBASE_SERVICE_ACCOUNT_PATH))
firebase_admin.initialize_app(cred)

security = HTTPBearer()


async def verify_firebase_token(res: HTTPAuthorizationCredentials = Depends(security)):
    """
    프론트엔드에서 보낸 Bearer 토큰을 검증하는 함수
    """
    token = res.credentials

    # 최대 2번 시도 (시간 오차 대비)
    for i in range(2):
        try:
            # check_revoked=True를 추가하면 보안성이 더 높아집니다.
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            # "Token used too early" 문구가 에러 메시지에 포함되어 있다면
            if "Token used too early" in str(e) and i == 0:
                time.sleep(1)  # 1초 대기 후 재시도
                continue

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"인증 실패: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    return None