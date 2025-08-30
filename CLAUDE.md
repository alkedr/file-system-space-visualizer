# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool that analyzes disk space usage for a given directory and produces an interactive HTML visualization. The tool displays files and directories as horizontal bars with heights proportional to their disk usage, making it easy to identify space-consuming items. Users can click on directories to navigate deeper into the directory structure.

## Technology Stack

- **Language**: Python 3.8+
- **CLI Framework**: argparse (built-in)
- **Visualization**: Pure HTML + CSS + JavaScript (no external dependencies)
- **File System Analysis**: pathlib (built-in)
- **Dependencies**: None (pure Python standard library)

## Architecture

The CLI tool is structured with:

- **main.py**: Main CLI entry point with complete functionality
- **scan_directory_recursive()**: Recursive directory scanning with depth limits and symbolic link handling
- **scan_directory()**: Compatibility wrapper for immediate children only
- **create_html_chart()**: Self-contained HTML generation with embedded JavaScript
- **format_size()**: Human-readable size formatting
- Complete error handling for permissions and symbolic links

## Development Commands

- `./run.sh main.py <directory>` - Run the tool (creates venv if needed)
- `./run.sh main.py --help` - Show help
- Example: `./run.sh main.py ~/Downloads`

The `run.sh` script automatically:
- Creates virtual environment if it doesn't exist
- Installs dependencies from requirements.txt (currently empty)
- Runs the tool with the venv Python

## Core Functionality

The tool:

1. Accepts a directory path as command line argument
2. Recursively scans the directory tree (max depth 3) to calculate sizes
3. Excludes symbolic links to prevent double-counting and match `du` behavior
4. Sorts items by size (largest first) at each directory level
5. Filters out items smaller than 1% (aggregated as "Other")
6. Generates a self-contained HTML file with embedded complete directory tree
7. Provides interactive navigation with breadcrumb trail
8. Uses percentage-based bar heights for responsive design

## Data Structure

The directory tree uses a list-based structure to preserve sorting:
```python
{
    'size': int,           # Total size in bytes
    'is_directory': bool,  # Whether this is a directory
    'path': str,          # Full filesystem path
    'name': str,          # Item name (for children only)
    'children': [...]     # List of child items (sorted by size)
}
```

## Interactive Features

- **Click Navigation**: Click directories to drill down
- **Breadcrumb Trail**: Click breadcrumb items to navigate back up
- **Bootstrap Styling**: Table-striped colors with hover effects
- **Responsive Design**: Flexbox layout with percentage-based heights
- **Embedded Data**: Complete directory tree embedded in HTML for offline use

## Output Format

- **Visualization**: Horizontal bars with proportional heights
- **Text Format**: `6.1% (30.1 GB) - filename`
- **Sorting**: Largest items at top, "Other" at bottom
- **File**: Saves as `disk_usage_chart.html` in current directory
- **Styling**: Bootstrap-inspired table-striped alternating colors