# Media Organizer Script

A smart Python utility to recursively scan, identify, and organize photo and video collections. It uses magic numbers (MIME types) and metadata (EXIF/Media headers) to accurately categorize files, regardless of their extensions.

## Features

- **Smart Identification**: Uses `file` command magic numbers to distinguish between photos, videos, and other files.
- **Metadata-Driven**: Extracts "Date Taken" from photos and videos to organize them into `Year/Month` folders.
- **Safe Organization**: 
    - **No Overwrites**: If a file with the same name exists, it appends a timestamp and counter.
    - **Non-Media Separation**: Moves documents and other files to a separate `NonMedia` directory while preserving their relative structure.
- **Flexible Modes**:
    - **Report Only**: Get a breakdown of file counts and types without moving anything.
    - **Dry Run**: Preview exactly where files will be moved.
    - **Organize**: Perform the actual file movement.
- **Extensive Format Support**: Supports standard formats (JPG, PNG, MP4, MOV) and many RAW formats (ARW, CR2, NEF, HEIC).

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/media-organizer.git
   cd media-organizer
   ```

2. **Install dependencies**:
   This script requires Python 3.9+ and some external libraries.
   ```bash
   pip install -r requirements.txt
   ```

3. **System Requirement**:
   The script uses the system `file` command (standard on macOS and Linux).

## Usage

### Generate a Report
Scan your source folder and see a breakdown of all file types:
```bash
python3 media_organizer.py /path/to/source --report-only
```

### Preview Organization (Dry Run)
See how files would be moved and renamed without actually performing the operation:
```bash
python3 media_organizer.py /path/to/source /path/to/destination --dry-run
```

### Run Organization
Perform the move and reorganization:
```bash
python3 media_organizer.py /path/to/source /path/to/destination
```

## Output Structure

```text
destination/
├── Photos/
│   └── 2023/
│       └── 01/
│           └── photo1.jpg
├── Videos/
│   └── 2022/
│       └── 12/
│           └── video1.mp4
├── NonMedia/
│   └── documents/
│       └── report.pdf
└── UnknownDate/
    └── Photos/
        └── legacy_photo.jpg
```

## Logs
Every time you run the script (except in Report mode), a detailed log is generated in `organization_log.txt` showing exactly which files were moved and to where.
