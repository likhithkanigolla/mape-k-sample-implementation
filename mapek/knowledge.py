import psycopg2

DB_HOST = "localhost"
DB_NAME = "mapek_dt"
DB_USER = "postgres"
DB_PASS = "postgres"

def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=5432,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
from app.logger import get_logger
import joblib

logger = get_logger()

def update_knowledge(data):
    from app.main import get_db_conn
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO monitor (node_id, temperature, humidity) VALUES (%s, %s, %s)",
        (data.node_id, data.temperature, data.humidity)
    )
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Data inserted into knowledge base: {data}")


def update_anomaly_label(node_id, data_id, anomaly_label):
    from app.main import get_db_conn
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE monitor SET anomaly_label = %s WHERE id = %s AND node_id = %s",
        (anomaly_label, data_id, node_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Anomaly label updated for node {node_id} with id {data_id}: {anomaly_label}")


def get_historical_data(node_id):
    conn = get_db_conn()
    cur = conn.cursor()
    # Determine table based on node_id prefix
    if node_id.startswith("water_quality"):
        cur.execute(
            "SELECT id, temperature, tds_voltage, uncompensated_tds, compensated_tds, timestamp FROM water_quality WHERE node_id = %s ORDER BY timestamp DESC LIMIT 100",
            (node_id,)
        )
    elif node_id.startswith("water_flow"):
        cur.execute(
            "SELECT id, flowrate, total_flow, pressure, pressure_voltage, timestamp FROM water_flow WHERE node_id = %s ORDER BY timestamp DESC LIMIT 100",
            (node_id,)
        )
    elif node_id.startswith("water_level"):
        cur.execute(
            "SELECT id, water_level, temperature, timestamp FROM water_level WHERE node_id = %s ORDER BY timestamp DESC LIMIT 100",
            (node_id,)
        )
    elif node_id.startswith("motor"):
        cur.execute(
            "SELECT id, status, voltage, current, power, energy, frequency, power_factor, timestamp FROM motor WHERE node_id = %s ORDER BY timestamp DESC LIMIT 100",
            (node_id,)
        )
    else:
        data = []
        cur.close()
        conn.close()
        return data
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def get_thresholds(node_id):
    from app.main import get_db_conn
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT temperature_threshold, humidity_threshold FROM thresholds WHERE node_id = %s",
        (node_id,)
    )
    thresholds = cur.fetchone()
    cur.close()
    conn.close()
    if thresholds:
        return {"temperature_threshold": thresholds[0], "humidity_threshold": thresholds[1]}
    return None


def get_node_ids():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT node_id FROM nodes")
    node_ids = cur.fetchall()
    cur.close()
    conn.close()
    return node_ids


def set_thresholds(node_id, temperature_threshold, humidity_threshold):
    from app.main import get_db_conn
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO thresholds (node_id, temperature_threshold, humidity_threshold) VALUES (%s, %s, %s) ON CONFLICT (node_id) DO UPDATE SET temperature_threshold = EXCLUDED.temperature_threshold, humidity_threshold = EXCLUDED.humidity_threshold",
        (node_id, temperature_threshold, humidity_threshold)
    )
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Thresholds set for node {node_id}: Temperature - {temperature_threshold}, Humidity - {humidity_threshold}")


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
    from app.main import get_db_conn
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT node_id FROM monitor")
    node_ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return node_ids


def update_knowledge(event, node_id):
    from app.main import get_db_conn
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO knowledge (event, node_id) VALUES (%s, %s)", (event, node_id))
    conn.commit()
    cur.close()
    conn.close()
