# TM1 Backup Service

A robust, automated backup utility for IBM Planning Analytics (TM1) databases. This tool provides reliable, compressed backups with intelligent retention management and log cleanup capabilities.

## Overview

TM1 Backup Service is a command-line utility designed to automate the backup process for TM1 databases. It uses 7-Zip compression to create efficient backup archives, manages backup retention automatically, and can clean up old TM1 log files to keep your environment tidy.

## Features

- **Automated Database Backup**: Creates compressed backups of TM1 database directories
- **Flexible Compression**: Supports both 7z (default) and ZIP formats
- **Feeder File Control**: Option to include or exclude feeder files from backups
- **Intelligent Retention**: Automatically manages backup files, keeping only the most recent N backups
- **Log File Cleanup**: Removes old TM1 log files based on configurable retention period
- **Timestamped Archives**: Each backup includes a timestamp for easy identification
- **Multi-threaded Compression**: Utilizes multi-threading for faster backup operations
- **Comprehensive Logging**: Detailed logging with automatic rotation (7-day retention)
- **Cross-platform**: Works on Windows (with bundled 7-Zip executable)

## Requirements

### For Running from Source
- Python 3.7 or higher
- Required Python packages:
  - `docopt` - Command-line argument parsing

### For Compiled Executable
- No Python installation required
- 7-Zip executable (7z.exe) must be in the same directory or in the `files` subdirectory

### System Requirements
- Windows operating system
- Sufficient disk space for backup files
- Read access to TM1 database directory
- Write access to backup destination directory

## Installation

### Option 1: Use Pre-compiled Executable (Recommended)
1. Download the latest release from the repository
2. Extract to your desired location
3. Ensure `7z.exe` is in the same directory or in a `files` subdirectory
4. Run from command line or Task Scheduler

### Option 2: Run from Source
1. Clone or download the repository
2. Install required packages:
   ```bash
   pip install docopt
   ```
3. Download 7-Zip and place `7z.exe` in a `files` subdirectory
4. Run using Python:
   ```bash
   python app.py <arguments>
   ```

## Usage

### Basic Syntax

```bash
tm1backup <servername> <source> <destination> <logdir> [options]
```

### Positional Arguments

| Argument | Description |
|----------|-------------|
| `<servername>` | TM1 instance name (used in backup filename) |
| `<source>` | Full path to TM1 database directory |
| `<destination>` | Directory where backup files will be stored |
| `<logdir>` | Full path to TM1 log directory |

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-f` | Include feeder files in backup | Excluded |
| `-k <kn>` | Keep most recent `kn` backup files | 1 |
| `-l <ln>` | Keep `ln` days of TM1 log files | -1 (disabled) |
| `-z` | Use ZIP format instead of 7z | 7z format |
| `-h` | Show help screen | - |
| `--version` | Show version information | - |

## Examples

### Example 1: Basic Backup
Create a backup with default settings (keeps 1 backup, excludes feeders, uses 7z format):

```bash
tm1backup SData "C:\TM1Data\SData" "D:\Backups\TM1" "C:\TM1Data\SData"
```

### Example 2: Keep Multiple Backups
Keep the 5 most recent backup files:

```bash
tm1backup SData "C:\TM1Data\SData" "D:\Backups\TM1" "C:\TM1Data\SData" -k 5
```

### Example 3: Include Feeder Files
Create backup including feeder files:

```bash
tm1backup SData "C:\TM1Data\SData" "D:\Backups\TM1" "C:\TM1Data\SData" -f
```

### Example 4: Clean Old Logs
Keep 7 days of TM1 log files, removing older ones:

```bash
tm1backup SData "C:\TM1Data\SData" "D:\Backups\TM1" "C:\TM1Data\SData" -l 7
```

### Example 5: Use ZIP Format
Create backup in ZIP format instead of 7z:

```bash
tm1backup SData "C:\TM1Data\SData" "D:\Backups\TM1" "C:\TM1Data\SData" -z
```

### Example 6: Complete Configuration
Keep 3 backups, include feeders, clean 14 days of logs:

```bash
tm1backup SData "C:\TM1Data\SData" "D:\Backups\TM1" "C:\TM1Data\SData" -f -k 3 -l 14
```

## Backup File Naming

Backup files are automatically named using the following pattern:

```
<servername>_Backup_<timestamp>.<format>
```

Example:
```
SData_Backup_20250123143052.7z
```

Where the timestamp format is: `YYYYMMDDHHmmSS`

## Scheduling Automated Backups

### Using Windows Task Scheduler

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, and press Enter

2. **Create a New Task**
   - Click "Create Task" (not "Create Basic Task")
   - Give it a name like "TM1 Daily Backup - SData"

3. **Configure General Tab**
   - Select "Run whether user is logged on or not"
   - Check "Run with highest privileges"

4. **Configure Triggers Tab**
   - Click "New"
   - Set schedule (e.g., Daily at 2:00 AM)
   - Ensure it's enabled

5. **Configure Actions Tab**
   - Click "New"
   - Action: "Start a program"
   - Program/script: Full path to `tm1backup.exe`
   - Add arguments: Your backup command arguments
   - Example arguments:
     ```
     SData "C:\TM1Data\SData" "D:\Backups\TM1" "C:\TM1Data\SData" -k 7 -l 14
     ```

6. **Configure Conditions Tab**
   - Uncheck "Start the task only if the computer is on AC power" (for laptops)

7. **Save the Task**
   - Enter credentials when prompted

### Example Batch File

You can also create a batch file for easier scheduling:

```batch
@echo off
cd /d "C:\Path\To\TM1Backup"
tm1backup.exe SData "C:\TM1Data\SData" "D:\Backups\TM1" "C:\TM1Data\SData" -k 7 -l 14
if errorlevel 1 (
    echo Backup failed! >> backup_errors.log
    exit /b 1
)
echo Backup completed successfully
exit /b 0
```

## Logging

The application maintains a log file (`TM1Backup.log`) in the same directory as the executable. The log includes:

- Backup operation start and completion times
- Configuration details for each backup
- File sizes of created backups
- Retention cleanup activities
- Any errors or warnings encountered

Logs are automatically rotated daily with 7 days of retention.

## Log File Cleanup

When the `-l` option is used with a value greater than 0, the tool will clean up old TM1 log files:

**Files cleaned:**
- `TM1ProcessError*.*` - All TM1 process error logs
- `TM1S??????????????.*` - TM1 server logs (14-digit timestamp pattern)

**Retention logic:**
- Files older than the specified number of days are removed
- More recent files are preserved
- Cleanup is performed after each successful backup

## Troubleshooting

### "Source path does not exist"
- Verify the TM1 database path is correct
- Ensure you have read permissions to the directory
- Check for typos in the path

### "7-Zip executable not found"
- Ensure `7z.exe` is in the same directory as the executable
- Or place it in a `files` subdirectory
- Verify the file name is exactly `7z.exe`

### "Destination path does not exist"
- Create the backup destination directory before running
- Verify you have write permissions to the directory

### Backup files not being cleaned up
- Verify the `-k` option is set with a value greater than 0
- Check that backup files follow the naming pattern `<servername>_Backup_*.<format>`
- Ensure the destination directory is writable

### Slow backup performance
- Consider using 7z format (default) instead of ZIP for better compression
- Check available disk space
- Verify no other processes are heavily accessing the source directory

## Best Practices

1. **Test your backup command manually** before scheduling it
2. **Monitor the log file** regularly for errors
3. **Verify backup files** can be extracted successfully
4. **Keep multiple backup copies** using the `-k` option (recommend 7-14 days)
5. **Store backups on a different drive** than the TM1 database for disaster recovery
6. **Schedule backups during low-usage periods** to minimize performance impact
7. **Test your restore procedure** periodically
8. **Clean up old logs** regularly using the `-l` option to save disk space

## File Size Considerations

### 7z Format (Default)
- **Pros**: Better compression ratio, smaller backup files
- **Cons**: Slightly longer compression time
- **Recommended for**: Most scenarios, especially with large databases

### ZIP Format
- **Pros**: Faster compression, universally compatible
- **Cons**: Larger backup files
- **Recommended for**: When backup time is more critical than storage space

### Feeder Files
- Including feeder files (`-f` option) can significantly increase backup size
- Only include feeders if you need to restore the exact rule compilation state
- Most restores work fine without feeder files (they will be regenerated)

## Exit Codes

The application returns the following exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Failure (check log for details) |
| 130 | User cancelled (Ctrl+C) |

These can be useful for monitoring in batch scripts or automation tools.

## Version History

**Version 7.0.0**
- Complete refactor with improved error handling
- Enhanced logging with rotation
- Better path validation
- Cleaner code structure with classes
- Improved documentation

## Support and Contributing

For issues, questions, or contributions, please contact Application Consulting Group, Inc.

## License

This project is licensed under the MIT License.

© 2025 Application Consulting Group, Inc.

```
MIT License

Copyright (c) 2025 Application Consulting Group, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Quick Reference Card

```bash
# Basic backup
tm1backup <server> <source> <dest> <logdir>

# Keep 7 backups
tm1backup <server> <source> <dest> <logdir> -k 7

# Include feeders
tm1backup <server> <source> <dest> <logdir> -f

# Clean 14 days of logs
tm1backup <server> <source> <dest> <logdir> -l 14

# Use ZIP format
tm1backup <server> <source> <dest> <logdir> -z

# Full example
tm1backup SData "C:\TM1\SData" "D:\Backup" "C:\TM1\SData" -f -k 7 -l 14
```