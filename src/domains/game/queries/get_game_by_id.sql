SELECT
    game_id,
    game_type
FROM
    game
WHERE
    game_id = %s;
