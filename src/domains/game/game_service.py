from typing import Optional
from uuid import UUID

from src.domains.game.dtos.game_dto import GameResponse
from src.utils.load_sql import load_sql


class GameService:
    """
    게임 정보를 조회하고 관리하는 서비스 클래스입니다.
    """

    def __init__(self, cursor):
        self.cursor = cursor

    def get_game_by_id(self, game_id: UUID) -> Optional[GameResponse]:
        """
        주어진 game_id에 해당하는 게임 정보를 조회합니다.
        """
        query = load_sql("domains/game", "get_game_by_id")
        self.cursor.execute(query, (game_id,))
        result = self.cursor.fetchone()
        if result:
            return GameResponse(**result)
        return None

    def create_game(self, game_id: UUID, game_type: str, user_id: UUID) -> GameResponse:
        """
        새로운 게임을 생성합니다.
        """
        query = load_sql("domains/game", "create_game")
        self.cursor.execute(query, (game_id, user_id, game_type))
        result = self.cursor.fetchone()
        return GameResponse(**result)

    def get_or_create_game(self, game_id: UUID, game_type: str, user_id: UUID) -> GameResponse:
        """
        게임이 존재하면 조회하고, 없으면 새로 생성합니다.
        """
        game = self.get_game_by_id(game_id)
        if game:
            return game

        return self.create_game(game_id=game_id, game_type=game_type, user_id=user_id)
