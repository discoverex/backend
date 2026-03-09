UPDATE users
SET sso_provider = %s, updated_at = CURRENT_TIMESTAMP
WHERE email = %s
RETURNING user_id, email, name, sso_provider, badges, level, exp, created_at, updated_at;
