#!/usr/bin/env python3

import argparse
from pathlib import Path
import json


def scan_directory_recursive(path, max_depth=3, current_depth=0, root_path=None):
    """Recursively scan directory tree and return complete structure."""
    if root_path is None:
        root_path = path
    
    if current_depth >= max_depth:
        # Just return size for very deep directories - avoid rglob to prevent double counting
        try:
            size = 0
            for item in path.iterdir():
                if item.is_file() and not item.is_symlink():
                    size += item.stat().st_size
                elif item.is_dir() and not item.is_symlink():
                    # For max depth, just get the immediate directory size, don't recurse
                    size += sum(f.stat().st_size for f in item.rglob('*') if f.is_file() and not f.is_symlink())
            return {'size': size, 'path': str(path.relative_to(root_path))}
        except (PermissionError, OSError):
            return {'size': 0, 'path': str(path.relative_to(root_path))}
    
    items = []
    total_size = 0
    
    for item in path.iterdir():
        try:
            if item.is_file() and not item.is_symlink():
                file_size = item.stat().st_size
                items.append({
                    'name': item.name,
                    'size': file_size,
                    'path': str(item.relative_to(root_path))
                })
                total_size += file_size
            elif item.is_dir() and not item.is_symlink():
                # Recursively scan subdirectory
                subdir_data = scan_directory_recursive(item, max_depth, current_depth + 1, root_path)
                subdir_data['name'] = item.name
                items.append(subdir_data)
                total_size += subdir_data['size']
        except (PermissionError, OSError):
            continue
    
    # Sort by size (largest first)
    items.sort(key=lambda x: x['size'], reverse=True)
    
    # Filter out very small items (less than 1% of total) and group into "Other"
    if total_size > 0:
        large_items = [item for item in items if item['size'] > total_size * 0.01]
        small_items = [item for item in items if item['size'] <= total_size * 0.01]
        
        if small_items:
            other_size = sum(item['size'] for item in small_items)
            large_items.append({
                'name': 'Other',
                'size': other_size,
                'path': None
            })
        
        children = large_items
    else:
        children = items
    
    result = {
        'size': total_size,
        'path': str(path.relative_to(root_path))
    }
    if children:
        result['children'] = children
    return result

def scan_directory(path):
    """Scan directory and return immediate children (for compatibility)."""
    tree = scan_directory_recursive(path, max_depth=1)
    # Convert list back to dict for backward compatibility
    return {item['name']: item for item in tree['children']}


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
        const rootPath = '{title}';
        let currentPath = '.';
        let navigationHistory = ['.'];
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
        
        let currentData = completeTree.children || [];
        
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
                const displayPath = path === '.' ? rootPath : rootPath + '/' + path;
                item.textContent = index === 0 ? displayPath.split('/').pop() || displayPath : path.split('/').pop() || path;
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
                    currentData = directoryData.children || [];
                    renderChart();
                }}
                
                const displayPath = currentPath === '.' ? rootPath : rootPath + '/' + currentPath;
                document.getElementById('current-path').textContent = displayPath;
                updateBreadcrumb();
                
                // Update browser history
                history.replaceState({{ path: currentPath }}, '', `#${{encodeURIComponent(currentPath)}}`);
            }}
        }}
        
        function renderChart() {{
            const container = document.getElementById('chart-container');
            container.innerHTML = '';
            
            // Calculate total size for percentage calculations
            const totalSize = currentData.reduce((sum, item) => sum + item.size, 0);
            
            currentData.forEach((item, index) => {{
                const bar = document.createElement('div');
                const isDirectory = item.children && item.children.length > 0;
                bar.className = 'bar' + (isDirectory ? ' clickable' : '');
                
                const percentage = totalSize > 0 ? (item.size / totalSize) * 100 : 0;
                bar.style.height = percentage + '%';
                bar.style.backgroundColor = generateColor(index);
                
                // Add click handler for directories
                if (isDirectory && item.path) {{
                    bar.onclick = () => navigateToDirectory(item.path, item.name);
                }}
                
                const text = document.createElement('div');
                text.className = 'bar-text';
                text.textContent = `${{percentage.toFixed(1)}}% (${{formatSize(item.size)}}) - ${{item.name}}`;
                
                bar.appendChild(text);
                container.appendChild(bar);
            }});
        }}
        
        function findDirectoryInTree(tree, targetPath) {{
            if (tree.path === targetPath) {{
                return tree;
            }}
            
            for (const child of tree.children || []) {{
                if (child.children && child.children.length > 0) {{
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
            const displayPath = path === '.' ? rootPath : rootPath + '/' + path;
            document.getElementById('current-path').textContent = displayPath;
            updateBreadcrumb();
            
            // Update chart data
            currentData = directoryData.children || [];
            renderChart();
            
            // Add to browser history
            history.pushState({{ path: path }}, '', `#${{encodeURIComponent(path)}}`);
        }}
        
        // Handle browser back/forward buttons
        window.addEventListener('popstate', (event) => {{
            if (event.state && event.state.path) {{
                const targetPath = event.state.path;
                
                // Find directory in tree
                const directoryData = findDirectoryInTree(completeTree, targetPath);
                if (directoryData) {{
                    // Update internal state to match browser history
                    currentPath = targetPath;
                    
                    // Rebuild navigation history up to this point
                    navigationHistory = ['.'];
                    if (targetPath !== '.') {{
                        // For simplicity, just add the target path
                        // In a more sophisticated implementation, we'd rebuild the full path
                        navigationHistory.push(targetPath);
                    }}
                    
                    // Update display
                    const displayPath = targetPath === '.' ? rootPath : rootPath + '/' + targetPath;
                    document.getElementById('current-path').textContent = displayPath;
                    updateBreadcrumb();
                    currentData = directoryData.children || [];
                    renderChart();
                }}
            }}
        }});
        
        // Initial render
        window.addEventListener('load', () => {{
            // Check for initial hash in URL
            const hash = window.location.hash;
            if (hash.length > 1) {{
                const initialPath = decodeURIComponent(hash.substring(1));
                const directoryData = findDirectoryInTree(completeTree, initialPath);
                if (directoryData) {{
                    currentPath = initialPath;
                    navigationHistory = ['.'];
                    if (initialPath !== '.') {{
                        navigationHistory.push(initialPath);
                    }}
                    const displayPath = initialPath === '.' ? rootPath : rootPath + '/' + initialPath;
                    document.getElementById('current-path').textContent = displayPath;
                    currentData = directoryData.children || [];
                }}
            }}
            
            updateBreadcrumb();
            renderChart();
            
            // Set initial browser history state
            history.replaceState({{ path: currentPath }}, '', `#${{encodeURIComponent(currentPath)}}`);
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