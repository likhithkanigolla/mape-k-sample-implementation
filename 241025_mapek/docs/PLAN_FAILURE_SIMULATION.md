# Plan Failure Simulation - Realistic Testing

## 🎯 Overview

The sensor scripts now simulate **realistic plan failures** to properly test the knowledge-based learning system. Plans don't always work in real life, and this simulation ensures the MAPE-K system learns to try alternatives.

## How It Works

### Plan Success Rates

Each plan has a different probability of working when executed:

```python
PLAN_SUCCESS_RATES = {
    "EMERGENCY_SHUTDOWN": 0.5,      # 50% - Often fails (not the right fix)
    "RECALIBRATE_SENSOR": 0.8,      # 80% - Usually works! (Best fix)
    "RESTART_DEVICE": 0.6,          # 60% - Sometimes works
    "NO_ACTION": 1.0,               # 100% - Always "works"
    "CHECK_POWER_SUPPLY": 0.7,      # 70% - Often works
    "ADJUST_PARAMETERS": 0.65       # 65% - Works more than half the time
}
```

### Execution Flow

**When MAPE-K sends a command:**

1. **Command Received** by sensor
2. **Random check** based on plan's success rate
3. **Two outcomes:**

   **✅ Success (Plan Worked):**
   ```
   - Sensor sets is_faulty = False
   - Sensor sets fault_fixed = True
   - Next cycle sends NORMAL data
   - MAPE-K detects: Problem FIXED
   - Knowledge Base: Plan SUCCESS ✅
   ```

   **❌ Failure (Plan Didn't Work):**
   ```
   - Sensor keeps is_faulty = True
   - Sensor sets fault_fixed = False  
   - Next cycle STILL sends ANOMALY data
   - MAPE-K detects: Problem STILL EXISTS
   - Knowledge Base: Plan FAILED ❌ → Try alternative
   ```

## Example Scenario

### Scenario: Water Quality Sensor Malfunction

**Cycle 1: Problem Detected**
```
[SENSOR] Anomaly detected - sending faulty data
[MAPE-K ANALYZE] Critical state detected
[MAPE-K PLAN] Try EMERGENCY_SHUTDOWN (first attempt)
[MAPE-K EXECUTE] Send command to sensor
```

**Sensor Receives Command:**
```python
success_rate = 0.5  # EMERGENCY_SHUTDOWN has 50% success rate
random.random() = 0.73  # Random number > 0.5
# Result: PLAN FAILS ❌
```

**Sensor Response:**
```
❌ FAILED: Plan 'EMERGENCY_SHUTDOWN' DID NOT WORK!
   Success rate: 50.0%
   Sensor still faulty - need alternative plan
```

**Cycle 2: Verification**
```
[SENSOR] Still faulty - sends anomaly data
[MAPE-K ANALYZE] Still critical (previous plan failed)
[MAPE-K PLAN] Try RECALIBRATE_SENSOR (alternative #2)
[MAPE-K EXECUTE] Send command to sensor
```

**Sensor Receives Command:**
```python
success_rate = 0.8  # RECALIBRATE_SENSOR has 80% success rate
random.random() = 0.45  # Random number < 0.8
# Result: PLAN WORKS ✅
```

**Sensor Response:**
```
✅ SUCCESS: Plan 'RECALIBRATE_SENSOR' WORKED! Sensor fixed.
   Success rate: 80.0%
   Sensor calibrated/fixed - returning to normal operation
```

**Cycle 3: Success Confirmed**
```
[SENSOR] Fixed - sends normal data
[MAPE-K ANALYZE] Normal state (plan worked!)
[KNOWLEDGE BASE] Updates:
  - EMERGENCY_SHUTDOWN: Failed for CRITICAL (reduces priority)
  - RECALIBRATE_SENSOR: Success for CRITICAL (increases priority)
```

**Cycle 4+: Next Time Same Problem**
```
[MAPE-K PLAN] Try RECALIBRATE_SENSOR FIRST
               (learned it works better than EMERGENCY_SHUTDOWN)
```

## Sensor Log Examples

### When Plan Succeeds:
```
2025-11-07 15:23:45 - INFO - ============================================================
2025-11-07 15:23:45 - INFO - COMMAND RECEIVED from MAPE-K Server
2025-11-07 15:23:45 - INFO - ============================================================
2025-11-07 15:23:45 - INFO - Plan Code: RECALIBRATE_SENSOR
2025-11-07 15:23:45 - INFO - Description: Recalibrate sensor and check connections
2025-11-07 15:23:45 - INFO - ✅ SUCCESS: Plan 'RECALIBRATE_SENSOR' WORKED! Sensor fixed.
2025-11-07 15:23:45 - INFO -    Success rate: 80.0%
2025-11-07 15:23:45 - INFO -    Sensor calibrated/fixed - returning to normal operation
2025-11-07 15:23:45 - INFO - ============================================================
```

### When Plan Fails:
```
2025-11-07 15:22:30 - INFO - ============================================================
2025-11-07 15:22:30 - INFO - COMMAND RECEIVED from MAPE-K Server
2025-11-07 15:22:30 - INFO - ============================================================
2025-11-07 15:22:30 - INFO - Plan Code: EMERGENCY_SHUTDOWN
2025-11-07 15:22:30 - INFO - Description: Emergency system shutdown
2025-11-07 15:22:30 - WARNING - ❌ FAILED: Plan 'EMERGENCY_SHUTDOWN' DID NOT WORK!
2025-11-07 15:22:30 - WARNING -    Success rate: 50.0%
2025-11-07 15:22:30 - WARNING -    Sensor still faulty - need alternative plan
2025-11-07 15:22:30 - INFO - ============================================================
```

### Next Cycle After Failed Plan:
```
2025-11-07 15:23:30 - WARNING - [Cycle 45] STILL FAULTY - Last command 'EMERGENCY_SHUTDOWN' did not fix issue: {'node_id': 'water_quality_1', 'temperature': 52.3, ...}
```

### Next Cycle After Successful Plan:
```
2025-11-07 15:24:30 - INFO - [Cycle 46] FIXED - Normal operation restored by 'RECALIBRATE_SENSOR': {'node_id': 'water_quality_1', 'temperature': 25.8, ...}
```

## Benefits of This Simulation

### 1. **Realistic Testing**
- Not all fixes work in real life
- Some solutions are better than others
- System must handle failures gracefully

### 2. **Forces Learning**
- System can't rely on first plan always working
- Must track which plans actually fix problems
- Learns optimal strategy through trial and error

### 3. **Tests Alternative Plans**
- Ensures alternative plan mechanism works
- Validates that system tries multiple solutions
- Confirms knowledge base learning is functioning

### 4. **Real-World Preparation**
- Simulates unpredictable hardware behavior
- Tests system resilience
- Proves system won't give up after one failure

## Observing the Learning

Watch the system learn over time:

```bash
# See which plans are most successful
psql -U postgres -d mapek_dt -c "
SELECT plan_code, success_rate, total_attempts, successful_attempts
FROM plan_alternatives
WHERE problem_state = 'CRITICAL' AND total_attempts > 0
ORDER BY success_rate DESC;"
```

**Example Output After 10 Cycles:**
```
     plan_code      | success_rate | total_attempts | successful_attempts
--------------------+--------------+----------------+--------------------
 RECALIBRATE_SENSOR |        75.00 |              8 |                   6
 RESTART_DEVICE     |        60.00 |              5 |                   3
 EMERGENCY_SHUTDOWN |        40.00 |              5 |                   2
```

You'll see `RECALIBRATE_SENSOR` emerging as the best solution!

## Configuring Success Rates

To change how often plans work, edit the sensor script:

```python
PLAN_SUCCESS_RATES = {
    "EMERGENCY_SHUTDOWN": 0.4,      # Make it worse (30%)
    "RECALIBRATE_SENSOR": 0.95,     # Make it better (95%)
    "RESTART_DEVICE": 0.5,          # 50-50 chance
    "MY_CUSTOM_PLAN": 0.7           # Add new plans
}
```

## Key Points

1. **Plan execution ≠ Plan success**: A plan can execute successfully but not fix the problem
2. **Persistence**: Sensors stay faulty until a plan actually works
3. **Realistic**: Mirrors real-world where some fixes work better than others
4. **Learning enabled**: System discovers which plans work through experience

## What You'll See in Logs

**MAPE-K will:**
- Try a plan
- Check if it worked next cycle
- If failed → Try alternative plan
- If succeeded → Record success and increase that plan's priority
- Over time → Always try most successful plan first

**Sensors will:**
- Log whether each plan succeeded or failed
- Continue sending fault data if plan didn't work
- Send normal data only when a plan succeeds
- Show which plan finally fixed the issue

This makes the MAPE-K system **truly intelligent** - it learns from failures! 🧠✨
