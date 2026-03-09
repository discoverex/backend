from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.domains.score.dtos.score_dto import ScoreCreateRequest, ScoreResponse
from src.utils.load_sql import load_sql


class ScoreService:
    """
    게임별 사용자 점수를 기록하고 조회하는 서비스 클래스입니다.
    """

    def __init__(self, cursor):
        self.cursor = cursor

    def register_score(self, user_id: UUID, request: ScoreCreateRequest) -> ScoreResponse:
        """
        사용자의 게임 점수를 DB에 등록합니다.
        """
        query = load_sql("domains/score", "insert_score")
        self.cursor.execute(
            query,
            (user_id, request.game_id, request.game_type, request.score)
        )
        result = self.cursor.fetchone()
        return ScoreResponse(**result)

    def get_user_scores(
        self, 
        user_id: Optional[UUID] = None, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> List[ScoreResponse]:
        """
        조건에 맞는 사용자들의 점수 목록을 최고점 순으로 조회합니다.
        """
        query = load_sql("domains/score", "get_scores")
        # SQL 파라미터 매핑 (NULL 대응)
        params = (
            user_id, user_id,
            start_date, start_date,
            end_date, end_date
        )
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        
        return [ScoreResponse(**row) for row in results]
