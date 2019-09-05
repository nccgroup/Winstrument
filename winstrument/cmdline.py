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
import cmd2,sys
from winstrument.winstrument import Winstrument
from colorama import Fore, Back, Style
from cmd2 import with_argument_list
import winstrument.utils as utils
class FridaCmd(cmd2.Cmd):
    prompt = "> "
    def __init__(self, app):
        shortcuts = dict(cmd2.DEFAULT_SHORTCUTS)
        shortcuts.update({"exit":"quit","q":"quit","use":"load"})
        self._target = "C:\\Windows\\System32\\Notepad.exe"
        self._app = app
        cmd2.Cmd.__init__(self,shortcuts=shortcuts)



    @with_argument_list
    def do_list(self, arg):
        """
        usage: list
        Show a list of all available and loaded modules.
        """
        available = self._app.get_available_modules()
        loaded = self._app.get_loaded_modules()
        print("Loaded Modules:")
        for module in loaded:
            if module in available:
                available.remove(module)
            print (module)
        print("Available Modules:")
        for module in available:
            print (module)

    @with_argument_list
    def do_unload(self, arg):
        """
        usage: unload [modulenmae]
        Unload the speicfied loaded module, so it will no longer be used to instrument the target
        """
        self._app.unload_module(arg[0])

    #override the cmd2 function because the message is incorrect with our overriden do_set
    def pexcept(self, errmsg, end='\n', apply_style = True):
        if self.debug and sys.exc_info() != (None,None,None):
            import traceback
            traceback.print_exc()
            
        if isinstance(errmsg, Exception):
            err = f"{Fore.RED}EXCEPTION of type {type(errmsg)} occurred with message: {errmsg}{Style.RESET_ALL}"
        else:
            err = f"{Fore.RED}{errmsg}"

        if not self.debug and 'debug' in self.settable:
            err += f"\n{Fore.YELLOW}For more complete error output, use \"config debug true\" {Style.RESET_ALL}" 
        self.perror(err, end=end, apply_style=False)
    
    @with_argument_list
    def do_load(self, arg):
        """
        usage: load [modulename]
        Load the selected module to be instrument, if it exists
        """
        self._app.load_module(arg[0])

    def _get_formatter_list(self):
        formatter_list = utils.get_formatters()
        output = []
        for formatter in formatter_list:
            output.append(formatter.name)
        return "\n".join(output)

    @with_argument_list
    def do_info(self, args):
        """usage: info [modulename]
        Displays info about modules.
        """
        if len(args) > 1:
            self.perror("usage: info [modulename]")
            return
        elif len(args) == 0:
            metadata = self._app.metadata
            for modname in metadata.keys():
                print(modname)
                print(metadata[modname]["description"])
                print()

        else:
            modulename = args[0]
            if modulename.lower() not in self._app.get_available_modules():
                self.perror(f"invalid module {args[0]}")
                return
            try:
                description = self._app.metadata[modulename.lower()]["description"]
                self.poutput(description)
            except (KeyError, AttributeError):
                self.perror(f"No description for module {modulename}")
    @with_argument_list
    def do_show(self, arg):
        """usage: show [modulename [format]]
        Shows the output from modulename in the specified format
        Run without arguments to view available formats
        """
        if len(arg) > 2:
            self.perror("usage: show [modulename [format]]")
        if len(arg) < 1:
            info = f"Available formatters:\n{self._get_formatter_list()}"
            self.poutput(info)
            return
        
        if len(arg) == 1:
            self.print_format(arg[0], sys.stdout )
            return
        elif len(arg) == 2:
            self.print_format(arg[0], sys.stdout, arg[1])


    def print_format(self, modulename, outfile, formatter=None):
        if formatter is not None:
            try: 
                style = utils.get_formatter(formatter)
            except ValueError:
                print(f"Invalid format\nAvailable formatters:\n{self._get_formatter_list()}")
                return
            self._app.print_saved_output(modulename, style, output=outfile)
        else:
            self._app.print_saved_output(modulename, output=outfile) 

    @with_argument_list
    def do_export(self,args):
        """usage: export <modulename> <filename> [format]
            Exports the stored output of module <modulename> to the file stored in filename in the given format
        """
        if len(args) < 1:
            self.perror("usage: export <modulename> <filename> [format]")
            info = f"Available formatters:\n{self._get_formatter_list()}"
            self.poutput(info)
            return

        if len(args) != 2 and len(args) != 3:
            self.perror("usage: export <modulename> <filename> [format]")
            return

        with open(args[1], 'w+') as outfile:
            if len(args) == 2:
                self.print_format(args[0], outfile)
            elif len(args) == 3:
                self.print_format(args[0], outfile, args[2])

    @with_argument_list
    def do_exportall(self,args):
        """usage: exportall <filename> [format] 
        Export stored output from all modules into the specified file
        Optionally specify the preferred format to output.
        """
        if len(args) < 1:
            self.perror("usage: export <modulename> <filename> [json|table]")
            info = f"Available formatters:\n{self._get_formatter_list()}"
            self.poutput(info)
            return

        if len(args) != 1 and len(args) != 2:
                self.perror("usage: exportall <filename> [format]")
                return
        else:
            with open(args[0], 'w+') as outfile:                    
                if len(args) == 1:
                    self._app.export_all(outfile)
                    return
                else:
                    try: 
                        style = utils.get_formatter(args[1])
                    except ValueError:
                        print(f"Invalid Formatter\nAvailable formatters:\n{self._get_formatter_list()}")
                    self._app.export_all(outfile,formatter=style)
        
    def do_config(self,args):
        """
        usage: config [setting, [value]]
        Configure options related to the CLI 
        """

        super().do_set(args)
    @with_argument_list
    def do_set(self,args):
        """ 
        usage: set [setting [value]]
        Configure settings for winsturment framework
        with no arguments: show settings
        with [setting]: show value of [setting]
        with [setting [value]]: set [setting] to [value]
        """
        if len(args) == 0:
            settings = self._app.get_all_settings(self._app.CORE_MODNAME)
            for key, value in settings.items():
                self.poutput(f"{key}={value}")
        elif len(args) == 1:
            value = self._app.get_setting(self._app.CORE_MODNAME, args[0])
            self.poutput(f"{args[0]}={value}")
        elif len(args) == 2:
            self._app.set_setting(self._app.CORE_MODNAME,args[0], args[1])
        else:
            pass

    @with_argument_list
    def do_run(self,arg):
        """
        usage: run
        Spawn and instrument the targer pocess
        """
        target = self._app.get_setting(self._app.CORE_MODNAME,"target")
        args = self._app.get_setting(self._app.CORE_MODNAME,"args")
        if target != "":
            self._app.run(target, args)
        else:
            print("Error: must specify target first")

    def do_quit(self, arg):
        """
        Usage: quit
        Save settings and (optionally) output, and quit the app.
        """
        self._app.quit()
        return True

def main():
    app = Winstrument()
    cmd = FridaCmd(app)
    sys.exit(cmd.cmdloop())

if __name__ == '__main__':
    main()