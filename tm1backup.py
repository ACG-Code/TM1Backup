"""
Usage:
    TM1Backup <servername> <source> <destination> <logdir> <sevenzip> [options]
    TM1Backup (-h | --version)

Arguments:
    <servername>    TM1 Instance Name
    <source>        TM1 Database Location
    <destination>   Location to place backup files
    <logdir>        Location of TM1 Log files
    <sevenzip>      Location of 7-Zip Executable

Options:
    -f              Backup Feeder files
    -k <kn>         Keep <kn> number of backup files
    -l <ln>         Keep <ln> days of Log files
    -h              Show this screen
    --version       Show Version information
"""

import logging
import os
import time

from docopt import docopt

from backup_service import BackupService
from baselogger import logger, APP_NAME

APP_VERSION = "4.0"


def main(args: dict) -> bool:
    try:
        backup_dict = {}
        server = args.get("<servername>")
        source = args.get("<source>")
        destination = args.get("<destination>")
        logdir = args.get("<logdir>")
        seven = args.get("<sevenzip>")
        feeders = args.get("-f")
        keep = args.get("-k")
        logs = args.get("-l")
        if not os.path.exists(source):
            raise ValueError(f"Source Path '{source}' does not exist")
        if not os.path.exists(destination):
            raise ValueError(f"Destination path '{destination}' does not exist")
        if not os.path.exists(logdir):
            raise ValueError(f"TM1 Log DIR '{logdir}' does not exist")
        if not os.path.exists(seven):
            raise ValueError(f"7-Zip not located at '{seven}'")
        backup_dict = {
            'server': server,
            'source': source,
            'destination': destination,
            'logdir': logdir,
            'sevenzip': seven,
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
        else:
            backup_dict['keep'] = 1
            backup_dict['logs'] = -99
        bkp = BackupService(**backup_dict)
        bkp.backup()
        return True
    except ValueError as v:
        logging.info(v)
        return False


if __name__ == "__main__":
    start_time = time.perf_counter()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logger.info(f"Starting Backup.  Arguments received from CMD: {cmd_args}")
    success = main(cmd_args)
    if success:
        end_time = time.perf_counter()
        logger.info(f"Backup complete in {round(end_time - start_time, 2)} seconds.")
    else:
        logger.info("Errors occurred during backup routine. See logs")
        raise SystemExit
