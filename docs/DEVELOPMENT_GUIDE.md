# Development Guide - Duplicate Photo Finder

> Complete guide for setting up, developing, testing, and contributing to the duplicate photo finder project.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [Coding Standards](#coding-standards)
- [Testing Strategy](#testing-strategy)
- [Contributing Guidelines](#contributing-guidelines)
- [Release Process](#release-process)

---

## Development Setup

### Prerequisites

#### Required Software

```bash
# Python 3.12 or higher
python --version  # Should be 3.12+

# Git for version control
git --version

# Optional but recommended: uv for faster dependency management
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### External Dependencies

```bash
# ExifTool (macOS)
brew install exiftool

# ExifTool (Ubuntu/Debian)
sudo apt-get install libimage-exiftool-perl

# ExifTool (Windows)
# Download from: https://exiftool.org/
```

### Local Development Setup

#### 1. Clone Repository

```bash
git clone https://github.com/username/duplicate_photo_finder.git
cd duplicate_photo_finder
```

#### 2. Create Virtual Environment

**Using uv (recommended):**
```bash
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

**Using standard Python:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

#### 3. Install Dependencies

**Using uv:**
```bash
uv pip install -e .
```

**Using pip:**
```bash
pip install -e .
```

#### 4. Verify Installation

```bash
# Test ExifTool integration
python -c "from duplicated_img_detect_improved import check_exiftool_exists; print(check_exiftool_exists())"

# Run basic functionality test
python duplicated_img_detect_improved.py --help
```

### Development Environment

#### Recommended IDE Setup

**VS Code Extensions:**
- Python (Microsoft)
- Pylance (Microsoft)
- Black Formatter
- isort
- mypy

**VS Code Settings (.vscode/settings.json):**
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### Development Dependencies

Add to `pyproject.toml` for development:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.0.0",
    "flake8>=6.0.0",
]
```

---

## Project Architecture

### Code Organization

```
duplicated_img_detect_improved.py
├── Data Models
│   └── ImageMetadata (dataclass)
├── External Tool Integration
│   ├── check_exiftool_exists()
│   ├── get_camera_model_single()
│   └── get_image_resolution_exiftool()
├── Metadata Extraction
│   ├── get_image_resolution() [Updated: force_exiftool parameter]
│   ├── calculate_image_hash()
│   └── get_file_size()
├── Core Processing
│   ├── process_single_image() [Updated: force_exiftool parameter]
│   └── process_images_parallel() [Updated: force_exiftool parameter]
├── File Management
│   ├── suggest_best_file()
│   └── remove_duplicate_files() [Updated: dest_dir parameter]
├── Utilities
│   ├── format_file_size()
│   └── parse_arguments() [Updated: new CLI options]
└── Entry Point
    └── if __name__ == "__main__" [Updated: new argument handling]
```

### Design Patterns

#### 1. Dataclass Pattern
```python
@dataclass
class ImageMetadata:
    """Clean data structure with built-in methods."""
    path: Path
    file_size: int
    # ... other fields
    
    def get_identifier(self) -> Tuple:
        """Business logic method."""
        return (self.camera_model or "", self.hash or "", ...)
```

#### 2. Strategy Pattern
```python
def get_image_resolution(image_path: Path, exiftool_available: bool, force_exiftool: bool = False):
    """Different strategies based on file type, tool availability, and user preferences."""
    # Force ExifTool if requested and available
    if force_exiftool and exiftool_available:
        return get_image_resolution_exiftool(image_path)
    
    # Use ExifTool for RAW files
    if file_ext == '.arw' and exiftool_available:
        return get_image_resolution_exiftool(image_path)
    elif file_ext in standard_formats:
        # Try PIL first, fallback to ExifTool
        pass
```

#### 3. Factory Pattern
```python
def process_images_parallel(directory: str, max_workers: Optional[int] = None, force_exiftool: bool = False):
    """Factory for creating ThreadPoolExecutor with smart defaults and tool validation."""
    # Validate ExifTool requirement if forced
    exiftool_available = check_exiftool_exists()
    if force_exiftool and not exiftool_available:
        sys.exit("ExifTool required but not available")
    
    if max_workers is None:
        max_workers = min(32, (os.cpu_count() or 1) * 4)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # ... processing logic with force_exiftool parameter
```

#### 4. Command Pattern (File Operations)
```python
def remove_duplicate_files(duplicates, auto_select_best=False, group_by_group=True, dest_dir=None):
    """Command pattern for file operations - delete or move based on configuration."""
    if dest_dir:
        # Move command with organized directory structure
        for group in duplicates:
            group_dest = create_group_directory(dest_dir, group_metadata)
            shutil.move(file_path, group_dest)
    else:
        # Delete command
        os.remove(file_path)
```

### Data Flow

```
Directory Input
    ↓
File Discovery (rglob)
    ↓
Parallel Processing (ThreadPoolExecutor)
    ↓
Metadata Extraction (per image)
    ├── File Size
    ├── Hash Calculation
    ├── Camera Model (ExifTool)
    └── Resolution (PIL/ExifTool)
    ↓
Duplicate Grouping (by identifier)
    ↓
User Interaction & File Management
    ↓
Statistics & Logging
```

---

## Coding Standards

### Code Style

#### Python Style Guide
- Follow PEP 8 with Black formatter
- Line length: 88 characters (Black default)
- Use type hints for all functions and methods
- Prefer pathlib over os.path

#### Type Hints
```python
# Good: Complete type annotations
def process_single_image(image_path: Path, exiftool_available: bool) -> Optional[ImageMetadata]:
    pass

# Good: Generic types
from typing import Dict, List, Tuple, Optional
def process_images_parallel(directory: str) -> Dict[Tuple, List[ImageMetadata]]:
    pass
```

#### Error Handling
```python
# Good: Specific exception handling with logging
try:
    result = subprocess.run(['exiftool', '-ver'], capture_output=True, timeout=5)
    return result.returncode == 0
except subprocess.TimeoutExpired:
    logger.warning("ExifTool check timed out")
    return False
except FileNotFoundError:
    logger.warning("ExifTool not found")
    return False
except Exception as e:
    logger.error(f"Unexpected error checking ExifTool: {e}")
    return False
```

#### Logging Standards
```python
# Use structured logging with appropriate levels
logger.info(f"Found {len(image_paths)} image files to process")
logger.warning(f"No read permission for {image_path}")
logger.error(f"Error processing {image_path}: {str(e)}")

# Include context in log messages
logger.debug(f"Processing {image_path} with ExifTool={'available' if exiftool_available else 'unavailable'}")
```

### Documentation Standards

#### Docstrings
```python
def calculate_image_hash(image_path: Path) -> Tuple[Path, Optional[str]]:
    """Calculate a hash for the image content.
    
    Uses SHA-256 algorithm with chunked reading for memory efficiency.
    Suitable for files of any size without loading entire file into memory.
    
    Args:
        image_path: Path to the image file to hash
        
    Returns:
        Tuple containing the original path and hex digest hash,
        or None if calculation failed
        
    Raises:
        Logs errors but doesn't raise exceptions
    """
```

#### Code Comments
```python
# Use comments for complex logic only
for byte_block in iter(lambda: img_file.read(4096), b""):
    sha256_hash.update(byte_block)  # 4KB chunks for memory efficiency

# Avoid obvious comments
file_size = image_path.stat().st_size  # Don't comment this
```

---

## Testing Strategy

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_metadata.py         # ImageMetadata tests
├── test_extraction.py       # Metadata extraction tests
├── test_processing.py       # Core processing tests
├── test_file_operations.py  # File management tests
├── test_cli.py             # Command-line interface tests
└── fixtures/
    ├── sample_images/       # Test image files
    └── expected_results/    # Expected test outputs
```

### Unit Testing Framework

#### Setup pytest configuration

**pyproject.toml:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=duplicated_img_detect_improved",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--strict-markers",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "requires_exiftool: marks tests that require ExifTool",
]
```

#### Sample Test Cases

**test_metadata.py:**
```python
import pytest
from pathlib import Path
from duplicated_img_detect_improved import ImageMetadata

class TestImageMetadata:
    def test_get_identifier_complete_metadata(self):
        """Test identifier generation with all metadata present."""
        metadata = ImageMetadata(
            path=Path("test.jpg"),
            file_size=1024,
            hash="abc123",
            camera_model="Sony A7R IV",
            resolution=(3840, 2160)
        )
        
        expected = ("Sony A7R IV", "abc123", (3840, 2160), 1024)
        assert metadata.get_identifier() == expected
    
    def test_get_identifier_missing_metadata(self):
        """Test identifier generation with missing metadata."""
        metadata = ImageMetadata(
            path=Path("test.jpg"),
            file_size=1024,
            hash=None,
            camera_model=None,
            resolution=None
        )
        
        expected = ("", "", (0, 0), 1024)
        assert metadata.get_identifier() == expected
```

**test_extraction.py:**
```python
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from duplicated_img_detect_improved import check_exiftool_exists, calculate_image_hash, get_image_resolution

class TestExifToolIntegration:
    @pytest.mark.requires_exiftool
    def test_check_exiftool_exists_with_exiftool(self):
        """Test ExifTool detection when tool is available."""
        assert check_exiftool_exists() is True
    
    @patch('subprocess.run')
    def test_check_exiftool_exists_not_found(self, mock_run):
        """Test ExifTool detection when tool is not available."""
        mock_run.side_effect = FileNotFoundError()
        assert check_exiftool_exists() is False
    
    @pytest.mark.requires_exiftool
    def test_force_exiftool_standard_image(self, sample_jpg_file):
        """Test forced ExifTool usage on standard image formats."""
        # Should use ExifTool instead of PIL when forced
        resolution = get_image_resolution(sample_jpg_file, exiftool_available=True, force_exiftool=True)
        assert resolution is not None
        assert isinstance(resolution, tuple)
        assert len(resolution) == 2
    
    def test_force_exiftool_unavailable_error(self, sample_jpg_file):
        """Test error handling when ExifTool is forced but unavailable."""
        with patch('duplicated_img_detect_improved.check_exiftool_exists', return_value=False):
            with pytest.raises(SystemExit):
                from duplicated_img_detect_improved import process_images_parallel
                process_images_parallel(str(sample_jpg_file.parent), force_exiftool=True)

class TestHashCalculation:
    def test_calculate_image_hash_success(self, tmp_path):
        """Test successful hash calculation."""
        # Create test file
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"test image content")
        
        path, hash_value = calculate_image_hash(test_file)
        
        assert path == test_file
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA-256 hex length
    
    def test_calculate_image_hash_nonexistent_file(self):
        """Test hash calculation with non-existent file."""
        path, hash_value = calculate_image_hash(Path("nonexistent.jpg"))
        
        assert hash_value is None
```

**test_file_operations.py:**
```python
import pytest
from pathlib import Path
from unittest.mock import patch
from duplicated_img_detect_improved import remove_duplicate_files, ImageMetadata

class TestFileOperations:
    def test_remove_duplicates_with_destination_directory(self, tmp_path):
        """Test moving duplicates to destination directory."""
        # Setup test files
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        dest_dir = tmp_path / "destination"
        
        test_file1 = source_dir / "image1.jpg"
        test_file2 = source_dir / "image2.jpg"
        test_file1.write_bytes(b"test image content")
        test_file2.write_bytes(b"test image content")
        
        # Create metadata for duplicates
        metadata1 = ImageMetadata(
            path=test_file1, file_size=100, hash="abc123",
            camera_model="Canon EOS R5", resolution=(1920, 1080)
        )
        metadata2 = ImageMetadata(
            path=test_file2, file_size=100, hash="abc123",
            camera_model="Canon EOS R5", resolution=(1920, 1080)
        )
        
        duplicates = {
            ("Canon EOS R5", "abc123", (1920, 1080), 100): [metadata1, metadata2]
        }
        
        # Mock user input to select first file and proceed
        with patch('builtins.input', side_effect=['yes', '1']):
            remove_duplicate_files(
                duplicates, 
                auto_select_best=False,
                group_by_group=False,
                dest_dir=str(dest_dir)
            )
        
        # Verify destination directory structure
        assert dest_dir.exists()
        group_dir = dest_dir / "Canon_EOS_R5_abc123de"
        assert group_dir.exists()
        
        # Verify one file was moved
        moved_files = list(group_dir.glob("*.jpg"))
        assert len(moved_files) == 1
        
        # Verify source file still exists (the one that was kept)
        remaining_files = list(source_dir.glob("*.jpg"))
        assert len(remaining_files) == 1
    
    def test_destination_directory_creation_error(self, tmp_path):
        """Test handling of destination directory creation errors."""
        # Try to create destination in read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir(mode=0o444)  # Read-only
        
        duplicates = {}  # Empty for simplicity
        
        # Should handle gracefully and return early
        remove_duplicate_files(duplicates, dest_dir=str(readonly_dir / "nested"))
        
        # Should not crash, just log error and return
        assert True  # Test passes if no exception raised
```

### Integration Testing

**test_integration.py:**
```python
class TestEndToEndProcessing:
    @pytest.mark.slow
    def test_process_images_parallel_complete_workflow(self, sample_image_directory):
        """Test complete processing workflow with sample images."""
        duplicates = process_images_parallel(str(sample_image_directory))
        
        # Verify results structure
        assert isinstance(duplicates, dict)
        for identifier, group in duplicates.items():
            assert isinstance(identifier, tuple)
            assert len(identifier) == 4  # camera, hash, resolution, size
            assert isinstance(group, list)
            assert all(isinstance(img, ImageMetadata) for img in group)
            assert len(group) > 1  # Should only return actual duplicates
```

### Performance Testing

**test_performance.py:**
```python
import time
import pytest
from duplicated_img_detect_improved import process_images_parallel

class TestPerformance:
    @pytest.mark.slow
    def test_processing_speed_benchmark(self, large_image_directory):
        """Benchmark processing speed for performance regression."""
        start_time = time.time()
        duplicates = process_images_parallel(str(large_image_directory))
        processing_time = time.time() - start_time
        
        # Adjust thresholds based on your requirements
        images_per_second = len(list(large_image_directory.rglob("*.*"))) / processing_time
        assert images_per_second > 10  # Minimum performance threshold
```

### Test Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| Core Functions | 95% |
| Error Handling | 90% |
| CLI Interface | 85% |
| Integration Points | 80% |
| **Overall Target** | **90%** |

---

## Contributing Guidelines

### Git Workflow

#### Branch Strategy
```bash
# Feature development
git checkout -b feature/add-new-format-support
git checkout -b fix/hash-calculation-bug
git checkout -b docs/api-documentation

# Main branches
main        # Production-ready code
develop     # Integration branch (if using)
```

#### Commit Message Format
```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(metadata): add support for Canon CR2 RAW files

- Add CR2 to supported extensions list
- Update ExifTool integration for Canon metadata
- Add tests for CR2 file processing

Closes #123
```

### Pull Request Process

#### 1. Pre-submission Checklist
- [ ] Code follows style guidelines (Black, isort)
- [ ] All tests pass (`pytest`)
- [ ] Type checking passes (`mypy`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

#### 2. Code Quality Checks
```bash
# Run full test suite
pytest

# Check code formatting
black --check .
isort --check-only .

# Type checking
mypy duplicated_img_detect_improved.py

# Linting
flake8 duplicated_img_detect_improved.py
```

#### 3. PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows the style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
```

### Code Review Guidelines

#### For Authors
- Keep PRs focused and small (<300 lines when possible)
- Provide clear description and context
- Include tests for new functionality
- Update documentation as needed

#### For Reviewers
- Check for code quality and maintainability
- Verify test coverage
- Test locally when significant changes
- Provide constructive feedback
- Approve only when confident in changes

---

## Release Process

### Version Management

#### Semantic Versioning
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible

#### Release Checklist

**Pre-release:**
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version number updated in pyproject.toml

**Release:**
- [ ] Create release tag: `git tag -a v0.2.0 -m "Release v0.2.0"`
- [ ] Push tag: `git push origin v0.2.0`
- [ ] Create GitHub release with changelog
- [ ] Update documentation

**Post-release:**
- [ ] Monitor for issues
- [ ] Update development version number
- [ ] Plan next release cycle

### Distribution

#### PyPI Package (Future)
```bash
# Build package
python -m build

# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*
```

---

## Troubleshooting

### Common Development Issues

#### ExifTool Not Found
```bash
# Check ExifTool installation
which exiftool

# Install on macOS
brew install exiftool

# Install on Ubuntu
sudo apt-get install libimage-exiftool-perl
```

#### Permission Errors
```bash
# Ensure proper file permissions
chmod +r test_images/*
chmod +x duplicated_img_detect_improved.py
```

#### Performance Issues
- Reduce `max_workers` for limited systems
- Check available memory for large file sets
- Monitor CPU usage during processing

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Or use --verbose flag
python duplicated_img_detect_improved.py /path/to/photos --verbose
```

---

## Additional Resources

### Documentation
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [ExifTool Documentation](https://exiftool.org/TagNames/)

### Tools
- [Black Code Formatter](https://black.readthedocs.io/)
- [mypy Type Checker](https://mypy.readthedocs.io/)
- [Pillow Documentation](https://pillow.readthedocs.io/)

---

*Development Guide maintained by the project contributors*  
*Last updated: $(date)*