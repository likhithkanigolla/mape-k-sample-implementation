
try:
    import structlog
except ImportError:
    structlog = None
try:
    from prometheus_client import Counter, Histogram, Gauge
except ImportError:
    Counter = Histogram = Gauge = None

if Histogram:
    mape_loop_duration = Histogram('mape_loop_duration_seconds')
    sensor_readings_total = Counter('sensor_readings_total', ['node_id', 'sensor_type'])
    threshold_violations = Counter('threshold_violations_total', ['node_id', 'parameter'])
else:
    mape_loop_duration = sensor_readings_total = threshold_violations = None

if structlog:
    logger = structlog.get_logger()
else:
    import logging
    logger = logging.getLogger('MAPE-K System')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s:%(message)s')

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler('logs/mape_k_system.log')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
