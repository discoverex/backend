INSERT INTO users (email, name, password, sso_provider)
VALUES (%s, %s, %s, 'none')
RETURNING user_id, email, name, sso_provider, badges, level, exp, created_at, updated_at;
