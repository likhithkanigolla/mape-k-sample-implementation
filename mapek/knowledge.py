"""
Knowledge Base for MAPE-K Digital Twin System
Handles database connections and system knowledge storage
"""

import psycopg2
from contextlib import contextmanager
import os

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'mapek_dt'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASS', 'postgres'),
    'port': os.getenv('DB_PORT', '5432')
}

def get_db_conn():
    """Get a database connection."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

@contextmanager
def database_transaction():
    """Context manager for database transactions."""
    conn = get_db_conn()
    if conn is None:
        raise Exception("Could not establish database connection")
    
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# System knowledge and thresholds for real IoT sensors
SYSTEM_THRESHOLDS = {
    # Water Quality Sensor Thresholds
    'temperature': (15.0, 35.0),           # Celsius - normal water temperature range
    'tds_voltage': (0.5, 2.5),             # Volts - TDS sensor voltage
    'uncompensated_tds': (100, 500),       # ppm - Total Dissolved Solids
    'compensated_tds': (100, 500),         # ppm - Temperature compensated TDS
    
    # Water Flow Sensor Thresholds  
    'flowrate': (1.0, 15.0),               # L/min - Normal flow rate
    'total_flow': (100, 2000),             # L - Cumulative flow
    'pressure': (1.0, 5.0),                # Bar - Water pressure
    'pressure_voltage': (0.5, 2.5),        # Volts - Pressure sensor voltage
    
    # Water Level Sensor Thresholds
    'water_level': (1.0, 10.0),            # m - Water level height
    
    # Motor Sensor Thresholds
    'voltage': (220, 240),                 # V - Motor voltage
    'current': (1.0, 10.0),                # A - Motor current
    'power': (100, 2000),                  # W - Motor power
    'energy': (0, 150),                    # kWh - Energy consumption
    'frequency': (49, 51),                 # Hz - AC frequency
    'power_factor': (0.8, 1.0),            # Power factor
}

def get_threshold(parameter: str):
    """Get threshold for a parameter."""
    return SYSTEM_THRESHOLDS.get(parameter)

def initialize_database():
    """Initialize database with basic tables if they don't exist."""
    try:
        conn = get_db_conn()
        if conn is None:
            print("Cannot initialize database - no connection")
            return False
            
        cur = conn.cursor()
        
        # Create basic tables if they don't exist
        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS nodes (
                node_id VARCHAR(50) PRIMARY KEY,
                ip_address VARCHAR(15),
                node_type VARCHAR(20),
                location VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS thresholds (
                parameter VARCHAR(50) PRIMARY KEY,
                min_value FLOAT,
                max_value FLOAT,
                unit VARCHAR(20),
                description TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS water_flow (
                id SERIAL PRIMARY KEY,
                node_id VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                flowrate FLOAT,
                total_flow FLOAT,
                pressure FLOAT,
                pressure_voltage FLOAT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS water_level (
                id SERIAL PRIMARY KEY,
                node_id VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                water_level FLOAT,
                temperature FLOAT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS water_quality (
                id SERIAL PRIMARY KEY,
                node_id VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                temperature FLOAT,
                tds_voltage FLOAT,
                uncompensated_tds FLOAT,
                compensated_tds FLOAT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS motor (
                id SERIAL PRIMARY KEY,
                node_id VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(10),
                voltage FLOAT,
                current FLOAT,
                power FLOAT,
                energy FLOAT,
                frequency FLOAT,
                power_factor FLOAT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "analyze" (
                id SERIAL PRIMARY KEY,
                node_id VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result TEXT,
                state VARCHAR(20)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS plan (
                plan_id SERIAL PRIMARY KEY,
                plan_code VARCHAR(20) UNIQUE,
                node_id VARCHAR(50),
                command VARCHAR(100),
                parameters TEXT,
                priority INT,
                state VARCHAR(50),
                description TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS execute (
                id SERIAL PRIMARY KEY,
                node_id VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result TEXT
            )
            """
        ]
        
        for sql in tables_sql:
            cur.execute(sql)
        
        # Insert default thresholds
        for param, (min_val, max_val) in SYSTEM_THRESHOLDS.items():
            cur.execute(
                "INSERT INTO thresholds (parameter, min_value, max_value) VALUES (%s, %s, %s) ON CONFLICT (parameter) DO NOTHING",
                (param, min_val, max_val)
            )
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False
