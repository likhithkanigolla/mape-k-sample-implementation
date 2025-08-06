# Example Scenario: Digital Twin MAPE-K System

## Scenario: Smart Building Environment Monitoring

Imagine a smart building equipped with multiple IoT sensor nodes. Each node measures temperature and humidity in different rooms. The goal is to maintain optimal environmental conditions and detect anomalies automatically.

---

## Step-by-Step Usage Guide

### Step 1: Set Thresholds for a Node
- **Endpoint:** `POST /iot/thresholds`
- **Payload Example:**
  ```json
  {
    "node_id": "node1",
    "temperature_threshold": 30.0,
    "humidity_threshold": 70.0
  }
  ```
- **What happens:**
  - The system stores the thresholds for node1 in the knowledge base. These will be used for anomaly detection.

### Step 2: Send IoT Data
- **Endpoint:** `POST /iot/data`
- **Payload Example:**
  ```json
  {
    "node_id": "node1",
    "temperature": 28.5,
    "humidity": 65.0
  }
  ```
- **What happens:**
  - The system stores the data (Monitor).
  - It analyzes the data using thresholds and (if available) the ML model (Analyze).
  - If an anomaly is detected, it plans an action (Plan) and executes it (Execute), such as logging an alert.

### Step 3: Train the ML Model (Optional, but recommended for advanced anomaly detection)
- **Endpoint:** `POST /iot/train_model/{node_id}`
- **Example:**
  ```
  POST /iot/train_model/node1
  ```
- **What happens:**
  - The system uses historical data for node1 to train a machine learning model for anomaly detection.
  - The model is stored and will be used in future analysis steps.

### Step 4: Retrieve Data and Thresholds (for monitoring or debugging)
- **Get all historical data:**
  - `GET /get_data/node1`
- **Get latest data:**
  - `GET /get_latest_data/node1`
- **Get all node IDs:**
  - `GET /get_all_node_ids`
- **Get thresholds for a node:**
  - `GET /get_thresholds/node1`

---

## What Happens Internally (MAPE-K Loop)
- **Monitor:** Data is stored in the knowledge base.
- **Analyze:** Data is checked against thresholds and/or ML model for anomalies.
- **Plan:** If an anomaly is found, the system decides what action to take (e.g., alert).
- **Execute:** The planned action is carried out (e.g., log alert, notify).
- **Knowledge:** All thresholds, data, and models are stored and updated for future use.

---

This step-by-step guide helps you understand what values to pass, what endpoints to call, and what happens at each stage in the MAPE-K loop for this smart building scenario.

For more details on API usage and endpoints, see the README.md.
