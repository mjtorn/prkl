ALTER TABLE auth_user DROP CONSTRAINT auth_user_username_key;
-- DROP INDEX auth_user_username_key;
CREATE UNIQUE INDEX auth_user_username_key ON auth_user(lower(username));

