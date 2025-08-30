#!/usr/bin/env python3

import argparse
from pathlib import Path
import json


def scan_directory_recursive(path, max_depth=3, current_depth=0):
    """Recursively scan directory tree and return complete structure."""
    if current_depth >= max_depth:
        # Just return size for very deep directories
        try:
            size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            return {'size': size, 'is_directory': True, 'path': str(path), 'children': {}}
        except (PermissionError, OSError):
            return {'size': 0, 'is_directory': True, 'path': str(path), 'children': {}}
    
    data = {}
    total_size = 0
    
    for item in path.iterdir():
        try:
            if item.is_file():
                file_size = item.stat().st_size
                data[item.name] = {
                    'size': file_size,
                    'is_directory': False,
                    'path': str(item),
                    'children': {}
                }
                total_size += file_size
            elif item.is_dir():
                # Recursively scan subdirectory
                subdir_data = scan_directory_recursive(item, max_depth, current_depth + 1)
                data[item.name] = subdir_data
                total_size += subdir_data['size']
        except (PermissionError, OSError):
            continue
    
    return {
        'size': total_size,
        'is_directory': True,
        'path': str(path),
        'children': data
    }

def scan_directory(path):
    """Scan directory and return immediate children (for compatibility)."""
    tree = scan_directory_recursive(path, max_depth=1)
    return tree['children']


def format_size(bytes):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


def create_html_chart(data, title, root_path):
    """Generate HTML chart with embedded JavaScript and full directory tree."""
    if not data:
        print("No data to display")
        return
    
    # Get complete directory tree
    complete_tree = scan_directory_recursive(Path(root_path))
    
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
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        
        .title {{
            text-align: center;
            font-size: 14px;
            font-weight: bold;
            padding: 10px 0;
            margin: 0;
            flex-shrink: 0;
        }}
        
        .breadcrumb {{
            background-color: #f0f0f0;
            padding: 10px;
            font-size: 12px;
            border-bottom: 1px solid #ddd;
            flex-shrink: 0;
        }}
        
        .chart-container {{
            width: 100%;
            flex: 1;
            position: relative;
            overflow: hidden;
        }}
        
        .bar {{
            width: 100%;
            position: relative;
            display: flex;
            align-items: center;
            overflow: hidden;
        }}
        
        .bar.clickable {{
            cursor: pointer;
        }}
        
        .bar.clickable:hover {{
            background-color: #e2e6ea !important;
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
        
        .breadcrumb-item {{
            display: inline-block;
            margin-right: 5px;
            cursor: pointer;
            color: #007bff;
            text-decoration: underline;
        }}
        
        .breadcrumb-item:hover {{
            color: #0056b3;
        }}
        
        .breadcrumb-separator {{
            margin: 0 5px;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1 class="title">Disk Space Usage: <span id="current-path">{title}</span></h1>
    <div class="breadcrumb" id="breadcrumb"></div>
    <div class="chart-container" id="chart-container"></div>
    
    <script>
        const completeTree = {json.dumps(complete_tree)};
        let currentPath = '{title}';
        let navigationHistory = ['{title}'];
        function generateColor(index) {{
            // Bootstrap table-striped colors (alternating white and light gray)
            return index % 2 === 0 ? '#ffffff' : '#f8f9fa';
        }}
        
        function formatSize(bytes) {{
            const units = ['B', 'KB', 'MB', 'GB', 'TB'];
            let size = bytes;
            let unitIndex = 0;
            
            while (size >= 1024 && unitIndex < units.length - 1) {{
                size /= 1024;
                unitIndex++;
            }}
            
            return `${{size.toFixed(1)}} ${{units[unitIndex]}}`;
        }}
        
        function prepareChartData(directoryData) {{
            if (!directoryData || !directoryData.children) return [];
            
            const items = Object.entries(directoryData.children).map(([name, info]) => ([
                name, info.size, info.is_directory, info.path
            ]));
            
            // Sort by size (largest first)
            const sortedItems = items.sort((a, b) => b[1] - a[1]);
            
            // Filter out very small items (less than 1% of total)
            const totalSize = sortedItems.reduce((sum, item) => sum + item[1], 0);
            const largeItems = sortedItems.filter(item => item[1] > totalSize * 0.01);
            
            if (largeItems.length < sortedItems.length) {{
                const otherSize = sortedItems
                    .filter(item => item[1] <= totalSize * 0.01)
                    .reduce((sum, item) => sum + item[1], 0);
                largeItems.push(["Other", otherSize, false, null]);
            }}
            
            // Convert to chart format
            const filteredTotal = largeItems.reduce((sum, item) => sum + item[1], 0);
            return largeItems.map(([name, size, isDirectory, path], index) => ({{
                name: name,
                size: size,
                formatted_size: formatSize(size),
                percentage: (size / filteredTotal) * 100,
                color_index: index,
                is_directory: isDirectory,
                path: path
            }}));
        }}
        
        let currentData = prepareChartData(completeTree);
        
        function updateBreadcrumb() {{
            const breadcrumbDiv = document.getElementById('breadcrumb');
            breadcrumbDiv.innerHTML = '';
            
            navigationHistory.forEach((path, index) => {{
                if (index > 0) {{
                    const separator = document.createElement('span');
                    separator.className = 'breadcrumb-separator';
                    separator.textContent = '/';
                    breadcrumbDiv.appendChild(separator);
                }}
                
                const item = document.createElement('span');
                item.className = 'breadcrumb-item';
                item.textContent = index === 0 ? path.split('/').pop() || path : path.split('/').pop();
                item.onclick = () => navigateToHistoryIndex(index);
                breadcrumbDiv.appendChild(item);
            }});
        }}
        
        function navigateToHistoryIndex(index) {{
            if (index < navigationHistory.length - 1) {{
                navigationHistory = navigationHistory.slice(0, index + 1);
                currentPath = navigationHistory[index];
                
                // Find directory in tree and update chart
                const directoryData = findDirectoryInTree(completeTree, currentPath);
                if (directoryData) {{
                    currentData = prepareChartData(directoryData);
                    renderChart();
                }}
                
                document.getElementById('current-path').textContent = currentPath;
                updateBreadcrumb();
            }}
        }}
        
        function renderChart() {{
            const container = document.getElementById('chart-container');
            const containerHeight = container.clientHeight;
            container.innerHTML = '';
            
            currentData.forEach((item, index) => {{
                const bar = document.createElement('div');
                bar.className = 'bar' + (item.is_directory ? ' clickable' : '');
                
                const heightPercent = item.percentage;
                const height = (heightPercent / 100) * containerHeight;
                
                bar.style.height = height + 'px';
                bar.style.backgroundColor = generateColor(item.color_index);
                
                // Add click handler for directories
                if (item.is_directory && item.path) {{
                    bar.onclick = () => navigateToDirectory(item.path, item.name);
                }}
                
                const text = document.createElement('div');
                text.className = 'bar-text';
                text.textContent = `${{item.percentage.toFixed(1)}}% (${{item.formatted_size}}) - ${{item.name}}`;
                
                bar.appendChild(text);
                container.appendChild(bar);
            }});
        }}
        
        function findDirectoryInTree(tree, targetPath) {{
            if (tree.path === targetPath) {{
                return tree;
            }}
            
            for (const [name, child] of Object.entries(tree.children)) {{
                if (child.is_directory) {{
                    const found = findDirectoryInTree(child, targetPath);
                    if (found) return found;
                }}
            }}
            return null;
        }}
        
        
        function navigateToDirectory(path, name) {{
            console.log('Navigating to:', path);
            
            // Find directory in embedded tree
            const directoryData = findDirectoryInTree(completeTree, path);
            
            if (!directoryData) {{
                alert(`Directory not found: ${{path}}`);
                return;
            }}
            
            // Add to navigation history
            navigationHistory.push(path);
            currentPath = path;
            
            // Update display
            document.getElementById('current-path').textContent = path;
            updateBreadcrumb();
            
            // Update chart data
            currentData = prepareChartData(directoryData);
            renderChart();
        }}
        
        // Initial render
        window.addEventListener('load', () => {{
            updateBreadcrumb();
            renderChart();
        }});
        
        window.addEventListener('resize', () => {{
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
    
    create_html_chart(data, str(path), str(path))
    return 0


if __name__ == "__main__":
    exit(main())