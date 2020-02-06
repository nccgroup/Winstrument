# Winstrument
Winstrument is a framework of modular scripts to aid in instrumenting Windows software using Frida for reverse engineering and attack surface analysis.

### Contents
* [Installation](#installation)
* [Usage](#usage)
* [Project Structure](#project-structure)
* [Modules](#modules)
* [CLI](#cli)
* [Troubleshooting](#troubleshooting)
* [Copyright](#copyright)

## Installation
This project supports python 3.7.
Assuming you already have Python and pip installed, simply:

~~~
pip install winstrument
~~~
and then to execute the program, run:
~~~
winstrument
~~~

In some cases, such as a fresh Windows 10 install, you may encounter a SSL error in pip when installing Frida. If this happens, see [Troubleshooting](#troubleshooting) below.
## Usage

To run the winstrument REPL, simply run `winstrument`.
Here's a quick example of instrumenting `notepad.exe` with the `registry` module. For full info on the available CLI commands, see [the CLI section](#CLI) below.

```
PS C:\winstrument> winstrument
> set target C:\Windows\System32\notepad.exe
> use registry
> run
Spawned 1144
instrumented process with pid: 1144 and path: C:\Windows\System32\notepad.exe

<User closes notepad from GUI>

detached from 1144 for reason process-terminated
> show registry
module    time               target                           function          hkey                subkey                                                                       value
--------  -----------------  -------------------------------  ----------------  ------------------  ---------------------------------------------------------------------------  ---------------------------------
registry  2019-08-19 07:03:07  C:\Windows\System32\notepad.exe  RegGetValueW      0x2f4               SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize                 AppsUseLightTheme
<...>
```

In the above example, the user indicates the target process, in this case `notepad.exe`. They then indicate they want to use the `registry` module, which enumerates registry-related system calls made by the program. After the process is done (the user closes Notepad), the stored output can be viewed using `show registry`.
## Project Structure

The main python file `winstrument.py` initializes the Frida device and spawns an instance of the target process. 
`cmdline.py` provides a commandline interface using cmd2. This is the main script entry point when Winstrument is run directly from the command line. The commands are documented below. 

It then goes through each enabled module, instantiates it, and calls that modules's `load_scripts()` method to instrument the process.
Finally, it calls `get_output()` and `on_finish()` for each module when detached from the target.

Modules are contained in .py files in the `modules/` directory. A module consists of a subclass of `base_module.BaseInstrumentation` which defines the code to inject, message handling for that injected code, and output.
The module APIs are defined further in the "Modules" section below.

Each module stores metadata such as its description `modules/metadata.toml`. The section should be headed with the name of the module (case insensitive).
For example, here is the section corresponding to the `dlls`  module:

~~~ toml
[DLLS]
description = """Hooks LoadLibrary-family system calls and outputs DLL loads where part of the search path might be
writable by the current user or a low-privileged user group."""
~~~

The program stores settings in `settings.toml` in `%APPDATA%/winstrument`.
As most, if not all, modules will inject Javascript into the target process, the `modules/js/` directory contains Frida Javascript snippets which are loaded and injected by modules. 
These files should have the same name as the module i.e. the module `dlls.py` would use JS from `js/dlls.js`.


## Modules

As described above, each module subclasses `BaseInstrumentation` from `base_module.py`

Each module should define its name (the name of the python and js files without the extension) as a static class attribute called `modulename`. 
Modules may use or override the following methods from `BaseInstrumentation`:
* `__init__(self,*args,**kwargs)` - In addition to any module specific init code, this constructor should call `super().__init__(*args,**kwargs)`.  
* `load_script(self)` - This method generally should not need to be overridden, as the implementation in `BaseInstrumentation` should be sufficient for most use cases. To hook onto Frida events, override `register_callbacks()` instead. `load_script` should be used to load the javascript file to instrument, call `session.create_script` from Frida, add any desired callbacks, then calls the script objects's `load()` method to instrument.
* `register_callbacks(self)` - Called by `BaseInstrumentation.load_script` prior to loading the script into the target process. Used to register events such as `_session.on('message')` etc. The `BaseInstrumentation` version adds a hook for on_message by default.
* `write_message(message)` takes a JSON-like message as a dict, writes it the sqlite database and saves it to be output later.
* `post_load(self)` Called by `BaseInstrumentation.load_script` after the script is loaded inside the target process. This could be used, for example, to call rpc methods exported by the script.
* `get_output(self)` - Called by the main script when the target is detached. This method should return a list, where each entry is one MoudleMessage object (from `data/module_message.py`). Generally doesn't need to be overridden.
* `on_message(self,message,data)` - Callback for handling the frida `message` event, which is triggered by `send` in injected JS
* `on_finish(self)` - Callback called by the main script when the target becomes detached. Perform any cleanup operations required here.

## CLI

The Winstrument shell provides the following commands:
* `list` - Display all available and loaded modules
* `load <modulename>`/`use <modulename>` - Enable the module with the given name
* `unload <modulename>` - Disable the module with the given name
* `set [setting [value]]` - With no arguments, show all settings and their values.  With one argument, show value of `setting`. With two arguments, set `setting` to `value`. Settings persist across multiple runs.
* `show [modulename [format]]` - Display stored input from `modulename` in the specified `format`. Run without arguments to view a list of formatters.
* `info <modulename>` - Prints a description of of the module with the given name.
* `run` - Start instrumentation.
* `q`/`quit`/`exit` - Quits the CLI (obviously).

## Troubleshooting

### Pip fails with "SSL Certificate Verify Failed" when installing Frida
This seems to occur mostly on a new installation of Windows. Frida's setup.py tries to pull a .egg file from https://files.pythonhosted.org. In some cases, this fails because the SSL certificate for that domain does not verify. This appears to be a side-effect of the way Windows loads root CAs. Windows seems to not ship all the root CAs in a default install, instead preferring to pull them as needed when websites are visited. As a result, the root CA that signed `files.pythonhosted.org`'s SSL cert might not be in the system trust store.

To resolve this issue, visit https://files.pythonhosted.org manually in Edge or Chrome to get Windows to add the root CA to its trust store, then try `pip install` again.
Note that visiting the page in Firefox will **not** work, because Firefox uses its own trust store rather than the system store.


## Copyright
Winstrument is licensed under GPLv3. For more details see the LICENSE file.