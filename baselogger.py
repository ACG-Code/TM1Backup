import logging
import os
import sys

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(__file__)

print(application_path)

APP_NAME = "TM1Backup"
FILENAME = APP_NAME + '.log'
LOG_FILE = os.path.join(application_path, FILENAME)

logger = logging

logging.basicConfig(
        filename=LOG_FILE,
        format="%(asctime)s - " + APP_NAME + " - %(levelname)s - %(message)s",
        level=logging.INFO
    )
logging.getLogger().addHandler((logging.StreamHandler(sys.stdout)))
