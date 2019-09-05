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
from datetime import datetime
import winstrument.utils as utils
import os

class ModuleMessage():
    def __init__(self, module, target, data, time=datetime.now().strftime("%Y-%m-%d %T")):
        self.module = module
        self.time = time
        self.target = target
        self.data = data
    def flatten(self):
        fulldata = {"module": self.module, "time": self.time, "target": self.target}
        fulldata.update(self.data)
        return fulldata
    def truncate_path(self):
        """
        Return a copy of the message with the target path elipsized
        """
        return ModuleMessage(self.module, utils.elipsize_path(self.target), self.data, self.time)