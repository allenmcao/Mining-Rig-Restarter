import logging
import sys
import os

# Setup logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '../rig_restarter.log')),
        logging.StreamHandler(sys.stdout)
    ]
)

# logger object named after module: https://docs.python.org/3/howto/logging.html#advanced-logging-tutorial
logger = logging.getLogger(__name__)