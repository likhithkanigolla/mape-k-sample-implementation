import sqlite3
from app.logger import get_logger
import joblib

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
    anomaly_label INTEGER DEFAULT 0,
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
    
def update_anomaly_label(node_id, data_id, anomaly_label):
    with conn:
        c.execute('''
        UPDATE iot_data
        SET anomaly_label = ?
        WHERE id = ?
        AND node_id = ?
        ''', (anomaly_label, data_id, node_id))
    logger.info(f"Anomaly label updated for node {node_id} with id {data_id}: {anomaly_label}")


def get_historical_data(node_id):
    c.execute('''
    SELECT id,temperature, humidity, timestamp, anomaly_label FROM iot_data
    WHERE node_id = ?
    ORDER BY timestamp DESC
    LIMIT 100
    ''', (node_id,))
    return c.fetchall()

def get_thresholds(node_id):
    c.execute('''
    SELECT temperature_threshold, humidity_threshold FROM thresholds
    WHERE node_id = ?
    ''', (node_id,))
    return c.fetchone()

def get_node_ids():
    c.execute('''
    SELECT DISTINCT node_id FROM iot_data
    ''')
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

# def store_ml_model(node_id, model):
#     c.execute('''
#     INSERT OR REPLACE INTO ml_models (node_id, model)
#     VALUES (?, ?)
#     ''', (node_id, model))
#     conn.commit()
    
# def get_ml_model(node_id):
#     c.execute('''
#     SELECT model FROM ml_models
#     WHERE node_id = ?
#     ''', (node_id,))
#     model_blob = c.fetchone()

#     if model_blob:
#         try:
#             # Deserialize the model from the stored bytes object using joblib.load
#             model = joblib.load(model_blob[0])
#             return model
#         except Exception as e:
#             logger.error(f"Error loading model for node {node_id}: {e}")
#             return None
#     else:
#         logger.warning(f"No model found for node_id: {node_id}")
#         return None

def store_ml_model(node_id, model):
    model_filename = f"ml-models/{node_id}_model.pkl"
    joblib.dump(model, model_filename)
    
def get_ml_model(node_id):
    model_filename = f"ml-models/{node_id}_model.pkl"
    try:
        model = joblib.load(model_filename)
        return model
    except FileNotFoundError:
        logger.warning(f"No model found for node_id: {node_id}")
        return None
    except Exception as e:
        logger.error(f"Error loading model for node {node_id}: {e}")
        return None

def get_all_node_ids():
    conn = sqlite3.connect('knowledge.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT node_id FROM historical_data")
    node_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return node_ids
