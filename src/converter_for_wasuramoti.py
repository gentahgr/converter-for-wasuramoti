#!/usr/bin/env python3
# -*- coding: utf-8
"""
Hyakunin isshu audio converter for WASURAMOTI

読み上げ音声コンバータ for わすらもち

音声ソース:
文英堂　シグマベスト　原色　小倉百人一首　添付CD内 MP3 data
ISBN:978-4-578-24504-9

Copyright (C) 2023, Gentaro Muramatsu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---
dependency: ffmpeg https://ffmpeg.org/

default source directory: ./source
default target directory: ./wasuramoti_reader/serino
"""

import subprocess
from pathlib import Path
import argparse
import sys
import re
import logging
from typing import List, Dict, Optional

__version__ = 0.1

# constants

logger = logging.getLogger(__name__)

FFMPEG_executable_name = "ffmpeg"
FFMEPG_marker = b"ffmpeg"

default_prefix = 'serino'
default_source_directory = Path('./source')
default_dest_directory = Path('./wasuramoti_reader/' + default_prefix)


def generate_file(ffmpeg: Path, source: Path, dest: Path, start_time: str, end_time: str) -> None:
    """split specified range of original file and convert it into ogg vorbis format.
    """
    cmd = [ffmpeg, '-i', source, '-y', '-ss', start_time, '-to', end_time, '-acodec', 'libvorbis', dest]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, check=False)
    if p.returncode != 0:
        logger.error("Execution failure: cmd={}, stderr={}, stdout={}".format(cmd, p.stderr, p.stdout))
        return

    logger.debug("Execution result: returncode={} stderr={}, stdout={}".format(p.returncode, p.stderr, p.stdout))


def detect_silence(ffmpeg: Path, source: Path, silence_threshold, silence_duration) -> List[Dict[str, str]]:
    """Find silence part and return array of silence ranges

        Thanks to chatGPT
    """
    cmd = [ffmpeg, '-i', source, '-af', 'silencedetect=noise={}:d={}'.format(silence_threshold, silence_duration),
           '-f', 'null', '-']
    detect_silence_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
    logger.debug("Silent detection result: ".format(detect_silence_output))
    silent_parts = []
    for line in detect_silence_output.splitlines():
        logger.debug(line)
        if 'silence_start' in line:
            start_time = line.split('silence_start: ')[1].split(' ')[0]
            silent_parts.append({'start': start_time})
        elif 'silence_end' in line:
            end_time = line.split('silence_end: ')[1].split(' ')[0]
            silent_parts[-1]['end'] = end_time

    return silent_parts


def split_and_generate_file(ffmpeg: Path, head: str, src: Path, dest_dir: Path, prefix: str):
    
    silences = detect_silence(ffmpeg, src, '-50dB', '0.4')
    if len(silences) != 4:
        logger.warning("File {} could be split at unexpected points".format(str(src)))
        logger.debug("silences: {}".format(silences))

    generate_file(ffmpeg, src, dest_dir / ("{}_{}_1.ogg".format(prefix, head)), silences[0]["end"], silences[1]["start"])
    generate_file(ffmpeg, src, dest_dir / ("{}_{}_2.ogg".format(prefix, head)), silences[1]["end"], silences[2]["start"])


def validate_dir_path(msg: str, d: Path) -> bool:
    """check if valid data is in the directory"""

    p = Path(d)
    if not p.exists():
        logger.error("{} {} does not exist.".format(msg, d))
        return False

    elif not p.is_dir():
        logger.error("{} {} is not a directory.".format(msg, d))
        return False
    
    return True


def convert_files_main(ffmpeg: Path, src_dir: Path, dest_dir: Path, reader_name: str):
    """Generate sound files for Wasramoti

    """
    
    # get list of files in the source directory to look up file name.
    # path pattenn
    source_file_pattern = re.compile(r'^(0[0-9][0-9]|100)_.*\.mp3')

    # check existance
    src_path = Path(src_dir)
    if not validate_dir_path("source directory", src_dir):
        return

    dest_path = Path(dest_dir)
    if not validate_dir_path("target directory", dest_dir):
        return

    files = [f for f in src_path.iterdir() if f.is_file() and source_file_pattern.match(f.name)]
    
    # check duplicate entry
    source_files = {"{:03d}".format(i): None for i in range(0, 101)}
    for f in files:
        head = f.name[0:3]
        if head in source_files:
            if source_files[head] is None:
                source_files[head] = f
            else:
                logger.warning("{} found twice or more. Only the first file is taken".format(head))
        else:
            logger.warning("irregular file header found: {}".format(head))

    not_found = [k for k in source_files.keys() if source_files[k] is None]
    if len(not_found) > 0:
        logger.warning("File for some indexes are not found: {}".format(not_found))
        
    # convert 000
    if source_files["000"] is not None:
        logger.info("Processing {}...".format("000"))
        
        generate_file(ffmpeg, source_files["000"], dest_path / (reader_name + "_000_1.ogg"), "0:0.53", "0:16.62")
        generate_file(ffmpeg, source_files["000"], dest_path / (reader_name + "_000_2.ogg"), "0:17.93", "0:25.98")
    else:
        logger.info("Skipped: {}".format("000"))
    
    # convert 001 to 100
    for i in range(100):
        # i: 0..99 -> head: 001 .. 100
        head = "{:03d}".format(i + 1)
        if head in source_files and source_files[head] is not None:
            logger.info("Processing {}...".format(head))
            split_and_generate_file(ffmpeg, head, source_files[head], dest_path, reader_name)
        else:
            logger.info("Skipped: {}".format(head))


def get_ffmpeg_path(ffmpeg_opt_path: Optional[Path]) -> Optional[Path]:

    defpath = Path(__file__).parent / FFMPEG_executable_name

    paths = []
    if ffmpeg_opt_path is not None:
        paths.append(ffmpeg_opt_path)
    paths.append(Path(defpath))
    paths.append(Path(FFMPEG_executable_name))  # add default search path

    for p in paths:
        # validte ffmepg executable
        logger.debug("Trying to execute {}".format(str(p)))
        try:
            proc = subprocess.run([str(p), '-version'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            if proc.returncode == 0 and FFMEPG_marker in proc.stdout:
                logger.info("FFMPEG path: {}".format(p))
                return p
        except OSError:
            # Skip execution failure and try another
            logger.debug("Execution failure.")
            pass

    logger.error("Valid ffmpeg executable did not found.")
    return None


def config_logger(debug: bool) -> None:
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)


def main(argv) -> int:

    parser = argparse.ArgumentParser(description='Generate sound file for Wasramoti')
    parser.add_argument('--src', type=Path, nargs='?', metavar='DIR',
                        const=default_source_directory, default=default_source_directory,
                        help='directory where source files are stored')
    parser.add_argument('--dst', type=Path, nargs='?', metavar='DIR',
                        const=default_dest_directory, default=default_dest_directory,
                        help='directory where generated files are stored')
    parser.add_argument('--prefix', type=str, nargs='?', metavar='NAME',
                        const=default_prefix, default=default_prefix,
                        help='prefix string for each sound file (default: {})'.format((default_prefix)))
    parser.add_argument('--ffmpeg-path', type=Path, nargs='?', metavar='FILE', default=None,
                        help='path to ffmpeg executable')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug message')
    params = parser.parse_args(argv[1:])

    config_logger(params.debug)
    logger.debug("Logger configured")
    logger.debug("Params: {}".format(params))

    ffmpeg = get_ffmpeg_path(params.ffmpeg_path)
    if ffmpeg is None:
        print("ffmpeg not found", file=sys.stderr)
        return 1

    # create destination directory
    params.dst.mkdir(parents=True, exist_ok=True)
    convert_files_main(ffmpeg, params.src, params.dst, params.prefix)
    return 0


def get_logger() -> logging.Logger:
    return logger


if __name__ == '__main__':
    sys.exit(main(sys.argv))
