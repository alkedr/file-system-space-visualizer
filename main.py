#!/usr/bin/env python3

import argparse
from pathlib import Path
import json


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


def create_html_chart(data, title):
    """Generate HTML chart with embedded JavaScript."""
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
    
    # Keep original order so largest items appear at top
    # (HTML stacks from top to bottom, so no reversal needed)
    
    # Prepare data for JavaScript
    chart_data = []
    total_size = sum(size for _, size in filtered_data)
    
    for i, (name, size) in enumerate(filtered_data):
        percentage = (size / total_size) * 100
        chart_data.append({
            'name': name,
            'size': size,
            'formatted_size': format_size(size),
            'percentage': percentage,
            'color_index': i
        })
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Disk Space Usage: {title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background-color: white;
        }}
        
        .title {{
            text-align: center;
            font-size: 14px;
            font-weight: bold;
            padding: 10px 0;
            margin: 0;
        }}
        
        .chart-container {{
            width: 100%;
            height: calc(100vh - 50px);
            position: relative;
        }}
        
        .bar {{
            width: 100%;
            position: relative;
            display: flex;
            align-items: center;
            overflow: hidden;
        }}
        
        .bar-text {{
            position: absolute;
            left: 2%;
            font-size: 10px;
            font-weight: bold;
            color: black;
            z-index: 10;
            white-space: nowrap;
        }}
    </style>
</head>
<body>
    <h1 class="title">Disk Space Usage: {title}</h1>
    <div class="chart-container" id="chart-container"></div>
    
    <script>
        const data = {json.dumps(chart_data)};
        
        function generateColor(index) {{
            // Matplotlib's tab10 color palette
            const tab10Colors = [
                '#1f77b4',  // blue
                '#ff7f0e',  // orange
                '#2ca02c',  // green
                '#d62728',  // red
                '#9467bd',  // purple
                '#8c564b',  // brown
                '#e377c2',  // pink
                '#7f7f7f',  // gray
                '#bcbd22',  // olive
                '#17becf'   // cyan
            ];
            return tab10Colors[index % tab10Colors.length];
        }}
        
        function renderChart() {{
            const container = document.getElementById('chart-container');
            const containerHeight = container.clientHeight;
            
            data.forEach((item, index) => {{
                const bar = document.createElement('div');
                bar.className = 'bar';
                
                const heightPercent = item.percentage;
                const height = (heightPercent / 100) * containerHeight;
                
                bar.style.height = height + 'px';
                bar.style.backgroundColor = generateColor(item.color_index);
                
                const text = document.createElement('div');
                text.className = 'bar-text';
                text.textContent = `${{item.percentage.toFixed(1)}}% (${{item.formatted_size}}) - ${{item.name}}`;
                
                bar.appendChild(text);
                container.appendChild(bar);
            }});
        }}
        
        // Render chart when page loads
        window.addEventListener('load', renderChart);
        window.addEventListener('resize', () => {{
            document.getElementById('chart-container').innerHTML = '';
            renderChart();
        }});
    </script>
</body>
</html>"""
    
    output_file = "disk_usage_chart.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Chart saved as: {output_file}")


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
    
    create_html_chart(data, str(path))
    return 0


if __name__ == "__main__":
    exit(main())