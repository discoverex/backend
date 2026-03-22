import psycopg2
from psycopg2.extras import RealDictCursor, register_uuid

from src.configs import setting
from src.utils.logger import info, error

# UUID
register_uuid()


def get_db_connection():
    """
    PostgreSQL 데이터베이스 연결을 생성합니다.
    """
    try:
        conn = psycopg2.connect(
            user=setting.DB_USER,
            password=setting.DB_PASSWORD,
            host=setting.DB_HOST,
            port=setting.DB_PORT,
            database=setting.DB_NAME
        )
        return conn
    except Exception as e:
        error(f"데이터베이스 연결 실패: {str(e)}")
        raise e

def check_db_connection():
    """
    DB 서버의 생존 여부를 확인합니다. (Health Check용)
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 가장 가벼운 쿼리로 실제 응답 확인
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                info(f"✅ DB와 성공적으로 연결되었습니다.")
                return True
    except Exception as e:
        error(f"DB Health Check 실패: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()
    return False

def get_db_cursor():
    """
    FastAPI Depends에서 사용할 수 있는 DB 커서 생성기입니다.
    """
    conn = get_db_connection()
    # RealDictCursor를 사용하면 컬럼명을 키로 하는 딕셔너리로 결과를 받을 수 있습니다.
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        error(f"DB 작업 중 오류 발생: {str(e)}")
        raise e
    finally:
        cursor.close()
        conn.close()
