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
import sys,os
import frida
import winstrument.utils as utils
from colorama import Fore, Back, Style
import threading
from frida_tools.application import Reactor
import importlib, pkgutil
import sqlite3
import json
import toml
from winstrument.db_connection import DBConnection
from winstrument.data.module_message import ModuleMessage 


class Winstrument():
    #adapted from https://github.com/frida/frida-python/blob/master/examples/child_gating.py
    CORE_MODNAME = "core"

    def __init__(self):
        self._db = DBConnection(os.path.join(os.path.dirname(__file__),"db.sqlite3"))
        self.settings_default = {"target": "C:\\Windows\\System32\\Notepad.exe", "verbosity": "0"}
        db_settings = self._db.restore_settings(self.CORE_MODNAME)
        self.settings = {}
        self.settings[self.CORE_MODNAME] = db_settings if db_settings else self.settings_default

        self.metadata = self.get_metadata()
        self._stop_requested = threading.Event()
        self._reactor = Reactor(run_until_return=lambda reactor: self._stop_requested.wait())
        self._device = frida.get_local_device()
        self._sessions = set()

        self._device.on("child-added", lambda child: self._reactor.schedule(lambda: self._on_child_added(child)))
        self._device.on("child-removed", lambda child: self._reactor.schedule(lambda: self._on_child_removed(child)))
        self._base_module = importlib.import_module("winstrument.base_module",None)
        self._modules_to_load=[]
        self._available_modules = self._enumerate_modules()
        self._loaded_modules = []
        self._instrumentations = []

    def get_metadata(self, filename="metadata.toml"):
        """ Parse the metadata.toml file for module metadata like descriptions, if present.
        Returns dict of metadata, or None if the file is not present or invalid.
        """

        metadata_filepath = os.path.join(os.path.dirname(__file__),"modules",filename)
        try:
            metadata = toml.load(metadata_filepath)
            return dict((k.lower(), v) for k,v in metadata.items()) #modulenames are lowercase
                
        except toml.TomlDecodeError:
            metadata = None
        return metadata

    def get_all_settings(self,modname):
        """
        Retrieve all settings for a given module name
        modname - str
        Returns a nested dict of settings for all modules keyed by module name
        """
        return self.settings[modname].copy()

    def set_all_settings(self,modname,settings):
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
        self.settings[modname][key] = val

    def get_setting(self, modname, key):
        """
        Get the setting with the speicfied key
        modname - str
        key - str
        Returns the setting value, or None if the key does not exist
        """
        return self.settings[modname].get(key,None)

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
            raise TypeError(f"Can't parse value {val} as boolean for {key}")

    def get_available_modules(self):
        """
        Gets a list of all available modules (from modules/metadata.toml)
        returns a list with module names
        """
        return self._available_modules.copy()
    
    def get_loaded_modules(self):
        """
        Gets a list of all modules that have already been loaded
        returns a list of module names
        """
        return [mod for mod in self._loaded_modules]

    def export_all(self, outfile, formatter=utils.format_table):
        """
        Write the output for all modules to the given output stream in the desired format
        outfile - file stream object. This could be a normal file or sys.stdout 
        formatter - callable which takes a list of ModuleMessage objects and returns a string to output. See utils.py
        No return, but writes the output stream
        """

        for module in self.get_available_modules():
            self.print_saved_output(module,formatter,outfile)
            
    def print_saved_output(self, modulename, formatter=utils.format_table, output=sys.stdout):
        """
        Write the output for the given module to the given output stream in the desired format.
        modulename - str
        formatter - callable which takes a list of ModuleMessage objects and returns a string to output. See utils.py
        outfile - file stream object. This could be a normal file or sys.stdout 
        No return, but writes the output stream
        """
        messages = self._db.read_messages(modulename)
        if formatter is None:
            formatter = utils.format_table
        verbosity = self.get_setting_int(self.CORE_MODNAME,"verbosity") or 0
        output.write(formatter(messages,verbosity)+"\n")

    def unload_module(self, module):
        """
        Unloads the given module. It will not be injected with the target is run
        module - str
        """
        try:
            self._modules_to_load.remove(module)
            self._loaded_modules.remove(module)
        except ValueError:
            print (f"Can't unload because {module} wasn't loaded")
        if module not in self._available_modules:
            self._available_modules.append(module)
        self._initialize_modules()

    def load_module(self, module):
        """
        Loads the given module, if it hasn't already been loaded.
        modulename - str
        """
        if module not in self._modules_to_load:
            self._modules_to_load.append(module)
        else:
            print(f"Error: {module} is already loaded")
            return
        self._initialize_modules()

    def _enumerate_modules(self,moudlepath="modules"):
        """
        Returns a list of available modules. Uses metadata file if available, otherwise falls back to all modules in the modulepath
        """
        if self.metadata:
            available_modules = [key.lower() for key in self.metadata.keys()]
        else: #metadata file missing or broken, fall back to module discovery based on path
            available_modules = [name for _, name, _, in pkgutil.iter_modules([os.path.join(os.path.dirname(__file__), moudlepath)])]
        return available_modules

    def _initialize_modules(self, modulepath = "winstrument.modules"):
        """
        Import python modules that are set to be loaded. If the module is not found, print a warning to STDOUT and remove the module from the _modules_to_load list.
        modulepath: string - Python import path for modules. This is a Python path, not a Windows path.jjjj
        """
        for modulename in self._modules_to_load:
            try:
                module = importlib.import_module(f"{modulepath}.{modulename}")
                if module not in self._loaded_modules:
                    self._loaded_modules.append(modulename)
                    
            except ImportError:
                print(f"Error: module '{modulename}' not found, skiping!")
                self._modules_to_load.remove(modulename)
                continue

    def run(self,target=None,arglist=None):
        """
            Schedule frida to spawn the target process, then instrument it.
            target: str - path to target to spawn
            arglist: list - arguments to pass to target when spawned
        """
        if target:
            process = target
            args = arglist
        else:
            process = self.get_setting(self.CORE_MODNAME,"target")
            args = self.get_setting(self.CORE_MODNAME,args)
        self._reactor.schedule(lambda: self._start(process,args))
        self._reactor.run()

    def _start(self,target,args=None):
        """
        Spawn the target process and then instrument it with any available scripts.
        If not found, write a warning to STDERR.
        target: str - Path to the process to spawn
        args: list or None - list of command line arguments to use with the target


        """
        cmd = [target]
        if args:
            cmd.append(args)
        try:
            pid = self._device.spawn(cmd)
        except frida.ExecutableNotFoundError:
            sys.stderr.write(f"{Fore.RED}Target {target} not found! Make sure the path is correct.\n{Style.RESET_ALL}")
            self.stop()
            return 
        print("Spawned " + str(pid))
        self._instrument(pid, target)

    def _stop_if_idle(self): 
        """
        Helper function used with Frida reactor. Stops the reactor if there are no queued child sessions.
        """
        if len(self._sessions) == 0:
            self.stop()

    def stop(self):
        """
        Signal that the Frida reactor has been requested to stop, then stop it.
        """
        self._stop_requested.set()
        self._reactor.stop()

    def quit(self):
        """
        Save settings to database. If save output if always_persist is set, otherwise prompt. """
        self._db.save_settings(self.CORE_MODNAME,self.settings[self.CORE_MODNAME])
        always_persist = self.get_setting(self.CORE_MODNAME,'always_persist')
        persist = True
        if not always_persist:
            response = input("Save stored output in DB [Y]/n?")
            if not (response.lower() == "y" or response.lower() == ""):
                persist = False
        if not persist:
            self._db.clear_output()
        
    def _instrument(self, pid, path):
        """
        Iterates over currently loaded modules and performs instrumentation on the target process for each.
        pid: int - PID of the spawned process
        path: str - filesystem path to the spawned process executable.
        """
        try:
            session = self._device.attach(pid)
        except frida.TransportError as e:
            sys.stderr.write(f"{Fore.RED} Got exception {repr(e)} when attaching to {pid}\n{Style.RESET_ALL}")
            return

        session.on('detached',lambda reason: self._reactor.schedule(lambda: self._on_detach(pid, session, reason)))
        session.enable_child_gating() #pause child processes until manually resumed
        for moduleclass in self._base_module.BaseInstrumentation.__subclasses__():
            if moduleclass.modulename in self._loaded_modules: # module might have been unloaded by user
                instrumentation = moduleclass(session, path, self._db)
                self._instrumentations.append(instrumentation)
                instrumentation.load_script()
        print(f"instrumented process with pid: {pid} and path: {path}")
        self._device.resume(pid)
        self._sessions.add(session)

    def _on_detach(self, pid, session, reason):
        """
        Callback called when the Frdia becomes detached froma  process.
        Calls the on_finish method for any loaded instrumentations, removes the old session and prints output, if verbosity is high enough.
        pid: int - PID of detached process
        session: Frida Session object - session corresponded to the detached process
        reason: str - Reason provided by Frida for why the target terminated
        """
        print (f"detached from {pid} for reason {reason}")
        for instrumentation in self._instrumentations: 
            instrumentation.on_finish()
        self._instrumentations.clear() #reset for next session, if any
        self._sessions.remove(session)
        verbosity = self.get_setting_int(self.CORE_MODNAME,"verbosity") or 0
        if verbosity >= 1:
            self.export_all(sys.stdout)

        self._reactor.schedule(self._stop_if_idle, delay=0.5)

    def _on_child_added(self, child):
        """
        Callback called by Frida reactor when a new child is spawned from the target process.
        child - object
        """
        self._instrument(child.pid,child.path)
    
    def _on_child_removed(self,child):
        """
        Callback called by Frida reactor when a child process ends.
        child - object
        """
        print(f"Child removed: {child.pid}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("usage: {0} <target>".format(sys.argv[0]))
        sys.exit(1)
    app = Winstrument()
    if len(sys.argv) >=3:
        args = sys.argv[2]
    else:
        args = None
    app.run(sys.argv[1],args)
    
