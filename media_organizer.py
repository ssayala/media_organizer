import os
import shutil
import datetime
from pathlib import Path
from collections import Counter, defaultdict
from PIL import Image
from PIL.ExifTags import TAGS
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_mime_type(file_path):
    import subprocess
    try:
        result = subprocess.run(['file', '--mime-type', '-b', str(file_path)], 
                               capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception:
        return "unknown/unknown"

def get_safe_path(target_file_path):
    if not target_file_path.exists():
        return target_file_path
    
    base = target_file_path.stem
    suffix = target_file_path.suffix
    parent = target_file_path.parent
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    
    counter = 1
    while True:
        new_name = f"{base}_{date_str}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def get_photo_date(file_path):
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return None
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == 'DateTimeOriginal':
                    return datetime.datetime.strptime(value[:19], '%Y:%m:%d %H:%M:%S')
    except Exception:
        pass
    return None

def get_video_date(file_path):
    try:
        parser = createParser(str(file_path))
        if not parser:
            return None
        with parser:
            metadata = extractMetadata(parser)
            if metadata and metadata.has('creation_date'):
                value = metadata.get('creation_date')
                if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
                    value = datetime.datetime(value.year, value.month, value.day)
                return value
    except Exception:
        pass
    return None

def run_task(source_dir, target_dir, mode="organize"):
    source_path = Path(source_dir).resolve()
    target_path = Path(target_dir).resolve() if target_dir else None
    
    # Stats structure
    stats = {
        "Photos": {"count": Counter(), "size": defaultdict(int)},
        "Videos": {"count": Counter(), "size": defaultdict(int)},
        "Non-Media": {"count": Counter(), "size": defaultdict(int)},
        "totals": {
            "Photos": {"count": 0, "size": 0},
            "Videos": {"count": 0, "size": 0},
            "Non-Media": {"count": 0, "size": 0}
        },
        "moved": [],
        "errors": []
    }

    print(f"Scanning {source_path}...")

    for file_path in source_path.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Skip target if inside source or the log file
        if (target_path and target_path in file_path.parents) or file_path == target_path:
            continue
        if file_path.name == "organization_log.txt":
            continue

        file_size = file_path.stat().st_size
        mime = get_mime_type(file_path)
        ext = file_path.suffix.lower() or ".no_ext"
        
        # Smart detection
        is_photo = mime.startswith('image/') or ext in ['.raw', '.arw', '.cr2', '.nef', '.dng', '.heic']
        is_video = mime.startswith('video/') or ext in ['.mkv', '.mov', '.mp4', '.avi', '.3gp']

        if is_photo:
            category = "Photos"
        elif is_video:
            category = "Videos"
        else:
            category = "Non-Media"

        # Update stats
        stats["totals"][category]["count"] += 1
        stats["totals"][category]["size"] += file_size
        stats[category]["count"][ext] += 1
        stats[category]["size"][ext] += file_size

        if mode == "report":
            continue

        # Handle organization/dry-run logic
        date = None
        if is_photo:
            date = get_photo_date(file_path)
        elif is_video:
            date = get_video_date(file_path)

        if category == "Non-Media":
            dest = target_path / "NonMedia" / file_path.relative_to(source_path)
        else:
            if date:
                year = str(date.year)
                month = f"{date.month:02d}"
                dest_dir = target_path / category / year / month
            else:
                dest_dir = target_path / "UnknownDate" / category
            dest = dest_dir / file_path.name

        if mode == "organize":
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest = get_safe_path(dest)
            try:
                shutil.move(str(file_path), str(dest))
                stats["moved"].append(f"{category}: {file_path.name} -> {dest}")
            except Exception as e:
                stats["errors"].append(f"Error moving {file_path}: {e}")
        elif mode == "dry-run":
            stats["moved"].append(f"[DRY RUN] {category}: {file_path.name} -> {dest}")

    return stats

if __name__ == "__main__":
    import sys
    args = sys.argv
    if len(args) < 2:
        print("Usage:")
        print("  Report only:    python3 media_organizer.py <source_folder> --report-only")
        print("  Organize files: python3 media_organizer.py <source_folder> <target_folder>")
        print("  Dry run move:   python3 media_organizer.py <source_folder> <target_folder> --dry-run")
        sys.exit(1)

    # Separate positional args from flags so flags are never captured as paths
    positional = [a for a in args[1:] if not a.startswith('--')]
    src = positional[0] if positional else None

    # Determine mode
    if "--report-only" in args:
        mode = "report"
        dst = None
    elif "--dry-run" in args:
        mode = "dry-run"
        dst = positional[1] if len(positional) > 1 else None
    else:
        mode = "organize"
        dst = positional[1] if len(positional) > 1 else None

    if not os.path.exists(src):
        print(f"Source directory {src} does not exist.")
        sys.exit(1)

    if mode != "report" and not dst:
        print("Error: Target directory is required for organization/dry-run.")
        sys.exit(1)

    res = run_task(src, dst, mode)
    
    print(f"\n--- {'DETAILED REPORT' if mode == 'report' else 'SUMMARY REPORT'} ---")
    if mode == "dry-run":
        print("NOTE: This was a DRY RUN. No files were moved.")
    
    for cat in ["Photos", "Videos", "Non-Media"]:
        total_cat_count = res['totals'][cat]['count']
        total_cat_size = format_size(res['totals'][cat]['size'])
        print(f"\n{cat.upper()} (Total: {total_cat_count} | Size: {total_cat_size})")
        
        # Sort by count
        for ext, count in res[cat]["count"].most_common():
            size_str = format_size(res[cat]["size"][ext])
            print(f"  {ext:10} : {count:5} files ({size_str})")

    if mode != "report":
        print(f"\nErrors encountered: {len(res['errors'])}")
        if res['errors']:
            print("\n--- Errors ---")
            for err in res['errors']:
                print(err)
        
        with open("organization_log.txt", "w") as f:
            for entry in res['moved']:
                f.write(entry + "\n")
        print(f"\nDetailed log written to organization_log.txt")
