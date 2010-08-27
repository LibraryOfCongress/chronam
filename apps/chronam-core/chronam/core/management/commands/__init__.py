import logging
import logging.config
import os

def configure_logging(config_file, log_file):
    if os.path.exists(config_file):
        logging.config.fileConfig(config_file)
    else:
        logging.basicConfig()
        logging.getLogger().setLevel(logging.INFO)
        _file_handler = logging.FileHandler(log_file)
        _formatter = logging.Formatter("""[%(asctime)s %(levelname)s %(name)s] %(message)s""")
        _file_handler.setFormatter(_formatter)
        logging.getLogger().addHandler(_file_handler)

