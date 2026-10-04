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
import wx


class TreePanel(wx.Panel):
    def __init__(self, parent, ini_mgr, details_ctrl):
        super().__init__(parent)
        self.ini = ini_mgr
        self.details = details_ctrl

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.tree = wx.TreeCtrl(
            self,
            style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_LINES_AT_ROOT
        )

        sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

        self.root = self.tree.AddRoot("ROOT")

        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_select)

        self.refresh()

    # ------------------------------------------------------------------

    def refresh(self):
        """Rebuild the tree from backup folders."""
        self.tree.DeleteChildren(self.root)

        backup_path = self.ini.backup_path
        ident = self.ini.identifier.lower()
        published_name = self.ini.published_path.lower()

        if not os.path.isdir(backup_path):
            return

        for entry in sorted(os.listdir(backup_path)):
            full = os.path.join(backup_path, entry)

            # Skip Published folder
            if entry.lower() == published_name:
                continue

            # Only folders
            if not os.path.isdir(full):
                continue

            # Folder must contain ESP backups
            esp_files = [
                f for f in os.listdir(full)
                if f.lower().endswith(".esp") and ident in f.lower()
            ]

            if not esp_files:
                continue

            # Add folder node
            folder_node = self.tree.AppendItem(self.root, entry)

            # Add ESP backup files
            for esp in sorted(esp_files):
                self.tree.AppendItem(folder_node, esp)

        self.tree.Expand(self.root)

    # ------------------------------------------------------------------

    def on_select(self, event):
        """Update details panel when a file is selected."""
        item = event.GetItem()
        if not item.IsOk():
            return

        parent = self.tree.GetItemParent(item)
        if not parent.IsOk():
            return

        folder = self.tree.GetItemText(parent)
        filename = self.tree.GetItemText(item)

        # If user clicked a folder, clear details
        if not filename.lower().endswith(".esp"):
            self.details.SetValue("")
            return

        full_path = os.path.join(self.ini.backup_path, folder, filename)

        # Show details
        try:
            size = os.path.getsize(full_path)
            self.details.SetValue(
                f"File: {filename}\n"
                f"Folder: {folder}\n"
                f"Full Path:\n{full_path}\n\n"
                f"Size: {size} bytes"
            )
        except Exception:
            self.details.SetValue("")

    # ------------------------------------------------------------------

    def get_selected_file(self):
        """Return full path of selected ESP backup file."""
        item = self.tree.GetSelection()
        if not item.IsOk():
            return None

        filename = self.tree.GetItemText(item)
        if not filename.lower().endswith(".esp"):
            return None

        parent = self.tree.GetItemParent(item)
        if not parent.IsOk():
            return None

        folder = self.tree.GetItemText(parent)
        return os.path.join(self.ini.backup_path, folder, filename)
