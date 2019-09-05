# Copyright (C) 2019  NCC Group
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from winstrument.data.module_message import ModuleMessage
from tabulate import tabulate
import json
from collections import namedtuple
import os


def format_table(messagelist, verbosity=0):
    if verbosity < 1:
        return tabulate([elipsize_message(message).flatten() for message in messagelist],headers="keys")
    else:
        return tabulate([message.flatten() for message in messagelist],headers="keys")
def format_json(messagelist,verbosity=0):
    return json.dumps([message.flatten() for message in messagelist])


def mask_to_str(mask, enum_map):
    """
    Attempts to produce a string of set flags from the given mask and dict of enum value-to-name mappings
    mask: int - bitmask from e.g. Windows API 
    enum_map: dict[int -> str]
    returns a string in the form: FLAG 1 | FLAG 2 ...
    """
    flags_set = []
    for flag in enum_map.keys():
        if mask & flag == flag:
            flags_set.append(enum_map[flag])
    return " | ".join(flags_set)

def format_grep(messagelist, verbosity = 0):

    outlines = []
    sep = "|"
    for message in messagelist:
        outline = f"{message.module}{sep}{message.time}{sep}{message.target}"
        for k,v in message.data.items():
            outline += f"{sep}{k}:{v}"
        outlines.append(outline)
    return "\n".join(outlines)

def elipsize_path(path):
    """
    Converts a full Windows path into a path like C:/.../filename.exe
    path - str
    Return - shortened path: str
    """
    path_start, tail = os.path.splitdrive(path)
    last_part = os.path.split(tail)[-1]
    return f"{path_start}/.../{last_part}"

def elipsize_message(message):
    """
    Creates a new message from the original with the target path shortend
    """
    new_target = elipsize_path(message.target)
    return ModuleMessage(message.module,new_target,message.data,time=message.time)

def get_formatters():
    """
    Returns namedtuple of all available formatters and human readable names
    Fields:
    name - human readable name for use in command arguments etc
    function - function object to the formatter
    """
    Formatter = namedtuple("Formatter","name function")
    formatters = [Formatter(name="table",function=format_table),
    Formatter(name="json",function=format_json),
    Formatter(name="grep",function=format_grep)]
    return formatters

def get_formatter(name):
    """
    Returns the formatter callback for the formatter with the speicfied name.
    Returns None if no such formatter exists
    """
    formatter_list = get_formatters()
    for formatter in formatter_list:
        if name.lower() == formatter.name.lower():
            return formatter.function
    raise ValueError(f"No formatter {name}")