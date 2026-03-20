# Parameter-Based MAPE-K Implementation

## 🎯 What Changed?

The MAPE-K loop has been redesigned to work at **parameter level** instead of device level, with **automatic escalation** when plans fail.

### Before (State-Based)
```
Device is "critical" → Try RESTART_DEVICE plan → Hope it works
```

### After (Parameter-Based with Escalation)
```
Temperature = 55°C (bad) 
  Cycle 1: → Try Level 1: RESTART_TEMP_SENSOR
  Cycle 2: Still bad → Escalate to Level 2: RESTART_DEVICE  
  Cycle 3: Still bad → Escalate to Level 3: EMERGENCY_SHUTDOWN
  Cycle 4: Temperature = 25°C ✅ Fixed!
```

## 📋 Files Updated

### 1. setup_knowledge_base.sql
**Changes:**
- ❌ Removed `plan_alternatives` table (too complex)
- ✅ Extended `plans` table with:
  - `parameter` VARCHAR(50) - Which parameter (temperature, tds, etc.)
  - `success_rate` DECIMAL - Learned success rate (50-100%)
  - `total_attempts` INTEGER - How many times tried
  - `successful_attempts` INTEGER - How many times worked
  - `escalation_level` INTEGER - 1 (service), 2 (device), 3 (shutdown)
- ✅ Modified `issue_tracking` to track parameters with thresholds
- ✅ Modified `plan_effectiveness` to record parameter-level outcomes
- ✅ Added 40+ parameter-specific plans with 3 escalation levels each

**Example Plans:**
```sql
-- Temperature (3 levels)
('HIGH_TEMPERATURE', 'RESTART_TEMP_SENSOR', 'temperature', 1, 80.00),
('HIGH_TEMPERATURE', 'RESTART_DEVICE', 'temperature', 2, 70.00),
('HIGH_TEMPERATURE', 'EMERGENCY_SHUTDOWN', 'temperature', 3, 95.00),

-- TDS (3 levels)
('HIGH_TDS', 'RECALIBRATE_TDS_SENSOR', 'compensated_tds', 1, 85.00),
('HIGH_TDS', 'CLEAN_SENSOR', 'compensated_tds', 2, 75.00),
('HIGH_TDS', 'REPLACE_SENSOR', 'compensated_tds', 3, 90.00),
```

### 2. plain_mapek/knowledge.py
**Complete rewrite** - Now parameter-based:

**Key Methods:**
```python
# Record issue for a specific parameter
record_issue_detected(node_id, parameter, problem_value, threshold_min, threshold_max)

# Record plan execution for a parameter
record_plan_execution(node_id, parameter, plan_code, escalation_level)

# Check if parameter is now within threshold (plan worked!)
verify_plan_effectiveness(node_id, parameter, current_value, threshold_min, threshold_max)

# Get best plan for a parameter (with escalation logic)
get_best_plan_for_parameter(node_id, parameter, state)
  → Returns: (plan_code, escalation_level, description)
  → Automatically escalates: Level 1 → 2 → 3 if previous attempts failed
```

**Escalation Logic:**
```python
# Check if there's an existing issue
if issue exists and attempts > 0:
    # Escalate!
    current_escalation = min(issue.escalation_level + 1, 3)
else:
    # First attempt, start at level 1
    current_escalation = 1

# Get plan at this escalation level
SELECT plan_code FROM plans 
WHERE parameter = ? AND escalation_level = ?
ORDER BY success_rate DESC
```

### 3. plain_mapek/analyze.py
**Redesigned** - Parameter-level violation tracking:

**What It Does Now:**
- Checks **each parameter** individually against thresholds
- Records violations with actual values and thresholds:
  ```python
  kb.record_issue_detected(
      node_id="water_quality_1",
      parameter="temperature",
      problem_value=55.0,
      threshold_min=20.0,
      threshold_max=30.0
  )
  ```
- Returns `violated_parameters` list (e.g., `['temperature', 'tds_voltage']`)
- Verifies if previously bad parameters are now good:
  ```python
  kb.verify_plan_effectiveness(
      node_id="water_quality_1",
      parameter="temperature",
      current_value=25.0,  # Now within threshold!
      threshold_min=20.0,
      threshold_max=30.0
  )
  ```

**Log Output:**
```
Parameter violation: water_quality_1.temperature = 55.0 
  (expected: 20.0-30.0) → State: HIGH_TEMPERATURE

Analyzer: water_quality_1 - State: critical 
  (2/5 violations in: temperature, tds_voltage)
```

### 4. plain_mapek/plan.py
**Redesigned** - Parameter-specific plan selection:

**What It Does Now:**
- For each violated parameter, selects a **specific plan**
- Uses knowledge base escalation logic:
  ```python
  plan_info = kb.get_best_plan_for_parameter(
      node_id="water_quality_1",
      parameter="temperature",
      state="HIGH_TEMPERATURE"
  )
  # Returns: ("RESTART_TEMP_SENSOR", 1, "Restart temperature sensor")
  ```
- Returns plans with:
  - `parameter`: Which parameter this targets
  - `escalation_level`: Which level (1, 2, or 3)

**Log Output:**
```
Planner: Selected plan 'RESTART_TEMP_SENSOR' (Level 1) 
  for water_quality_1.temperature (state: HIGH_TEMPERATURE)
```

### 5. plain_mapek/execute.py
**Redesigned** - Passes parameter and escalation info:

**What It Does Now:**
- Sends commands with **parameter** and **escalation_level**:
  ```python
  payload = {
      'node_id': 'water_quality_1',
      'plan_code': 'RESTART_TEMP_SENSOR',
      'parameter': 'temperature',
      'escalation_level': 1
  }
  ```
- Records execution in knowledge base:
  ```python
  kb.record_plan_execution(
      node_id="water_quality_1",
      parameter="temperature",
      plan_code="RESTART_TEMP_SENSOR",
      escalation_level=1
  )
  ```

**Log Output:**
```
Sending command to Gateway for water_quality_1.temperature: RESTART_TEMP_SENSOR
Recorded execution: water_quality_1.temperature → RESTART_TEMP_SENSOR (Level 1)
Executor: Executed 'RESTART_TEMP_SENSOR' Level 1 
  for water_quality_1.temperature - Status: success
```

## 📊 How Escalation Works

### Example: Temperature Too High (55°C, threshold: 20-30°C)

#### Cycle 1: First Detection
```
Monitor → temperature = 55°C
Analyze → Record issue: temperature violated (55.0, expected 20-30)
Plan    → Get plan for 'temperature': Level 1 = RESTART_TEMP_SENSOR
Execute → Send command + Record execution
```

#### Cycle 2: Still High
```
Monitor → temperature = 55°C (still bad!)
Analyze → Issue still exists, attempts = 1
Plan    → Get plan for 'temperature': 
           attempts > 0 → Escalate!
           Level 2 = RESTART_DEVICE
Execute → Send command + Record execution
```

#### Cycle 3: Still High
```
Monitor → temperature = 55°C (still bad!)
Analyze → Issue still exists, attempts = 2
Plan    → Get plan for 'temperature':
           attempts > 0 → Escalate!
           Level 3 = EMERGENCY_SHUTDOWN
Execute → Send command + Record execution
```

#### Cycle 4: Fixed!
```
Monitor → temperature = 25°C ✅
Analyze → Verify effectiveness:
           temperature now within 20-30
           → EMERGENCY_SHUTDOWN worked!
           → Update success rates:
              * RESTART_TEMP_SENSOR: 80% → 75% (failed)
              * RESTART_DEVICE: 70% → 65% (failed)
              * EMERGENCY_SHUTDOWN: 95% → 96% (succeeded!)
           → Mark issue as resolved
```

## 🎯 Benefits

### 1. **Targeted Fixes**
```
❌ Before: "Device is bad, restart everything"
✅ After:  "Temperature is bad, restart temp sensor only"
```

### 2. **Automatic Escalation**
```
❌ Before: Pick random alternative plan from plan_alternatives table
✅ After:  Automatically try Level 1 → 2 → 3 until it works
```

### 3. **Learning**
```
❌ Before: No feedback, same plan every time
✅ After:  Tracks success rates per parameter/level
           - RESTART_TEMP_SENSOR for temperature: 75%
           - RESTART_DEVICE for temperature: 65%
           - EMERGENCY_SHUTDOWN for temperature: 96% ✅
```

### 4. **Simpler Schema**
```
❌ Before: plans + plan_alternatives (2 tables, complex joins)
✅ After:  Just plans table with escalation_level column
```

## 🗄️ Database Setup

### Step 1: Drop old database
```bash
psql -U postgres -c "DROP DATABASE mapek_dt;"
psql -U postgres -c "CREATE DATABASE mapek_dt;"
```

### Step 2: Create base schema
```bash
psql -U postgres -d mapek_dt -f setup_complete_database.sql
```

### Step 3: Add knowledge base tables and parameter plans
```bash
psql -U postgres -d mapek_dt -f setup_knowledge_base.sql
```

### Step 4: Verify plans
```bash
psql -U postgres -d mapek_dt -c "
SELECT parameter, plan_code, escalation_level, success_rate 
FROM plans 
WHERE parameter IS NOT NULL 
ORDER BY parameter, escalation_level;
"
```

Should see output like:
```
    parameter    |        plan_code         | escalation_level | success_rate 
-----------------+--------------------------+------------------+--------------
 compensated_tds | RECALIBRATE_TDS_SENSOR   |                1 |        85.00
 compensated_tds | CLEAN_SENSOR             |                2 |        75.00
 compensated_tds | REPLACE_SENSOR           |                3 |        90.00
 temperature     | RESTART_TEMP_SENSOR      |                1 |        80.00
 temperature     | RESTART_DEVICE           |                2 |        70.00
 temperature     | EMERGENCY_SHUTDOWN       |                3 |        95.00
```

## 🧪 Testing

### 1. Start the system
```bash
cd /Users/likhithkanigolla/IIITH/code-files/Digital-Twin/mape-k/241025_mapek
./scripts/start_all.sh
```

### 2. Watch logs
```bash
tail -f logs/mapek.log | grep -E "(Analyzer|Planner|Executor)"
```

### 3. Look for escalation
You should see patterns like:
```
Analyzer: water_quality_1.temperature = 55.0 (expected: 20-30) → HIGH_TEMPERATURE
Planner: Selected 'RESTART_TEMP_SENSOR' (Level 1) for water_quality_1.temperature
Executor: Executed 'RESTART_TEMP_SENSOR' Level 1 - Status: success

[Next cycle if still bad]
Planner: Selected 'RESTART_DEVICE' (Level 2) for water_quality_1.temperature
Executor: Executed 'RESTART_DEVICE' Level 2 - Status: success

[Next cycle if still bad]
Planner: Selected 'EMERGENCY_SHUTDOWN' (Level 3) for water_quality_1.temperature
Executor: Executed 'EMERGENCY_SHUTDOWN' Level 3 - Status: success
```

### 4. Query knowledge base
```bash
# See active issues
psql -U postgres -d mapek_dt -c "SELECT * FROM active_issues;"

# See success rates by parameter
psql -U postgres -d mapek_dt -c "SELECT * FROM best_plans_by_parameter;"

# See escalation patterns
psql -U postgres -d mapek_dt -c "SELECT * FROM escalation_analysis;"
```

## 📝 Next Steps

1. ✅ **Database recreated** with new schema
2. ✅ **knowledge.py** rewritten (parameter-based)
3. ✅ **analyze.py** rewritten (parameter-level violation tracking)
4. ✅ **plan.py** rewritten (parameter-specific plan selection)
5. ✅ **execute.py** rewritten (parameter + escalation recording)
6. ⏳ **monitor.py** - Needs verification (probably already works)
7. ⏳ **Other sensors** - Apply plan failure simulation to:
   - motor_sensor.py
   - water_flow_sensor.py
   - water_level_sensor.py
8. ⏳ **Test entire system** with new parameter-based approach

## 🎉 Summary

We simplified the design by:
- ❌ Removing `plan_alternatives` table
- ✅ Using existing `plans` table with escalation levels
- ✅ Tracking issues/plans at **parameter level** (temperature, TDS, etc.)
- ✅ Automatic escalation: Level 1 → 2 → 3
- ✅ Learning success rates per parameter/plan combination

The system is now **smarter**, **simpler**, and **more targeted** in fixing problems!
