import time
import psycopg2
import random

DB_HOST = "localhost"
DB_NAME = "your_db_name"
DB_USER = "your_db_user"
DB_PASS = "your_db_password"

NODE_IDS = ["node1", "node2", "node3"]

def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# This script is not needed for MAPE-K loop. You can use FastAPI endpoints for data insertion.
def insert_data():
    conn = get_db_conn()
    cur = conn.cursor()
    for node_id in NODE_IDS:
        temperature = round(random.uniform(20, 40), 2)
        humidity = round(random.uniform(30, 70), 2)
        cur.execute(
            "INSERT INTO monitor (node_id, temperature, humidity) VALUES (%s, %s, %s)",
            (node_id, temperature, humidity)
        )
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    while True:
        insert_data()
        print("Inserted new data for all nodes.")
        time.sleep(60)  # Insert every minute
