# ***********************************************************************
"""
Module Name : esp_restore.py
Author      : Chris Anderson
Create Date : 2026-10-04
Description : Simple wxPython utility to manage Starfield ESP backups.
              - Shows backup folders/files in a TreeView
              - Displays file details in a right-hand pane
              - Restores selected backup to Starfield Data folder
              - Creates backups from Data folder into structured folders
              - Uses espr.ini for paths and identifier configuration
This file is Copyright Chris Anderson (c) 2026
"""
# ***********************************************************************

import os
import shutil
import configparser
from datetime import datetime
from typing import Optional

import wx


INI_NAME = "espr.ini"
INI_SECTION = "ESPR"


class IniManager:
    def __init__(self):
        self.config = configparser.ConfigParser()

        # Default values
        self.backup_path = r"C:\Users\chris\Mod-Backup"
        self.restore_path = r"C:\Program Files (x86)\Steam\steamapps\common\Starfield\Data"
        self.identifier = "VPRTech"

        # Ensure INI exists or load it
        self._load_or_create()

    def _load_or_create(self):
        if os.path.exists(INI_NAME):
            try:
                self.config.read(INI_NAME)
                if self.config.has_section(INI_SECTION):
                    self.backup_path = self.config.get(INI_SECTION, "BackupPath", fallback=self.backup_path)
                    self.restore_path = self.config.get(INI_SECTION, "RestorePath", fallback=self.restore_path)
                    self.identifier = self.config.get(INI_SECTION, "Identifier", fallback=self.identifier)
                else:
                    # INI exists but missing section → recreate cleanly
                    self._save()
            except Exception:
                # Corrupt INI → recreate cleanly
                self._save()
        else:
            # INI missing → create with defaults
            self._save()

    def _save(self):
        if not self.config.has_section(INI_SECTION):
            self.config.add_section(INI_SECTION)

        self.config.set(INI_SECTION, "BackupPath", self.backup_path)
        self.config.set(INI_SECTION, "RestorePath", self.restore_path)
        self.config.set(INI_SECTION, "Identifier", self.identifier)

        with open(INI_NAME, "w") as f:
            self.config.write(f)

    def update(self, backup_path, restore_path, identifier):
        self.backup_path = backup_path
        self.restore_path = restore_path
        self.identifier = identifier
        self._save()


class ErrorDialog:
    @staticmethod
    def show(parent: Optional[wx.Window], title: str, message: str):
        dlg = wx.MessageDialog(parent, message, title, style=wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        

class SettingsDialog(wx.Dialog):
    def __init__(self, parent, ini_mgr):
        super().__init__(parent, title="Settings", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        pnl = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # --- controls created with pnl as parent ---
        self.txt_backup = wx.TextCtrl(pnl, value=ini_mgr.backup_path)
        self.txt_restore = wx.TextCtrl(pnl, value=ini_mgr.restore_path)
        self.txt_identifier = wx.TextCtrl(pnl, value=ini_mgr.identifier)

        grid = wx.FlexGridSizer(3, 2, 5, 5)
        grid.Add(wx.StaticText(pnl, label="Backup Path:"), 0, wx.ALIGN_RIGHT)
        grid.Add(self.txt_backup, 1, wx.EXPAND)
        grid.Add(wx.StaticText(pnl, label="Restore Path:"), 0, wx.ALIGN_RIGHT)
        grid.Add(self.txt_restore, 1, wx.EXPAND)
        grid.Add(wx.StaticText(pnl, label="Identifier:"), 0, wx.ALIGN_RIGHT)
        grid.Add(self.txt_identifier, 1, wx.EXPAND)
        grid.AddGrowableCol(1, 1)

        btn_ok = wx.Button(pnl, wx.ID_OK)
        btn_cancel = wx.Button(pnl, wx.ID_CANCEL)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(btn_ok, 0, wx.ALL, 5)
        btn_sizer.Add(btn_cancel, 0, wx.ALL, 5)

        sizer.Add(grid, 1, wx.ALL | wx.EXPAND, 10)
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        pnl.SetSizer(sizer)

        # --- THIS WAS MISSING ---
        dlg_sizer = wx.BoxSizer(wx.VERTICAL)
        dlg_sizer.Add(pnl, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(dlg_sizer)

        self.SetAffirmativeId(wx.ID_OK)
        self.SetEscapeId(wx.ID_CANCEL)
        
    def apply(self):
        backup = self.txt_backup.GetValue().strip()
        restore = self.txt_restore.GetValue().strip()
        ident = self.txt_identifier.GetValue().strip()
        return backup, restore, ident


class BackupManager:
    def __init__(self, ini_mgr: IniManager, parent):
        self.ini_mgr = ini_mgr
        self.parent = parent

    def _ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    def run_backup(self):
        source_folder = self.ini_mgr.restore_path
        backup_folder = self.ini_mgr.backup_path
        identifier = self.ini_mgr.identifier

        try:
            self._ensure_dir(backup_folder)
        except Exception as e:
            ErrorDialog.show(self.parent, "Backup Error",
                             f"Error creating backup folder.\n\nDetails: {e}")
            return

        try:
            for entry in os.scandir(source_folder):
                if not entry.is_file():
                    continue
                if not entry.name.lower().endswith(".esp"):
                    continue

                base_name = os.path.splitext(entry.name)[0]  # e.g. VPRTech_ShipHabs01
                if not base_name.startswith(identifier):
                    continue

                file_backup_folder = os.path.join(backup_folder, base_name)
                self._ensure_dir(file_backup_folder)

                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                backup_name = f"{base_name}.esp.{timestamp}"
                backup_path = os.path.join(file_backup_folder, backup_name)

                # Get existing backups
                backups = sorted(
                    [f for f in os.scandir(file_backup_folder) if f.is_file() and f.name.startswith(base_name + ".esp.")],
                    key=lambda f: f.stat().st_mtime
                )

                needs_backup = True
                if backups:
                    latest = backups[-1]
                    latest_time = latest.stat().st_mtime
                    src_time = entry.stat().st_mtime
                    if src_time <= latest_time:
                        needs_backup = False

                if needs_backup:
                    shutil.copy2(entry.path, backup_path)

                    # Keep only latest 10
                    backups = sorted(
                        [f for f in os.scandir(file_backup_folder) if f.is_file() and f.name.startswith(base_name + ".esp.")],
                        key=lambda f: f.stat().st_mtime
                    )
                    if len(backups) > 10:
                        for old in backups[:-10]:
                            try:
                                os.remove(old.path)
                            except Exception:
                                # Non-fatal
                                pass

            wx.MessageBox("Backup complete.", "Backup", wx.OK | wx.ICON_INFORMATION)
        except PermissionError:
            ErrorDialog.show(self.parent, "Backup Error",
                             "Backup failed due to a permissions issue.\n"
                             "Verify Starfield CK and Starfield are not currently running.")
        except FileNotFoundError:
            ErrorDialog.show(self.parent, "Backup Error",
                             "Backup failed because one or more paths were not found.\n"
                             "Verify the Restore and Backup paths in Settings.")
        except Exception as e:
            ErrorDialog.show(self.parent, "Backup Error",
                             f"An unexpected error occurred during backup.\n\nDetails: {e}")


class TreePanel(wx.Panel):
    def __init__(self, parent, mainframe, ini_mgr: IniManager, details_ctrl: wx.TextCtrl):
        super().__init__(parent)
        self.mainframe = mainframe
        self.ini_mgr = ini_mgr
        self.details_ctrl = details_ctrl
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.tree = wx.TreeCtrl(self, style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT)
        sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

        self.root = self.tree.AddRoot("Starfield_Mods")
        self._populate_tree()
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_selection_changed)

    def _populate_tree(self):
        self.tree.DeleteChildren(self.root)
        backup_path = self.ini_mgr.backup_path
        identifier = self.ini_mgr.identifier

        if not os.path.isdir(backup_path):
            return

        matches = 0

        try:
            for entry in sorted(os.scandir(backup_path), key=lambda e: e.name.lower()):
                if not entry.is_dir():
                    continue
                if not entry.name.startswith(identifier + "_"):
                    continue

                matches += 1

                parent_node = self.tree.AppendItem(self.root, entry.name)
                files = sorted(
                    [f for f in os.scandir(entry.path)
                    if f.is_file() and f.name.lower().endswith(".esp.")],
                    key=lambda f: f.name.lower()
                )

                for f in files:
                    child = self.tree.AppendItem(parent_node, f.name)
                    self.tree.SetItemData(child, f.path)

                self.tree.Collapse(parent_node)

            if matches == 0:
                self.details_ctrl.SetValue(f"No results found with Identifier: {identifier}")
            else:
                self.details_ctrl.SetValue("")

        except Exception as e:
            ErrorDialog.show(self, "Tree Error",
                            f"Error populating tree from backup path.\n\nDetails: {e}")

    def on_selection_changed(self, event):
        item = event.GetItem()
        path = self.tree.GetItemData(item)
        if not path:
            self.details_ctrl.SetValue("")
            return

        try:
            st = os.stat(path)
            lines = [
                f"File: {os.path.basename(path)}",
                f"Full Path: {path}",
                f"Size: {st.st_size} bytes",
                f"Created: {datetime.fromtimestamp(st.st_ctime)}",
                f"Modified: {datetime.fromtimestamp(st.st_mtime)}",
            ]
            self.details_ctrl.SetValue("\n".join(lines))
        except Exception as e:
            ErrorDialog.show(self, "Details Error",
                             f"Unable to read file details.\n\nDetails: {e}")
            self.details_ctrl.SetValue("")


class MainFrame(wx.Frame):
    def __init__(self, ini_mgr: IniManager):
        super().__init__(None, title="ESP Restore", size=(wx.Size(900, 600)))
        self.ini_mgr = ini_mgr

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        splitter = wx.SplitterWindow(panel, style=wx.SP_LIVE_UPDATE)
        left_panel = wx.Panel(splitter)
        right_panel = wx.Panel(splitter)

        right_sizer = wx.BoxSizer(wx.VERTICAL)
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        self.txt_details = wx.TextCtrl(right_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        right_sizer.Add(self.txt_details, 1, wx.EXPAND | wx.ALL, 5)
        right_panel.SetSizer(right_sizer)
             
        self.tree_panel = TreePanel(left_panel, self, self.ini_mgr, self.txt_details)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(self.tree_panel, 1, wx.EXPAND | wx.ALL, 5)
        left_panel.SetSizer(left_sizer)

        splitter.SplitVertically(left_panel, right_panel, sashPosition=300)

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

        self.backup_mgr = BackupManager(self.ini_mgr, self)

        self.btn_settings.Bind(wx.EVT_BUTTON, self.on_settings)
        self.btn_backup.Bind(wx.EVT_BUTTON, self.on_backup)
        self.btn_restore.Bind(wx.EVT_BUTTON, self.on_restore)
        self.btn_quit.Bind(wx.EVT_BUTTON, self.on_quit)

    def _get_selected_file(self):
        item = self.tree_panel.tree.GetSelection()
        if not item.IsOk():
            return None
        path = self.tree_panel.tree.GetItemData(item)
        return path

    def on_settings(self, event):
        dlg = SettingsDialog(self, self.ini_mgr)
        if dlg.ShowModal() == wx.ID_OK:
            backup, restore, ident = dlg.apply()
            self.ini_mgr.update(backup, restore, ident)
            self.tree_panel._populate_tree()
        dlg.Destroy()

    def on_backup(self, event):
        self.backup_mgr.run_backup()
        self.tree_panel._populate_tree()

    def on_restore(self, event):
        src_path = self._get_selected_file()
        if not src_path:
            ErrorDialog.show(self, "Restore Error",
                             "No backup file selected.\n\nSelect a file in the tree before restoring.")
            return

        try:
            filename = os.path.basename(src_path)
            # Strip everything to the right of ".esp"
            if ".esp" not in filename.lower():
                ErrorDialog.show(self, "Restore Error",
                                 "Selected file does not appear to be a valid ESP backup.")
                return

            base_part = filename[:filename.lower().find(".esp")] + ".esp"
            dest_path = os.path.join(self.ini_mgr.restore_path, base_part)

            shutil.copy2(src_path, dest_path)

            wx.MessageBox(f"Restored:\n{base_part}\n\nto:\n{self.ini_mgr.restore_path}",
                          "Restore", wx.OK | wx.ICON_INFORMATION)
        except PermissionError:
            ErrorDialog.show(self, "Restore Error",
                             "Restore failed due to a permissions issue.\n"
                             "Verify Starfield CK and Starfield are not currently running.")
        except FileNotFoundError:
            ErrorDialog.show(self, "Restore Error",
                             "Restore failed because one or more paths were not found.\n"
                             "Verify the Restore and Backup paths in Settings.")
        except Exception as e:
            ErrorDialog.show(self, "Restore Error",
                             f"An unexpected error occurred during restore.\n\nDetails: {e}")

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
