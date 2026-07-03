# CLAUDE.md

## Project Overview

**SuperfastSync** is a file server benchmarking application (similar to Dropbox) built with Python. It provides a web interface for uploading and downloading files while tracking performance metrics like transfer speeds and client information. Licensed under Apache 2.0.

### Purpose
- Simple file server for benchmarking upload/download performance
- Not intended as a production multi-user SaaS application
- Focus on simplicity and functionality over enterprise features

## Project Structure

```
SuperfastSync/
├── LICENSE                 # Apache License 2.0
├── .gitignore             # Python-focused gitignore
├── CLAUDE.md              # This file
├── pyproject.toml         # uv package configuration (to be created)
├── app/                   # Application code (to be created)
│   ├── __init__.py
│   ├── server.py          # Flask application
│   ├── routes.py          # Route handlers
│   ├── benchmarks.py      # Performance tracking
│   ├── templates/         # HTML templates
│   └── static/            # CSS, JS, assets
└── storage/               # File storage directory (sandboxed)
```

## Development Setup

### Prerequisites
- Python 3.10+
- uv package manager

### Installation
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the application
uv run python -m app.server
```

## Project Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Keep code simple - no over-engineering
- Use type hints where applicable
- Maintain clear, concise docstrings

### Git Workflow
- Main branch: `main`
- Keep commits atomic and well-described
- Clean working tree currently maintained

### Testing
- Manual testing through web interface
- Performance benchmarking via dashboard metrics

### Dependencies
- **Flask** - Lightweight web framework
- **Werkzeug** - WSGI utilities (included with Flask)
- Additional utilities as needed for IP lookup, DNS resolution

## Architecture

### Stack
- **Backend**: Flask (Python)
- **Frontend**: HTML templates with modern CSS and JavaScript
- **Package Management**: uv
- **File Storage**: Local directory (`./storage/`) - sandboxed for security

### Security Constraints
- **IMPORTANT**: Application must ONLY read from and write to the `./storage/` directory
- No access to parent directories or other filesystem locations
- Path traversal protection required

### Data Flow
1. Client uploads file via drag-and-drop interface
2. Flask receives file, tracks upload metrics (speed, client IP)
3. File saved to `./storage/` directory
4. Metrics stored (client IP, reverse DNS, AS lookup, speeds)
5. Dashboard displays historical benchmark data

## Key Features

### File Operations
- **Browse Files**: View all files in storage directory with a clean, modern UI
- **Upload Files**: Drag-and-drop or click to upload (no type/size restrictions)
- **Download Files**: Download any stored file
- **Synthetic Test Files**: Pre-configured test files (100MB, 500MB, 1GB) generated on-the-fly for download benchmarking without consuming disk space

### Benchmarking & Metrics
- **Max Transfer Speed**: Peak upload/download speed
- **Average Transfer Speed**: Mean transfer rate
- **Client Information**:
  - Client IP address
  - Reverse DNS lookup
  - AS (Autonomous System) lookup
- **Dashboard**: Historical view of all benchmark data

### UI/UX
- Modern, clean interface
- Drag-and-drop file uploads
- Responsive design
- Real-time upload progress (optional enhancement)

## Notes for AI Assistants

### Current State
- Fresh project initialization
- Git repository initialized
- No source code yet

### When Contributing
- Keep code simple - no over-engineering
- Prioritize functionality over abstraction
- **Security**: Ensure all file operations are sandboxed to `./storage/`
- Update this CLAUDE.md as the project evolves

### Implementation Notes
- Use Flask's `send_from_directory()` for secure file serving
- Implement path traversal protection (no `../` in filenames)
- Track transfer speeds using start/end timestamps and file sizes
- Use Python's `socket` module for reverse DNS
- Consider using a simple JSON file or SQLite for storing benchmark history

### Synthetic Test Files
The application includes synthetic test files that appear in the file list but are generated on-the-fly:
- **test-100mb.bin** - 100 MB file for download speed testing
- **test-500mb.bin** - 500 MB file for download speed testing
- **test-1gb.bin** - 1 GB file for download speed testing

These files:
- Do not consume disk space
- Are generated using a repeating byte pattern during download
- Cannot be deleted (protected in UI and API)
- Are visually distinguished with a blue gradient background and "Test File" badge
- Use streaming responses for efficient memory usage

Implementation in `app/synthetic.py` - modify `SYNTHETIC_FILES` list to add/remove/change test files.
