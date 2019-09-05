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
from winstrument.base_module import BaseInstrumentation
import win32security

class Impersonate(BaseInstrumentation):
    modulename = "impersonate" 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def on_message(self, message, data):
        if message["type"] == "error":
            print(message)
        else:
            payload = message["payload"]
            token = message["token"]
            sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
            name,domain, _ = win32security.LookupAccountSid(None,sid)
            user = f"{domain}\\{name}"
            data = {"function": payload["function"], "user": user}
            self.write_message(data)
