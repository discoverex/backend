UPDATE users
SET password = %s, updated_at = CURRENT_TIMESTAMP
WHERE user_id = %s;
