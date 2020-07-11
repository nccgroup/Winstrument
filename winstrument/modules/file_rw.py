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
        self.files_read = {}
        self.files_written = {}


        self.modes = {
             "0x80000000": "GENERIC_READ",
             "0x40000000": "GENERIC_WRITE",
             "0xc0000000": "GENERIC_READ | GENERIC_WRITE",
             "0x10000000": "GENERIC_ALL"
        }

    def get_files_written(self):
        return self.files_written

    def get_files_read(self):
        return self.files_read

    def on_message(self, message,data):
        if message["type"] == "error":
            print("Error: {0}".format(message))
            return
        date=None
        payload = message["payload"]

        function = payload["function"]
        if function == "CreateFileW":
            modenum = payload["mode"]
            modename = self. modes.get(payload["mode"], modenum)
            fh = payload["fh"]
            if fh == 0xffffffff: #INVALID HANDLE
                fh = "INVALID_HANDLE_VALUE"
            if modename == "GENERIC_READ":
                if not fh in self.files_read: 
                  data = {"function": function, "fh": fh, "path": payload["path"], "mode": modename}
                  self.files_read[fh] = data
            elif modename == "GENERIC_WRITE":
                if not fh in self.files_written:
                  data = {"function": function, "fh": fh, "path": payload["path"], "mode": modename}
                  self.files_written[fh] = data
            else: #both
                if not fh in self.files_read: 
                  data = {"function": function, "fh": fh, "path": payload["path"], "mode": modename}
                  self.files_read[fh] = data
                if not fh in self.files_written:
                  data = {"function": function, "fh": fh, "path": payload["path"], "mode": modename}
                  self.files_written[fh] = data
        elif function == "WriteFile":
            fh = payload["fh"]
            numbytes = payload["bytes_written"]
            if fh in self.files_written:
                prevbytes = self.files_written[fh].get("bytes",0)
                self.files_written[fh]["function"] = function
                self.files_written[fh]["bytes"] = prevbytes + numbytes
              #  path = self.files_written[fh]["path"]
              #  data = {"function": function, "fh": fh, "path": path, "bytes": numbytes}
   
        elif function == "ReadFile" or function == "ReadFileEx":
            fh = payload["fh"]
            numbytes = payload.get("bytes_read",payload["bytes_to_read"]) #no bytes_read for ReadFileEx
            if fh in self.files_read:
               prevbytes= self.files_read[fh].get("bytes",0)
               self.files_read[fh]["function"] = function
               self.files_read[fh]["bytes"] = prevbytes + numbytes
               # path = self._file_handles[fh]["path"]
               # data = {"function" : function, "fh": fh, "path":path, "bytes":numbytes}
        # 
      #  if data:
          #  self.write_message(data)
    def on_finish(self):
        for fh in self.files_read.values():
            if fh.get("bytes",0) > 0:
                self.write_message(fh)
        for fh in self.files_written.values():
            if fh.get("bytes",0) > 0:
                self.write_message(fh)