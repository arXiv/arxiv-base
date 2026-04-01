-- Create test policy class (required by tapir_users foreign key)
INSERT INTO tapir_policy_classes (class_id, name, description, password_storage, recovery_policy, permanent_login)
VALUES (1, 'test_policy', 'Test policy class', 0, 0, 0);

-- Create test user
INSERT INTO tapir_users (
    user_id,
    first_name,
    last_name,
    suffix_name,
    email,
    policy_class,
    joined_date,
    flag_approved,
    flag_email_verified
)
VALUES (
    1,
    'Test',
    'User',
    '',
    'test_user@example.com',
    1,
    UNIX_TIMESTAMP(),
    1,
    1
);
