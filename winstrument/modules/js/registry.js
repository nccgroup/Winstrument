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
var hkeys={};
    ["RegOpenKeyExW"].forEach(function(name) {
        Interceptor.attach(Module.getExportByName("KernelBase.dll",name), {
            //This should theoretically also hook RegOpenKeyW from Kernel32.dll/ADVAPI.dll because those calls go to RegOpenKeyExW in KernelBase (on Win 10 at least)
            onEnter: function(args) {
                this.hkey = args[0].toString();
                this.subkey = args[1].readUtf16String();
                this.hsubkey = args[4];
                send({"function": name, "hkey": this.hkey, "subkey": this.subkey});

            },
            onLeave: function(ret){
                if (ret.toInt32() === 0) {
                    hkeys[this.hsubkey.readInt()] = this.subkey;
                }
            }
        });
    });
    ["RegGetValueW"].forEach(function(name) {

        Interceptor.attach(Module.getExportByName("KernelBase.dll",name), {
            onEnter: function(args) {
                    this.hkey = args[0].toString();
                    this.subkey = args[1].readUtf16String();
                    this.value = args[2].readUtf16String();
                    send({"function": name, "hkey":this.hkey, "subkey": this.subkey, "value":this.value });
            },
        })
    });

    Interceptor.attach(Module.getExportByName("KernelBase.dll","RegQueryValueExW"), {
        onEnter: function(args) {
            if(args[0].toInt32() in hkeys)
            {
                var val = args[1].readUtf16String();
                if (val)
                {
                    var hkey = args[0].toInt32();
                    var path = hkeys[hkey];
                    send({
                        "function":"RegQueryValueExW",
                        "subkey": path,
                        "value": val
                    });
                }
            }
        }
    });
