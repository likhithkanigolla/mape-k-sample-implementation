# Knowledge-Based Intelligent MAPE-K System

## 🧠 Overview

This system implements a **learning MAPE-K loop** that gets smarter over time by tracking plan effectiveness and adapting its strategy based on historical success rates.

## Key Improvements

### 1. **Individual Sensor Logging** ✅
Each IoT sensor now logs to its own file in the `logs/` directory:
- `logs/water_quality.log` - Water quality sensor events
- `logs/water_level.log` - Water level sensor events  
- `logs/water_flow.log` - Water flow sensor events
- `logs/motor.log` - Motor sensor events
- `logs/plain_mapek.log` - MAPE-K loop events

### 2. **Knowledge Base** 🎓
The system now learns from experience through three new database tables:

####  `plan_effectiveness`
Tracks every plan execution and whether it fixed the problem:
```sql
- node_id: Which device had the problem
- problem_state: What state was detected (critical, warning, etc.)
- plan_code: Which plan was executed
- was_successful: Did it work? (TRUE/FALSE)
- cycles_to_fix: How many MAPE-K cycles until fixed
- alternative_tried: Which alternative was this (0=first, 1=second, etc.)
```

#### `plan_alternatives`
Maintains alternative plans for each problem with success rates:
```sql
- problem_state: The problem type
- plan_code: Available plan to try
- priority: Order to try (1=first, 2=second, 3=third)
- success_rate: Historical success rate (0-100%)
- total_attempts: How many times tried
- successful_attempts: How many times it worked
```

#### `issue_tracking`
Tracks ongoing issues that need resolution:
```sql
- node_id: Which device
- problem_state: Current problem
- attempts: How many plans have been tried
- is_resolved: Whether it's fixed
- plan_executed: Last plan tried
```

### 3. **Intelligent Plan Selection** 🤖

The system now intelligently selects plans:

**First Detection:**
- System detects a critical state on `water_quality_1`
- Knowledge base suggests `EMERGENCY_SHUTDOWN` (highest success rate)
- Plan is executed and recorded

**Verification (Next Cycle):**
- System checks if sensor is now normal
- **If YES**: Records success, updates success rate ✅
- **If NO**: Records failure, tries alternative plan ⚠️

**Alternative Plans (If First Failed):**
1. Try `EMERGENCY_SHUTDOWN` (first attempt)
2. If fails → Try `RECALIBRATE_SENSOR` (second attempt)
3. If fails → Try `RESTART_DEVICE` (third attempt)
4. System learns which works best and updates priorities

### 4. **Feedback Loop** 🔄

```
CYCLE 1: Detect Problem → Select Best Plan → Execute
         ↓
CYCLE 2: Verify if Fixed
         ├─ FIXED ✅ → Record success → Increase plan's success rate
         └─ NOT FIXED ❌ → Record failure → Try alternative plan
                ↓
CYCLE 3: If still broken → Try next alternative
         ...continues until resolved
```

## How It Works

### Analysis Phase (analyze.py)
```python
# When problem detected
if state == 'critical':
    kb.record_issue_detected(node_id, 'critical', details)

# When system is normal
if state == 'normal':
    kb.verify_plan_effectiveness(node_id, 'normal')  # Did previous plan work?
```

### Planning Phase (plan.py)
```python
# Get best plan based on history
best_plan, alternative_num = kb.get_best_plan_for_problem(state, node_id)

# If first attempt failed, this returns the NEXT best plan
if alternative_num > 0:
    logger.info(f"Trying alternative #{alternative_num+1}")
```

### Execution Phase (execute.py)
```python
# Record that we executed this plan
kb.record_plan_execution(node_id, state, plan_code, alternative_num)
```

## Real-World Example

### Scenario: Water Quality Sensor Malfunction

**Cycle 1: Problem Detection**
```
[MONITOR] water_quality_1 - Temperature: 55°C (threshold: 20-30°C)
[ANALYZE] State: CRITICAL (4/4 violations)
          → Knowledge Base: Record new issue
[PLAN]    Knowledge Base suggests: EMERGENCY_SHUTDOWN (90% success rate)
[EXECUTE] Sending EMERGENCY_SHUTDOWN to water_quality_1
```

**Cycle 2: Verification**
```
[MONITOR] water_quality_1 - Temperature: 55°C (still high!)
[ANALYZE] State: CRITICAL (4/4 violations)
          → Knowledge Base: EMERGENCY_SHUTDOWN FAILED ❌
[PLAN]    Knowledge Base suggests: RECALIBRATE_SENSOR (alternative #2, 75% success rate)
[EXECUTE] Sending RECALIBRATE_SENSOR to water_quality_1
```

**Cycle 3: Success!**
```
[MONITOR] water_quality_1 - Temperature: 25°C (normal)
[ANALYZE] State: NORMAL (0/4 violations)
          → Knowledge Base: RECALIBRATE_SENSOR WORKED ✅
          → Update: RECALIBRATE_SENSOR now 80% success rate for CRITICAL
[PLAN]    NO_ACTION (system operating normally)
```

**Future Cycles:**
Next time `water_quality_1` has a CRITICAL issue, the system will try `RECALIBRATE_SENSOR` FIRST because it learned it works better than `EMERGENCY_SHUTDOWN` for this device!

## Querying the Knowledge Base

### See which plans work best
```sql
SELECT * FROM best_plans_by_problem;
```

### Check active issues
```sql
SELECT * FROM active_issues;
```

### View plan effectiveness history
```sql
SELECT * FROM plan_effectiveness_summary;
```

### Get success rates for a specific problem
```sql
SELECT plan_code, success_rate, total_attempts
FROM plan_alternatives
WHERE problem_state = 'CRITICAL'
ORDER BY success_rate DESC;
```

## Alternative Plans by Problem State

### CRITICAL Problems
1. `EMERGENCY_SHUTDOWN` (Priority 1)
2. `RECALIBRATE_SENSOR` (Priority 2)
3. `RESTART_DEVICE` (Priority 3)

### WARNING Problems
1. `RECALIBRATE_SENSOR` (Priority 1)
2. `CHECK_CONNECTIONS` (Priority 2)
3. `ADJUST_PARAMETERS` (Priority 3)

### ANOMALY Problems
1. `RECALIBRATE_SENSOR` (Priority 1)
2. `CHECK_POWER_SUPPLY` (Priority 2)
3. `RESTART_DEVICE` (Priority 3)

## System Intelligence Features

### ✅ Learning
- Tracks which plans work for which problems
- Updates success rates after every attempt
- Builds knowledge over time

### ✅ Adaptation
- If a plan fails, tries alternatives automatically
- Prioritizes plans with higher historical success
- Device-specific learning (what works for sensor A might differ from sensor B)

### ✅ Persistence
- All knowledge stored in database
- Survives system restarts
- Accumulates wisdom over weeks/months

### ✅ Transparency
- Logs show which alternative is being tried
- Can query why a plan was selected
- Full audit trail of decisions

## Benefits

1. **Self-Healing**: System tries multiple solutions until problem is fixed
2. **Learning**: Gets smarter with each problem encountered
3. **Resilience**: Doesn't give up after first plan fails
4. **Efficiency**: Over time, always tries the most effective plan first
5. **Adaptability**: Different devices can have different "best" solutions

## Monitoring Knowledge Growth

Watch your system get smarter:

```bash
# See how many plans have been learned
psql -U postgres -d mapek_dt -c "
SELECT problem_state, COUNT(*) as plans_tried, 
       AVG(success_rate) as avg_success_rate
FROM plan_alternatives 
WHERE total_attempts > 0
GROUP BY problem_state;"
```

## Configuration

All alternative plans are configured in `setup_knowledge_base.sql`. You can add more alternatives by inserting into `plan_alternatives`:

```sql
INSERT INTO plan_alternatives (problem_state, plan_code, priority) 
VALUES ('CRITICAL', 'MY_NEW_PLAN', 4);
```

The system will automatically start trying this plan if the first 3 fail!

## This is True MAPE-K! 🎉

This implementation demonstrates the **Knowledge** component that makes MAPE-K different from simple control loops:

- **Memory**: Remembers what worked and what didn't
- **Learning**: Improves decisions based on experience  
- **Reasoning**: Selects plans based on historical effectiveness
- **Adaptation**: Changes strategy when environment changes

Your system is now a **living, learning brain** that manages your IoT infrastructure! 🧠✨
