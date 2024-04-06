# Code by Sergio1260

# Obtains info and tracks for the video player


from os import sep, linesep
from actions import isornot
from subprocess import check_output


def track_wk(source,index):
    cmd=f'ffmpeg -i "{source}" -map 0:s:{str(index)} -f webvtt -'
    if sep==chr(92): cmd+=" 2>nul"
    else: cmd+=" 2>/dev/null"
    out = check_output(cmd, shell=True)
    out = str(out, encoding="UTF8")
    return out

def get_info(source):
    cmd="ffprobe -v error -select_streams s -show_entries stream_tags=title -of csv=p=0"
    cmd+=' "'+str(source)+'"'
    if sep==chr(92): cmd+=" 2>nul"
    else: cmd+=" 2>/dev/null"
    out=check_output(cmd, shell=True)
    out=str(out, encoding="UTF8")
    out=out.split(linesep)
    out.pop()
    return out

def get_track(arg,root):
    separator=arg.find("/")
    index=arg[:separator]
    file=arg[separator+1:]
    file=isornot(file,root)
    out=track_wk(file,index)
    return out
