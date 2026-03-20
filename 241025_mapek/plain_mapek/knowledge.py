"""
Knowledge Base for intelligent MAPE-K system
Tracks plan effectiveness and learns from experience at parameter level
"""
import psycopg2
from logger import logger
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'mapek_dt',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432
}

def get_db_conn():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def get_node_ids():
    """Get all unique node IDs from the database"""
    node_ids = []
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        # Get node IDs from all sensor tables
        cur.execute("""
            SELECT DISTINCT node_id FROM water_quality
            UNION
            SELECT DISTINCT node_id FROM water_flow
            UNION
            SELECT DISTINCT node_id FROM water_level
            UNION
            SELECT DISTINCT node_id FROM motor
            UNION
            SELECT DISTINCT node_id FROM nodes WHERE is_active = TRUE
        """)
        
        node_ids = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error getting node IDs: {e}")
    
    return node_ids


class KnowledgeBase:
    """
    Knowledge Base for tracking plan effectiveness and learning at parameter level
    Uses escalation strategy: Level 1 → Level 2 → Level 3
    """
    
    def record_issue_detected(self, node_id, parameter, problem_value, threshold_min, threshold_max):
        """Record when a parameter issue is first detected"""
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO issue_tracking 
                (node_id, parameter, problem_value, threshold_min, threshold_max, 
                 detected_timestamp, escalation_level, attempts)
                VALUES (%s, %s, %s, %s, %s, NOW(), 1, 0)
                ON CONFLICT (node_id, parameter, detected_timestamp) 
                DO NOTHING
            """, (node_id, parameter, problem_value, threshold_min, threshold_max))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording issue detection: {e}")
    
    def record_plan_execution(self, node_id, parameter, plan_code, escalation_level):
        """Record that a plan was executed for a parameter issue"""
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            # Get the current issue details
            cur.execute("""
                SELECT problem_value, threshold_min, threshold_max
                FROM issue_tracking
                WHERE node_id = %s AND parameter = %s AND is_resolved = FALSE
                ORDER BY detected_timestamp DESC
                LIMIT 1
            """, (node_id, parameter))
            
            issue_data = cur.fetchone()
            if not issue_data:
                conn.close()
                return
            
            problem_value, threshold_min, threshold_max = issue_data
            
            # Update issue tracking
            cur.execute("""
                UPDATE issue_tracking 
                SET plan_executed = %s,
                    execution_timestamp = NOW(),
                    escalation_level = %s,
                    attempts = attempts + 1
                WHERE node_id = %s 
                AND parameter = %s 
                AND is_resolved = FALSE
            """, (plan_code, escalation_level, node_id, parameter))
            
            # Record in plan effectiveness (will verify later)
            cur.execute("""
                INSERT INTO plan_effectiveness 
                (node_id, parameter, problem_value, threshold_min, threshold_max,
                 plan_code, execution_timestamp, escalation_level)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
            """, (node_id, parameter, problem_value, threshold_min, threshold_max, 
                  plan_code, escalation_level))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Knowledge: Recorded plan execution - {plan_code} (L{escalation_level}) for {node_id}.{parameter}")
            
        except Exception as e:
            logger.error(f"Error recording plan execution: {e}")
    
    def verify_plan_effectiveness(self, node_id, parameter, current_value, threshold_min, threshold_max):
        """
        Check if previously executed plans fixed the parameter issue
        Called during Monitor phase to verify effectiveness
        """
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            # FIRST: Check for OLD unverified plan executions that should be marked as failed
            # Look for executions older than 60 seconds that are still NULL
            cur.execute("""
                SELECT plan_code, execution_timestamp, escalation_level
                FROM plan_effectiveness
                WHERE node_id = %s 
                AND parameter = %s
                AND was_successful IS NULL
                AND (NOW() - execution_timestamp) > INTERVAL '60 seconds'
                ORDER BY execution_timestamp ASC
            """, (node_id, parameter))
            
            old_unverified = cur.fetchall()
            
            for plan_code, execution_ts, escalation_level in old_unverified:
                seconds_elapsed = (datetime.now() - execution_ts).total_seconds()
                
                # Mark as failed
                cur.execute("""
                    UPDATE plan_effectiveness
                    SET was_successful = FALSE,
                        verification_timestamp = NOW(),
                        cycles_to_fix = NULL
                    WHERE node_id = %s 
                    AND parameter = %s
                    AND plan_code = %s
                    AND execution_timestamp = %s
                """, (node_id, parameter, plan_code, execution_ts))
                
                self._update_plan_success_rate(parameter, plan_code, False)
                
                logger.warning(f"Knowledge: Plan {plan_code} (L{escalation_level}) FAILED for {node_id}.{parameter} - Not fixed after {seconds_elapsed:.0f}s")
            
            # SECOND: Get active issues for this node and parameter
            cur.execute("""
                SELECT id, plan_executed, detected_timestamp, execution_timestamp, escalation_level
                FROM issue_tracking
                WHERE node_id = %s AND parameter = %s AND is_resolved = FALSE 
                AND plan_executed IS NOT NULL
            """, (node_id, parameter))
            
            active_issues = cur.fetchall()
            
            for issue in active_issues:
                issue_id, plan_code, detected_ts, execution_ts, escalation_level = issue
                
                # Check if current value is now within threshold (fixed!)
                is_fixed = threshold_min <= current_value <= threshold_max
                
                if is_fixed:
                    # Calculate cycles to fix
                    cycles = self._calculate_cycles(detected_ts, datetime.now())
                    
                    # Mark issue as resolved
                    cur.execute("""
                        UPDATE issue_tracking
                        SET is_resolved = TRUE, resolved_timestamp = NOW()
                        WHERE id = %s
                    """, (issue_id,))
                    
                    # Update plan effectiveness
                    cur.execute("""
                        UPDATE plan_effectiveness
                        SET was_successful = TRUE,
                            verification_timestamp = NOW(),
                            cycles_to_fix = %s
                        WHERE node_id = %s 
                        AND parameter = %s
                        AND plan_code = %s
                        AND execution_timestamp = %s
                    """, (cycles, node_id, parameter, plan_code, execution_ts))
                    
                    # Update plan success rate in plans table
                    self._update_plan_success_rate(parameter, plan_code, True)
                    
                    logger.info(f"Knowledge: Plan {plan_code} (L{escalation_level}) SUCCESSFUL for {node_id}.{parameter} - Fixed in {cycles} cycles")
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error verifying plan effectiveness: {e}")
    
    def get_best_plan_for_parameter(self, node_id, parameter, state):
        """
        Get the best plan for a specific parameter issue using escalation strategy
        Returns (plan_code, escalation_level, description)
        """
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            # Check current escalation level for this issue
            cur.execute("""
                SELECT escalation_level, attempts
                FROM issue_tracking
                WHERE node_id = %s 
                AND parameter = %s 
                AND is_resolved = FALSE
                ORDER BY detected_timestamp DESC
                LIMIT 1
            """, (node_id, parameter))
            
            issue_info = cur.fetchone()
            current_escalation = issue_info[0] if issue_info else 1
            attempts = issue_info[1] if issue_info else 0
            
            # If previous attempt failed, escalate
            if attempts > 0:
                current_escalation = min(current_escalation + 1, 3)  # Max level 3
            
            # Get best plan for this parameter at current escalation level
            cur.execute("""
                SELECT plan_code, description, success_rate, escalation_level
                FROM plans
                WHERE parameter = %s 
                AND escalation_level = %s
                AND state = %s
                ORDER BY success_rate DESC, priority ASC
                LIMIT 1
            """, (parameter, current_escalation, state))
            
            plan = cur.fetchone()
            
            if not plan:
                # Fallback: try any plan for this parameter
                cur.execute("""
                    SELECT plan_code, description, success_rate, escalation_level
                    FROM plans
                    WHERE parameter = %s
                    ORDER BY success_rate DESC, escalation_level ASC
                    LIMIT 1
                """, (parameter,))
                plan = cur.fetchone()
            
            cur.close()
            conn.close()
            
            if plan:
                plan_code, description, success_rate, escalation_level = plan
                logger.info(f"Knowledge: Selected {plan_code} (L{escalation_level}, {success_rate}% success) for {parameter}")
                return plan_code, escalation_level, description
            
            return None, 1, None
            
        except Exception as e:
            logger.error(f"Error getting best plan: {e}")
            return None, 1, None
    
    def _calculate_cycles(self, start_time, end_time):
        """Calculate how many MAPE-K cycles elapsed"""
        seconds = (end_time - start_time).total_seconds()
        # Assuming 60 second cycles
        return max(1, int(seconds / 60))
    
    def _update_plan_success_rate(self, parameter, plan_code, was_successful):
        """Update the success rate of a plan in plans table"""
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            if was_successful:
                cur.execute("""
                    UPDATE plans
                    SET total_attempts = COALESCE(total_attempts, 0) + 1,
                        successful_attempts = COALESCE(successful_attempts, 0) + 1,
                        success_rate = ROUND(100.0 * (COALESCE(successful_attempts, 0) + 1) / (COALESCE(total_attempts, 0) + 1), 2),
                        last_used = NOW()
                    WHERE parameter = %s AND plan_code = %s
                """, (parameter, plan_code))
            else:
                cur.execute("""
                    UPDATE plans
                    SET total_attempts = COALESCE(total_attempts, 0) + 1,
                        success_rate = ROUND(100.0 * COALESCE(successful_attempts, 0) / (COALESCE(total_attempts, 0) + 1), 2),
                        last_used = NOW()
                    WHERE parameter = %s AND plan_code = %s
                """, (parameter, plan_code))
            
            rows_updated = cur.rowcount
            conn.commit()
            
            if rows_updated > 0:
                # Log the update
                cur.execute("""
                    SELECT success_rate, total_attempts, successful_attempts
                    FROM plans
                    WHERE parameter = %s AND plan_code = %s
                """, (parameter, plan_code))
                result = cur.fetchone()
                if result:
                    new_rate, total, successful = result
                    status = "SUCCESS" if was_successful else "FAILURE"
                    logger.info(
                        f"Knowledge: Updated {plan_code} for {parameter} - "
                        f"{status} → Success rate: {new_rate}% ({successful}/{total})"
                    )
            
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating plan success rate: {e}")
    
    def get_knowledge_summary(self):
        """Get a summary of the knowledge base"""
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            # Get plan effectiveness summary by parameter
            cur.execute("""
                SELECT parameter, plan_code, success_rate, total_attempts
                FROM plan_effectiveness_by_parameter
                ORDER BY success_rate DESC
                LIMIT 10
            """)
            
            summary = cur.fetchall()
            cur.close()
            conn.close()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting knowledge summary: {e}")
            return []
