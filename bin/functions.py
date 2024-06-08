from os.path import commonpath, join, isdir, relpath, abspath
from os.path import getmtime, getsize, exists
from datetime import datetime as dt
from os import listdir, pardir, sep, scandir, access, R_OK
from pathlib import Path
from argparse import ArgumentParser

# Some file formats
file_types = {
    "SRC": [".c", ".cpp", ".java", ".py", ".html", ".css", ".js", ".php", ".rb", ".go", ".xml", ".ini", ".json", ".bat", ".cmd", ".sh", ".md", ".xmls", ".yml", ".yaml", ".ini", ".asm", ".cfg", ".sql", ".htm", ".config"],
    "IMG": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".tiff", ".ico", ".webp"],
    "Audio": [".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".wma"],
    "DOC": [".doc", ".docx", ".odt", ".rtf"],
    "DB": [".xls", ".xlsx", ".ods", ".csv", ".tsv", ".db", ".odb"],
    "PP": [".ppt", ".pptx", ".odp"],
    "Video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "PDF": [".pdf"],
    "HdImg": [".iso", ".img", ".vdi", ".vmdk", ".vhd"],
    "Compress": [".zip", ".7z", ".rar", ".tar", ".gzip"],
    "BIN": [".exe", ".dll", ".bin", ".sys", ".so"]
}

# Check if the text is binary
textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))

def init():
    parser = ArgumentParser(description="Arguments for the webFILE")
    parser.add_argument("-b", "--bind", type=str, required=True, help="Specify IP address to bind", metavar="IP")
    parser.add_argument("-p", "--port", type=int, required=True, help="Specify port number")
    parser.add_argument("-d", "--dir", type=str, required=True, help="Specify directory to share")
    parser.add_argument("--dirsize", action="store_true", help="Show folder size")
    parser.add_argument("--subtitle_cache", action="store_true", help="Enable caching of subtitles")
    args = parser.parse_args()
    return args.port, args.bind, args.dir, args.dirsize, args.subtitle_cache

def fix_pth_url(path):
    try:
        return path.replace("'", "%27").replace("&", "%26").replace(chr(92), "%5C").replace("#", "%23")
    except Exception as e:
        print(f"An error occurred in fix_pth_url: {e}")
        return path

def sort_results(paths, folder_path):
    try:
        dirs = []
        files = []
        for x in paths:
            fix = join(folder_path, x)
            if isdir(fix):
                dirs.append(x)
            else:
                files.append(x)
        dirs.sort()
        files.sort()
        return dirs + files
    except Exception as e:
        print(f"An error occurred in sort_results: {e}")
        return paths

def readable(num, suffix="B"):
    try:
        for unit in ["", "Ki", "Mi", "Gi", "Ti"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f} Yi{suffix}"
    except Exception as e:
        print(f"An error occurred in readable: {e}")
        return f"{num} {suffix}"

def unreadable(size_str):
    try:
        if size_str != "0":
            size, unit = size_str.split(" ")
            size = float(size)
            units = {'B': 1, 'KiB': 1024, 'MiB': 1024**2, 'GiB': 1024**3, 'TiB': 1024**4}
            return int(size * units.get(unit, 1))
        else:
            return 0
    except Exception as e:
        print(f"An error occurred in unreadable: {e}")
        return 0

def unreadable_date(date_str):
    try:
        if date_str == '##-##-#### ##:##:##':
            return float(0)
        return dt.strptime(date_str, '%d-%m-%Y %H:%M:%S').timestamp()
    except Exception as e:
        print(f"An error occurred in unreadable_date: {e}")
        return 0

def get_file_type(path):
    try:
        if isdir(path):
            return "DIR"
        else:
            file_extension = Path(path).suffix
            for types, extensions in file_types.items():
                if file_extension in extensions:
                    return types
            with open(path, mode="rb") as file:
                if not is_binary_string(file.read(1024)):
                    return "Text"
            return "File"
    except Exception as e:
        print(f"An error occurred in get_file_type: {e}")
        return "Unknown"

def is_subdirectory(parent, child):
    try:
        return commonpath([parent]) == commonpath([parent, child])
    except Exception as e:
        print(f"An error occurred in is_subdirectory: {e}")
        return False

def get_directory_size(directory):
    total = 0
    try:
        for entry in scandir(directory):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_directory_size(entry.path)
    except NotADirectoryError:
        return getsize(directory)
    except PermissionError:
        return 0
    except Exception as e:
        print(f"An error occurred in get_directory_size: {e}")
        return 0
    return total

def get_folder_content(folder_path, root, folder_size):
    try:
        items = listdir(folder_path)
        items = sort_results(items, folder_path)
        content = []
        for item in items:
            try:
                item_path = join(folder_path, item)
                description = get_file_type(item_path)
                size = "0"
                if description != "DIR":
                    size = readable(getsize(item_path))
                elif folder_size:
                    size = readable(get_directory_size(item_path))
                try:
                    mtime = dt.fromtimestamp(getmtime(item_path)).strftime("%d-%m-%Y %H:%M:%S")
                except Exception as e:
                    mtime = "##-##-#### ##:##:##"
                    print(f"An error occurred in getting mtime for {item_path}: {e}")
                item_path = relpath(item_path, start=root).replace(sep, "/")
                content.append({'name': item, 'path': item_path, 'description': description, "size": size, "mtime": mtime})
            except Exception as e:
                print(f"An error occurred while processing item {item}: {e}")
        return content
    except Exception as e:
        print(f"An error occurred in get_folder_content: {e}")
        return []


