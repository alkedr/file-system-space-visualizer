#!/usr/bin/env python3

import argparse
from pathlib import Path
import matplotlib.pyplot as plt


def scan_directory(path):
    """Scan directory and return sizes of immediate children."""
    data = {}
    
    for item in path.iterdir():
        try:
            if item.is_file():
                data[item.name] = item.stat().st_size
            elif item.is_dir():
                size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                data[item.name] = size
        except (PermissionError, OSError):
            continue
    
    return data


def format_size(bytes):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


def create_bar_chart(data, title):
    """Generate and display horizontal bar chart with row heights proportional to size."""
    if not data:
        print("No data to display")
        return
    
    names = list(data.keys())
    sizes = list(data.values())
    
    # Sort by size (largest first)
    sorted_data = sorted(zip(names, sizes), key=lambda x: x[1], reverse=True)
    
    # Filter out very small items (less than 1% of total)
    total = sum(sizes)
    large_items = [(name, size) for name, size in sorted_data if size > total * 0.01]
    
    if len(large_items) < len(sorted_data):
        other_size = sum(size for name, size in sorted_data if size <= total * 0.01)
        # Put "Other" at the end (bottom of chart)
        filtered_data = large_items + [("Other", other_size)]
    else:
        filtered_data = large_items
    
    # Reverse order so largest items appear at top
    filtered_data = filtered_data[::-1]
    
    names, sizes = zip(*filtered_data) if filtered_data else ([], [])
    
    # Calculate proportional heights
    total_size = sum(sizes)
    proportions = [size / total_size for size in sizes]
    
    # Create figure with height proportional to number of items
    fig, ax = plt.subplots(figsize=(12, max(8, len(names) * 0.5)))
    
    # Create horizontal bars with heights proportional to size
    y_positions = []
    current_y = 0
    for i, prop in enumerate(proportions):
        height = prop * 10  # Scale factor for visibility
        y_positions.append(current_y + height / 2)
        
        # Create bar
        ax.barh(current_y + height / 2, 1, height=height, 
                label=f"{names[i]} ({format_size(sizes[i])}) - {prop*100:.1f}%")
        
        # Add text label
        ax.text(0.02, current_y + height / 2, 
                f"{prop*100:.1f}% ({format_size(sizes[i])}) - {names[i]}",
                va='center', ha='left', fontsize=10, weight='bold')
        
        current_y += height
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, current_y)
    ax.set_title(f"Disk Space Usage: {title}", fontsize=14, weight='bold')
    
    # Remove y-axis ticks and labels
    ax.set_yticks([])
    ax.set_xticks([])
    
    # Remove spines for cleaner look
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Remove margins
    plt.subplots_adjust(left=0, right=1, bottom=0, top=0.95)
    
    output_file = "disk_usage_chart.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight', pad_inches=0)
    print(f"Chart saved as: {output_file}")
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Visualize disk space usage as a pie chart")
    parser.add_argument("directory", help="Directory to analyze")
    
    args = parser.parse_args()
    
    path = Path(args.directory)
    
    if not path.exists():
        print(f"Error: Directory '{path}' does not exist")
        return 1
    
    if not path.is_dir():
        print(f"Error: '{path}' is not a directory")
        return 1
    
    print(f"Scanning directory: {path}")
    data = scan_directory(path)
    
    if not data:
        print("No accessible files or directories found")
        return 1
    
    create_bar_chart(data, str(path))
    return 0


if __name__ == "__main__":
    exit(main())