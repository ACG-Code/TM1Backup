"""
Usage:
    TM1_backup <server> <source> <destination> <logdir> [options]
    TM1_backup (-h | --version)

Arguments:
    <server>            TM1 Instance Name
    <source>            TM1 Database location
    <destination>       Location to place backup files
    <logdir>            Location of TM1 Log files

Options:
    -f                  Include Feeder files
    -k <kn>             Keep <kn> number of Backup files
    -l <ln>             Keep <ln> days of logs
    -h                  Show this screen
    --version           Show Version Information
"""

import os
import time

from docopt import docopt

from baselogger import logger, APP_NAME
from local_backup_service import LocalBackupService

APP_VERSION = '4.1'


def main(args: dict) -> bool:
    """ Error checking and backup initiation"""
    try:
        backup_dict = {}
        server = args.get("<server>")
        source = args.get("<source>")
        destination = args.get("<destination>")
        logdir = args.get("<logdir>")
        feeders = args.get("-f")
        keep = args.get("-k")
        logs = args.get("-l")
        if not os.path.exists(source):
            raise ValueError(f"Source path '{source}' not found")
        if not os.path.exists(destination):
            raise ValueError(f"Destination path '{destination}' not found")
        if not os.path.exists(logdir):
            raise ValueError(f"Logging path '{logdir}' not found")
        backup_dict = {
            'server': server,
            'source': source,
            'destination': destination,
            'logdir': logdir,
            'feeders': feeders
        }
        if keep and logs:
            backup_dict['keep'] = keep
            backup_dict['logs'] = logs
        elif keep:
            backup_dict['keep'] = keep
            backup_dict['logs'] = -99
        elif logs:
            backup_dict['keep'] = 1
            backup_dict['logs'] = logs
        bkp = LocalBackupService(**backup_dict)
        bkp.backup()
        return True
    except ValueError as v:
        logger.info(v)
        return False


if __name__ == "__main__":
    start_time = time.perf_counter()
    cmd_args = docopt(__doc__, version=f"{APP_NAME} by ACGI, Version={APP_VERSION}")
    logger.info(f"Starting backup.  Arguments received from CMD: {cmd_args}")
    success = main(cmd_args)
    if success:
        end_time = time.perf_counter()
        logger.info(f"Backup complete in {round(end_time - start_time, 2)} seconds")
    else:
        logger.info("Errors occurred during backup routine.  See logs")
        raise SystemExit
