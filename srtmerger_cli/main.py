#!/usr/bin/env python
# author: Iraj Jelodari

import codecs
import datetime
import re
import sys
from enum import StrEnum
from os import PathLike
from typing import Optional

import chardet
from loguru import logger

logger.remove()
logger.add(sys.stdout, level="DEBUG", enqueue=True)
logger.add(sys.stderr, level="WARNING", format="{time} {level} {message}", enqueue=True)


class Colors(StrEnum):
    RED = "#FF003B"
    BLUE = "#00ADFF"
    GREEN = "#B4FF00"
    WHITE = "#FFFFFF"
    YELLOW = "#FFEB00"


TIME_PATTERN = r"\d{1,2}:\d{1,2}:\d{1,2},\d{1,5} --> \d{1,2}:\d{1,2}:\d{1,2},\d{1,5}\r\n"


def detect_encoding(file_path: PathLike):
    with open(file_path, "rb") as f:
        raw_data = f.read(10000)  # Read a chunk of the file
        result = chardet.detect(raw_data)
        return result["encoding"]


class Merger:
    """
    SRT Merger allows you to merge subtitle files, no matter what language
    are the subtitles encoded in. The result of this merge will be a new subtitle
    file which will display subtitles from each merged file.
    """

    def __init__(self, output_path: str = ".", output_name: str = "subtitle_name.srt", output_encoding="utf-8"):
        self.timestamps = []
        self.subtitles = []
        self.lines = []
        self.output_path = output_path
        self.output_name = output_name
        self.output_encoding = output_encoding

    def _insert_bom(self, content, encoding):
        encoding = encoding.replace("-", "").replace("_", "").replace(" ", "").upper()
        if encoding in ["UTF64LE", "UTF16", "UTF16LE"]:
            return codecs.BOM + content
        if encoding in ["UTF8"]:
            return codecs.BOM_UTF8 + content
        if encoding in ["UTF32LE"]:
            return codecs.BOM_UTF32_LE + content
        if encoding in ["UTF64BE"]:
            return codecs.BOM64_BE + content
        if encoding in ["UTF16BE"]:
            return codecs.BOM_UTF32_BE + content
        if encoding in ["UTF32BE"]:
            return codecs.BOM_UTF32_BE + content
        if encoding in ["UTF32"]:
            return codecs.BOM_UTF32 + content
        return content

    def _set_subtitle_color(self, subtitle, color):
        """
        Set a color for subtitle
        """
        return f'<font color="{color!s}">{subtitle!s}</font>' if color else subtitle

    def _put_subtitle_top(self, subtitle):
        """
        Put the subtitle at the top of the screen
        """
        return "{\\an8}" + subtitle

    def _split_dialogs(self, dialogs, subtitle, color=None, top=False):
        for dialog in dialogs:
            if dialog.startswith("\r\n"):
                dialog = dialog.replace("\r\n", "", 1)
            dialog = dialog.removeprefix("\n")
            if dialog == "" or dialog == "\n" or dialog.rstrip().lstrip() == "":
                continue
            try:
                dialog = dialog.removeprefix("\r\n")
                time = dialog.split("\n", 2)[1].split("-->")[0].split(",")[0]
            except Exception:
                continue
            timestamp = datetime.datetime.strptime(time, "%H:%M:%S").timestamp()
            text_and_time = dialog.split("\n", 1)[1]
            texts = text_and_time.split("\n")[1:]
            time = text_and_time.split("\n")[0]
            text = ""
            for t in texts:
                text += t + "\n"
            if text == "" or text == "\n":
                continue
            text = self._set_subtitle_color(text, color)
            if top is True:
                text = self._put_subtitle_top(text)
            text_and_time = "%s\n%s\n" % (time, text)
            # Previuos dialog for same timestamp
            prev_dialog_for_same_timestamp = subtitle["dialogs"][timestamp] = subtitle["dialogs"].get(timestamp, "")
            prev_dialog_without_timestamp = re.sub(TIME_PATTERN, "", prev_dialog_for_same_timestamp)
            if re.findall(TIME_PATTERN, text_and_time):
                time = re.findall(TIME_PATTERN, text_and_time)[0]
            subtitle["dialogs"][timestamp] = text_and_time + prev_dialog_without_timestamp
            self.timestamps.append(timestamp)

    def _encode(self, text):
        codec = self.output_encoding
        try:
            return bytes(text, encoding=codec)
        except Exception as e:
            logger.error('Problem in "{}" to encoding by {}. \nError: {}', repr(text), codec, e)
            return b"An error has been occured in encoding by specifed `output_encoding`"

    def add(self, subtitle_address: PathLike, codec: str | None = None, color=Colors.WHITE, top=False):
        if not codec:
            codec = detect_encoding(subtitle_address)
            logger.debug("Detected codec = {}", codec)
        subtitle = {"address": subtitle_address, "codec": codec, "color": color, "dialogs": {}}
        with open(subtitle_address) as file:
            try:
                data = file.buffer.read().decode(codec)
            except UnicodeDecodeError as err:
                if codec == "ascii":
                    logger.warning("Chardet incorrectly guessed ascii encoding for sub file.\n{}", err)
                    file.buffer.seek(0) # Move buffer pointer again to the beginning
                    data = file.buffer.read().decode("utf-8")
                else:
                    logger.error("Error while decoding:\n{}", err)
                    raise
            dialogs = re.split("\r\n\r|\n\n", data)
            subtitle["data"] = data
            logger.debug("Some decoded data = {}", data[:50])
            subtitle["raw_dialogs"] = dialogs
            self._split_dialogs(dialogs, subtitle, color, top)
            self.subtitles.append(subtitle)

    def get_output_path(self):
        if self.output_path.endswith("/"):
            return self.output_path + self.output_name
        return self.output_path + "/" + self.output_name

    def merge(self):
        self.lines = []
        self.timestamps = list(set(self.timestamps))
        self.timestamps.sort()
        count = 1
        for t in self.timestamps:
            for sub in self.subtitles:
                if t in sub["dialogs"].keys():
                    line = self._encode(sub["dialogs"][t].replace("\n\n", ""))
                    if count == 1:
                        byteOfCount = self._insert_bom(
                            bytes(str(count), encoding=self.output_encoding),
                            self.output_encoding,
                        )
                    else:
                        byteOfCount = "\n".encode(self.output_encoding) + bytes(
                            str(count),
                            encoding=self.output_encoding,
                        )
                    if sub["dialogs"][t].endswith("\n") != True:
                        sub["dialogs"][t] = sub["dialogs"][t] + "\n"
                    dialog = byteOfCount + "\n".encode(self.output_encoding) + line
                    self.lines.append(dialog)
                    count += 1
        if self.lines[-1].endswith(b"\x00\n\x00"):
            self.lines[-1] = self.lines[-1][:-3] + b"\x00"
        if self.lines[-1].endswith(b"\n"):
            self.lines[-1] = self.lines[-1][:-1] + b""
        with open(self.get_output_path(), "w", encoding=self.output_encoding) as output:
            output.buffer.writelines(self.lines)
            logger.success('"{}" created successfully.', output.name)


# How to use?
#
# m = Merger(output_name="new.srt")
# m.add('./test_srt/en.srt')
# m.add('./test_srt/fa.srt', color="yellow", codec="cp1256", top=True)
# m.merge()
