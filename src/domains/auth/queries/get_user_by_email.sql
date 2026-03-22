SELECT 
    user_id, email, name, password, sso_provider, badges, level, exp, created_at, updated_at, last_logout_at
FROM users 
WHERE email = %s AND is_deleted = false;
