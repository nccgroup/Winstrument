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
Interceptor.attach(Module.getExportByName('kernel32.dll','WriteFile'), {
        onEnter: function(args) {
            var data = {
                function: "WriteFile",
                fh: args[0].toString(),
                bytes_to_write: args[2].toInt32(),
                bytes_written_ptr: args[3]

            }
            this.data = data
        },
        onLeave: function(ret) {
            if(this.data["bytes_written_ptr"].toInt32() !== 0){
                this.data["bytes_written"] = this.data["bytes_written_ptr"].readU32()
            }
            else{
                this.data["bytes_written"] = this.data["bytes_to_write"]
            }
            send(this.data)
        }
    });

    Interceptor.attach(Module.getExportByName('kernel32.dll','ReadFile'), {
        onEnter: function(args) {
            var data = {
                function: "ReadFile",
                fh: args[0].toString(),
                bytes_to_read: args[2].toInt32(),
                bytes_read_ptr: args[3]
            }
            this.data = data;
        },
        onLeave: function(ret) {
            if(this.data["bytes_read_ptr"].toInt32() !== 0){

                this.data["bytes_read"] = this.data["bytes_read_ptr"].readU32();
            }
            else{
                this.data["bytes_read"] = this.data["bytes_to_read"]
            }
            send(this.data);
        }

    });
Interceptor.attach(Module.getExportByName('kernel32.dll','ReadFileEx'), {
        onEnter: function(args) {
            var data = {
                function: "ReadFileEx",
                fh: args[0].toString(),
                bytes_to_read: args[2].toInt32()
            }
            send(data)
        }
});
Interceptor.attach(Module.getExportByName('kernel32.dll','CreateFileW'), { //Unicode Version, need to handle encoding differently for ansi one, but otherwise identical
            onEnter: function(args) {
                     this.function = "CreateFileW";
                     this.path = args[0].readUtf16String();
                     this.mode = args[1].toString();
                },
            onLeave: function(ret) {
                var data = {
                    "function": this.function,
                    "path": this.path,
                    "mode": this.mode,
                    "fh": ret.toString()
                }

                send(data)
            }
         });
Interceptor.attach(Module.getExportByName('kernel32.dll','CreateFileA'), { //ANSI Version
            onEnter: function(args) {
                     this.function = "CreateFileA";
                     this.path = args[0].readAnsiString();
                     this.mode = args[1].toString();
                },
            onLeave: function(ret) {
                var data = {
                    "function": this.function,
                    "path": this.path,
                    "mode": this.mode,
                    "fh": ret.toString()
                }

                send(data)
            }
         });
