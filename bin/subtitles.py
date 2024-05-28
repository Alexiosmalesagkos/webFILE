# Code by Sergio1260
# Obtains info and extracts tracks from a video file
# It is used for the video player subtitles
# Also fixes weird things with the codecs when
# converting formats like ASS/SSA to webVTT

from os import sep, linesep, remove, mkdir
from subprocess import Popen, PIPE
from multiprocessing import Process, Queue
from io import StringIO
import pysubs2
from random import choice
from sys import path
from glob import glob
from os.path import exists

cache_dir = path[0]
del path # Free memory
cache_dir=cache_dir.split(sep)
cache_dir.pop()
cache_dir="/".join(cache_dir)
cache_dir+="/cache/"


def get_codec(source, index):
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', f's:{index}',
        '-show_entries', 'stream=codec_name',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        source
    ]
    return Popen(cmd, stdout=PIPE).communicate()[0].decode('UTF8').strip()


def convert(src, ret):
    subs = pysubs2.SSAFile.from_string(src.decode('UTF8'))
    del src # Free memory
    with StringIO() as tmp:
        subs.to_file(tmp, "vtt", apply_styles=False)
        del subs # Free memory 
        out = tmp.getvalue()
    
    subs = pysubs2.SSAFile.from_string(out)
    del out # Free memory
    grouped_events,oldtxt = {},""

    for event in subs:
        key = (event.start, event.end)
        if key not in grouped_events:
            if oldtxt != event.text:
                grouped_events[key] = event.text
        elif oldtxt != event.text:
            
            grouped_events[key] += " "+event.text
        oldtxt = event.text
    
    del subs.events, oldtxt  # Free memory
    subs.events = [
        pysubs2.SSAEvent(start=start, end=end, text=text)
        for (start, end), text in grouped_events.items()
    ]
    del grouped_events # Free memory

    with StringIO() as tmp:
        subs.to_file(tmp, "vtt", apply_styles=False)
        del subs  # Free memory
        out = tmp.getvalue()

    ret.put(out) # Return values


def get_info(source):
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 's',
        '-show_entries', 'stream_tags=title',
        '-of', 'csv=p=0',
        source
    ]
    try:
        output = Popen(cmd, stdout=PIPE).communicate()[0].decode('UTF8').split(linesep)
        return ["Track " + str(index + 1) if not title else title for index, title in enumerate(output) if title]
    except Exception: return []


# Checks if it exists both dir and index file
# If they are missing it creates them again
def get_subs_cache():
    file=cache_dir+"index.txt"
    if exists(file):
        file = open(file,"r").read()
        file = file.split("\n\n")
        file.pop()
    else:
        if not exists(cache_dir[:-1]):
            mkdir(cache_dir[:-1])
        open(file,"w").close()
        files = glob(cache_dir+"*", recursive=False)
        for x in files: remove(x)
        del files; file = []
    
    dic = {}
    for x in file:
        x=x.split("\n")
        dic[x[0]]=[x[1],x[2]]

    return dic


def save_subs_cache(dic):
    out=""
    for x in dic:
       out+=x+"\n"
       out+=dic[x][0]+"\n"+dic[x][1]
       out+="\n\n"
    open(cache_dir+"index.txt","w").write(out)
    del out # Free memory


def random_str(length):
    characters = [chr(i) for i in range(48, 58)] + [chr(i) for i in range(65, 91)] + [chr(i) for i in range(97, 123)]
    random_string = ''.join(choice(characters) for _ in range(length))
    return random_string


def get_track(file,index):
    codec = get_codec(file, index)
    cmd = [
        'ffmpeg', '-i', file,
        '-map', f'0:s:{index}',
        '-f', codec, '-'
    ]
    process = Popen(cmd, stdout=PIPE, stderr=PIPE)
    source, _ = process.communicate()
    del process # Free memory
    
    if not codec=="webvtt":
        ret = Queue()
        proc = Process(target=convert, args=(source, ret))
        del source # Free memory
        proc.start(); out = ret.get(); proc.join()
        del proc, ret # Free memory
        return out

    else: return source.decode("UTF-8")
    
