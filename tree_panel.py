# ***********************************************************************
"""
Module Name : tree_panel.py
Author      : Chris Anderson
Create Date : 2026-10-04
Description : TreeView panel showing ESP backup folders and files.

Rules:
    - Show ONLY ESP backup folders (mod folders).
    - Show ONLY ESP backup files inside those folders.
    - DO NOT show Published folder.
    - DO NOT show ESM files.
    - Identifier may appear ANYWHERE in filename.
"""
# ***********************************************************************

import os
import shutil
import socket
import wx
import win32security
from datetime import datetime

computer = socket.gethostname()

def get_owner(path):
    sd = win32security.GetFileSecurity(path, win32security.OWNER_SECURITY_INFORMATION)
    owner_sid = sd.GetSecurityDescriptorOwner()
    name, domain, type = win32security.LookupAccountSid(None, owner_sid)
    return f"{domain}\\{name}"

def get_attributes(path):
    attrs = []

    # Windows marks normal files as Archive (A)
    attrs.append("A")

    # Read-only
    if not os.access(path, os.W_OK):
        attrs.append("R")

    # Hidden (simple heuristic)
    if os.path.basename(path).startswith("."):
        attrs.append("H")

    return "".join(attrs)

class TreePanel(wx.Panel):
    def __init__(self, parent, ini_mgr, details_ctrl):
        super().__init__(parent)
        self.ini = ini_mgr
        self.details = details_ctrl

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.tree = wx.TreeCtrl(
            self,
            style=wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT
        )

        sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

        self.root = self.tree.AddRoot("Starfield_Mods")

        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_select)

        self.refresh()

    # ------------------------------------------------------------------

    def refresh(self):
        """Rebuild the tree from backup folders."""
        self.tree.DeleteChildren(self.root)

        backup_path = self.ini.backup_path
        ident = self.ini.identifier.lower()
        published_name = self.ini.published_path.lower()

        # Ensure backup folder exists
        if not os.path.isdir(backup_path):
            os.makedirs(backup_path, exist_ok=True)

        for entry in sorted(os.listdir(backup_path)):
            full = os.path.join(backup_path, entry)

            # Skip Published folder
            if entry.lower() == published_name:
                continue

            # Only folders
            if not os.path.isdir(full):
                continue

            # Folder must contain identifier ANYWHERE in its name
            if ident not in entry.lower():
                continue

            # Collect ESP files (only .esp for now)
            esp_files = sorted(os.listdir(full))

            # Skip folders with no ESPs
            if not esp_files:
                continue

            # Add folder node
            folder_node = self.tree.AppendItem(self.root, entry)

            # Add ESP backup files
            for esp in sorted(esp_files):
                self.tree.AppendItem(folder_node, esp)

    # ------------------------------------------------------------------

    def on_select(self, event):
        item = event.GetItem()
        if not item.IsOk():
            return

        parent = self.tree.GetItemParent(item)
        if not parent.IsOk():
            return

        # If user clicked a folder → clear details
        if parent == self.root:
            self.details.SetValue("")
            return
        
        folder = self.tree.GetItemText(parent)
        filename = self.tree.GetItemText(item)

        full_path = os.path.join(self.ini.backup_path, folder, filename)
        self.selected_file = full_path

        try:
            st = os.stat(full_path)

            owner = get_owner(full_path)
            attrs = get_attributes(full_path)
            computer = socket.gethostname()

            total, used, free = shutil.disk_usage(full_path)
            total_tb = round(total / (1024**4), 2)
            free_tb = round(free / (1024**4), 2)
            space_used = round((used / total) * 100)

            lines = [
                f"File Name: {filename}",
                f"Full Path: {full_path}",
                f"Size: {st.st_size} bytes",
                f"Created: {datetime.fromtimestamp(st.st_ctime)}",
                f"Modified: {datetime.fromtimestamp(st.st_mtime)}",
                f"Accessed: {datetime.fromtimestamp(st.st_atime)}",
                "",
                f"Name: {filename}",
                f"Size: {round(st.st_size/1024,1)} KB",
                f"Item type: {os.path.splitext(filename)[1]} File",
                f"Date modified: {datetime.fromtimestamp(st.st_mtime)}",
                f"Date created: {datetime.fromtimestamp(st.st_ctime)}",
                f"Date accessed: {datetime.fromtimestamp(st.st_atime)}",
                f"Attributes: {attrs}",
                "Perceived type: Unspecified",
                f"Owner: {owner}",
                "Rating: Unrated",
                f"Total size: {total_tb} TB",
                f"Computer: {computer} (this PC)",
                f"File extension: {os.path.splitext(filename)[1]}",
                f"Filename: {filename}",
                f"Space free: {free_tb} TB",
                "Shared: No",
                f"Folder name: {os.path.basename(os.path.dirname(full_path))}",
                f"File location: {os.path.dirname(full_path)}",
                f"Folder: {os.path.basename(os.path.dirname(full_path))} ({os.path.dirname(os.path.dirname(full_path))})",
                f"Path: {full_path}",
                f"Type: {os.path.splitext(filename)[1]} File",
                "Link status: Unresolved",
                f"Space used: {space_used}%",
            ]

            self.details.SetValue("\n".join(lines))

        except Exception as e:
            self.details.SetValue(f"Error reading file:\n{e}")

    # ------------------------------------------------------------------

    def get_selected_file(self):
        return getattr(self, "selected_file", None)

