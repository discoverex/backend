import urllib3
from minio import Minio

from configs.setting import MINIO_EXTERNAL_URL, CF_ACCESS_CLIENT_ID, CF_ACCESS_CLIENT_SECRET, MINIO_ACCESS_KEY, \
    MINIO_SECRET_KEY, APP_ENV
from src.utils.logger import info, error


class CloudflareHttpClient(urllib3.PoolManager):
    """
    Cloudflare Access(Zero Trust)를 통과하기 위한 커스텀 HTTP 클라이언트입니다.
    """
    def __init__(self, client_id, client_secret, *args, **kwargs):
        self.client_id = client_id
        self.client_secret = client_secret
        
        # 기본 헤더 설정 (만약의 경우를 대비)
        headers = kwargs.get("headers", {})
        headers.update({
            "CF-Access-Client-Id": client_id,
            "CF-Access-Client-Secret": client_secret,
        })
        kwargs["headers"] = headers

        super().__init__(*args, **kwargs)

    def urlopen(self, method, url, redirect=True, **kw):
        # 1. 요청 헤더 가져오기 (없으면 생성)
        headers = kw.get('headers', {})
        
        # 2. Cloudflare Access 헤더 강제 주입
        if self.client_id and self.client_secret:
            headers["CF-Access-Client-Id"] = self.client_id
            headers["CF-Access-Client-Secret"] = self.client_secret
        
        kw['headers'] = headers

        # 3. 로깅 (민감 정보 보호를 위해 ID/Secret은 일부만 출력하거나 생략 권장)
        if APP_ENV == 'local':
            info(f"[MinIO-Debug] Method: {method} | URL: {url}")
            info(f"[MinIO-Debug] CF-ID: {headers.get('CF-Access-Client-Id')[:5] if headers.get('CF-Access-Client-Id') else 'None'}...")

        # 4. 실제 요청 수행
        return super().urlopen(method, url, redirect=redirect, **kw)

class MinioClientHolder:
    """
    초기화된 MinIO 클라이언트를 전역적으로 관리하는 홀더 클래스입니다.
    """
    def __init__(self):
        self.client: Minio = None

# 전역 홀더 인스턴스
minio_client_holder = MinioClientHolder()

def initialize_minio():
    """
    FastAPI startup 시 호출되어 MinIO 클라이언트를 단 한 번 초기화합니다.
    """
    if minio_client_holder.client is not None:
        info("MinIO 클라이언트가 이미 초기화되어 있습니다.")
        return

    info("MinIO 클라이언트를 초기화 중 (Cloudflare Access 적용)...")
    try:
        # 1. 엔드포인트에서 프로토콜 제거
        # URL에서 프로토콜(http://, https://)만 제거하고 포트는 유지해야 할 수도 있음
        endpoint = MINIO_EXTERNAL_URL.replace("https://", "").replace("http://", "")
        
        # 포트가 명시되어 있지 않고 secure=True인 경우 기본 443 사용
        # 만약 포트를 split(":")으로 날려버리면 커스텀 포트 사용 시 문제 발생 가능
        # endpoint = endpoint.split(":")[0]  # 기존 코드: 포트 제거 -> 잠재적 문제

        # 2. Cloudflare 인증 정보가 포함된 커스텀 HTTP 클라이언트 생성
        custom_http_client = CloudflareHttpClient(
            CF_ACCESS_CLIENT_ID,
            CF_ACCESS_CLIENT_SECRET
        )

        # 3. 클라이언트 생성 및 홀더에 저장
        minio_client_holder.client = Minio(
            endpoint,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=True,  # Cloudflare 통과 시 HTTPS 필수
            http_client=custom_http_client
        )
        info(f"MinIO 클라이언트가 성공적으로 초기화되었습니다. (Endpoint: {endpoint})")
    except Exception as e:
        error(f"MinIO 초기화 실패: {str(e)}")
        raise RuntimeError(f"MinIO 초기화 실패: {str(e)}")

def get_minio_client() -> Minio:
    """
    초기화된 MinIO 클라이언트를 반환합니다.
    """
    if minio_client_holder.client is None:
        # 안전장치: 혹시 초기화되지 않았다면 시도해봅니다.
        initialize_minio()
    return minio_client_holder.client
