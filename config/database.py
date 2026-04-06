import os
import pymysql
import pathlib
from dotenv import load_dotenv

# 현재 모듈(database.py) 위치를 기준으로 최상위 프로젝트 경로 탐색
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
env_path = ROOT_DIR / ".env"

# .env 파일 로드
load_dotenv(dotenv_path=env_path)

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'job_data_platform'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_connection():
    """DB 연결 객체를 반환합니다."""
    return pymysql.connect(**DB_CONFIG)
