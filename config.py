
# ============================================================
# config.py - Hashira v2 Configuration
# ============================================================

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'put-your-db-password-here',   # ← your MySQL password
    'database': 'hashira_db',
    'autocommit': True
}

GEMINI_API_KEY = "XYZZZZZZZZZZ"   # ← your key
APP_SECRET_KEY = "hashira_v2_ultra_secret_2024"
DEBUG_MODE     = True


def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
    return None