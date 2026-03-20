"""
Plan component - Parameter-based plan selection with escalation
Uses knowledge base to select best plan for each violated parameter
"""
from logger import logger
from knowledge import get_db_conn, KnowledgeBase
from scenarios import SCENARIO_CATALOG

class Planner:
    """Planner service to select appropriate action plans based on parameters"""
    
    def __init__(self):
        self.kb = KnowledgeBase()
        logger.info("Planner service initialized (parameter-based)")

        # Scenario severity ordering so critical adaptations are scheduled first.
        self.scenario_priority = {
            'S11': 1,
            'S10': 2,
            'S4': 3,
            'S2': 4,
            'S3': 5,
            'S7': 6,
            'S5': 7,
            'S6': 8,
            'S8': 9,
            'S9': 10,
            'S1': 11,
        }
    
    def _get_state_for_parameter(self, parameter, analysis_result):
        """
        Get the state for a specific parameter based on analysis result
        Returns the appropriate state string (HIGH_TEMPERATURE, LOW_TDS, etc.)
        """
        parameter_states = analysis_result.get('parameter_states', {})
        if parameter in parameter_states:
            return parameter_states[parameter]

        param_value = analysis_result.get(parameter)
        
        if param_value == 1:
            # Parameter is OK
            return 'NORMAL'
        
        # Parameter has a violation, need to determine if HIGH or LOW
        # This info should come from thresholds, but we can infer from parameter type
        
        # For now, we'll use a simple heuristic:
        # Temperature violations typically mean HIGH_TEMPERATURE
        # TDS violations typically mean HIGH_TDS or LOW_TDS (depends on actual value)
        # We need the actual sensor data to determine this properly
        
        # The analyzer should pass this information, but for now we'll default to common cases
        if parameter == 'temperature':
            return 'HIGH_TEMPERATURE'  # Most common case
        elif parameter in ['tds_voltage', 'compensated_tds']:
            return 'HIGH_TDS'  # Most common case
        elif parameter == 'water_level':
            return 'LOW_WATER_LEVEL'  # Most common case
        elif parameter == 'flowrate':
            return 'LOW_FLOW'  # Most common case
        elif parameter == 'pressure':
            return 'LOW_PRESSURE'  # Most common case
        elif parameter == 'current':
            return 'HIGH_CURRENT'  # Most common case - current overload
        elif parameter == 'voltage':
            return 'LOW_VOLTAGE'  # Most common case - voltage drop
        elif parameter == 'frequency':
            return 'LOW_FREQUENCY'  # Most common case - frequency drop
        elif parameter == 'power_factor':
            return 'LOW_POWER_FACTOR'  # Most common case - poor power factor
        elif parameter in ['power', 'energy']:
            # Power and energy are calculated values, typically indicate other issues
            # Skip these - they'll be fixed when voltage/current/frequency are fixed
            return 'NORMAL'  # Return NORMAL to skip plan selection for these
        
        return 'UNKNOWN'

    def _build_scenario_plan(self, scenario_event):
        """Build an executable plan from a detected scenario event."""
        scenario_code = scenario_event['code']
        scenario_info = SCENARIO_CATALOG.get(scenario_code, {})
        default_plan_code = scenario_info.get('default_plan_code', 'HANDLE_SCENARIO')
        adaptation = scenario_info.get('adaptation', 'Apply scenario-specific recovery')
        goal = scenario_info.get('goal', 'Stabilize system')

        return {
            'code': default_plan_code,
            'description': adaptation,
            'priority': self.scenario_priority.get(scenario_code, 99),
            'escalation_level': 1,
            'scenario_code': scenario_code,
            'adaptation_goal': goal,
        }
    
    def select_plans(self, analysis_results):
        """
        Select plans strictly from detected S1-S11 scenario events.
        Legacy parameter-based and NO_ACTION plan paths are intentionally disabled.
        """
        selected_plans = []
        
        for result in analysis_results:
            node_id = result.get('node_id')
            state = result.get('state', '')
            scenario_events = result.get('scenario_events', [])

            # Scenario-first planning: map S1-S11 detections to adaptation plans.
            if scenario_events:
                sorted_events = sorted(
                    scenario_events,
                    key=lambda event: self.scenario_priority.get(event['code'], 99),
                )
                for event in sorted_events:
                    scenario_plan = self._build_scenario_plan(event)
                    selected_plans.append({
                        'node_id': node_id,
                        'state': state,
                        'parameter': event.get('parameter'),
                        'scenario': event,
                        'plan': scenario_plan,
                    })

                    logger.info(
                        f"Planner: Scenario {event['code']} selected "
                        f"plan '{scenario_plan['code']}' for {node_id}"
                    )

            if not scenario_events:
                logger.info(
                    f"Planner: No S1-S11 scenario event for {node_id}; no plan selected"
                )
        
        return selected_plans
