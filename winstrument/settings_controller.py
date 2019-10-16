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
import os
import toml
class SettingsController:

    def __init__(self,filename):
        self.settings = {}
        self._settings_filename = filename
        self.read_settings()
   
    def read_settings(self):
        if not os.path.exists(self._settings_filename):
            self.settings = {}
            return
        with open(self._settings_filename,'r') as settings_file:
           self.settings = toml.loads(settings_file.read())
   
    def save_settings(self):
        with open(self._settings_filename, 'w') as settings_file:
          settings_file.write(toml.dumps(self.settings))
   
    def get_module_settings(self,modname):
        """
        Retrieve all settings for a given module name
        modname - str
        Returns a dict of settings for the module, or an empty dict if the module does not exist
        """
        try:
            settings = self.settings[modname].copy()
        except KeyError:
            settings = {}
        return settings

    def set_module_settings(self,modname,settings):
        """
        Set settings for an entire module all at once using the dict contained in settings
        modname - str
        settings - dict of string keys with any-type values
        """
        self.settings[modname] = settings

    def set_setting(self, modname, key, val):
        """
        Set setting with key to given value for modname
        modname - str
        key - str
        val - any type
        """
        try:
          self.settings[modname][key] = val
        except KeyError:
            self.settings[modname] = {key: val}

    def get_setting(self, modname, key):
        """
        Get the setting with the specified key
        modname - str
        key - str
        Returns the setting value if it exists
        Returns None if the key does not exist, or the module has no config       """
        try:
            return self.settings[modname].get(key,None)
        except KeyError: #module does not exist
           return None

    def get_setting_int(self, modname, key):
        """
        Gets the int representation of the setting stored in  the given key.
        modname - str
        key - str
        Returns the setting value as int. Returns None if the setting isn't parsable to int or does not exist.
        """
        val=self.settings[modname].get(key,None)
        try: 
            num = int(val)
        except TypeError:
            num = None
        return num
            
    def get_setting_boolean(self, modname, key):
        """
        Gets the boolean representation of the string setting stored in key for modname
        modname - str
        key - str
        Returns True/False depending on setting value
        Returns None if the value can't be interpreted as a boolean or does not exist

        """

        val = self.settings[modname].get(key,"").lower()
        if val == "yes" or val == "true":
            return True
        elif val == "no" or val == "false":
            return False
        else:
            return None