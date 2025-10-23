"""
Unit tests for TM1 Backup Service (app.py)

Run tests with:
    pytest test_app.py -v
    pytest test_app.py -v --cov=app --cov-report=html
"""

import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

import pytest

# Import the module to test
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import app


class TestPathResolution:
    """Test path resolution functionality."""

    def test_resolve_paths_frozen_app(self):
        """Test path resolution for frozen (compiled) application."""
        with patch.object(sys, 'frozen', True, create=True):
            with patch.object(sys, 'executable', r'C:\Apps\TM1Backup.exe'):
                app_path, base_path, log_file = app.resolve_paths()

                assert app_path == r'C:\Apps'
                assert log_file == r'C:\Apps\TM1Backup.log'

    def test_resolve_paths_script(self):
        """Test path resolution for script execution."""
        with patch.object(sys, 'frozen', False, create=True):
            app_path, base_path, log_file = app.resolve_paths()

            assert os.path.isabs(app_path)
            assert log_file.endswith('TM1Backup.log')


class TestVersionAndYearRetrieval:
    """Test version and year retrieval functions."""

    def test_get_file_version_exists(self, tmp_path):
        """Test getting version from file when it exists."""
        version_file = tmp_path / 'app_version.txt'
        version_file.write_text("FileVersion', '7.2.3'")

        version = app.get_file_version(str(tmp_path))
        assert version == '7.2.3'

    def test_get_file_version_missing(self, tmp_path):
        """Test getting version when file doesn't exist."""
        version = app.get_file_version(str(tmp_path))
        assert version == app.APP_VERSION

    def test_get_file_version_invalid_format(self, tmp_path):
        """Test getting version with invalid file format."""
        version_file = tmp_path / 'app_version.txt'
        version_file.write_text("Invalid content")

        version = app.get_file_version(str(tmp_path))
        assert version == app.APP_VERSION

    def test_get_year_exists(self, tmp_path):
        """Test getting year from file when it exists."""
        year_file = tmp_path / 'app_year.txt'
        year_file.write_text("2025")

        year = app.get_year(str(tmp_path))
        assert year == '2025'

    def test_get_year_missing(self, tmp_path):
        """Test getting year when file doesn't exist."""
        year = app.get_year(str(tmp_path))
        assert year == app.APP_YEAR

    def test_get_year_empty(self, tmp_path):
        """Test getting year with empty file."""
        year_file = tmp_path / 'app_year.txt'
        year_file.write_text("")

        year = app.get_year(str(tmp_path))
        assert year == app.APP_YEAR


class TestBackupError:
    """Test custom BackupError exception."""

    def test_backup_error_raised(self):
        """Test that BackupError can be raised and caught."""
        with pytest.raises(app.BackupError) as exc_info:
            raise app.BackupError("Test error message")

        assert "Test error message" in str(exc_info.value)


class TestPathValidation:
    """Test path validation functionality."""

    def test_validate_paths_all_valid(self, tmp_path):
        """Test validation when all paths are valid."""
        source = tmp_path / "source"
        source.mkdir()
        destination = tmp_path / "destination"
        destination.mkdir()
        logdir = tmp_path / "logs"
        logdir.mkdir()
        sevenzip = tmp_path / "7z.exe"
        sevenzip.write_text("dummy")

        # Should not raise any exception
        app.validate_paths(
            str(source),
            str(destination),
            str(logdir),
            str(sevenzip)
        )

    def test_validate_paths_source_missing(self, tmp_path):
        """Test validation when source path doesn't exist."""
        with pytest.raises(app.BackupError) as exc_info:
            app.validate_paths(
                str(tmp_path / "nonexistent"),
                str(tmp_path),
                str(tmp_path),
                str(tmp_path / "7z.exe")
            )
        assert "Source path does not exist" in str(exc_info.value)

    def test_validate_paths_source_not_directory(self, tmp_path):
        """Test validation when source is a file not directory."""
        source = tmp_path / "file.txt"
        source.write_text("test")

        with pytest.raises(app.BackupError) as exc_info:
            app.validate_paths(
                str(source),
                str(tmp_path),
                str(tmp_path),
                str(tmp_path / "7z.exe")
            )
        assert "Source path is not a directory" in str(exc_info.value)

    def test_validate_paths_destination_missing(self, tmp_path):
        """Test validation when destination doesn't exist."""
        source = tmp_path / "source"
        source.mkdir()

        with pytest.raises(app.BackupError) as exc_info:
            app.validate_paths(
                str(source),
                str(tmp_path / "nonexistent"),
                str(tmp_path),
                str(tmp_path / "7z.exe")
            )
        assert "Destination path does not exist" in str(exc_info.value)

    def test_validate_paths_logdir_missing(self, tmp_path):
        """Test validation when log directory doesn't exist."""
        source = tmp_path / "source"
        source.mkdir()
        dest = tmp_path / "dest"
        dest.mkdir()

        with pytest.raises(app.BackupError) as exc_info:
            app.validate_paths(
                str(source),
                str(dest),
                str(tmp_path / "nonexistent"),
                str(tmp_path / "7z.exe")
            )
        assert "TM1 log directory does not exist" in str(exc_info.value)

    def test_validate_paths_sevenzip_missing(self, tmp_path):
        """Test validation when 7-Zip executable doesn't exist."""
        source = tmp_path / "source"
        source.mkdir()

        with pytest.raises(app.BackupError) as exc_info:
            app.validate_paths(
                str(source),
                str(tmp_path),
                str(tmp_path),
                str(tmp_path / "7z.exe")
            )
        assert "7-Zip executable not found" in str(exc_info.value)


class TestBackupService:
    """Test BackupService class."""

    @pytest.fixture
    def mock_paths(self, tmp_path):
        """Create mock directory structure for testing."""
        source = tmp_path / "source"
        source.mkdir()
        destination = tmp_path / "destination"
        destination.mkdir()
        logdir = tmp_path / "logs"
        logdir.mkdir()
        sevenzip = tmp_path / "7z.exe"
        sevenzip.write_text("dummy")

        return {
            'source': str(source),
            'destination': str(destination),
            'logdir': str(logdir),
            'sevenzip': str(sevenzip)
        }

    def test_init_default_params(self, mock_paths):
        """Test BackupService initialization with default parameters."""
        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip']
        )

        assert service.server == 'TestServer'
        assert service.feeders is False
        assert service.keep == 1
        assert service.logs == -1
        assert service.zip_format == '7z'
        assert service.zipfile.endswith('.7z')
        assert 'TestServer_Backup_' in service.zipfile

    def test_init_custom_params(self, mock_paths):
        """Test BackupService initialization with custom parameters."""
        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip'],
            feeders=True,
            keep=5,
            logs=7,
            zip_format='zip'
        )

        assert service.feeders is True
        assert service.keep == 5
        assert service.logs == 7
        assert service.zip_format == 'zip'
        assert service.zipfile.endswith('.zip')

    def test_build_command_without_feeders(self, mock_paths):
        """Test command building without feeder files."""
        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip'],
            feeders=False
        )

        assert mock_paths['sevenzip'] in service.cmd
        assert 'a' in service.cmd  # Add command
        assert '-t7z' in service.cmd
        assert '-xr!*.FEEDERS' in service.cmd
        assert mock_paths['source'] in service.cmd

    def test_build_command_with_feeders(self, mock_paths):
        """Test command building with feeder files."""
        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip'],
            feeders=True
        )

        assert '-xr!*.FEEDERS' not in service.cmd

    def test_build_command_zip_format(self, mock_paths):
        """Test command building with ZIP format."""
        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip'],
            zip_format='zip'
        )

        assert '-tzip' in service.cmd

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_backup_success(self, mock_getsize, mock_exists, mock_run, mock_paths):
        """Test successful backup operation."""
        mock_run.return_value = Mock(returncode=0, stderr='')
        mock_exists.return_value = True
        mock_getsize.return_value = 1024 * 1024  # 1 MB

        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip']
        )

        result = service.backup()

        assert result is True
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_backup_7zip_failure(self, mock_run, mock_paths):
        """Test backup when 7-Zip fails."""
        mock_run.return_value = Mock(returncode=1, stderr='Error message')

        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip']
        )

        result = service.backup()

        assert result is False

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_backup_file_not_created(self, mock_exists, mock_run, mock_paths):
        """Test backup when file is not created."""
        mock_run.return_value = Mock(returncode=0, stderr='')
        mock_exists.return_value = False

        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip']
        )

        result = service.backup()

        assert result is False

    def test_clean_backups_removes_old_files(self, mock_paths):
        """Test cleanup of old backup files."""
        destination = Path(mock_paths['destination'])

        # Create multiple backup files with different timestamps
        for i in range(5):
            backup_file = destination / f"TestServer_Backup_202501{i:02d}120000.7z"
            backup_file.write_text("dummy")
            # Set different modification times
            os.utime(backup_file, (time.time() - (86400 * (5 - i)), time.time() - (86400 * (5 - i))))

        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip'],
            keep=2
        )

        service.clean_backups()

        # Should keep only 2 most recent files
        remaining_files = list(destination.glob('TestServer_Backup_*.7z'))
        assert len(remaining_files) == 2

    def test_clean_backups_keeps_all_if_under_limit(self, mock_paths):
        """Test cleanup doesn't remove files if under limit."""
        destination = Path(mock_paths['destination'])

        # Create only 2 backup files
        for i in range(2):
            backup_file = destination / f"TestServer_Backup_202501{i:02d}120000.7z"
            backup_file.write_text("dummy")

        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip'],
            keep=5
        )

        service.clean_backups()

        remaining_files = list(destination.glob('TestServer_Backup_*.7z'))
        assert len(remaining_files) == 2

    def test_clean_logs_removes_old_files(self, mock_paths):
        """Test cleanup of old TM1 log files."""
        logdir = Path(mock_paths['logdir'])

        # Create old log files
        old_time = time.time() - (86400 * 10)  # 10 days old

        old_error_log = logdir / "TM1ProcessError_20250101.log"
        old_error_log.write_text("error")
        os.utime(old_error_log, (old_time, old_time))

        old_server_log = logdir / "TM1S20250101120000.log"
        old_server_log.write_text("log")
        os.utime(old_server_log, (old_time, old_time))

        # Create recent log files
        recent_log = logdir / "TM1ProcessError_20250123.log"
        recent_log.write_text("recent")

        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip'],
            logs=7
        )

        service.clean_logs()

        # Old files should be removed, recent file should remain
        assert not old_error_log.exists()
        assert not old_server_log.exists()
        assert recent_log.exists()

    def test_clean_logs_keeps_recent_files(self, mock_paths):
        """Test cleanup keeps files within retention period."""
        logdir = Path(mock_paths['logdir'])

        # Create recent log files (2 days old)
        recent_time = time.time() - (86400 * 2)

        recent_log = logdir / "TM1ProcessError_20250122.log"
        recent_log.write_text("recent")
        os.utime(recent_log, (recent_time, recent_time))

        service = app.BackupService(
            server='TestServer',
            source=mock_paths['source'],
            destination=mock_paths['destination'],
            logdir=mock_paths['logdir'],
            sevenzip=mock_paths['sevenzip'],
            logs=7
        )

        service.clean_logs()

        # Recent file should still exist
        assert recent_log.exists()


class TestMainFunction:
    """Test main execution function."""

    @pytest.fixture
    def mock_args(self):
        """Create mock command-line arguments."""
        return {
            '<servername>': 'TestServer',
            '<source>': r'C:\TM1\Data',
            '<destination>': r'D:\Backups',
            '<logdir>': r'C:\TM1\Logs',
            '-f': False,
            '-k': '3',
            '-l': '7',
            '-z': False
        }

    @patch('app.BackupService')
    @patch('app.validate_paths')
    def test_main_success(self, mock_validate, mock_service_class, mock_args, tmp_path):
        """Test successful main execution."""
        mock_service = Mock()
        mock_service.backup.return_value = True
        mock_service_class.return_value = mock_service

        base_path = str(tmp_path)
        result = app.main(mock_args, base_path)

        assert result is True
        mock_validate.assert_called_once()
        mock_service.backup.assert_called_once()

    @patch('app.validate_paths')
    def test_main_validation_failure(self, mock_validate, mock_args, tmp_path):
        """Test main when path validation fails."""
        mock_validate.side_effect = app.BackupError("Invalid path")

        base_path = str(tmp_path)
        result = app.main(mock_args, base_path)

        assert result is False

    @patch('app.BackupService')
    @patch('app.validate_paths')
    def test_main_backup_failure(self, mock_validate, mock_service_class, mock_args, tmp_path):
        """Test main when backup fails."""
        mock_service = Mock()
        mock_service.backup.return_value = False
        mock_service_class.return_value = mock_service

        base_path = str(tmp_path)
        result = app.main(mock_args, base_path)

        assert result is False

    @patch('app.BackupService')
    @patch('app.validate_paths')
    def test_main_with_feeders(self, mock_validate, mock_service_class, mock_args, tmp_path):
        """Test main with feeders option enabled."""
        mock_args['-f'] = True
        mock_service = Mock()
        mock_service.backup.return_value = True
        mock_service_class.return_value = mock_service

        base_path = str(tmp_path)
        result = app.main(mock_args, base_path)

        # Check that BackupService was initialized with feeders=True
        call_kwargs = mock_service_class.call_args[1]
        assert call_kwargs['feeders'] is True

    @patch('app.BackupService')
    @patch('app.validate_paths')
    def test_main_with_zip_format(self, mock_validate, mock_service_class, mock_args, tmp_path):
        """Test main with ZIP format option."""
        mock_args['-z'] = True
        mock_service = Mock()
        mock_service.backup.return_value = True
        mock_service_class.return_value = mock_service

        base_path = str(tmp_path)
        result = app.main(mock_args, base_path)

        # Check that BackupService was initialized with zip_format='zip'
        call_kwargs = mock_service_class.call_args[1]
        assert call_kwargs['zip_format'] == 'zip'

    def test_main_invalid_keep_value(self, mock_args, tmp_path):
        """Test main with invalid keep value."""
        mock_args['-k'] = 'invalid'

        base_path = str(tmp_path)
        result = app.main(mock_args, base_path)

        assert result is False


class TestLogging:
    """Test logging setup."""

    def test_setup_logging_creates_handlers(self, tmp_path):
        """Test that logging setup creates both file and console handlers."""
        log_file = tmp_path / "test.log"

        app.setup_logging(str(log_file))

        logger = app.logging.getLogger()
        handlers = logger.handlers

        # Should have file and stream handlers
        assert len(handlers) >= 2
        assert log_file.exists()


class TestIntegration:
    """Integration tests for complete workflows."""

    @patch('subprocess.run')
    def test_full_backup_workflow(self, mock_run, tmp_path):
        """Test complete backup workflow from start to finish."""
        # Setup directories
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("data")

        destination = tmp_path / "destination"
        destination.mkdir()

        logdir = tmp_path / "logs"
        logdir.mkdir()

        sevenzip = tmp_path / "7z.exe"
        sevenzip.write_text("dummy")

        # Mock subprocess to simulate successful 7z execution
        mock_run.return_value = Mock(returncode=0, stderr='')

        # Create backup service
        service = app.BackupService(
            server='TestServer',
            source=str(source),
            destination=str(destination),
            logdir=str(logdir),
            sevenzip=str(sevenzip),
            keep=2
        )

        # Mock the file existence check after 7z runs
        with patch('os.path.exists') as mock_exists:
            with patch('os.path.getsize') as mock_getsize:
                mock_exists.return_value = True
                mock_getsize.return_value = 1024 * 1024

                result = service.backup()

        assert result is True
        mock_run.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])