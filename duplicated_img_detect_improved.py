#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
from pathlib import Path
import os
import hashlib
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from PIL import Image
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('duplicate_detection.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ImageMetadata:
    """Image metadata used for comparison."""
    path: Path
    file_size: int
    hash: Optional[str] = None
    camera_model: Optional[str] = None
    resolution: Optional[Tuple[int, int]] = None
    
    def get_identifier(self) -> Tuple:
        """Get a tuple that can identify this image for duplicate detection."""
        return (self.camera_model or "", self.hash or "", self.resolution or (0, 0), self.file_size)

def check_exiftool_exists() -> bool:
    """Check if ExifTool is installed and available."""
    try:
        result = subprocess.run(
            ['exiftool', '-ver'],
            capture_output=True,
            text=True,
            timeout=5
        )
        logger.info(f"ExifTool version: {result.stdout.strip()}")
        return result.returncode == 0
    except Exception as e:
        logger.warning(f"ExifTool not found or error: {str(e)}")
        return False

def get_camera_model_single(image_path: Path) -> Tuple[Path, Optional[str]]:
    """Process a single file with ExifTool to extract camera model."""
    try:
        result = subprocess.run(
            ['exiftool', '-Model', '-s3', str(image_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return image_path, result.stdout.strip()
        return image_path, None
    except Exception as e:
        logger.error(f"Error extracting camera model from {image_path}: {str(e)}")
        return image_path, None

def get_image_resolution_exiftool(image_path: Path) -> Optional[Tuple[int, int]]:
    """Get the resolution of an image using ExifTool."""
    try:
        result = subprocess.run(
            ['exiftool', '-ImageWidth', '-ImageHeight', '-s3', '-sep', 'x', str(image_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            # ExifTool output format should be "WidthxHeight"
            dimensions = result.stdout.strip()
            # Try to parse dimensions in format "WidthxHeight"
            if 'x' in dimensions:
                width, height = dimensions.split('x')
                try:
                    return (int(width), int(height))
                except ValueError:
                    logger.error(f"Invalid resolution format from ExifTool: {dimensions}")
                    return None
            # Try parsing dimensions in separate lines format
            elif '\n' in dimensions:
                width, height = dimensions.split('\n')
                try:
                    return (int(width), int(height))
                except ValueError:
                    logger.error(f"Invalid resolution format from ExifTool: {dimensions}")
                    return None
        return None
    except Exception as e:
        logger.error(f"Error getting resolution with ExifTool for {image_path}: {str(e)}")
        return None

def get_image_resolution(image_path: Path, exiftool_available: bool) -> Optional[Tuple[int, int]]:
    """Get the resolution of an image, using ExifTool for RAW files."""
    file_ext = image_path.suffix.lower()
    
    # For RAW files, use ExifTool if available
    if file_ext == '.arw' and exiftool_available:
        return get_image_resolution_exiftool(image_path)
    
    # For standard image formats, try PIL first
    if file_ext in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp'}:
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            logger.error(f"Error getting resolution with PIL for {image_path}: {str(e)}")
            
            # Fall back to ExifTool if PIL fails and ExifTool is available
            if exiftool_available:
                logger.info(f"Trying ExifTool for resolution of {image_path}")
                return get_image_resolution_exiftool(image_path)
            
    return None

def calculate_image_hash(image_path: Path) -> Tuple[Path, Optional[str]]:
    """Calculate a hash for the image content."""
    try:
        # For large files, use a buffer to avoid loading the entire file into memory
        sha256_hash = hashlib.sha256()
        with open(image_path, 'rb') as img_file:
            # Read the file in chunks
            for byte_block in iter(lambda: img_file.read(4096), b""):
                sha256_hash.update(byte_block)
        return image_path, sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {image_path}: {str(e)}")
        return image_path, None

def get_file_size(image_path: Path) -> int:
    """Get the file size in bytes."""
    try:
        return image_path.stat().st_size
    except Exception as e:
        logger.error(f"Error getting file size for {image_path}: {str(e)}")
        return 0

def process_single_image(image_path: Path, exiftool_available: bool) -> Optional[ImageMetadata]:
    """Process a single image to extract all metadata."""
    try:
        # Check file permissions
        if not os.access(image_path, os.R_OK):
            logger.warning(f"No read permission for {image_path}")
            return None
            
        file_size = get_file_size(image_path)
        
        # Extract camera model if ExifTool is available
        camera_model = None
        if exiftool_available:
            _, camera_model = get_camera_model_single(image_path)
        
        # Get image hash
        _, img_hash = calculate_image_hash(image_path)
        
        # Get resolution
        resolution = get_image_resolution(image_path, exiftool_available)
            
        return ImageMetadata(
            path=image_path,
            file_size=file_size,
            hash=img_hash,
            camera_model=camera_model,
            resolution=resolution
        )
    except Exception as e:
        logger.error(f"Error processing {image_path}: {str(e)}")
        return None

def process_images_parallel(directory: str, max_workers: Optional[int] = None) -> Dict[Tuple, List[ImageMetadata]]:
    """Process images in parallel using ThreadPoolExecutor."""
    # Check if ExifTool is available
    exiftool_available = check_exiftool_exists()
    if not exiftool_available:
        logger.warning("ExifTool not found. Metadata extraction will be limited.")
    
    # If max_workers not specified, use a reasonable default
    if max_workers is None:
        max_workers = min(32, (os.cpu_count() or 1) * 4)
    
    # Collect all image paths first
    image_paths = [
        p for p in Path(directory).rglob("*.*")
        if p.suffix.lower() in {'.arw', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp'}
    ]
    
    logger.info(f"Found {len(image_paths)} image files to process.")
    
    # Process all files to gather metadata
    image_metadata_list: List[ImageMetadata] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(process_single_image, path, exiftool_available): path 
            for path in image_paths
        }
        
        # Collect metadata as it completes
        for future in as_completed(future_to_path):
            try:
                metadata = future.result()
                if metadata:
                    image_metadata_list.append(metadata)
            except Exception as e:
                logger.error(f"Error processing future: {str(e)}")
    
    # Group by identifier
    duplicates: Dict[Tuple, List[ImageMetadata]] = {}
    for metadata in image_metadata_list:
        identifier = metadata.get_identifier()
        if identifier not in duplicates:
            duplicates[identifier] = []
        duplicates[identifier].append(metadata)
                
    # Filter to only include duplicates
    return {k: v for k, v in duplicates.items() if len(v) > 1}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0 or unit == 'GB':
            break
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} {unit}"

def suggest_best_file(duplicates: List[ImageMetadata]) -> int:
    """Suggest the best file to keep based on resolution and file size."""
    best_idx = 0
    max_score = -1
    
    for idx, metadata in enumerate(duplicates):
        # Score is based on resolution first, then file size
        resolution_score = 0
        if metadata.resolution:
            resolution_score = metadata.resolution[0] * metadata.resolution[1]
        
        # We normalize the file size score to avoid it dominating the decision
        size_score = metadata.file_size / 1000000  # Convert to MB
        
        # Overall score prioritizes resolution
        score = resolution_score * 0.9 + size_score * 0.1
        
        if score > max_score:
            max_score = score
            best_idx = idx
            
    return best_idx

def remove_duplicate_files(duplicates: Dict[Tuple, List[ImageMetadata]], auto_select_best: bool = False, group_by_group: bool = True):
    """Remove duplicate files after confirmation."""
    duplicate_count = sum(len(group) - 1 for group in duplicates.values())
    logger.info(f"Found {len(duplicates)} groups with {duplicate_count} total duplicate files.")
    
    if not group_by_group:
        user_input = input("Do you want to remove duplicated files? (yes/no): ").strip().lower()
        if user_input != 'yes':
            print("Removal canceled.")
            return
    
    total_removed = 0
    total_space_saved = 0
    
    for key, dup_metadata in duplicates.items():
        camera_model, img_hash, resolution, _ = key
        print(f"\nDuplicate images group:")
        print(f"  Camera Model: {camera_model or 'N/A'}")
        print(f"  Hash: {img_hash[:8]}...{img_hash[-8:] if img_hash else 'N/A'}")
        
        for idx, metadata in enumerate(dup_metadata):
            resolution_str = f"{metadata.resolution[0]}x{metadata.resolution[1]}" if metadata.resolution else "Unknown"
            print(f"  [{idx+1}] {metadata.path}")
            print(f"      Size: {format_file_size(metadata.file_size)}, Resolution: {resolution_str}")
        
        # Group-by-group confirmation
        if group_by_group:
            confirm = input(f"\n  Process this duplicate group? (yes/no/skip): ").strip().lower()
            if confirm == 'skip':
                print("  Skipping this group.")
                continue
            elif confirm != 'yes':
                print("  Skipping this group.")
                continue
        
        if auto_select_best:
            keep_idx = suggest_best_file(dup_metadata)
            print(f"\n  Automatically selected to keep file #{keep_idx+1} (best resolution/quality)")
        else:
            keep_input = input("\n  Enter the number of the file to keep (default is 1): ").strip()
            try:
                keep_idx = int(keep_input) - 1 if keep_input else 0
                if keep_idx < 0 or keep_idx >= len(dup_metadata):
                    print("  Invalid selection. Keeping file #1.")
                    keep_idx = 0
            except ValueError:
                print("  Invalid input. Keeping file #1.")
                keep_idx = 0
        
        # Remove all files except the one to keep
        for idx, metadata in enumerate(dup_metadata):
            if idx != keep_idx:
                try:
                    if os.access(metadata.path, os.W_OK):
                        os.remove(metadata.path)
                        print(f"  Removed: {metadata.path}")
                        total_removed += 1
                        total_space_saved += metadata.file_size
                    else:
                        print(f"  No permission to remove: {metadata.path}")
                except Exception as e:
                    logger.error(f"Error removing {metadata.path}: {str(e)}")
    
    print(f"\nRemoval complete. Removed {total_removed} files, saving {format_file_size(total_space_saved)}.")

def parse_arguments():
    """Parse command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Detect and optionally remove duplicate images with enhanced comparison.")
    parser.add_argument("directory", type=str, help="Directory to search for images")
    parser.add_argument("--max_workers", type=int, default=None, help="Maximum number of worker threads")
    parser.add_argument("--list_duplicates", action='store_true', help="List all duplicated files")
    parser.add_argument("--remove_duplicates", action='store_true', help="Remove duplicated files after confirmation")
    parser.add_argument("--auto_select_best", action='store_true', 
                        help="Automatically select the best quality file to keep (based on resolution and size)")
    parser.add_argument("--group_by_group", action='store_true', 
                        help="Ask for confirmation for each group of duplicates separately")
    parser.add_argument("--verbose", action='store_true', help="Enable verbose logging")

    return parser.parse_args()

# Usage example:
if __name__ == "__main__":
    args = parse_arguments()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    if not os.path.isdir(args.directory):
        logger.error(f"Directory not found: {args.directory}")
        sys.exit(1)
    
    logger.info(f"Scanning directory: {args.directory}")
    duplicates = process_images_parallel(args.directory, max_workers=args.max_workers)

    for key, dup_metadata in duplicates.items():
        camera_model, img_hash, resolution, _ = key
        print(f"\nDuplicate images group:")
        print(f"  Camera Model: {camera_model or 'N/A'}")
        print(f"  Hash: {img_hash[:8]}...{img_hash[-8:] if img_hash else 'N/A'}")
        
        if args.list_duplicates:
            for idx, metadata in enumerate(dup_metadata):
                resolution_str = f"{metadata.resolution[0]}x{metadata.resolution[1]}" if metadata.resolution else "Unknown"
                print(f"  [{idx+1}] {metadata.path}")
                print(f"      Size: {format_file_size(metadata.file_size)}, Resolution: {resolution_str}")
                
    if args.remove_duplicates:
        remove_duplicate_files(duplicates, auto_select_best=args.auto_select_best, group_by_group=args.group_by_group)
