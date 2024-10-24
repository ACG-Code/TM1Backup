# TM1Backup
TM1Backup utility for IBM Cognos TM1.

## Usage:

`TM1backup.exe <servername> <source directory> <backup destination> <log directory> [options]`

### Positional Arguments (required):

  `<servername>`        The name of the TM1 server.

  `<source directory>`      The source directory to backup.

  `<backup destination>`    The backup destination directory.

  `<log directory>`         The log directory.

### Options:

`-f`    include Feeder files

`-k <number> `  Keep <number> of backups

`-l <number>`   Log level (0-3)

`-z` Use ZIP format

`-h` Show this help message and exit

`--version` Show program's version number and exit