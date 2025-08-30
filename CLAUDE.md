# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool that analyzes disk space usage for a given directory and produces a visual pie chart representation. The tool helps users quickly understand which subdirectories or files are consuming the most space.

## Technology Stack

- **Language**: Python 3.8+
- **CLI Framework**: argparse (built-in)
- **Visualization**: matplotlib
- **File System Analysis**: pathlib (built-in)
- **Dependencies**: matplotlib only

## Architecture

The CLI tool should be structured with:

- Main CLI entry point with argument parsing
- Directory scanning and size calculation module
- Data processing for chart generation
- Visualization rendering module
- Output handling (display/save chart)

## Development Commands

Commands will be established once the Python project structure is set up:

- `python -m pip install -e .` - Install in development mode
- `python -m pytest` - Run tests
- `python -m flake8` or `ruff` - Linting
- `python -m mypy` - Type checking

## Core Functionality

The tool should:

1. Accept a directory path as command line argument
2. Recursively scan the directory to calculate sizes
3. Aggregate data for visualization
4. Generate a pie chart showing space distribution
5. Display or save the chart based on user options

## Getting Started

Initial development steps:

1. Set up Python project structure (pyproject.toml/setup.py)
2. Implement directory scanning functionality
3. Add command line interface
4. Integrate chart generation library
5. Add tests and documentation