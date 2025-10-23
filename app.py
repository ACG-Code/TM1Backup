"""
TM1 Backup Service - Refactored

Usage:
    tm1backup <servername> <source> <destination> <logdir> [options]
    tm1backup (-h | --version)

Positional Arguments:
    <servername>    TM1 Instance Name
    <source>        TM1 Database Location
    <destination>   Location to place backup files
    <logdir>        Location of TM1 Log files

Options:
    -f              Backup Feeder files
    -k <kn>         Keep <kn> number of backup files [default: 1]
    -l <ln>         Keep <ln> days of Log files [default: -1]
    -z              Use ZIP Format (default is 7z)
    -h              Show this screen
    --version       Show Version information

© 2025 Application Consulting Group, Inc.
"""
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Tuple

from docopt import docopt

# Application configuration
APP_NAME = 'TM1Backup'
APP_VERSION = '7.0.0'
APP_YEAR = '2025'


class BackupError(Exception):
    """Custom exception for backup errors"""
    pass


def resolve_paths() -> Tuple[str, str, str]:
    """
    Resolve application paths for both frozen and non-frozen execution.

    Returns:
        Tuple of (app_path, base_path, log_file)
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable (PyInstaller)
        app_path = os.path.dirname(sys.executable)
        base_path = getattr(sys, '_MEIPASS', app_path)
    else:
        # Running as script
        app_path = os.path.abspath(os.path.dirname(__file__))
        base_path = os.path.join(app_path, 'files')

    log_file = os.path.join(app_path, f'{APP_NAME}.log')
    return app_path, base_path, log_file


def get_file_version(app_path: str) -> str:
    """
    Get version from app_version.txt file if it exists.

    Args:
        app_path: Path to application directory

    Returns:
        Version string or APP_VERSION constant
    """
    try:
        version_file = os.path.join(app_path, 'app_version.txt')
        if os.path.exists(version_file):
            with open(version_file, 'r') as file:
                for line in file:
                    match = re.search(r"FileVersion',\s*'([\d.]+)'", line)
                    if match:
                        return match.group(1)
    except Exception:
        pass
    return APP_VERSION


def get_year(app_path: str) -> str:
    """
    Get copyright year from app_year.txt file if it exists.

    Args:
        app_path: Path to application directory

    Returns:
        Year string or APP_YEAR constant
    """
    try:
        year_file = os.path.join(app_path, 'app_year.txt')
        if os.path.exists(year_file):
            with open(year_file, 'r') as file:
                year_str = file.read().strip()
                if year_str:
                    return year_str
    except Exception:
        pass
    return APP_YEAR


def setup_logging(log_file: str):
    """
    Setup logging with rotation and both file and console handlers.

    Args:
        log_file: Path to log file
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.handlers.clear()

    # File handler with rotation (keeps 7 days of logs)
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setFormatter(
        logging.Formatter(f'%(asctime)s - {APP_NAME} - %(levelname)s - %(message)s')
    )

    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(
        logging.Formatter(f'%(asctime)s - {APP_NAME} - %(levelname)s - %(message)s')
    )

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


class BackupService:
    """
    Backup Service for TM1 Database Backups using 7-Zip compression.
    """

    def __init__(
        self,
        server: str,
        source: str,
        destination: str,
        logdir: str,
        sevenzip: str,
        feeders: bool = False,
        keep: int = 1,
        logs: int = -1,
        zip_format: str = '7z'
    ):
        """
        Initialize the backup service.

        Args:
            server: TM1 server name
            source: Source directory to backup
            destination: Destination directory for backup files
            logdir: TM1 log directory
            sevenzip: Path to 7-Zip executable
            feeders: Whether to include feeder files
            keep: Number of backup files to retain
            logs: Days of logs to retain (-1 means don't clean)
            zip_format: Compression format ('7z' or 'zip')
        """
        self.server = server
        self.source = source
        self.destination = destination
        self.logdir = logdir
        self.sevenzip = sevenzip
        self.feeders = feeders
        self.keep = keep
        self.logs = logs
        self.zip_format = zip_format

        # Generate timestamp
        self.timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        # Create backup filename
        self.zipfile = os.path.join(
            self.destination,
            f'{self.server}_Backup_{self.timestamp}.{self.zip_format}'
        )

        # Build 7-Zip command
        self._build_command()

        # Log configuration
        self._log_configuration()

    def _build_command(self):
        """Build the 7-Zip command based on configuration."""
        base_cmd = [
            self.sevenzip,
            'a',  # Add to archive
            self.zipfile,
            f'-t{self.zip_format}',  # Archive type
            '-mmt',  # Multi-threading
            '-mx=5',  # Compression level (5 = normal)
        ]

        if not self.feeders:
            base_cmd.append('-xr!*.FEEDERS')  # Exclude feeder files

        base_cmd.extend(['--', self.source])

        self.cmd = base_cmd

    def _log_configuration(self):
        """Log the backup configuration."""
        logging.info(f"Server name: {self.server}")
        logging.info(f"Source path: {self.source}")
        logging.info(f"Destination path: {self.destination}")
        logging.info(f"Logging path: {self.logdir}")
        logging.info(f"7-Zip located at: {self.sevenzip}")
        logging.info(f"Backup format: {self.zip_format}")

        if self.feeders:
            logging.info("Feeder files will be included in backup")
        else:
            logging.info("Feeder files will be excluded from backup")

        if self.keep > 0:
            logging.info(f"Backup file retention: {self.keep} files")

        if self.logs > 0:
            logging.info(f"Log file retention: {self.logs} days")

    def backup(self) -> bool:
        """
        Perform the backup operation.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logging.info(f"Starting backup of '{self.source}'")
            logging.info(f"Backup file: {self.zipfile}")

            # Execute 7-Zip command
            result = subprocess.run(
                self.cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )

            if result.returncode != 0:
                logging.error(f"7-Zip failed with return code {result.returncode}")
                if result.stderr:
                    logging.error(f"Error output: {result.stderr}")
                return False

            logging.info("Backup compression completed successfully")

            # Verify backup file was created
            if not os.path.exists(self.zipfile):
                logging.error(f"Backup file was not created: {self.zipfile}")
                return False

            file_size = os.path.getsize(self.zipfile) / (1024 * 1024)  # Size in MB
            logging.info(f"Backup file size: {file_size:.2f} MB")

            # Clean old backups if configured
            if self.keep > 0:
                self.clean_backups()

            # Clean old logs if configured
            if self.logs > 0:
                self.clean_logs()

            return True

        except subprocess.SubprocessError as e:
            logging.error(f"Subprocess error during backup: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during backup: {e}", exc_info=True)
            return False

    def clean_backups(self):
        """
        Clean old backup files, keeping only the specified number of most recent files.
        """
        try:
            logging.info(f"Cleaning backup directory: {self.destination}")

            # Get all backup files sorted by modification time (oldest first)
            backup_files = sorted(
                Path(self.destination).glob(f'{self.server}_Backup_*.{self.zip_format}'),
                key=lambda x: x.stat().st_mtime
            )

            # Calculate how many files to remove
            files_to_remove = len(backup_files) - self.keep

            if files_to_remove > 0:
                for file in backup_files[:files_to_remove]:
                    try:
                        logging.info(f"Removing old backup: {file.name}")
                        os.remove(file)
                    except OSError as e:
                        logging.error(f"Failed to remove {file.name}: {e}")

                logging.info(f"Backup cleanup complete - removed {files_to_remove} file(s)")
            else:
                logging.info("No backup files to remove")

        except Exception as e:
            logging.error(f"Error during backup cleanup: {e}", exc_info=True)

    def clean_logs(self):
        """
        Clean old TM1 log files based on retention period.
        """
        try:
            logging.info(f"Cleaning TM1 log directory: {self.logdir}")

            cutoff_time = time.time() - (self.logs * 86400)  # Convert days to seconds
            removed_count = 0

            # Clean TM1ProcessError files
            for file in Path(self.logdir).glob('TM1ProcessError*.*'):
                try:
                    if file.stat().st_mtime < cutoff_time:
                        logging.info(f"Removing log file: {file.name}")
                        os.remove(file)
                        removed_count += 1
                except OSError as e:
                    logging.error(f"Failed to remove {file.name}: {e}")

            # Clean TM1S* log files (pattern: TM1S + 14 digits)
            for file in Path(self.logdir).glob('TM1S??????????????.*'):
                try:
                    if file.stat().st_mtime < cutoff_time:
                        logging.info(f"Removing log file: {file.name}")
                        os.remove(file)
                        removed_count += 1
                except OSError as e:
                    logging.error(f"Failed to remove {file.name}: {e}")

            logging.info(f"Log cleanup complete - removed {removed_count} file(s)")

        except Exception as e:
            logging.error(f"Error during log cleanup: {e}", exc_info=True)


def validate_paths(source: str, destination: str, logdir: str, sevenzip: str):
    """
    Validate that all required paths exist.

    Args:
        source: Source directory path
        destination: Destination directory path
        logdir: Log directory path
        sevenzip: 7-Zip executable path

    Raises:
        BackupError: If any path is invalid
    """
    if not os.path.exists(source):
        raise BackupError(f"Source path does not exist: {source}")

    if not os.path.isdir(source):
        raise BackupError(f"Source path is not a directory: {source}")

    if not os.path.exists(destination):
        raise BackupError(f"Destination path does not exist: {destination}")

    if not os.path.isdir(destination):
        raise BackupError(f"Destination path is not a directory: {destination}")

    if not os.path.exists(logdir):
        raise BackupError(f"TM1 log directory does not exist: {logdir}")

    if not os.path.isdir(logdir):
        raise BackupError(f"TM1 log path is not a directory: {logdir}")

    if not os.path.exists(sevenzip):
        raise BackupError(f"7-Zip executable not found: {sevenzip}")

    if not os.path.isfile(sevenzip):
        raise BackupError(f"7-Zip path is not a file: {sevenzip}")


def main(args: dict, base_path: str) -> bool:
    """
    Main execution function.

    Args:
        args: Parsed command-line arguments
        base_path: Base path for resources

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract arguments
        server = args['<servername>']
        source = args['<source>']
        destination = args['<destination>']
        logdir = args['<logdir>']
        feeders = args['-f']
        keep = int(args['-k']) if args['-k'] else 1
        logs = int(args['-l']) if args['-l'] else -1
        zip_format = 'zip' if args['-z'] else '7z'

        # Locate 7-Zip
        sevenzip = os.path.join(base_path, '7z.exe')

        # Validate all paths
        validate_paths(source, destination, logdir, sevenzip)

        # Create backup service
        backup_service = BackupService(
            server=server,
            source=source,
            destination=destination,
            logdir=logdir,
            sevenzip=sevenzip,
            feeders=feeders,
            keep=keep,
            logs=logs,
            zip_format=zip_format
        )

        # Perform backup
        success = backup_service.backup()

        if success:
            logging.info("Backup operation completed successfully")
        else:
            logging.error("Backup operation failed")

        return success

    except BackupError as e:
        logging.error(f"Backup error: {e}")
        return False
    except ValueError as e:
        logging.error(f"Invalid argument: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    try:
        start_time = time.perf_counter()

        # Setup paths and logging
        app_path, base_path, log_file = resolve_paths()
        version = get_file_version(app_path)
        year = get_year(app_path)
        setup_logging(log_file)

        # Log startup info
        logging.info(f"{APP_NAME} Version: {version} | © {year} Application Consulting Group, Inc.")

        # Create copyright string for docopt
        copyright_text = f"{APP_NAME}\nVersion: {version}\n© {year} Application Consulting Group, Inc."

        cmd_args = docopt(__doc__, version=copyright_text)

        success = main(cmd_args, base_path)

        if success:
            end_time = time.perf_counter()
            logging.info(f"Finished successfully in {round(end_time - start_time, 2)} seconds.")
            sys.exit(0)
        else:
            logging.error("Backup failed.")
            sys.exit(1)

    except KeyboardInterrupt:
        logging.info("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)