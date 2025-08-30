# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool that analyzes disk space usage for a given directory and produces a visual bar chart representation. The tool displays files and directories as horizontal bars with heights proportional to their disk usage, making it easy to identify space-consuming items.

## Technology Stack

- **Language**: Python 3.8+
- **CLI Framework**: argparse (built-in)
- **Visualization**: matplotlib
- **File System Analysis**: pathlib (built-in)
- **Dependencies**: matplotlib only

## Architecture

The CLI tool is structured with:

- **main.py**: Main CLI entry point with argument parsing
- **scan_directory()**: Directory scanning and size calculation using pathlib
- **create_bar_chart()**: Proportional bar chart generation with matplotlib
- **format_size()**: Human-readable size formatting
- Error handling for invalid paths and permissions

## Development Commands

- `./run.sh main.py <directory>` - Run the tool (creates venv if needed)
- `./run.sh main.py --help` - Show help
- Example: `./run.sh main.py ~/Downloads`

The `run.sh` script automatically:
- Creates virtual environment if it doesn't exist
- Installs dependencies from requirements.txt
- Runs the tool with the venv Python

## Core Functionality

The tool:

1. Accepts a directory path as command line argument
2. Recursively scans the directory to calculate sizes
3. Sorts items by size (largest first)
4. Filters out items smaller than 1% (aggregated as "Other")
5. Generates a horizontal bar chart with heights proportional to disk usage
6. Saves chart as `disk_usage_chart.png`
7. Displays format: `percent% (size) - filename`

## Output Format

- **Visualization**: Horizontal bars with proportional heights
- **Text Format**: `6.1% (30.1 GB) - filename`
- **Sorting**: Largest items at top, "Other" at bottom
- **File**: Saves as `disk_usage_chart.png` in current directory