from subprocess import Popen
from sys import path, argv
from os.path import exists, isdir
from os import sep
from time import sleep as delay
import logging

# Setup logging
logging.basicConfig(filename='web_file_sharing_server.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

def init():
    try:
        if len(argv) == 1:
            file_path = path[0] + sep + "bin" + sep + "config.cfg"
        else:
            file_path = argv[1]

        with open(file_path, "r") as file:
            config_lines = file.readlines()

        config = {}
        for line in config_lines:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = map(str.strip, line.split(":", 1))
                config[key] = value

        config.setdefault("port", "80")
        config.setdefault("listen", "127.0.0.1")
        config.setdefault("show.folder.size", "false")
        config.setdefault("use.subtitle.cache", "false")

        if "folder" not in config:
            raise ValueError("[CFG_FILE]: A FOLDER PATH IS NEEDED")
        
        root = config["folder"]
        if not (exists(root) and isdir(root)):
            raise ValueError("[CFG_FILE]: THE SPECIFIED FOLDER PATH IS NOT VALID")

        port = config["port"]
        listen = config["listen"]

        subtitle_cache = config["use.subtitle.cache"].upper() == "TRUE"
        folder_size = config["show.folder.size"].upper() == "TRUE"

        if "-" in port:
            start, end = map(int, port.split("-"))
            ports = [str(x) for x in range(start, end + 1)]
        else:
            ports = [x.strip() for x in port.split(",")]

        listen = [x.strip() for x in listen.split(",")]
        return ports, listen, root, folder_size, subtitle_cache

    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Configuration error: {e}")
        print(e)
        exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print("An unexpected error occurred:", e)
        exit(1)

def main():
    try:
        ports, listen, root, folder_size, subtitle_cache = init()
        py_exec = path[0] + sep + "bin" + sep + "main.py"
        python = "python" if sep == chr(92) else "python3"

        for ip in listen:
            for port in ports:
                args = [python, py_exec, "-b", ip, "-p", port, "-d", root]
                if folder_size:
                    args.append("--dirsize")
                if subtitle_cache:
                    args.append("--subtitle_cache")
                Popen(args)
                delay(0.1)

        # Wait forever
        while True:
            delay(1)

    except KeyboardInterrupt:
        print("Server stopped by user.")
        exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print("An unexpected error occurred:", e)
        exit(1)

if __name__ == "__main__":
    main()

