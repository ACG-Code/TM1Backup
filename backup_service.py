import os
import subprocess
from datetime import datetime
from pathlib import Path
import zipfile

import arrow


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
        self.ZIP = kwargs.get("zip")

        date = datetime.now()
        self.tmst = date.strftime('%Y%m%d%H%M%S')

        # self.source = Path(f'"{self.source}"')
        self.zipfile = Path(f'"{self.destination}\{self.server}_Backup_{self.tmst}.7z"')
        # self.seven = Path(f'"{self.seven}"')

        # Output directories
        print(f"Server name: {self.server}")
        print(f"Source path: {self.source}")
        print(f"Logging path: {self.logdir}")
        print(f"7-zip located at {self.seven}")

        if self.feeders:
            print("Feeder files will be backed up")
            self.cmd = fr"{self.seven} a {self.zipfile} -t7Z -mmt -mx=1 -- {self.source}"
        else:
            self.cmd = fr"{self.seven} a {self.zipfile} -t7Z -mmt -mx=1 -xr!*.FEEDERS -- {self.source}"

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
        if self.ZIP:
            print(fr"Backup file to be generated: {self.destination}\{self.server}_Backup_{self.tmst}.zip")
            self.zip_folder(fr"{self.destination}\{self.server}_Backup_{self.tmst}.zip", source_path=self.source)
        else:
            print(f"Backup file to be generated: {self.zipfile}")
            no_window = 0X08000000
            subprocess.call(self.cmd, creationflags=no_window)
        if self.keep:
            self.clean_dir(path=self.destination, days=self.keep)
        if self.logs != -99:
            self.clean_logs(logdir=self.logdir, log_days=self.logs)

    def zip_folder(self, output_file: str, source_path: str) -> None:
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(str(source_path)):
                for file in files:
                    if self.feeders is False:
                        if not file.endswith('.feeders'):
                            file_path = os.path.join(root, file)
                            archive_path = os.path.relpath(file_path, source_path)
                            zip_file.write(file_path, archive_path)
                    else:
                        file_path = os.path.join(root, file)
                        archive_path = os.path.relpath(file_path, source_path)
                        zip_file.write(file_path, archive_path)

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
