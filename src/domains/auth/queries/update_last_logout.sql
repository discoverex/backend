UPDATE users
SET last_logout_at = CURRENT_TIMESTAMP
WHERE user_id = %s;
