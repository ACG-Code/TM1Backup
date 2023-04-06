import os
import re
import string
import subprocess
from datetime import datetime
from pathlib import Path

import arrow

from baselogger import logger


class LocalBackupService:
    """
    Backup Service for local backups
    """
    def __init__(self, **kwargs):
        self.server = kwargs.get('server')
        self.source = kwargs.get('source')
        self.destination = kwargs.get('destination')
        self.logdir = kwargs.get("logdir")
        try:
            self.keep = int(kwargs.get("keep"))
        except TypeError:
            self.keep = None
        self.feeders = kwargs.get('feeders')
        self.logs = kwargs.get('logs')
        try:
            self.logs = int(self.logs)
        except TypeError:
            self.logs = None

        if self.logs == -99:
            self.logs = None

        date = datetime.now()
        self.tmst = date.strftime('%Y%m%d%H%M%S')

        self.source = Path(f'"{self.source}"')
        self.zipfile = Path(fr'"{self.destination}\{self.server}_Backup_{self.tmst}.7z"')
        self.seven = self.find_file_in_all_drives('7z.exe')
        self.seven = Path(f'"{self.seven}"')

        # Output Directories
        logger.info(f"Server name: {self.server}")
        logger.info(f"Source path: {self.source}")
        logger.info(f"Destination path: {self.destination}")
        logger.info(f"7-zip located at: {self.seven}")
        logger.info(f"Zip file to be generated: {self.zipfile}")
        if self.feeders:
            logger.info("Feeder files will be backed up")
            self.cmd = fr'{self.seven} a {self.zipfile} -t7z -mmt -mx=1 -- {self.source}'
        else:
            logger.info("Feeder files will be ignored")
            self.cmd = fr'{self.seven} a {self.zipfile} -mmt -mx=1 -xr!*FEEDERS -- {self.source}'
        logger.info(f"{self.cmd}")
        if self.keep:
            logger.info(f"Backup file retention {self.keep}")
        if self.logs:
            logger.info(f"Log file retention {self.logs} days")

    @staticmethod
    def clean_dir(path: str, days: int) -> None:
        """
        Cleans backup destination directory is needed
        :param path: Str path of Backup Destination
        :param days: Number of files to keep
        :return: None
        """
        logger.info(f"Beginning clean of '{path}'")
        for file in sorted(Path(path).glob('*.*'))[:-days]:
            logger.info(f"Removing {file}")
            os.remove(file)
        logger.info("Cleaning complete")

    @staticmethod
    def clean_logs(logdir: str, log_days: int) -> None:
        """
        Clean log directory if needed
        :param logdir: Log directory (STR)
        :param log_days: Number of days of log files to retain
        :return: None
        """
        logger.info(f"Beginning clean of {logdir}")
        log_days = int(log_days)
        rm_date = arrow.now().shift(days=-log_days)
        for file in Path(logdir).glob('TM1ProcessError*.*'):
            file_dt = arrow.get(file.stat().st_mtime)
            if file_dt <= rm_date:
                logger.info(f"Removing {file}")
                os.remove(file)
        for file in Path(logdir).glob('TM1S??????????????.*'):
            file_dt = arrow.get(file.stat().st_mtime)
            if file_dt <= rm_date:
                logger.info(f"Removing {file}")
                os.remove(file)
        logger.info("Log cleaning complete")

    def find_file(self, root_dir: str, rex: re) -> os.path or None:
        """

        :param root_dir: Directory to be search (STR)
        :param rex: Compiled RE object representation of file
        :return: None
        """
        for root, dirs, files in os.walk(root_dir):
            for f in files:
                result = rex.search(f)
                if result:
                    return os.path.join(root, f)

    def find_file_in_all_drives(self, file: str) -> str:
        """
        Search all drives for a specific file
        :param file: file to be found
        :return: Str path of file
        """
        rex = re.compile(file)
        dl = string.ascii_uppercase
        for drive in dl:
            if os.path.exists('%s:' % drive):
                return self.find_file(''.join([str('%s:' % drive), '\\']), rex)

    def backup(self) -> None:
        """
        Main method to perform backup and call sub routines
        :return: None
        """
        logger.info(f"Beginning backup of {self.source}")
        no_window = 0X08000000
        subprocess.call(self.cmd, creationflags=no_window)
        if self.keep:
            self.clean_dir(path=self.destination, days=self.keep)
        if self.logs:
            self.clean_logs(logdir=self.logdir, log_days=self.logs)
