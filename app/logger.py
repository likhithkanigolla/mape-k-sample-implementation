import logging

logging.basicConfig(
    filename='logs/mape_k_system.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

def get_logger():
    return logging.getLogger('MAPE-K System')
