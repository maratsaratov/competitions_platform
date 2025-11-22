import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-2025'
    DB_CONFIG = {
    'host': 'localhost',
    'database': 'competitions_db',
    'user': 'postgres',
    'password': 'tennissuper369',
    'port': '7431'
}