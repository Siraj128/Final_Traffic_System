import os

# Configuration
ROOT_DIR = r'C:\Users\Siraj\Desktop\Traffic_System_Root - Copy'
EXCLUDE_DIRS = {
    'node_modules', '.git', '.venv', 'venv', 'build', 'android', 'ios', 
    '__pycache__', '.dart_tool', '.vscode', '.idea', 'dist', 'out'
}
EXTENSIONS = {
    '.py': 'Python',
    '.dart': 'Dart',
    '.js': 'JavaScript',
    '.html': 'HTML',
    '.css': 'CSS',
    '.json': 'JSON/Config',
    '.yaml': 'YAML/Config',
    '.md': 'Markdown'
}

def count_lines():
    stats = {lang: {'files': 0, 'lines': 0} for lang in EXTENSIONS.values()}
    total_files = 0
    total_lines = 0

    for root, dirs, files in os.walk(ROOT_DIR):
        # Filter excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXTENSIONS:
                lang = EXTENSIONS[ext]
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for line in f)
                        stats[lang]['files'] += 1
                        stats[lang]['lines'] += lines
                        total_files += 1
                        total_lines += lines
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    print("\n" + "="*40)
    print(f"{'Language':<15} | {'Files':<10} | {'Lines':<10}")
    print("-" * 40)
    for lang, data in sorted(stats.items(), key=lambda x: x[1]['lines'], reverse=True):
        if data['files'] > 0:
            print(f"{lang:<15} | {data['files']:<10} | {data['lines']:<10}")
    print("-" * 40)
    print(f"{'TOTAL':<15} | {total_files:<10} | {total_lines:<10}")
    print("="*40 + "\n")

if __name__ == "__main__":
    count_lines()
