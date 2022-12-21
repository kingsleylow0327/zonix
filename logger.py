import logging

class Logger():
    
    def __init__(self, module) -> None:
        self.logger = logging.getLogger(module)
        logging.basicConfig(level=logging.INFO)
    
    def get_logger(self):
        return self.logger