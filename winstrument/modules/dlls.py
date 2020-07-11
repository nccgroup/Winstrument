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

import frida,sys
import win32api
import win32con
import win32security
import ntsecuritycon
import pywintypes
import collections
import os
import uuid
from winstrument.base_module import BaseInstrumentation

class DLLs(BaseInstrumentation):

    modulename="dlls"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dll_paths = []
        self._loaded_dlls = set()
        self._known_dlls = None
        self._dll_perms = {}

    def _parse_ace_entry(self, ace):
#        ace_types = {win32security.ACCESS_ALLOWED_ACE_TYPE: "ACCESS_ALOWED_ACE",
#            win32security.ACCESS_DENIED_ACE_TYPE: "ACCESS_DENIED_ACE",
#             win32security.SYSTEM_AUDIT_ACE_TYPE: "SYSTEM_AUDIT_ACE"}
        ace_flag_types = ["OBJECT_INHERIT_ACE", "CONTAINER_INHERIT_ACE",
            "NO_PROPAGATE_INHERIT_ACE", "INHERIT_ONLY_ACE", "INHERITED_ACE"]
        ace_perms = [
        "FILE_ADD_FILE","FILE_APPEND_DATA", "FILE_ADD_SUBDIRECTORY","FILE_READ_EA",
        "FILE_WRITE_EA","FILE_EXECUTE","FILE_TRAVERSE","FILE_DELETE_CHILD","FILE_READ_ATTRIBUTES",
        "FILE_WRITE_ATTRIBUTES","FILE_ALL_ACCESS", "FILE_GENERIC_READ","FILE_GENERIC_WRITE","FILE_GENERIC_EXECUTE"]
#        ace_type = ace_types[ace[0][0]]
        ace_flags = ace[0][1]
        ace_mask = ace[1]
        sid = ace[2]
        permlist = set()
        flags = set()

        for perm in ace_perms:
            mask_const = getattr(ntsecuritycon, perm)
            if ace_mask & mask_const == mask_const:
                permlist.add(perm)

        for flag in ace_flag_types:
            flag_const = getattr(win32security,flag)
            if ace_flags & flag_const == flag_const:
                flags.add(flag)
        try:
            name,domain, _ = win32security.LookupAccountSid(None,sid)
        except pywintypes.error:
            name = None
            domain = None
        flagstr = ','.join([flag for flag in flags]) if len(flags) != 0 else 'N/A'
        perms = ",".join([perm for perm in permlist]) if len(permlist) != 0 else 'NONE'
        if name and domain:
            principal = f"{domain}\\{name}"
        else:
            principal = str(sid)
        AceEntry = collections.namedtuple("AceEntry", "sid principalname perms flags")
        return AceEntry(sid=sid,principalname=principal,perms=perms,flags=flagstr)

    def _get_users_with_write_perms(self,filepath):
        users = set()
        try:
            acl = self._get_acl(filepath)
        except pywintypes.error: #pylint: disable=no-member
            return []
        aces = self._get_aces(acl)
        for ace in aces:
            ace_entry = self._parse_ace_entry(ace)
            write_dir_perms={"FILE_GENERIC_WRITE","FILE_ADD_FILE","FILE_WRITE_FILE","WRITE_DAC","WRITE_OWNER"}

            if any(perm in ace_entry.perms for perm in write_dir_perms):
                users.add(ace_entry.principalname)
        return users

    def _get_aces(self, acl):
        ace_count = acl.GetAceCount()
        aces = []
        for i in range(ace_count):
            ace = acl.GetAce(i)
            aces.append(ace)
        return aces

    def _get_known_dlls(self):
        known_dll_subkey= "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\KnownDLLs"
        known_dlls_hkey = win32api.RegOpenKeyEx(win32con.HKEY_LOCAL_MACHINE, known_dll_subkey)
        known_dlls = []
        idx = 0
        done = False
        while not done:
            try:
                dllname = win32api.RegEnumValue(known_dlls_hkey,idx)[1]
                known_dlls.append(dllname.lower())
                idx = idx + 1
            except pywintypes.error: #pylint: disable=no-member
                done = True
        return known_dlls

    def _get_dll_search_path(self):
        """
        Returns a list of paths for which the system will search for DLLs
        Per MSDN the DLL search order is as follows:
        1. The directory from which the application loaded.
        2. The system directory. Use the GetSystemDirectory function to get the path of this directory.
        3. The 16-bit system directory. There is no function that obtains the path of this directory, but it is searched.
        4. The Windows directory. Use the GetWindowsDirectory function to get the path of this directory.
        5. The current directory.
        6. The directories that are listed in the PATH environment variable. Note that this does not include the per-application path specified by the App Paths registry key. The App Paths key is not used when computing the DLL search path.

        Note: any DLLS in the KnownDLLs registry key will bypass he search order
        """

        process_dir = os.path.dirname(self._processpath)
        systemdir = win32api.GetSystemDirectory()
        #Note: 16 bit System doesn't exist on x64 arch so I'm not checking this. If someone wants to add this feel free to PR.
        windir = win32api.GetWindowsDirectory()
        current_dir = os.getcwd()
        pathdirs = os.environ["PATH"].split(';')
        pathdirs = filter(lambda path: path != '' and not path.isspace(), pathdirs) #remove empty paths
        dirs = [process_dir,systemdir,windir,current_dir]
        dirs.extend(pathdirs)
        return dirs

    def _resolve_relative_dll_path(self, dllpath):
        #ignore any duplicate loads
        if not dllpath.lower().endswith(".dll"):
            dllpath = dllpath + ".dll"
        if dllpath.lower() in self._loaded_dlls:
            return
        searched = []
        if not self._known_dlls:
            self._known_dlls = self._get_known_dlls()
        if dllpath.lower() in self._known_dlls:
            dll_abspath = os.path.join(win32api.GetSystemDirectory(),dllpath) #known dlls should be here
            self._loaded_dlls.add(dllpath.lower())
            found = True
            return
        dirs = self._get_dll_search_path()
        found = False
        for dirpath in dirs:
            if found:
                break
            dll_abspath = os.path.join(dirpath,dllpath)
            searched.append(dirpath)
            if os.path.exists(dll_abspath):
                self._loaded_dlls.add(dllpath.lower())
                found = True

        for path in searched:
            if self._is_path_writeable(path):
                data = {"dll": dllpath, "writeable_path": path }
                self.write_message(data)
    def _is_path_writeable(self, path):
        current_user = f"{win32api.GetDomainName()}\\{win32api.GetUserName()}"
        auth_users = "NT AUTHORITY\\Authenticated Users"
        all_users = "BUILTIN\\USERS"
        write_users = self._get_users_with_write_perms(path)
        writeable = False
        for user in write_users:
            if auth_users.lower() == user.lower() or current_user.lower() == user.lower() or all_users.lower()==user.lower():
                writeable = True
        return writeable
    def _get_writable_search_dirs(self):
            for dirpath in self._get_dll_search_path():
                write_users = self._get_users_with_write_perms(dirpath)
                write_users = ",".join(write_users)
                if write_users:
                    data = {"path": dirpath, "can_write": write_users}
                    self.write_message(data)

    def _get_acl(self,filepath):
        dll_sd = win32security.GetFileSecurity(filepath, win32security.OWNER_SECURITY_INFORMATION | win32security.DACL_SECURITY_INFORMATION)
        acl = dll_sd.GetSecurityDescriptorDacl()
        return acl

    def on_message(self, message, data):
        if message["type"] == "error":
            print(f"Error: {message}")
            return
        elif message["type"] == "send":
            payload = message["payload"]
            dllpath = payload['lib_filename']
            if dllpath is not None:
                dllname = os.path.basename(dllpath)
                if not os.path.isabs(dllpath): #Don't need to resolve names that are already absolute
                    self._resolve_relative_dll_path(dllpath)
                else:
                    if self._is_path_writeable(dllpath):
                        data = {"dll": dllname, "writeable_path": dllpath}
                        self.write_message(data)

