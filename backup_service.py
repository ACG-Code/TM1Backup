import os
import subprocess
from datetime import datetime
from pathlib import Path

import arrow
# pyinstaller --onefile -i .\ACG.ico -n TM1Backup --add-binary=".\files\7z.exe;." --add-binary=".\files\7z.dll;." .\tm1backup.py

class BackupService:
    """
    Backup Service for Cloud Backups
    """
    def __init__(self, **kwargs):
        self.server = kwargs.get("server")
        self.source = kwargs.get("source")
        self.destination = kwargs.get("destination")
        self.logdir = kwargs.get("logdir")
        self.seven = kwargs.get("sevenzip")
        self.feeders = kwargs.get("feeders")
        self.keep = int(kwargs.get("keep"))
        self.logs = int(kwargs.get("logs"))

        date = datetime.now()
        self.tmst = date.strftime('%Y%m%d%H%M%S')

        self.source = Path(f'"{self.source}"')
        self.zipfile = Path(f'"{self.destination}\{self.server}_Backup_{self.tmst}.7z"')
        # self.seven = Path(f'"{self.seven}"')

        # Output directories
        print(f"Server name: {self.server}")
        print(f"Source path: {self.source}")
        print(f"Logging path: {self.logdir}")
        print(f"7-zip located at {self.seven}")
        print(f"Backup file to be generated: {self.zipfile}")

        if self.feeders:
            print("Feeder files will be backed up")
            self.cmd = fr"{self.seven} a {self.zipfile} -t7Z -mmt -mx=1 -- {self.source}"
        else:
            self.cmd = fr"{self.seven} a {self.zipfile} -t7Z -mmt -mx=1 -xr!*.FEEDERS -- {self.source}"
        print(self.cmd)

        if self.keep:
            print(f"Backup file retention {self.keep}")
        if self.logs != -99:
            print(f"Log file retention {self.logs}")

    def backup(self) -> None:
        """
        Main method to perform backup and call sub routines
        :return: None
        """
        print(f"Backing up '{self.source}'")
        no_window = 0X08000000
        subprocess.call(self.cmd, creationflags=no_window)
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
        print(f"Beginning clean of folder '{path}'")
        for file in sorted(Path(path).glob('*.*'))[:-int(days)]:
            print(f"Removing {file}")
            os.remove(file)
        print("Cleaning complete")

    @staticmethod
    def clean_logs(logdir: str, log_days: int) -> None:
        """
        Cleans TM1 Log directory if needed
        :param logdir: String path of logging directory
        :param log_days: Number of days worth of logs to keep
        :return: None
        """
        print(f"Beginning clean of log dir '{logdir}")
        log_days = int(log_days)
        rm_date = arrow.now().shift(days=-log_days)
        for file in Path(logdir).glob('TM1ProcessError*.*'):
            file_dt = arrow.get(file.stat().st_mtime)
            if file_dt <= rm_date:
                print(f"Removing {file}")
                os.remove(file)
        for file in Path(logdir).glob('TM1S??????????????.*'):
            file_dt = arrow.get(file.stat().st_mtime)
            if file_dt <= rm_date:
                print(f"Removing {file}")
                os.remove(file)
        print("Log cleaning complete")
