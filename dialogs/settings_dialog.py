# ***********************************************************************
"""
Module Name : settings_dialog.py
Author      : Chris Anderson
Create Date : 2026-10-04
Description : Settings dialog for editing INI values.

Fields:
    BackupPath
    RestorePath
    Identifier
    PublishedPath   (folder name only)
"""
# ***********************************************************************

import wx


class SettingsDialog(wx.Dialog):
    def __init__(self, parent, ini_mgr):
        super().__init__(parent, title="Settings", size=(wx.Size(500, 300)))
        self.ini = ini_mgr

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # -----------------------------
        # BackupPath
        # -----------------------------
        lbl_backup = wx.StaticText(panel, label="Backup Path:")
        self.txt_backup = wx.TextCtrl(panel, value=self.ini.backup_path)

        # -----------------------------
        # RestorePath
        # -----------------------------
        lbl_restore = wx.StaticText(panel, label="Restore Path:")
        self.txt_restore = wx.TextCtrl(panel, value=self.ini.restore_path)

        # -----------------------------
        # Identifier
        # -----------------------------
        lbl_ident = wx.StaticText(panel, label="Identifier:")
        self.txt_ident = wx.TextCtrl(panel, value=self.ini.identifier)

        # -----------------------------
        # PublishedPath (folder name only)
        # -----------------------------
        lbl_pub = wx.StaticText(panel, label="Published Folder Name:")
        self.txt_pub = wx.TextCtrl(panel, value=self.ini.published_path)

        # -----------------------------
        # Layout
        # -----------------------------
        grid = wx.FlexGridSizer(4, 2, 10, 10)
        grid.AddGrowableCol(1, 1)

        grid.Add(lbl_backup, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_backup, 1, wx.EXPAND)

        grid.Add(lbl_restore, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_restore, 1, wx.EXPAND)

        grid.Add(lbl_ident, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_ident, 1, wx.EXPAND)

        grid.Add(lbl_pub, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_pub, 1, wx.EXPAND)

        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 15)

        # Buttons
        btn_sizer = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(sizer)

    # ------------------------------------------------------------------

    def apply(self):
        """Return updated settings to caller."""
        backup = self.txt_backup.GetValue().strip()
        restore = self.txt_restore.GetValue().strip()
        ident = self.txt_ident.GetValue().strip()
        pub = self.txt_pub.GetValue().strip()

        return backup, restore, ident, pub
