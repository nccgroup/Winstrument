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

//registry subkey parsing logic sourced from https://www.fuzzysecurity.com/tutorials/29.html
["RegOpenKeyExW","RegGetValueW"].forEach(function (name) {
    Interceptor.attach(Module.getExportByName("KernelBase.dll",name), {
        //This should theoretically also hook RegOpenKeyW from Kernel32.dll/ADVAPI.dll because those calls go to RegOpenKeyExW in KernelBase (on Win 10 at least)
        onEnter: function(args) {
            this.subkey = args[1].readUtf16String();
            if (this.subkey && this.subkey.indexOf("CLSID\\") >= 0)
            {
                this.hasClsid =  1;
            }

        },
        onLeave: function(ret)
        {
            if (this.hasClsid && ret.toInt32() !== 0)
            {
                send({"function":name, "subkey": this.subkey});
            }
        }
    });
});
