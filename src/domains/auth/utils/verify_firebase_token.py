import os
import json
import time
import firebase_admin
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import credentials, auth

from src.configs.setting import FIREBASE_SERVICE_ACCOUNT_JSON

# 1. 환경변수에서 JSON 문자열 로드
firebase_json = FIREBASE_SERVICE_ACCOUNT_JSON

if not firebase_json:
    # 환경변수가 없을 경우 서버 구동 단계에서 에러를 발생시켜 잘못된 설정을 방지합니다.
    raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON 환경변수가 설정되지 않았습니다.")

try:
    # 2. JSON 문자열을 파이썬 딕셔너리로 변환
    cred_dict = json.loads(firebase_json)
    # 3. 딕셔너리 객체를 사용하여 Firebase 인증 객체 생성
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
except Exception as e:
    raise RuntimeError(f"Firebase 초기화 실패: {str(e)}")

security = HTTPBearer()


async def verify_firebase_token(res: HTTPAuthorizationCredentials = Depends(security)):
    """
    프론트엔드에서 보낸 Bearer 토큰을 검증하는 함수
    """
    token = res.credentials

    # 최대 2번 시도 (시간 오차 대비)
    for i in range(2):
        try:
            # ID 토큰 검증
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            # "Token used too early" 문구가 에러 메시지에 포함되어 있다면 (서버 간 시간 차이 대응)
            if "Token used too early" in str(e) and i == 0:
                time.sleep(1)  # 1초 대기 후 재시도
                continue

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"인증 실패: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return None