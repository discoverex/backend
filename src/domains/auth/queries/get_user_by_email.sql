SELECT 
    user_id, email, name, sso_provider, badges, level, exp, created_at, updated_at
FROM users 
WHERE email = %s AND is_deleted = false;
