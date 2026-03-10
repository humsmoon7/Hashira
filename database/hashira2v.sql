-- =============================================
-- HASHIRA v2 — COMPLETE DATABASE SCHEMA
-- Run with: mysql -u root -p < database/hashira.sql
-- =============================================

CREATE DATABASE IF NOT EXISTS hashira_db;
USE hashira_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(512) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    avatar VARCHAR(10) DEFAULT ' ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- 2. Chat Sessions Table (Fixed column names)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_uid VARCHAR(100) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    title VARCHAR(200) DEFAULT 'New Chat',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Chat History Table (Fixed column names)
CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_uid VARCHAR(100) NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    message LONGTEXT NOT NULL,
    mode ENUM('normal', 'exam') DEFAULT 'normal',
    has_image BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_uid) REFERENCES chat_sessions(session_uid) ON DELETE CASCADE
);

-- 4. Saved Messages Table
CREATE TABLE IF NOT EXISTS saved_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message LONGTEXT NOT NULL,
    note VARCHAR(300) DEFAULT '',
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Default Admin Account (password: admin123)
INSERT IGNORE INTO users (username, email, password_hash, role, avatar)
VALUES ('admin', 'admin@hashira.ai', 
'scrypt:32768:8:1$7wPONoXX3t2qRnFr$0bb629e618fda2b49faf1a8c0c6881a664a0fbcef28cd12bd4d3684f794478d906924104263b0561221211d1cb89437e5a2ff0298346c549be9c243acdbcadca', 
'admin', '👑');

-- Optional: Add indexes for better performance
CREATE INDEX idx_chat_history_session ON chat_history(session_uid);
CREATE INDEX idx_chat_history_created ON chat_history(created_at);
