import os
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class Config:
    db_host: str = os.getenv('DB_HOST', 'localhost')
    db_name: str = os.getenv('DB_NAME', 'mapek_dt')
    db_user: str = os.getenv('DB_USER', 'postgres')
    db_pass: str = os.getenv('DB_PASS', 'postgres')
    loop_interval: int = int(os.getenv('LOOP_INTERVAL', '60'))
    node_ips: Optional[Dict[str, str]] = None  # Load from DB or config file

config = Config()
