-- Auth Service: Initial Schema Migration
-- All 7 tables for the authentication system.
-- Run against MySQL 8.0+ with InnoDB and utf8mb4.

-- ============================================================
-- 1. users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id            CHAR(36) NOT NULL,
    email         VARCHAR(255) NOT NULL,
    password_hash VARCHAR(512) NOT NULL,
    role          ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    is_active     TINYINT(1) NOT NULL DEFAULT 1,
    is_verified   TINYINT(1) NOT NULL DEFAULT 0,
    display_name  VARCHAR(255) NULL,
    phone         VARCHAR(32) NULL,
    metadata      JSON NULL,
    created_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 2. refresh_tokens
-- ============================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          CHAR(36) NOT NULL,
    user_id     CHAR(36) NOT NULL,
    token_hash  CHAR(64) NOT NULL,
    expires_at  DATETIME(6) NOT NULL,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    revoked_at  DATETIME(6) NULL,
    user_agent  VARCHAR(512) NULL,
    ip_address  VARCHAR(45) NULL,
    PRIMARY KEY (id),
    INDEX idx_refresh_token_hash (token_hash),
    INDEX idx_refresh_user (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 3. api_keys
-- ============================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id              CHAR(36) NOT NULL,
    name            VARCHAR(255) NOT NULL,
    key_prefix      VARCHAR(16) NOT NULL,
    key_hash        CHAR(64) NOT NULL,
    created_by      CHAR(36) NOT NULL,
    expires_at      DATETIME(6) NULL,
    revoked_at      DATETIME(6) NULL,
    last_used_at    DATETIME(6) NULL,
    usage_count     BIGINT NOT NULL DEFAULT 0,
    rate_limit      INT NULL,
    created_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_api_key_hash (key_hash),
    INDEX idx_api_key_prefix (key_prefix),
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 4. rate_limits
-- ============================================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id            BIGINT NOT NULL AUTO_INCREMENT,
    key_type      VARCHAR(32) NOT NULL,
    key_value     VARCHAR(255) NOT NULL,
    attempts      INT NOT NULL DEFAULT 1,
    window_start  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    blocked_until DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE INDEX idx_rate_key (key_type, key_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 5. email_verification_tokens
-- ============================================================
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id          CHAR(36) NOT NULL,
    user_id     CHAR(36) NOT NULL,
    token_hash  CHAR(64) NOT NULL,
    expires_at  DATETIME(6) NOT NULL,
    used_at     DATETIME(6) NULL,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_verify_token_hash (token_hash),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 6. password_reset_tokens
-- ============================================================
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          CHAR(36) NOT NULL,
    user_id     CHAR(36) NOT NULL,
    token_hash  CHAR(64) NOT NULL,
    expires_at  DATETIME(6) NOT NULL,
    used_at     DATETIME(6) NULL,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_reset_token_hash (token_hash),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 7. audit_log
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGINT NOT NULL AUTO_INCREMENT,
    user_id     CHAR(36) NULL,
    event       VARCHAR(64) NOT NULL,
    ip_address  VARCHAR(45) NULL,
    user_agent  VARCHAR(512) NULL,
    details     JSON NULL,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_event (event),
    INDEX idx_audit_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
