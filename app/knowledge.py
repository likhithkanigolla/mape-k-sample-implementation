import sqlite3
from app.logger import get_logger

logger = get_logger()

# Initialize the database
conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()

# Create tables
c.execute('''
CREATE TABLE IF NOT EXISTS iot_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS thresholds (
    node_id TEXT PRIMARY KEY,
    temperature_threshold REAL NOT NULL,
    humidity_threshold REAL NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS ml_models (
    node_id TEXT PRIMARY KEY,
    model BLOB NOT NULL
)
''')

conn.commit()

def update_knowledge(data):
    with conn:
        c.execute('''
        INSERT INTO iot_data (node_id, temperature, humidity) 
        VALUES (?, ?, ?)
        ''', (data.node_id, data.temperature, data.humidity))
    logger.info(f"Data inserted into knowledge base: {data}")

def get_historical_data(node_id):
    c.execute('''
    SELECT temperature, humidity, timestamp FROM iot_data
    WHERE node_id = ?
    ORDER BY timestamp DESC
    LIMIT 100
    ''', (node_id,))
    return c.fetchall()

def set_thresholds(node_id, temperature_threshold, humidity_threshold):
    with conn:
        c.execute('''
        INSERT OR REPLACE INTO thresholds (node_id, temperature_threshold, humidity_threshold)
        VALUES (?, ?, ?)
        ''', (node_id, temperature_threshold, humidity_threshold))
    logger.info(f"Thresholds set for node {node_id}: Temperature - {temperature_threshold}, Humidity - {humidity_threshold}")

def get_thresholds(node_id):
    c.execute('''
    SELECT temperature_threshold, humidity_threshold FROM thresholds
    WHERE node_id = ?
    ''', (node_id,))
    return c.fetchone()

def store_ml_model(node_id, model):
    with conn:
        c.execute('''
        INSERT OR REPLACE INTO ml_models (node_id, model)
        VALUES (?, ?)
        ''', (node_id, model))
    logger.info(f"ML model stored for node {node_id}")

def get_ml_model(node_id):
    c.execute('''
    SELECT model FROM ml_models
    WHERE node_id = ?
    ''', (node_id,))
    return c.fetchone()
