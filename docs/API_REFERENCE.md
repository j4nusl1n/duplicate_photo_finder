# API Reference - Duplicate Photo Finder

> Complete API documentation for all classes, functions, and methods in the duplicate photo finder project.

## Table of Contents

- [Classes](#classes)
  - [ImageMetadata](#imagemetadata)
- [Core Functions](#core-functions)
  - [Detection & Validation](#detection--validation)
  - [Metadata Extraction](#metadata-extraction)
  - [Processing & Management](#processing--management)
  - [Utility Functions](#utility-functions)
- [Command Line Interface](#command-line-interface)
- [Usage Examples](#usage-examples)

---

## Classes

### ImageMetadata

```python
@dataclass
class ImageMetadata:
    """Image metadata used for comparison."""
```

A dataclass that encapsulates all relevant metadata for an image file used in duplicate detection.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `path` | `Path` | Full file system path to the image |
| `file_size` | `int` | File size in bytes |
| `hash` | `Optional[str]` | SHA-256 hash of file content (None if calculation failed) |
| `camera_model` | `Optional[str]` | Camera model from EXIF data (None if unavailable) |
| `resolution` | `Optional[Tuple[int, int]]` | Image dimensions as (width, height) (None if unavailable) |

#### Methods

##### get_identifier()

```python
def get_identifier(self) -> Tuple:
    """Get a tuple that can identify this image for duplicate detection."""
```

**Returns:**
- `Tuple`: A tuple containing `(camera_model, hash, resolution, file_size)` used for grouping duplicates

**Usage:**
```python
metadata = ImageMetadata(path=Path("photo.jpg"), file_size=1024)
identifier = metadata.get_identifier()
# Returns: ("", "", (0, 0), 1024)
```

---

## Core Functions

### Detection & Validation

#### check_exiftool_exists()

```python
def check_exiftool_exists() -> bool:
    """Check if ExifTool is installed and available."""
```

Verifies ExifTool installation by running the version command.

**Returns:**
- `bool`: `True` if ExifTool is available, `False` otherwise

**Side Effects:**
- Logs ExifTool version if found
- Logs warning if not found

**Usage:**
```python
if check_exiftool_exists():
    print("ExifTool is available for RAW file processing")
```

---

### Metadata Extraction

#### get_camera_model_single()

```python
def get_camera_model_single(image_path: Path) -> Tuple[Path, Optional[str]]:
    """Process a single file with ExifTool to extract camera model."""
```

Extracts camera model information from image EXIF data using ExifTool.

**Parameters:**
- `image_path` (`Path`): Path to the image file

**Returns:**
- `Tuple[Path, Optional[str]]`: Original path and camera model (None if extraction failed)

**Timeout:** 30 seconds

**Error Handling:**
- Logs errors and returns None for camera model on failure
- Handles subprocess timeouts and ExifTool errors

#### get_image_resolution_exiftool()

```python
def get_image_resolution_exiftool(image_path: Path) -> Optional[Tuple[int, int]]:
    """Get the resolution of an image using ExifTool."""
```

Extracts image resolution using ExifTool, supporting multiple output formats.

**Parameters:**
- `image_path` (`Path`): Path to the image file

**Returns:**
- `Optional[Tuple[int, int]]`: Image dimensions as (width, height) or None if failed

**Supported Formats:**
- "WidthxHeight" (e.g., "1920x1080")
- "Width\nHeight" (separate lines)

**Timeout:** 30 seconds

#### get_image_resolution()

```python
def get_image_resolution(image_path: Path, exiftool_available: bool, force_exiftool: bool = False) -> Optional[Tuple[int, int]]:
    """Get the resolution of an image, using ExifTool for RAW files or when forced."""
```

Smart resolution extraction with fallback strategies and forced ExifTool support.

**Parameters:**
- `image_path` (`Path`): Path to the image file
- `exiftool_available` (`bool`): Whether ExifTool is available
- `force_exiftool` (`bool`): Force use of ExifTool for all image types (default: False)

**Returns:**
- `Optional[Tuple[int, int]]`: Image dimensions or None if failed

**Strategy:**
1. If `force_exiftool` is True: Always use ExifTool when available
2. For .ARW files: Use ExifTool if available
3. For standard formats: Try PIL first, fallback to ExifTool (unless forced)
4. Return None if all methods fail

**Supported Extensions:**
- RAW: `.arw`
- Standard: `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`, `.gif`, `.bmp`

#### calculate_image_hash()

```python
def calculate_image_hash(image_path: Path) -> Tuple[Path, Optional[str]]:
    """Calculate a hash for the image content."""
```

Generates SHA-256 hash of file content using chunked reading for memory efficiency.

**Parameters:**
- `image_path` (`Path`): Path to the image file

**Returns:**
- `Tuple[Path, Optional[str]]`: Original path and hex digest hash (None if failed)

**Memory Optimization:**
- Reads file in 4KB chunks to avoid loading large files entirely into memory
- Suitable for files of any size

#### get_file_size()

```python
def get_file_size(image_path: Path) -> int:
    """Get the file size in bytes."""
```

Retrieves file size using path statistics.

**Parameters:**
- `image_path` (`Path`): Path to the image file

**Returns:**
- `int`: File size in bytes (0 if error occurred)

---

### Processing & Management

#### process_single_image()

```python
def process_single_image(image_path: Path, exiftool_available: bool, force_exiftool: bool = False) -> Optional[ImageMetadata]:
    """Process a single image to extract all metadata."""
```

Comprehensive metadata extraction for a single image file with optional forced ExifTool usage.

**Parameters:**
- `image_path` (`Path`): Path to the image file
- `exiftool_available` (`bool`): Whether ExifTool is available for metadata extraction
- `force_exiftool` (`bool`): Force use of ExifTool for all metadata extraction (default: False)

**Returns:**
- `Optional[ImageMetadata]`: Complete metadata object or None if processing failed

**Process:**
1. Check file read permissions
2. Extract file size
3. Extract camera model (if ExifTool available)
4. Calculate file hash
5. Extract image resolution
6. Return ImageMetadata object

**Error Handling:**
- Returns None for files without read permission
- Logs all errors and continues processing

#### process_images_parallel()

```python
def process_images_parallel(directory: str, max_workers: Optional[int] = None, force_exiftool: bool = False) -> Dict[Tuple, List[ImageMetadata]]:
    """Process images in parallel using ThreadPoolExecutor."""
```

Main processing function that handles concurrent image analysis and duplicate detection with optional forced ExifTool usage.

**Parameters:**
- `directory` (`str`): Root directory to scan for images
- `max_workers` (`Optional[int]`): Maximum worker threads (default: `min(32, cpu_count() * 4)`)
- `force_exiftool` (`bool`): Force use of ExifTool for all metadata extraction (default: False)

**Returns:**
- `Dict[Tuple, List[ImageMetadata]]`: Dictionary mapping duplicate group identifiers to lists of duplicate images

**Performance:**
- Uses ThreadPoolExecutor for parallel processing
- Automatically detects ExifTool availability
- Scans recursively through all subdirectories

**Supported Extensions:**
- `.arw`, `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`, `.gif`, `.bmp`

#### remove_duplicate_files()

```python
def remove_duplicate_files(duplicates: Dict[Tuple, List[ImageMetadata]], auto_select_best: bool = False, group_by_group: bool = True, dest_dir: Optional[str] = None):
    """Remove duplicate files after confirmation, or move them to destination directory."""
```

Interactive duplicate file removal or relocation with multiple confirmation modes.

**Parameters:**
- `duplicates` (`Dict[Tuple, List[ImageMetadata]]`): Duplicate groups from `process_images_parallel()`
- `auto_select_best` (`bool`): Whether to automatically select highest quality file (default: False)
- `group_by_group` (`bool`): Whether to confirm each group separately (default: True)
- `dest_dir` (`Optional[str]`): Destination directory to move duplicates to instead of deleting (default: None)

**Features:**
- Interactive user confirmation
- Automatic quality-based selection
- File permission checking before deletion/moving
- Detailed statistics reporting
- Organized destination directory structure with group subdirectories
- Automatic filename conflict resolution

**Destination Directory Behavior:**
- Creates subdirectories based on camera model and hash for organization
- Handles filename conflicts by adding numeric suffixes
- Uses `shutil.move()` for safe file operations
- Creates destination directory structure automatically

**Safety:**
- Requires explicit user confirmation
- Checks write permissions before deletion/moving
- Provides detailed information about each duplicate group

---

### Utility Functions

#### format_file_size()

```python
def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
```

Converts byte count to human-readable format.

**Parameters:**
- `size_bytes` (`int`): File size in bytes

**Returns:**
- `str`: Formatted size string (e.g., "1.25 MB", "500.00 KB")

**Units:** B, KB, MB, GB

#### suggest_best_file()

```python
def suggest_best_file(duplicates: List[ImageMetadata]) -> int:
    """Suggest the best file to keep based on resolution and file size."""
```

Implements quality-based file selection algorithm.

**Parameters:**
- `duplicates` (`List[ImageMetadata]`): List of duplicate images to evaluate

**Returns:**
- `int`: Index of the recommended file to keep

**Algorithm:**
- Resolution score: `width × height` (90% weight)
- Size score: `file_size / 1MB` (10% weight)
- Returns index of highest scoring file

#### parse_arguments()

```python
def parse_arguments():
    """Parse command line arguments."""
```

Configures and parses command-line interface using argparse.

**Returns:**
- `argparse.Namespace`: Parsed command-line arguments

---

## Command Line Interface

### Usage Syntax

```bash
python duplicated_img_detect_improved.py directory [OPTIONS]
```

### Arguments

#### Positional Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `directory` | `str` | Directory to search for images (required) |

#### Optional Arguments

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--max_workers` | `int` | `min(32, cpu_count() * 4)` | Maximum number of worker threads |
| `--list_duplicates` | `flag` | `False` | List all duplicated files without removal |
| `--remove_duplicates` | `flag` | `False` | Remove duplicated files after confirmation |
| `--auto_select_best` | `flag` | `False` | Automatically select best quality file to keep |
| `--group_by_group` | `flag` | `False` | Ask for confirmation for each duplicate group |
| `--force_exiftool` | `flag` | `False` | Force use of ExifTool for all metadata extraction (requires ExifTool) |
| `--dest_dir` | `str` | `None` | Destination directory to move duplicated photo groups to instead of deleting |
| `--verbose` | `flag` | `False` | Enable verbose logging (DEBUG level) |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Directory not found or not accessible |

---

## Usage Examples

### Basic Duplicate Detection

```python
from pathlib import Path
from duplicated_img_detect_improved import process_images_parallel

# Scan directory for duplicates
duplicates = process_images_parallel("/path/to/photos")

# Print duplicate groups
for identifier, group in duplicates.items():
    camera, hash_val, resolution, _ = identifier
    print(f"Found {len(group)} duplicates:")
    print(f"  Camera: {camera or 'Unknown'}")
    print(f"  Resolution: {resolution or 'Unknown'}")
    for img in group:
        print(f"    {img.path}")
```

### Custom Processing

```python
from duplicated_img_detect_improved import process_single_image, check_exiftool_exists

# Check ExifTool availability
exiftool_available = check_exiftool_exists()

# Process single image
metadata = process_single_image(Path("photo.jpg"), exiftool_available)
if metadata:
    print(f"Size: {metadata.file_size} bytes")
    print(f"Resolution: {metadata.resolution}")
    print(f"Camera: {metadata.camera_model}")
```

### Quality-Based Selection

```python
from duplicated_img_detect_improved import suggest_best_file, format_file_size

# Given a list of duplicates
duplicates = [metadata1, metadata2, metadata3]

# Get best file index
best_idx = suggest_best_file(duplicates)
best_file = duplicates[best_idx]

print(f"Best file: {best_file.path}")
print(f"Size: {format_file_size(best_file.file_size)}")
print(f"Resolution: {best_file.resolution}")
```

### Force ExifTool Usage

```python
from duplicated_img_detect_improved import process_images_parallel

# Force ExifTool for all metadata extraction
duplicates = process_images_parallel("/path/to/photos", force_exiftool=True)

# This will use ExifTool for all image types, not just RAW files
for identifier, group in duplicates.items():
    print(f"Processed {len(group)} images with ExifTool")
```

### Move Duplicates to Destination Directory

```python
from duplicated_img_detect_improved import process_images_parallel, remove_duplicate_files

# Scan for duplicates
duplicates = process_images_parallel("/path/to/photos")

# Move duplicates to organized destination directory instead of deleting
remove_duplicate_files(
    duplicates, 
    auto_select_best=True,
    group_by_group=False,
    dest_dir="/path/to/duplicate_archive"
)

# This creates subdirectories like:
# /path/to/duplicate_archive/Canon_EOS_R5_1a2b3c4d/IMG_001.jpg
# /path/to/duplicate_archive/Canon_EOS_R5_1a2b3c4d/IMG_002.jpg
```

### Command Line Usage Examples

```bash
# Basic duplicate detection with listing
python duplicated_img_detect_improved.py /path/to/photos --list_duplicates

# Force ExifTool for all metadata extraction
python duplicated_img_detect_improved.py /path/to/photos --force_exiftool --verbose

# Move duplicates to archive directory instead of deleting
python duplicated_img_detect_improved.py /path/to/photos \
    --remove_duplicates \
    --dest_dir /path/to/duplicate_archive \
    --auto_select_best

# Comprehensive processing with all new features
python duplicated_img_detect_improved.py /path/to/photos \
    --remove_duplicates \
    --force_exiftool \
    --dest_dir /path/to/duplicate_archive \
    --group_by_group \
    --verbose
```

---

## Error Handling

### Common Exceptions

| Exception | Cause | Handling |
|-----------|-------|----------|
| `FileNotFoundError` | Image file doesn't exist | Logged and skipped |
| `PermissionError` | No read/write access | Logged and skipped |
| `subprocess.TimeoutExpired` | ExifTool timeout | Logged and fallback used |
| `PIL.UnidentifiedImageError` | Corrupted image | Logged and ExifTool fallback |
| `ValueError` | Invalid resolution format | Logged and None returned |

### Logging Levels

| Level | Usage |
|-------|--------|
| `DEBUG` | Detailed processing information (--verbose flag) |
| `INFO` | General progress and ExifTool version |
| `WARNING` | Non-fatal issues (missing ExifTool, permissions) |
| `ERROR` | Processing errors for individual files |

---

*API Reference generated by: Claude Code SuperClaude Framework*