"""
Plain MAPE-K Implementation - Main Loop
Simple implementation without advanced software engineering patterns
"""
import time
from datetime import datetime
from monitor import Monitor
from analyze import Analyzer
from plan import Planner
from execute import Executor
from knowledge import get_db_conn
from logger import logger

class PlainMAPEK:
    """Plain MAPE-K system without design patterns"""
    
    def __init__(self):
        # Initialize MAPE-K components
        self.monitor = Monitor()
        self.analyzer = Analyzer()
        self.planner = Planner()
        self.executor = Executor()
        
        self.cycle_count = 0
        
        logger.info("=" * 60)
        logger.info("Plain MAPE-K System Initialized")
        logger.info("No advanced design patterns - Simple direct implementation")
        logger.info("=" * 60)
    
    def run_cycle(self):
        """Execute one MAPE-K cycle"""
        self.cycle_count += 1
        
        logger.info("")
        logger.info(f"{'=' * 60}")
        logger.info(f"MAPE-K Cycle #{self.cycle_count} - {datetime.now()}")
        logger.info(f"{'=' * 60}")
        
        try:
            # MONITOR: Read sensor data
            logger.info("\n[1] MONITOR Phase")
            sensor_data = self.monitor.read_sensors()
            
            if not sensor_data:
                logger.warning("No sensor data available")
                return
            
            # ANALYZE: Check data against thresholds
            logger.info("\n[2] ANALYZE Phase")
            analysis_results = self.analyzer.analyze(sensor_data)
            
            # Store analysis results in database
            self._store_analysis_results(analysis_results)
            
            # PLAN: Select appropriate action plans
            logger.info("\n[3] PLAN Phase")
            selected_plans = self.planner.select_plans(analysis_results)
            
            # Store plan selections in database
            self._store_plan_selections(selected_plans)
            
            # EXECUTE: Execute selected plans
            logger.info("\n[4] EXECUTE Phase")
            if selected_plans:
                execution_results = self.executor.execute(selected_plans)
                
                # Store execution results
                self._store_execution_results(execution_results)
            else:
                logger.info("No plans to execute - all systems normal")
            
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Cycle #{self.cycle_count} completed successfully")
            logger.info(f"{'=' * 60}")
        
        except Exception as e:
            logger.error(f"Error in MAPE-K cycle: {e}", exc_info=True)
    
    def _store_analysis_results(self, analysis_results):
        """Store analysis results in database"""
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            for result in analysis_results:
                node_id = result['node_id']
                state = result['state']
                violations = result.get('violations', 0)
                total_params = result.get('total_params', 0)
                
                cur.execute("""
                    INSERT INTO "analyze" (node_id, result, state, timestamp)
                    VALUES (%s, %s, %s, NOW())
                """, (node_id, str(result), state))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Stored {len(analysis_results)} analysis results")
        
        except Exception as e:
            logger.error(f"Error storing analysis results: {e}")
    
    def _store_plan_selections(self, selected_plans):
        """Store plan selections in database"""
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            for plan_item in selected_plans:
                node_id = plan_item['node_id']
                plan_code = plan_item['plan']['code']
                
                cur.execute("""
                    INSERT INTO plan_selection (node_id, plan_code, timestamp)
                    VALUES (%s, %s, NOW())
                """, (node_id, plan_code))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Stored {len(selected_plans)} plan selections")
        
        except Exception as e:
            logger.error(f"Error storing plan selections: {e}")
    
    def _store_execution_results(self, execution_results):
        """Store execution results in database"""
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            for result in execution_results:
                node_id = result['node_id']
                plan_code = result['plan_code']
                status = result['status']
                message = result.get('message', '')
                
                cur.execute("""
                    INSERT INTO execution (node_id, plan_code, status, message, timestamp)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (node_id, plan_code, status, message))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Stored {len(execution_results)} execution results")
        
        except Exception as e:
            logger.error(f"Error storing execution results: {e}")
    
    def run(self, interval=60):
        """Run MAPE-K loop continuously"""
        logger.info(f"\nStarting MAPE-K loop (interval: {interval} seconds)")
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.run_cycle()
                
                logger.info(f"\nWaiting {interval} seconds until next cycle...")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("\n\nMAPE-K loop stopped by user")
            logger.info(f"Total cycles completed: {self.cycle_count}")
        
        except Exception as e:
            logger.error(f"Fatal error in MAPE-K loop: {e}", exc_info=True)


if __name__ == "__main__":
    # Create and run the plain MAPE-K system
    mapek = PlainMAPEK()
    mapek.run(interval=60)  # Run every 60 seconds
