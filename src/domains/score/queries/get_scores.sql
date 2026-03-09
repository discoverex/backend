SELECT 
    user_id, game_id, game_type, last_score, updated_at
FROM user_scores
WHERE 1=1
    -- 사용자 필터
    AND (%s::uuid IS NULL OR user_id = %s::uuid)
    -- 게임 유형 필터
    AND (%s::varchar IS NULL OR game_type = %s::varchar)
    -- 시작 날짜 필터
    AND (%s::timestamp IS NULL OR updated_at >= %s::timestamp)
    -- 종료 날짜 필터
    AND (%s::timestamp IS NULL OR updated_at <= %s::timestamp)
ORDER BY last_score DESC, updated_at DESC;
