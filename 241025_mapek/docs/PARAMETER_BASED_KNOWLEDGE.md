# Parameter-Based Knowledge System with Escalation

## 🎯 Overview

The system now works at **parameter level** with **automatic escalation**, making it more realistic and intelligent:

- ❌ **REMOVED**: `plan_alternatives` table
- ✅ **USES**: Existing `plans` table with added success tracking columns
- ✅ **TRACKS**: Individual parameter issues (temperature, TDS, flow, etc.)
- ✅ **ESCALATES**: Level 1 → Level 2 → Level 3 automatically

## Key Changes

### 1. Plans Table Enhanced
```sql
ALTER TABLE plans ADD COLUMN:
- parameter VARCHAR(50)          -- Which parameter (temperature, tds_voltage, etc.)
- success_rate DECIMAL(5,2)     -- Learned from experience (starts at 50%)
- total_attempts INTEGER        -- How many times tried
- successful_attempts INTEGER   -- How many times worked
- escalation_level INTEGER      -- 1=restart service, 2=restart device, 3=shutdown
```

### 2. Parameter-Specific Plans

**Example: Temperature Issue**
```
Level 1: RESTART_TEMP_SENSOR (80% initial success rate)
Level 2: RESTART_DEVICE (70% initial success rate)
Level 3: EMERGENCY_SHUTDOWN (95% initial success rate)
```

**Example: TDS Issue**
```
Level 1: RECALIBRATE_TDS_SENSOR (85% success)
Level 2: CLEAN_SENSOR (75% success)
Level 3: REPLACE_SENSOR (90% success)
```

### 3. Escalation Strategy

```
Cycle 1: Temperature = 55°C (threshold: 20-30°C)
         → Try Level 1: RESTART_TEMP_SENSOR
         
Cycle 2: Temperature still 55°C
         → Level 1 failed, escalate!
         → Try Level 2: RESTART_DEVICE
         
Cycle 3: Temperature still 55°C
         → Level 2 failed, escalate!
         → Try Level 3: EMERGENCY_SHUTDOWN
         
Cycle 4: Temperature = 25°C  ✅
         → Level 3 worked!
         → Update success rates:
           * RESTART_TEMP_SENSOR: 80% → 75% (failed)
           * RESTART_DEVICE: 70% → 65% (failed)
           * EMERGENCY_SHUTDOWN: 95% → 96% (succeeded)
```

### 4. How It Works

#### Issue Detection (Analyze Phase)
```python
if temperature > threshold_max:
    kb.record_issue_detected(
        node_id="water_quality_1",
        parameter="temperature",
        problem_value=55.0,
        threshold_min=20.0,
        threshold_max=30.0
    )
```

#### Plan Selection (Plan Phase)
```python
plan_code, escalation_level, desc = kb.get_best_plan_for_parameter(
    node_id="water_quality_1",
    parameter="temperature",
    state="HIGH_TEMPERATURE"
)
# Returns: ("RESTART_TEMP_SENSOR", 1, "Restart temperature sensor service")
```

#### Plan Execution (Execute Phase)
```python
kb.record_plan_execution(
    node_id="water_quality_1",
    parameter="temperature",
    plan_code="RESTART_TEMP_SENSOR",
    escalation_level=1
)
```

#### Verification (Next Monitor Phase)
```python
kb.verify_plan_effectiveness(
    node_id="water_quality_1",
    parameter="temperature",
    current_value=25.0,
    threshold_min=20.0,
    threshold_max=30.0
)
# Detects: Value is now within threshold → Plan worked! ✅
```

## Benefits

### ✅ Simpler Design
- No separate `plan_alternatives` table
- All learning happens in existing `plans` table
- Single source of truth

### ✅ Parameter-Specific
- If temperature is bad → restart temperature sensor
- If TDS is bad → recalibrate TDS sensor
- Targeted fixes, not blanket solutions

### ✅ Automatic Escalation
- System automatically tries:
  1. Gentle fix (restart service)
  2. Medium fix (restart device)
  3. Nuclear option (shutdown)
- No manual alternative selection needed

### ✅ Learning
- Each parameter/plan combination tracks its own success rate
- System learns which escalation level typically works
- Different sensors can have different "best" solutions

## Database Schema

### Plans Table (Modified)
```sql
CREATE TABLE plans (
    id SERIAL PRIMARY KEY,
    state VARCHAR(50),              -- HIGH_TEMPERATURE, LOW_WATER_LEVEL, etc.
    plan_code VARCHAR(100),         -- RESTART_TEMP_SENSOR, etc.
    description TEXT,
    priority INTEGER,
    parameter VARCHAR(50),          -- NEW: temperature, tds_voltage, flowrate, etc.
    success_rate DECIMAL(5,2),     -- NEW: Learned rate (50-100%)
    total_attempts INTEGER,         -- NEW: How many times tried
    successful_attempts INTEGER,    -- NEW: How many times worked
    escalation_level INTEGER,       -- NEW: 1, 2, or 3
    last_used TIMESTAMP            -- NEW: When last used
);
```

### Issue Tracking (Modified)
```sql
CREATE TABLE issue_tracking (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50),
    parameter VARCHAR(50),          -- NEW: Specific parameter
    problem_value DECIMAL(10,2),    -- NEW: The bad value
    threshold_min DECIMAL(10,2),    -- NEW: Expected min
    threshold_max DECIMAL(10,2),    -- NEW: Expected max
    escalation_level INTEGER,       -- NEW: Current level (1, 2, or 3)
    attempts INTEGER,               -- How many plans tried
    is_resolved BOOLEAN,
    ...
);
```

### Plan Effectiveness (Modified)
```sql
CREATE TABLE plan_effectiveness (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50),
    parameter VARCHAR(50),           -- NEW: Which parameter
    problem_value DECIMAL(10,2),     -- NEW: The problematic value
    threshold_min DECIMAL(10,2),     -- NEW: Expected min
    threshold_max DECIMAL(10,2),     -- NEW: Expected max
    plan_code VARCHAR(100),
    escalation_level INTEGER,        -- NEW: Which level
    was_successful BOOLEAN,
    cycles_to_fix INTEGER,
    ...
);
```

## Example Plans Configured

### Temperature (3 levels)
```
Level 1: RESTART_TEMP_SENSOR      (80% success)
Level 2: RESTART_DEVICE            (70% success)
Level 3: EMERGENCY_SHUTDOWN        (95% success)
```

### TDS/Water Quality (3 levels each)
```
compensated_tds:
  Level 1: RECALIBRATE_TDS_SENSOR  (85% success)
  Level 2: CLEAN_SENSOR            (75% success)
  Level 3: REPLACE_SENSOR          (90% success)

tds_voltage:
  Level 1: RECALIBRATE_TDS_VOLTAGE (80% success)
  Level 2: CHECK_POWER_SUPPLY      (70% success)
  Level 3: RESTART_DEVICE          (85% success)
```

### Water Level (3 levels each)
```
LOW:
  Level 1: ACTIVATE_INLET_VALVE    (90% success)
  Level 2: ACTIVATE_PUMP           (85% success)
  Level 3: CHECK_INLET_BLOCKAGE    (75% success)

HIGH:
  Level 1: STOP_INLET              (95% success)
  Level 2: ACTIVATE_DRAIN          (90% success)
  Level 3: EMERGENCY_STOP          (100% success)
```

### Flow Rate (3 levels each)
```
HIGH:
  Level 1: REDUCE_VALVE_OPENING    (85% success)
  Level 2: REDUCE_PUMP_SPEED       (80% success)
  Level 3: STOP_PUMP               (95% success)

LOW:
  Level 1: INCREASE_VALVE_OPENING  (85% success)
  Level 2: INCREASE_PUMP_SPEED     (75% success)
  Level 3: CHECK_BLOCKAGES         (70% success)
```

### Motor/Power (3 levels each for current, voltage, frequency, power_factor)

## Querying the System

### See which parameters have issues
```sql
SELECT * FROM active_issues;
```

### Check best plans for each parameter
```sql
SELECT * FROM best_plans_by_parameter;
```

### See escalation patterns
```sql
SELECT * FROM escalation_analysis;
```

### Check parameter-specific success rates
```sql
SELECT * FROM plan_effectiveness_by_parameter
WHERE parameter = 'temperature';
```

## To Setup

1. **Drop and recreate database**:
```bash
psql -U postgres -c "DROP DATABASE mapek_dt;"
psql -U postgres -c "CREATE DATABASE mapek_dt;"
```

2. **Run complete setup**:
```bash
psql -U postgres -d mapek_dt -f setup_complete_database.sql
psql -U postgres -d mapek_dt -f setup_knowledge_base.sql
```

3. **Verify**:
```bash
psql -U postgres -d mapek_dt -c "SELECT parameter, plan_code, escalation_level, success_rate FROM plans WHERE parameter IS NOT NULL ORDER BY parameter, escalation_level;"
```

You should see plans organized by parameter with 3 escalation levels each!

## Next Steps

The analyze.py and plan.py files need to be updated to work with this parameter-based approach. I'm working on that now!
