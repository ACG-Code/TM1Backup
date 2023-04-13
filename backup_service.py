import os
from datetime import datetime
from pathlib import Path
from py7zr import SevenZipFile, FILTER_LZMA2, PRESET_DEFAULT

import arrow

from baselogger import logger


class BackupService:
    """
    Backup Service for Cloud Backups
    """
    def __init__(self, **kwargs):
        self.server = kwargs.get("server")
        self.source = rf'{kwargs.get("source")}'
        self.destination = kwargs.get("destination")
        self.logdir = kwargs.get("logdir")
        self.keep = int(kwargs.get("keep"))
        self.logs = int(kwargs.get("logs"))

        date = datetime.now()
        self.tmst = date.strftime('%Y%m%d%H%M%S')

        self.zipfile = rf'{self.destination}\{self.server}_Backup_{self.tmst}.7z'

        # Output directories
        logger.info(f"Server name: {self.server}")
        logger.info(f"Source path: {self.source}")
        logger.info(f"Logging path: {self.logdir}")
        logger.info(f"Backup file to be generated: {self.zipfile}")

        if self.keep:
            logger.info(f"Backup file retention {self.keep}")
        if self.logs != -99:
            logger.info(f"Log file retention {self.logs}")

    def backup(self) -> None:
        """
        Main method to perform backup and call sub routines
        :return: None
        """
        logger.info(f"Backing up '{self.source}'")
        filters = [{'id': FILTER_LZMA2, 'preset': PRESET_DEFAULT}]
        with SevenZipFile(self.zipfile, 'w', filters=filters) as zipfile:
            zipfile.writeall(self.source, os.path.basename(self.source))
        if self.keep:
            self.clean_dir(path=self.destination, days=self.keep)
        if self.logs != -99:
            self.clean_logs(logdir=self.logdir, log_days=self.logs)

    @staticmethod
    def clean_dir(path: str, days: int) -> None:
        """

        :param path: Path of backup destination
        :param days: Number of files to keep
        :return: None
        """
        logger.info(f"Beginning clean of folder '{path}'")
        for file in sorted(Path(path).glob('*.*'))[:-int(days)]:
            logger.info(f"Removing {file}")
            os.remove(file)
        logger.info("Cleaning complete")

    @staticmethod
    def clean_logs(logdir: str, log_days: int) -> None:
        """
        Cleans TM1 Log directory if needed
        :param logdir: String path of logging directory
        :param log_days: Number of days worth of logs to keep
        :return: None
        """
        logger.info(f"Beginning clean of log dir '{logdir}")
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
