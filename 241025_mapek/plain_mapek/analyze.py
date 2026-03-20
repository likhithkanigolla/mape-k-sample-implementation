"""
Analyze component - Parameter-based analysis with knowledge base recording
Records individual parameter violations for targeted plan selection
"""
import math
from collections import defaultdict, deque

from logger import logger
from knowledge import get_db_conn, KnowledgeBase
from scenarios import make_scenario_event

class Analyzer:
    """Analyzer service to check sensor data against thresholds at parameter level"""
    
    def __init__(self):
        self.thresholds = self._load_thresholds()
        self.kb = KnowledgeBase()
        # Sliding windows for scenario detection across cycles.
        self.param_history = defaultdict(lambda: deque(maxlen=8))
        self.zero_streak = defaultdict(int)
        self.connectivity_history = defaultdict(lambda: deque(maxlen=8))
        self.age_history = defaultdict(lambda: deque(maxlen=8))
        logger.info("Analyzer service initialized (parameter-based)")
    
    def _load_thresholds(self):
        """Load thresholds from database"""
        thresholds = {}
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            cur.execute("SELECT parameter, min_value, max_value FROM thresholds")
            rows = cur.fetchall()
            
            for row in rows:
                parameter = row[0]
                min_val = row[1]
                max_val = row[2]
                thresholds[parameter] = {'min': min_val, 'max': max_val}
            
            cur.close()
            conn.close()
            
            logger.info(f"Loaded {len(thresholds)} thresholds")
            
        except Exception as e:
            logger.error(f"Error loading thresholds: {e}")
        
        return thresholds
    
    def _get_state_for_parameter(self, parameter, value, threshold):
        """Determine state for a specific parameter"""
        min_val = threshold['min']
        max_val = threshold['max']
        
        # Temperature states
        if parameter == 'temperature':
            if value > max_val:
                return 'HIGH_TEMPERATURE'
            elif value < min_val:
                return 'LOW_TEMPERATURE'
        
        # TDS states
        elif parameter in ['tds_voltage', 'compensated_tds']:
            if value > max_val:
                return 'HIGH_TDS'
            elif value < min_val:
                return 'LOW_TDS'
        
        # Water level states
        elif parameter == 'water_level':
            if value > max_val:
                return 'HIGH_WATER_LEVEL'
            elif value < min_val:
                return 'LOW_WATER_LEVEL'
        
        # Flow rate states
        elif parameter == 'flowrate':
            if value > max_val:
                return 'HIGH_FLOW'
            elif value < min_val:
                return 'LOW_FLOW'
        
        # Pressure states
        elif parameter == 'pressure':
            if value > max_val:
                return 'HIGH_PRESSURE'
            elif value < min_val:
                return 'LOW_PRESSURE'
        
        # Motor/power states
        elif parameter in ['current', 'voltage', 'frequency', 'power_factor']:
            if value > max_val:
                return f'HIGH_{parameter.upper()}'
            elif value < min_val:
                return f'LOW_{parameter.upper()}'
        
        return 'NORMAL'

    def _record_param_history(self, node_id, parameter, value):
        """Store numeric values for trend, pattern and drift detection."""
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return

        if not math.isfinite(numeric_value):
            return

        self.param_history[(node_id, parameter)].append(numeric_value)

        if abs(numeric_value) < 1e-9:
            self.zero_streak[(node_id, parameter)] += 1
        else:
            self.zero_streak[(node_id, parameter)] = 0

    def _is_sensor_param(self, parameter):
        """True for physical sensor metrics; false for ids/meta fields."""
        return parameter in self.thresholds

    def _detect_s1_drift(self, node_id, parameter, threshold):
        """S1: Sensor readings drift over time."""
        history = list(self.param_history[(node_id, parameter)])
        if len(history) < 5:
            return None

        deltas = [history[i] - history[i - 1] for i in range(1, len(history))]
        monotonic_inc = all(d > 0 for d in deltas)
        monotonic_dec = all(d < 0 for d in deltas)
        if not (monotonic_inc or monotonic_dec):
            return None

        trend_span = abs(history[-1] - history[0])
        threshold_span = abs(float(threshold['max']) - float(threshold['min']))
        if threshold_span <= 0:
            return None

        # Drift even before crossing bounds: >30% of allowable range in one window.
        if trend_span >= 0.30 * threshold_span:
            return make_scenario_event(
                code='S1',
                node_id=node_id,
                parameter=parameter,
                details={
                    'history': history,
                    'trend_span': round(trend_span, 3),
                    'threshold_span': round(threshold_span, 3),
                },
                severity='warning',
            )
        return None

    def _detect_s2_invalid_values(self, node_id, parameter, value):
        """S2: Sensor produces invalid values."""
        if value is None:
            return make_scenario_event(
                code='S2',
                node_id=node_id,
                parameter=parameter,
                details={'reason': 'missing_value'},
                severity='critical',
            )

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return make_scenario_event(
                code='S2',
                node_id=node_id,
                parameter=parameter,
                details={'reason': 'non_numeric', 'value': str(value)},
                severity='critical',
            )

        if not math.isfinite(numeric_value):
            return make_scenario_event(
                code='S2',
                node_id=node_id,
                parameter=parameter,
                details={'reason': 'nan_or_inf'},
                severity='critical',
            )

        if abs(numeric_value) > 1_000_000:
            return make_scenario_event(
                code='S2',
                node_id=node_id,
                parameter=parameter,
                details={'reason': 'outlier_magnitude', 'value': numeric_value},
                severity='critical',
            )

        # Most IoT values here are expected to be non-negative.
        if parameter not in ['temperature'] and numeric_value < 0:
            return make_scenario_event(
                code='S2',
                node_id=node_id,
                parameter=parameter,
                details={'reason': 'negative_not_allowed', 'value': numeric_value},
                severity='critical',
            )

        return None

    def _detect_s3_constant_zero(self, node_id, parameter):
        """S3: Sensor produces constant zero values."""
        streak = self.zero_streak[(node_id, parameter)]
        if streak >= 3:
            return make_scenario_event(
                code='S3',
                node_id=node_id,
                parameter=parameter,
                details={'zero_streak': streak},
                severity='critical',
            )
        return None

    def _detect_s9_pattern_deviation(self, node_id, parameter):
        """S9: Sensor behaviour deviates from expected pattern."""
        history = list(self.param_history[(node_id, parameter)])
        if len(history) < 6:
            return None

        baseline = history[:-1]
        latest = history[-1]
        mean = sum(baseline) / len(baseline)
        variance = sum((v - mean) ** 2 for v in baseline) / max(1, len(baseline))
        std_dev = math.sqrt(variance)
        if std_dev <= 0:
            return None

        z_score = abs(latest - mean) / std_dev
        if z_score >= 3.0:
            return make_scenario_event(
                code='S9',
                node_id=node_id,
                parameter=parameter,
                details={
                    'z_score': round(z_score, 3),
                    'latest': round(latest, 3),
                    'mean': round(mean, 3),
                    'std_dev': round(std_dev, 3),
                },
                severity='warning',
            )
        return None

    def _detect_connectivity_scenarios(self, node_id, monitor_meta):
        """Detect S4/S5/S6/S11 using monitor-derived connectivity metadata."""
        events = []
        is_missing = monitor_meta.get('is_data_missing', True)
        is_stale = monitor_meta.get('is_stale', True)
        data_age_seconds = monitor_meta.get('data_age_seconds')

        connected = not is_missing and not is_stale
        self.connectivity_history[node_id].append(connected)
        if data_age_seconds is not None:
            self.age_history[node_id].append(float(data_age_seconds))

        history = list(self.connectivity_history[node_id])
        if is_missing or is_stale:
            events.append(
                make_scenario_event(
                    code='S4',
                    node_id=node_id,
                    details={
                        'is_missing': is_missing,
                        'is_stale': is_stale,
                        'data_age_seconds': data_age_seconds,
                    },
                    severity='critical',
                )
            )

        if len(history) >= 4:
            transitions = sum(1 for i in range(1, len(history)) if history[i] != history[i - 1])

            if transitions >= 3:
                events.append(
                    make_scenario_event(
                        code='S5',
                        node_id=node_id,
                        details={'connectivity_transitions': transitions, 'history': history},
                        severity='warning',
                    )
                )

            if transitions >= 4:
                events.append(
                    make_scenario_event(
                        code='S6',
                        node_id=node_id,
                        details={'reconnect_count': transitions, 'history': history},
                        severity='warning',
                    )
                )

        # S11: sustained service failure (3 latest cycles disconnected).
        if len(history) >= 3 and all(not h for h in history[-3:]):
            events.append(
                make_scenario_event(
                    code='S11',
                    node_id=node_id,
                    details={'recent_connectivity': history[-3:]},
                    severity='critical',
                )
            )

        return events

    def _detect_s7_s8_resource_scenarios(self, node_id, sensor_data):
        """Detect S7/S8 using power/current/energy pressure proxies."""
        events = []

        current = sensor_data.get('current')
        power = sensor_data.get('power')
        energy = sensor_data.get('energy')

        # S7: memory/processing overload proxy based on sustained power/current stress.
        try:
            if current is not None and power is not None:
                current_max = self.thresholds.get('current', {}).get('max')
                power_max = self.thresholds.get('power', {}).get('max')
                if current_max and power_max:
                    if float(current) > 1.2 * float(current_max) and float(power) > 1.1 * float(power_max):
                        events.append(
                            make_scenario_event(
                                code='S7',
                                node_id=node_id,
                                parameter='current',
                                details={'current': current, 'power': power},
                                severity='critical',
                            )
                        )
        except (TypeError, ValueError):
            pass

        # S8: high energy utilization / rapid rise.
        try:
            if energy is not None:
                energy_max = self.thresholds.get('energy', {}).get('max')
                if energy_max and float(energy) >= 0.9 * float(energy_max):
                    events.append(
                        make_scenario_event(
                            code='S8',
                            node_id=node_id,
                            parameter='energy',
                            details={'energy': energy, 'energy_max': energy_max},
                            severity='warning',
                        )
                    )

                history = list(self.param_history[(node_id, 'energy')])
                if len(history) >= 2:
                    delta = history[-1] - history[-2]
                    if energy_max and delta > 0.12 * float(energy_max):
                        events.append(
                            make_scenario_event(
                                code='S8',
                                node_id=node_id,
                                parameter='energy',
                                details={'energy_delta': round(delta, 3)},
                                severity='warning',
                            )
                        )
        except (TypeError, ValueError):
            pass

        return events

    def _get_recent_execution_issues(self):
        """Load recent execution failures to detect S10 action failures."""
        failures_by_node = defaultdict(list)
        try:
            conn = get_db_conn()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT node_id, plan_code, status, message
                FROM execution
                WHERE timestamp > NOW() - INTERVAL '10 minutes'
                  AND status IN ('failed', 'error')
                ORDER BY timestamp DESC
                """
            )

            for node_id, plan_code, status, message in cur.fetchall():
                failures_by_node[node_id].append({
                    'plan_code': plan_code,
                    'status': status,
                    'message': message,
                })

            cur.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Analyzer: Could not load recent execution failures ({e})")

        return failures_by_node

    def _dedupe_scenarios(self, scenario_events):
        """Remove duplicate scenario events for same (code, parameter)."""
        seen = set()
        deduped = []
        for event in scenario_events:
            key = (event['code'], event.get('parameter'))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(event)
        return deduped
    
    def analyze(self, sensor_data_list):
        """
        Analyze sensor data against thresholds at parameter level
        Records individual parameter violations in knowledge base
        """
        analysis_results = []
        recent_failures = self._get_recent_execution_issues()
        
        for sensor_data in sensor_data_list:
            node_id = sensor_data.get('node_id')
            result = {'node_id': node_id}
            violations = 0
            total_params = 0
            violated_parameters = []  # Track which specific parameters are bad
            parameter_states = {}
            scenario_events = []

            monitor_meta = sensor_data.get('_monitor', {})
            scenario_events.extend(self._detect_connectivity_scenarios(node_id, monitor_meta))
            
            # Check each parameter against thresholds
            for param, value in sensor_data.items():
                if param in ['node_id', 'timestamp']:
                    continue

                if param.startswith('_'):
                    continue

                if not self._is_sensor_param(param):
                    continue

                invalid_event = self._detect_s2_invalid_values(node_id, param, value)
                if invalid_event:
                    scenario_events.append(invalid_event)
                
                # Handle missing data
                if value is None:
                    result[param] = 0  # Missing data is a violation
                    violations += 1
                    total_params += 1
                    violated_parameters.append(param)
                    parameter_states[param] = 'MISSING_DATA'
                    
                    # Record missing data issue
                    if param in self.thresholds:
                        threshold = self.thresholds[param]
                        self.kb.record_issue_detected(
                            node_id=node_id,
                            parameter=param,
                            problem_value=None,
                            threshold_min=threshold['min'],
                            threshold_max=threshold['max']
                        )
                        logger.warning(f"Missing data for {node_id}.{param}")
                    continue
                
                # Check if threshold exists for this parameter
                if param in self.thresholds:
                    threshold = self.thresholds[param]
                    min_val = threshold['min']
                    max_val = threshold['max']
                    
                    if min_val <= value <= max_val:
                        result[param] = 1  # Within threshold (good)
                        parameter_states[param] = 'NORMAL'
                    else:
                        result[param] = 0  # Outside threshold (bad)
                        violations += 1
                        violated_parameters.append(param)
                    
                    # ALWAYS verify plan effectiveness (whether fixed or still broken)
                    # This ensures we detect failures when plans don't work
                    self.kb.verify_plan_effectiveness(
                        node_id=node_id,
                        parameter=param,
                        current_value=value,
                        threshold_min=min_val,
                        threshold_max=max_val
                    )
                    
                    # If parameter is still violated, record it
                    if result[param] == 0:
                        # Get specific state for this parameter
                        state = self._get_state_for_parameter(param, value, threshold)
                        parameter_states[param] = state
                        
                        # Record this parameter violation in knowledge base
                        self.kb.record_issue_detected(
                            node_id=node_id,
                            parameter=param,
                            problem_value=value,
                            threshold_min=min_val,
                            threshold_max=max_val
                        )
                        
                        logger.warning(
                            f"Parameter violation: {node_id}.{param} = {value} "
                            f"(expected: {min_val}-{max_val}) → State: {state}"
                        )

                    # Keep rolling history for scenario detection.
                    self._record_param_history(node_id, param, value)

                    # S1: drift over time.
                    s1_event = self._detect_s1_drift(node_id, param, threshold)
                    if s1_event:
                        scenario_events.append(s1_event)

                    # S3: constant zero values.
                    s3_event = self._detect_s3_constant_zero(node_id, param)
                    if s3_event:
                        scenario_events.append(s3_event)

                    # S9: expected pattern deviation.
                    s9_event = self._detect_s9_pattern_deviation(node_id, param)
                    if s9_event:
                        scenario_events.append(s9_event)
                    
                    total_params += 1
                else:
                    # No threshold defined, assume good
                    result[param] = 1
                    total_params += 1
            
            # Determine overall state (for backward compatibility)
            if total_params == 0:
                result['state'] = 'unknown'
            elif violations == 0:
                result['state'] = 'normal'
            elif violations < total_params / 2:
                result['state'] = 'warning'
            else:
                result['state'] = 'critical'
            
            result['violations'] = violations
            result['total_params'] = total_params
            result['violated_parameters'] = violated_parameters  # NEW: List of specific parameters with issues
            result['parameter_states'] = parameter_states

            # S7/S8: resource pressure / power usage scenarios.
            scenario_events.extend(self._detect_s7_s8_resource_scenarios(node_id, sensor_data))

            # S10: action execution failed recently for this node.
            if recent_failures.get(node_id):
                scenario_events.append(
                    make_scenario_event(
                        code='S10',
                        node_id=node_id,
                        details={'recent_failures': recent_failures[node_id][:3]},
                        severity='critical',
                    )
                )

            scenario_events = self._dedupe_scenarios(scenario_events)
            result['scenario_events'] = scenario_events
            
            analysis_results.append(result)
            
            if violations > 0:
                logger.info(
                    f"Analyzer: {node_id} - State: {result['state']} "
                    f"({violations}/{total_params} violations in: {', '.join(violated_parameters)})"
                )
            else:
                logger.info(f"Analyzer: {node_id} - State: normal (all parameters OK)")

            if scenario_events:
                scenario_codes = ', '.join(event['code'] for event in scenario_events)
                logger.warning(f"Analyzer: {node_id} scenario triggers detected: {scenario_codes}")
        
        return analysis_results
