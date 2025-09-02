import psycopg2
from psycopg2.extras import RealDictCursor
import os

class DatabaseConfig:
    # Факултетска база податоци
    DB_HOST = 'localhost'
    DB_PORT = 9999
    DB_NAME = 'db_202425z_va_prj_simlab25'
    DB_USER = 'db_202425z_va_prj_simlab25_owner'
    DB_PASSWORD = 'c9e5ebb7d332'
    
    @staticmethod
    def get_connection():
        """Врати конекција до базата"""
        try:
            conn = psycopg2.connect(
                host=DatabaseConfig.DB_HOST,
                port=DatabaseConfig.DB_PORT,
                database=DatabaseConfig.DB_NAME,
                user=DatabaseConfig.DB_USER,
                password=DatabaseConfig.DB_PASSWORD,
                cursor_factory=RealDictCursor  # За dictionary резултати
            )
            return conn
        except psycopg2.Error as e:
            print(f"Грешка при поврзување: {e}")
            return None