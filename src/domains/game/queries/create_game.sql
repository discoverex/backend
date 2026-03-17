INSERT INTO game (game_id, user_id, game_type)
VALUES (%s, %s, %s)
RETURNING game_id, user_id, game_type, created_at;
