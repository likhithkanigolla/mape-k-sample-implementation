# Database Setup Fixes

## Issues Fixed

### 1. ❌ Duplicate Key Violations
**Problem:** Plans were being inserted that already existed in the database from `setup_complete_database.sql`

**Error:**
```
ERROR: duplicate key value violates unique constraint "plans_unique"
DETAIL: Key (state, plan_code)=(LOW_WATER_LEVEL, ACTIVATE_PUMP) already exists.
```

**Solution:** Added `ON CONFLICT (state, plan_code) DO UPDATE SET` to all INSERT statements:
```sql
INSERT INTO plans (...) VALUES (...)
ON CONFLICT (state, plan_code) DO UPDATE SET
    parameter = EXCLUDED.parameter,
    escalation_level = EXCLUDED.escalation_level,
    success_rate = EXCLUDED.success_rate;
```

Now if a plan already exists, it will update the parameter/escalation/success_rate columns instead of failing.

### 2. ❌ Missing "attempts" Column
**Problem:** The `escalation_analysis` view was trying to use `AVG(attempts)` from `plan_effectiveness` table, but that column doesn't exist there.

**Error:**
```
ERROR: column "attempts" does not exist
LINE 8: ROUND(AVG(attempts), 2) as avg_attempts_to_fix,
```

**Solution:** Changed to use `AVG(cycles_to_fix)` which actually exists in the `plan_effectiveness` table:
```sql
-- Before:
ROUND(AVG(attempts), 2) as avg_attempts_to_fix,

-- After:
ROUND(AVG(cycles_to_fix), 2) as avg_cycles_to_fix,
```

**Note:** The `attempts` column exists in `issue_tracking` table, not `plan_effectiveness`.

### 3. ❌ Missing File: setup_iot_gateway_views.sql
**Problem:** The setup script tried to run `setup_iot_gateway_views.sql` but it didn't exist.

**Error:**
```
✗ setup_iot_gateway_views.sql not found
```

**Solution:** Created `setup_iot_gateway_views.sql` with useful IoT gateway analytics views:
- `sensor_health` - Shows which sensors are online/offline
- `recent_gateway_activity` - Last hour of sensor readings
- `command_execution_summary` - How many commands were executed per plan
- `gateway_throughput` - Readings per minute metrics

## How to Rerun Setup

Now you can safely rerun the setup:

```bash
cd /Users/likhithkanigolla/IIITH/code-files/Digital-Twin/mape-k/241025_mapek

# Option 1: Run full setup script (recommended)
./scripts/setup.sh

# Option 2: Manual database recreation
psql -U postgres -c "DROP DATABASE mapek_dt;"
psql -U postgres -c "CREATE DATABASE mapek_dt;"
psql -U postgres -d mapek_dt -f setup_complete_database.sql
psql -U postgres -d mapek_dt -f setup_knowledge_base.sql
psql -U postgres -d mapek_dt -f setup_iot_gateway_views.sql
```

## Expected Output

You should now see:
```
✓ Database created
[... table creation messages ...]
✓ All database tables created

[... knowledge base setup ...]
CREATE VIEW
CREATE VIEW
CREATE VIEW
✓ Knowledge base views created

[... IoT gateway views ...]
✓ IoT Gateway views created successfully!
📊 Views: sensor_health, recent_gateway_activity, command_execution_summary, gateway_throughput
```

## Verify Setup

Check that all tables and views were created:

```bash
# Check tables
psql -U postgres -d mapek_dt -c "\dt"

# Check views
psql -U postgres -d mapek_dt -c "\dv"

# Check parameter-specific plans
psql -U postgres -d mapek_dt -c "
SELECT parameter, plan_code, escalation_level, success_rate 
FROM plans 
WHERE parameter IS NOT NULL 
ORDER BY parameter, escalation_level;
"

# Check knowledge base views work
psql -U postgres -d mapek_dt -c "SELECT * FROM best_plans_by_parameter LIMIT 5;"
psql -U postgres -d mapek_dt -c "SELECT * FROM active_issues LIMIT 5;"
```

## Summary

All database setup errors have been fixed:
- ✅ Duplicate plan insertions now use `ON CONFLICT DO UPDATE`
- ✅ View uses correct column name (`cycles_to_fix` instead of `attempts`)
- ✅ Created missing `setup_iot_gateway_views.sql` file

The system is ready to run! 🚀
