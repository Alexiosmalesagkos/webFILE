from os.path import join, isdir, relpath, exists, pardir, abspath, getsize, isfile
from functions import get_folder_content, is_subdirectory, fix_pth_url, unreadable, unreadable_date
from subtitles import cache_dir, get_track, random_str, save_subs_cache, get_subs_cache, get_info
from os import access, R_OK, sep, listdir, remove

def sort_contents(folder_content, sort):
    try:
        if sort == "nd":
            dirs = [d for d in folder_content if d['description'] == 'DIR']
            files = [d for d in folder_content if d['description'] != 'DIR']
            return files[::-1] + dirs[::-1]
        elif sort in ("sp", "sd"):
            out = sorted(folder_content, key=lambda x: unreadable(x['size']))
            return out[::-1] if sort == "sp" else out
        elif sort in ("dp", "dd"):
            out = sorted(folder_content, key=lambda x: unreadable_date(x['mtime']))
            return out[::-1] if sort == "dp" else out
        else:
            return folder_content
    except KeyError as e:
        print(f"KeyError: {e} not found in folder content.")
        return folder_content
    except Exception as e:
        print(f"An error occurred during sorting: {e}")
        return folder_content

def isornot(path, root):
    try:
        path = path.replace("/", sep)
        path = abspath(join(root, path))
        if is_subdirectory(root, path):
            if not exists(path):
                raise FileNotFoundError(f"Path not found: {path}")
            if not access(path, R_OK):
                raise PermissionError(f"Permission denied: {path}")
        else:
            raise PermissionError(f"Path is not a subdirectory of root: {path}")
        return path
    except Exception as e:
        print(f"An error occurred in isornot: {e}")
        raise

def filepage_func(path, root, filetype):
    try:
        path = relpath(isornot(path, root), start=root)
        folder = sep.join(path.split(sep)[:-1])
        name = path.split(sep)[-1]
        out = get_folder_content(join(root, folder), root, False)
        path = path.replace(sep, "/")
        lst = [x["path"] for x in out if x["description"] == filetype]
        nxt = lst[(lst.index(path) + 1) % len(lst)]
        prev = lst[lst.index(path) - 1]
        nxt = "/" + fix_pth_url(nxt)
        prev = "/" + fix_pth_url(prev)
        return prev, nxt, name, path
    except Exception as e:
        print(f"An error occurred in filepage_func: {e}")
        return None, None, None, None

def index_func(folder_path, root, folder_size, sort):
    try:
        folder_path = isornot(folder_path, root)
        is_root = folder_path == root
        folder_content = get_folder_content(folder_path, root, folder_size)
        parent_directory = abspath(join(folder_path, pardir))
        if parent_directory == root:
            parent_directory = ""
        else:
            parent_directory = relpath(parent_directory, start=root)
        folder_path = relpath(folder_path, start=root)
        if folder_path == ".":
            folder_path = ""
        folder_path = "/" + folder_path.replace(sep, "/")
        parent_directory = parent_directory.replace(sep, "/")
        folder_content = sort_contents(folder_content, sort)
        par_root = (parent_directory == "")
        return folder_content, folder_path, parent_directory, is_root, par_root
    except Exception as e:
        print(f"An error occurred in index_func: {e}")
        return [], "", "", False, False

def sub_cache_handler(arg, root, subtitle_cache):
    try:
        separator = arg.find("/")
        index = arg[:separator]
        file = arg[separator + 1:]
        file = isornot(file, root)
        if subtitle_cache:
            dic = get_subs_cache()
            available = [x[0] for x in dic.values()]
            todelete = [x for x in listdir(cache_dir) if x not in available and isfile(join(cache_dir, x))]
            if "index.txt" in todelete:
                todelete.remove("index.txt")
            for x in todelete:
                try:
                    remove(join(cache_dir, x))
                except OSError as e:
                    print(f"Error removing file {x}: {e}")
            filesize = str(getsize(file))
            if arg not in dic:
                out = get_track(file, index)
                dic = get_subs_cache()
                if arg not in dic:
                    cache = random_str()
                    while cache in available:
                        cache = random_str()
                    dic[arg] = [cache, filesize]
                    with open(join(cache_dir, cache), "w", newline='') as f:
                        f.write(out)
                    save_subs_cache(dic)
            else:
                fix = (filesize == dic[arg][1])
                cache_path = join(cache_dir, dic[arg][0])
                if not fix or not exists(cache_path):
                    out = get_track(file, index)
                    dic[arg] = [dic[arg][0], filesize]
                    with open(cache_path, "w", newline='') as f:
                        f.write(out)
                    save_subs_cache(dic)
                else:
                    with open(cache_path, "r") as f:
                        out = f.read()
        else:
            out = get_track(file, index)
        return out
    except Exception as e:
        print(f"An error occurred in sub_cache_handler: {e}")
        return ""

    return out
