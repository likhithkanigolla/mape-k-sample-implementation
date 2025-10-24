"""
Database connection utilities for plain MAPE-K system
"""
import psycopg2
from logger import logger

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'mapek_dt',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432
}

def get_db_conn():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def get_node_ids():
    """Get all unique node IDs from the database"""
    node_ids = []
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        # Get node IDs from all sensor tables
        cur.execute("""
            SELECT DISTINCT node_id FROM water_quality
            UNION
            SELECT DISTINCT node_id FROM water_flow
            UNION
            SELECT DISTINCT node_id FROM water_level
            UNION
            SELECT DISTINCT node_id FROM motor
        """)
        
        node_ids = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error getting node IDs: {e}")
    
    return node_ids
