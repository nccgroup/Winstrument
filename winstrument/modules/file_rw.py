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

import frida
import sys
from winstrument.base_module import BaseInstrumentation

class FileRW(BaseInstrumentation):
    modulename = "file_rw"
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self._file_handles = {}
        self.file_writes = []
        self.file_reads  = []

        self.modes = {
             "0x80000000": "GENERIC_READ",
             "0x40000000": "GENERIC_WRITE",
             "0xc0000000": "GENERIC_READ | GENERIC_WRITE",
             "0x10000000": "GENERIC_ALL"
        }

    def get_file_writes(self):
        return self.file_writes

    def get_file_reads(self):
        return self.file_reads

    def on_message(self, message,data):
        if message["type"] == "error":
            print("Error: {0}".format(message))
            return

        payload = message["payload"]

        function = payload["function"]
        if function == "CreateFileW":
            modenum = payload["mode"]
            modename = self. modes.get(payload["mode"], modenum)
            fh = payload["fh"]
            if fh == 0xffffffff: #INVALID HANDLE
                fh = "INVALID_HANDLE_VALUE"
            data = {"function": function, "fh": payload["fh"], "path": payload["path"], "mode": modename}

        elif function == "WriteFile":
            fh = payload["fh"]
            numbytes = payload["bytes_written"]
            if fh in self._file_handles:
                path = self._file_handles[fh]["path"]
                data = {"function": function, "fh": fh, "path": path, "bytes": numbytes}
            else:
               data = None

        elif function == "ReadFile" or function == "ReadFileEx":
            fh = payload["fh"]
            numbytes = payload.get("bytes_read",payload["bytes_to_read"]) #no bytes_read for ReadFileEx
            if fh in self._file_handles:
                path = self._file_handles[fh]["path"]
                data = {"function" : function, "fh": fh, "path":path, "bytes":numbytes}
            else:
                data = None
        if data:
            self.write_message(data)
