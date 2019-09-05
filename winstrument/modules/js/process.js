/*
Copyright (C) 2019  NCC Group

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/
Interceptor.attach(Module.getExportByName('kernel32.dll',"CreateProcessW"), {
    onEnter: function(args) {
        var application = args[0].readUtf16String();
        var cmdline = args[1].readUtf16String();
        send({"function": "CreateProcessW", "application": application, "args": cmdline});

    }
});

Interceptor.attach(Module.getExportByName('kernel32.dll', "CreateProcessA"), {
    onEnter: function(args) {
        var application = args[0].readAnsiString();
        var cmdline = args[1].readAnsiString();
        send({"function":"CreateProcessA", "application": application, "args": cmdline});

    }
});