
try:
    import structlog
except ImportError:
    structlog = None

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
