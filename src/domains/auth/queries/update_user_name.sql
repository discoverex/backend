UPDATE users
SET name = %s, updated_at = CURRENT_TIMESTAMP
WHERE user_id = %s
RETURNING user_id, email, name, sso_provider, badges, level, exp, created_at, updated_at;
