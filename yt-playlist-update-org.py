#!/usr/bin/env python3
#
#  Author: Daniel M. German <dmg@turingmachine.org>
#
# Licensed under the GPLv3+
#
# Version 0.1
#
# The purpose of this script is to maintain a table in
# an org file with the contents of a play list in youtube,
# filter and keep those with #+YOUTUBE_UPDATE:
# extract from youtube update the playlist.

# it takes an org file as input and outputs the file
# youtube tables starting with #+YOUTUBE_UPDATE:
# see documentation

# how it is implemented:
#
# for each playlist
#
#   clean titles to remove "|"
#   parse the table, has 5 fields
#      index, datewatched, date published, url, title 
#   len is next
#   run the newplaylist, get list of "date;url;title"; reverse, enumerate from 1
#   filter newplaylist
#   append new items

# requirements:
#  yt-dlp


import sys
import functools
import subprocess
import collections

YouTube = collections.namedtuple('YouTube', ['url', 'offset', 'lines'])


YouTubeRecord = collections.namedtuple('YouTubeRecord',
                                       ["date", "minutes", "id", "title"])

TABLE_MARKER="#+YOUTUBE_UPDATE:"

#print('Number of arguments:', len(sys.argv), 'arguments.', file=sys.stderr)

inputFileName = sys.argv[1]

def split_url_offset(st):
    # Find the position of ":offset="
    offset_pos = st.find(":offset=")
    
    # If ":offset=" is found, split and return the parts
    if offset_pos != -1:
        url = st[:offset_pos]
        offset = st[offset_pos + len(":offset="):]
        try:
            return url.rstrip(), int(offset.rstrip())
        except ValueError:
            raise ValueError(f"Error: 'offset [{offset}]' is not a valid number.")
    
    # If ":offset=" is not found, return the string and None
    return st, 0


def gather_table(acc, line):
     #folds the line with the current accumulator
    (currentRecords, currentTable) = acc

    # the accumulator contains a pair: <sequence of lines or tables, currentTable>

    # if we are in a youtube table and it is a table
    #   keep adding rows
    # otherwise add table to sequence and current line

    # remove end-of-line
    line = line.rstrip("\n")
    # the accumulator is lines and the currently evaluated record
    if currentTable:
        # we are in a list
        if "|" in line:
            # keep adding it to the lines of the youtube record
            return (currentRecords, YouTube(currentTable.url, currentTable.offset, currentTable.lines + [line]))
        else:
            # finish current record and add current line
            return (currentRecords + [ currentTable ] + [line], None)

    elif line.startswith(TABLE_MARKER):
        url, offset = split_url_offset(line[len(TABLE_MARKER)+1:])
        return (currentRecords, YouTube(url, offset, []))
    else:
        return (currentRecords + [line], None)

def parse_yt_video_record(record):
    fields = record.split(";", maxsplit=3)
    # replace / from title so it does not mess org tables
    return fields

def yt_download_list(url):
    # get the playlist of a url

#    print("Retrieving: ", url, file=sys.stderr)
    command =  ['yt-dlp', '--flat-playlist', '--print' ,'%(upload_date)s;%(duration)s;%(id)s;%(title)s']
    result = subprocess.run(command + [url], capture_output=True, text=True)
    if result.returncode != 0:
        print("Unable to download playlist ", result.returncode, file=sys.stderr)
        sys.exit(1)

#    print("got: ", result.stdout)

    output = result.stdout #.encode(encoding='utf-8', errors='ignore')

#    print("--------------------")
#    print(output)
#    print("--------------------")

    # parse it
    videos = output.split('\n')
    videos = map(parse_yt_video_record, videos)
    videos = filter(lambda x: x and len(x[0]) > 1 and len(x) == 4, videos)
    # return the list reversed so we have in order of creation
    videos = map(lambda x: YouTubeRecord(*x), videos)
    return list(videos)[::-1]

def format_yt_record(record):
    i = record[0]
    video = record[1]
    (date, mins, id, title) = video
    
#    print(record[1])
    if mins == 'NA':
       mins = 0
    else:
        mins = float(mins)
    url = "https://www.youtube.com/watch?v=" + id

    title = title.replace('|', '/')

    if date == "NA":
        date = ''
    durationTime = "%d:%02d" % (mins // 60, mins % 60)
    return "|%d| | %s | %s | [[%s][%s]] |%s| "%(i, date,durationTime, url, id, title)


def yt_update_playlist(record):
#    print("Record >>>>>>>")
#    print(record)
#    print("<<<<<<<<<<<<<<")
    lastWatched = len(record.lines) +record.offset
    
    newList = list(enumerate(yt_download_list(record.url)))

#    print("++++++++++++++++")
#    print(already)

#    print("-------------------------------", lastWatched)

    toAppend = list(map(format_yt_record, newList[lastWatched:]))
#    print(toAppend)
#    print("-------------------------------")
    result = [TABLE_MARKER + " " + record.url  + ":offset=" + str(record.offset)] + record.lines + toAppend
    return "\n".join(result)


def process_youtube(record):
    if isinstance(record, YouTube):
#        print("To process record youtube\n")
        return yt_update_playlist(record)
    else:
        return record


    
with open(inputFileName, 'r') as file:

    # break the file into a sequence of lines
    #  or youtube playlist tables

    folded = functools.reduce(gather_table, file, ([], None))
    records = folded[0]

    if folded[1]: # in the middle of tabel
        records = records + [folded[1]]

    records = map(process_youtube, records)

    records = map(print, records)
    list(records)
