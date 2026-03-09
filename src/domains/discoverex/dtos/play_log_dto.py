from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class ClickCoordinate(BaseModel):
    x: int
    y: int

class TargetDistance(BaseModel):
    target_id: str
    distance: float

class NearestTarget(BaseModel):
    target_id: str
    distance: float
    is_duplicated_hit: bool

class GameState(BaseModel):
    remaining_targets_count: int
    current_score: int

class PlayLogEntry(BaseModel):
    event_id: str
    timestamp: datetime
    play_time_ms: int
    click_coordinate: ClickCoordinate
    result_type: str
    distances_to_remaining_targets: List[TargetDistance]
    nearest_found_target: Optional[NearestTarget] = None
    game_state: GameState

class PlayLogCreateRequest(BaseModel):
    user_id: UUID
    game_id: UUID
    play_logs: List[PlayLogEntry]
