INSERT INTO user_scores (user_id, game_id, game_type, last_score)
VALUES (%s, %s, %s, %s)
RETURNING user_id, game_id, game_type, last_score, updated_at;
