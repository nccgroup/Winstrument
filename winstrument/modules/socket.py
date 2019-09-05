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
import sys
import frida
from winstrument.base_module import BaseInstrumentation
class Socket(BaseInstrumentation):
    modulename = "socket"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sockets = []

    def on_message(self, message, data):
        if message["type"] == "send":
            payload = message["payload"]
            self.write_message(payload)