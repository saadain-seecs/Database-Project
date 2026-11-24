-- =====================================================================
--  Optional file 7 : admin accounts for the PharmaCare desktop GUI
--  Adds ONE new table; no existing table is changed.
--  Run once as root (the GUI can also create it itself when it is started with a user that may CREATE tables).
--  The first time the GUI starts it asks you to create the admin account;
--  passwords are stored as salted PBKDF2-SHA256 hashes, never as plain text.
-- =====================================================================
USE pharmacy_db;

CREATE TABLE IF NOT EXISTS app_users (
    user_id        INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    username       VARCHAR(50)   NOT NULL,
    password_hash  VARCHAR(255)  NOT NULL,
    full_name      VARCHAR(100)  NULL,
    is_active      BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login     DATETIME      NULL,
    CONSTRAINT pk_app_users      PRIMARY KEY (user_id),
    CONSTRAINT uq_app_username   UNIQUE (username)
) ENGINE = InnoDB;
