"""
Usage:
    TM1Backup <servername> <source> <destination> <logdir> [options]
    TM1Backup (-h | --version)

Arguments:
    <servername>    TM1 Instance Name
    <source>        TM1 Database Location
    <destination>   Location to place backup files
    <logdir>        Location of TM1 Log files

Options:
    -f              Backup Feeder files
    -k <kn>         Keep <kn> number of backup files
    -l <ln>         Keep <ln> days of Log files
    -z              Use ZIP Format
    -h              Show this screen
    --version       Show Version information
© 2022 Application Consulting Group, Inc.
"""
# pyinstaller --onefile -i .\ACG.ico -n TM1Backup --add-binary=".\files\7z.exe;." --add-binary=".\files\7z.dll;." .\tm1backup.py
import os
import sys
import time

from docopt import docopt

from backup_service import BackupService

APP_NAME = 'TM1Backup'
APP_VERSION = "6.1"

if getattr(sys, 'frozen', False):
    BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_PATH = r'.\files'


def main(args: dict) -> bool:
    try:
        server = args.get("<servername>")
        source = args.get("<source>")
        destination = args.get("<destination>")
        logdir = args.get("<logdir>")
        seven = os.path.join(BASE_PATH, '7z.exe')
        feeders = args.get("-f")
        keep = args.get("-k")
        logs = args.get("-l")
        _zip = args.get("-z")
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
            'feeders': feeders,
            "zip": _zip
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
        print(v)
        return False


if __name__ == "__main__":
    start_time = time.perf_counter()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}\nVersion: {APP_VERSION}\n© 2022 Application Consulting Group, Inc.")
    success = main(cmd_args)
    if success:
        end_time = time.perf_counter()
        print(f"Backup complete in {round(end_time - start_time, 2)} seconds.")
    else:
        print("Errors occurred during backup routine. See logs")
        raise SystemExit
