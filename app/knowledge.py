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

def get_all_data():
    c.execute('''
    SELECT * FROM iot_data
    ''')
    return c.fetchall()
