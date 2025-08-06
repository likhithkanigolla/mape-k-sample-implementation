# Digital Twin MAPE-K System

This project implements a Digital Twin system using the MAPE-K (Monitor, Analyze, Plan, Execute, Knowledge) architecture. It is built with FastAPI and supports IoT node data ingestion, threshold management, machine learning model training, and more.

## Features

- **Monitor:** Receives IoT node data (temperature, humidity, etc.)
- **Analyze:** Processes and analyzes incoming data
- **Plan:** Plans actions based on analysis
- **Execute:** Executes planned actions
- **Knowledge:** Stores thresholds, historical data, and ML models
- **Scheduler:** Retrains ML models daily

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- APScheduler
- Pydantic

Install dependencies:
```bash
pip install fastapi uvicorn apscheduler pydantic
```

## How to Run

1. **Navigate to the project directory:**
   ```bash
   cd /Users/likhithkanigolla/IIITH/code-files/Digital-Twin/mape-k
   ```

2. **Start the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Access the API documentation:**
   Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser for interactive Swagger docs.

## API Endpoints

- `POST /iot/data`  
  Submit IoT node data (temperature, humidity, etc.)

- `POST /iot/thresholds`  
  Set thresholds for a node

- `POST /iot/train_model/{node_id}`  
  Train the ML model for a specific node

- `GET /get_data/{node_id}`  
  Get all historical data for a node

- `GET /get_latest_data/{node_id}`  
  Get the latest data for a node

- `GET /get_all_node_ids`  
  List all node IDs

- `GET /get_thresholds/{node_id}`  
  Get thresholds for a node

## Logs

Logs are stored in `logs/mape_k_system.log`.

## Notes

- The system automatically retrains ML models for all nodes every day at midnight.
- Make sure all required submodules (`monitor`, `analyze`, `plan`, `execute`, `knowledge`, `ml_model`) are implemented in the `app` directory.

---

## How to Test / How to Use

You can interact with the API in two main ways:

### 1. Using Swagger UI (Recommended)
- After starting the server, open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser.
- You will see an interactive documentation page where you can try out all endpoints directly.

### 2. Using curl (Command Line)

**Submit IoT node data:**
```bash
curl -X POST "http://127.0.0.1:8000/iot/data" \
     -H "Content-Type: application/json" \
     -d '{"node_id": "node1", "temperature": 25.5, "humidity": 60.0}'
```

**Set thresholds for a node:**
```bash
curl -X POST "http://127.0.0.1:8000/iot/thresholds" \
     -H "Content-Type: application/json" \
     -d '{"node_id": "node1", "temperature_threshold": 30.0, "humidity_threshold": 70.0}'
```

**Train ML model for a node:**
```bash
curl -X POST "http://127.0.0.1:8000/iot/train_model/node1"
```

**Get all historical data for a node:**
```bash
curl "http://127.0.0.1:8000/get_data/node1"
```

**Get the latest data for a node:**
```bash
curl "http://127.0.0.1:8000/get_latest_data/node1"
```

**List all node IDs:**
```bash
curl "http://127.0.0.1:8000/get_all_node_ids"
```

**Get thresholds for a node:**
```bash
curl "http://127.0.0.1:8000/get_thresholds/node1"
```

---

## Scenario Example

See [SCENARIO.md](SCENARIO.md) for a real-world example and explanation of how the MAPE-K loop is applied in this project (e.g., smart building environment monitoring).

Feel free to contribute or raise issues!