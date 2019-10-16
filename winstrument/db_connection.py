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
import sqlite3
from winstrument.data.module_message import ModuleMessage
import sys
from datetime import datetime
import json
import os
import toml
class DBConnection():

    def __init__(self,dbpath):
        self._db = sqlite3.connect(dbpath,check_same_thread=False)
        self._dbpath = dbpath
        self._cursor = self._db.cursor()
        self._cursor.execute("""CREATE TABLE IF NOT EXISTS output 
                            (id INTEGER PRIMARY KEY,
                            modname TEXT NOT NULL,
                            time TEXT NOT NULL,
                            target TEXT NOT NULL,
                            message BLOB)""")
        self._db.commit()

    def write_message(self, message):
        """
        Insert the given message into the sqlite DB output table
        message - ModuleMessage object
        """
        self._cursor.execute("""INSERT INTO "output" (modname, time, target, message) VALUES (?,?,?,?)""", (message.module, message.time, message.target, json.dumps(message.data))) 
        self._db.commit()

    def clear_output(self):
        """
        Truncates the output table
        """
        self._cursor.execute('DELETE FROM "output"')
        self._db.commit()

    def read_messages(self, modname):
        """
        Get a list of all messages for the given module name
        modname: str - Name of the module for which to retrieve messages
        Return: list of ModuleMessage objects
        """
        self._cursor.execute("""SELECT "modname", "time", "target", "message" FROM "output" where modname= ? """,(modname,))
        messages = []
        for row in self._cursor.fetchall():
            module = row[0]
            time = row[1]
            target = row[2]
            data = json.loads(row[3])
            messages.append(ModuleMessage(module,target,data,time=time))
        return messages

    def close(self):
        self._db.close()
        os.remove(self._dbpath)


    