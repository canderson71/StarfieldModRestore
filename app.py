# ***********************************************************************
r"""
Module Name : app.py
Author      : Chris Anderson
Create Date : 2026-10-04
Description : Main wxPython application for ESP/ESM backup & restore.

Build (PyInstaller):
    pyinstaller --noconsole --onefile --icon ESP-R.ico --name ESPRestore app.py

Notes:
    - ESP files are treated as source (work-in-progress mods).
    - ESM files are treated as compiled/published output.
    - ESM backups go to BackupPath\PublishedPath (latest only, no restore).
    - ESP backups go to per-mod folders (last 10, restorable).
"""
# ***********************************************************************

import wx

from ini_manager import IniManager
from backup_manager import BackupManager
from restore_manager import RestoreManager
from tree_panel import TreePanel
from dialogs.settings_dialog import SettingsDialog
from dialogs.error_dialog import ErrorDialog

class MainFrame(wx.Frame):
    def __init__(self, ini_mgr: IniManager):
        super().__init__(None, title="ESP Restore", size=(wx.Size(900, 600)))
        self.ini_mgr = ini_mgr

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        splitter = wx.SplitterWindow(panel, style=wx.SP_LIVE_UPDATE)
        left_panel = wx.Panel(splitter)
        right_panel = wx.Panel(splitter)

        # Right side: details text
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.txt_details = wx.TextCtrl(
            right_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        right_sizer.Add(self.txt_details, 1, wx.EXPAND | wx.ALL, 5)
        right_panel.SetSizer(right_sizer)

        # Left side: tree panel
        self.tree_panel = TreePanel(left_panel, self.ini_mgr, self.txt_details)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(self.tree_panel, 1, wx.EXPAND | wx.ALL, 5)
        left_panel.SetSizer(left_sizer)

        splitter.SplitVertically(left_panel, right_panel, sashPosition=300)

        # Bottom buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_settings = wx.Button(panel, label="Settings")
        self.btn_backup = wx.Button(panel, label="Backup")
        self.btn_restore = wx.Button(panel, label="Restore")
        self.btn_quit = wx.Button(panel, label="Quit")

        btn_sizer.Add(self.btn_settings, 0, wx.ALL, 5)
        btn_sizer.AddStretchSpacer(1)
        btn_sizer.Add(self.btn_backup, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_restore, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_quit, 0, wx.ALL, 5)

        main_sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        panel.SetSizer(main_sizer)

        # Managers
        self.backup_mgr = BackupManager(self.ini_mgr, self)
        self.restore_mgr = RestoreManager(self.ini_mgr, self)

        # Events
        self.btn_settings.Bind(wx.EVT_BUTTON, self.on_settings)
        self.btn_backup.Bind(wx.EVT_BUTTON, self.on_backup)
        self.btn_restore.Bind(wx.EVT_BUTTON, self.on_restore)
        self.btn_quit.Bind(wx.EVT_BUTTON, self.on_quit)

    def on_settings(self, event):
        dlg = SettingsDialog(self, self.ini_mgr)
        if dlg.ShowModal() == wx.ID_OK:
            backup, restore, ident, published = dlg.apply()
            self.ini_mgr.update(backup, restore, ident, published)
            self.tree_panel.refresh()
        dlg.Destroy()

    def on_backup(self, event):
        self.backup_mgr.run_backup()
        self.tree_panel.refresh()

    def on_restore(self, event):
        src_path = self.tree_panel.get_selected_file()
        if not src_path:
            ErrorDialog.show(
                self,
                "Restore Error",
                "No backup file selected.\n\nSelect a file in the tree before restoring."
            )
            return

        self.restore_mgr.run_restore(src_path)

    def on_quit(self, event):
        self.Close(True)


class EspRestoreApp(wx.App):
    def OnInit(self):
        ini_mgr = IniManager()
        frame = MainFrame(ini_mgr)
        frame.Show()
        return True


if __name__ == "__main__":
    app = EspRestoreApp(False)
    app.MainLoop()
