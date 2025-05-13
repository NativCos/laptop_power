import os
import logging


_logger = logging.getLogger('laptop_power.config')
_logger.setLevel(logging.DEBUG)

class Config:
    dataBasePath = ':memory:'
    """env value = LAPTOPPOWER_DATABASE"""

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        if os.getenv('LAPTOPPOWER_DATABASE') is not None:
            self.dataBasePath = os.getenv('LAPTOPPOWER_DATABASE')
            _logger.info(f"Was set new data base: {self.dataBasePath}")
