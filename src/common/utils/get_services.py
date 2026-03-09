from fastapi.params import Depends

from src.configs.database import get_db_cursor
from src.domains.auth.auth_service import AuthService


def get_auth_service(cursor=Depends(get_db_cursor)):
    return AuthService(cursor)
