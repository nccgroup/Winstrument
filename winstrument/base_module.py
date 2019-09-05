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
import frida, sys
import os
import collections
from tabulate import tabulate
import toml
import winstrument.utils as utils
from winstrument.data.module_message import ModuleMessage

class BaseInstrumentation:
    modulename = "base_module"
    def __init__(self, session, path, db, settings={}):
        self._settings = settings
        self._session = session
        self._db = db
        self._script = None 
        self._processpath = path
        self._output = []
        self._messages = []


    def write_message(self, message):
        """ Writes the specified message dict to the database and stores in it in _messages as a ModuleMessage data object
        Parms:
            message - dict of key, value pairs
        No return
         """
        modulemessage = ModuleMessage(self.modulename, self._processpath, message)
        self._db.write_message(modulemessage)
        self._messages.append(modulemessage)

    def get_name(self):
        return self.modulename
        
    def load_script(self):
        """
        Load the associated JS file for this moudle into the Frida session, then hook any callbacks etc, and start the script
        """
        with open(os.path.join(os.path.dirname(__file__),"modules","js",f"{self.modulename}.js"),'r') as scriptfile:
            self._script = self._session.create_script(scriptfile.read())
        self.register_callbacks()
        self._script.load()
        self.on_load()
    
    def get_output(self):
        """ Returns a list of ModuleMessage objects
        Each object represents a single message sent by the module """
        return self._messages

    def on_load(self):
        """
        Callback called during load_script after the injected JS is running inside the target. Override in subclasses if desired.
        """
        pass

    def on_message(self, message, data):
        """
        Generic handler for frida's 'message' event.
        Simply saves the raw JSON payload recived as a ModuleMessage object.
        """
        if message["type"] == "error":
            print (f"Error: {message}")
        else:
            self.write_message(message["payload"])

    def register_callbacks(self):
        """
        Callback called in load_script before the JS is injeted in the target.
        Hook frida events like 'message', 'detached' etc here as needed
        """
        self._script.on("message", self.on_message)


    def on_finish(self):
        """
        Callback called after the target has been detached. Perform any desired cleanup operations here.
        """
        pass
            