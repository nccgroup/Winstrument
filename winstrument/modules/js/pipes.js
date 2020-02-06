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
var pipes = {}
Interceptor.attach(Module.getExportByName("Kernel32.dll", "CreateNamedPipeA"), {
    onEnter: function (args) {
        this.pipename = args[0].readAnsiString();
        this.openmode = args[1].toInt32();
        this.pipemode = args[1].toInt32();
    },
    onLeave: function (ret) {

        this.fh = ret.toInt32();
        pipes[this.fh] = this.pipename
        send({ "function": "CreateNamedPipeA", "fh": this.fh, "pipename": this.pipename, "openmode": this.openmode, "pipemode": this.pipemode });
    }

});

Interceptor.attach(Module.getExportByName("Kernel32.dll", "ConnectNamedPipe"), {
    onEnter: function (args) {
        this.fh = args[0].toInt32;
        this.pipename = pipes[this.fh];

        this.fh = ret.toInt32();
        send({ "function": "ConnectNamedPipe", "fh": this.fh, "pipename": this.pipename });
    }

});


Interceptor.attach(Module.getExportByName("Kernel32.dll", "CallNamedPipeA"), {
    onEnter: function (args) {
        this.name = args[0].readAnsiString();
        this.written = args[2].readInt();
        this.readptr = args[5];
    },
    onLeave: function (ret) {
        this.read = this.readptr.readInt();
        send({ "function": "CallNamedPipeA", "pipename": this.name, "written": this.written, read: this.read });
    }
});
