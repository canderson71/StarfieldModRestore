# ***********************************************************************
"""
Module Name : vprtech_mod_restore.py
Author      : Chris Anderson
Create Date : 2026-09-28
Description : Simple wxPython utility to browse VPRTech Starfield mod
              backups and restore a selected .esp into the Starfield
              Data folder, overwriting the existing file.
This file is Copyright Chris Anderson (c) 2026
"""
# ***********************************************************************

import datetime
import os
import shutil
import datetime
import os
import traceback
import win32com.client
import wx

# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------

BACKUP_ROOT = r"C:\Users\chris\Mod-Backup"
BACKUP_FOLDER_PREFIX = "VPRTech_"
STARFIELD_DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Starfield\Data"


# -----------------------------------------------------------------------
# Common error dialog
# -----------------------------------------------------------------------

class ErrorDialog(wx.MessageDialog):
    """
    ErrorDialog: Shows a human-readable error message with optional details.
    """

    def __init__(self, parent, message, details=None):
        full_msg = message
        if details:
            full_msg += f"\n\nDetails:\n{details}"
        super().__init__(
            parent,
            full_msg,
            "Error",
            style=wx.OK | wx.ICON_ERROR
        )


def show_error(parent, user_message, exc=None):
    """
    show_error: Helper to display errors with a clear explanation.
    """
    details = None
    if exc:
        details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    dlg = ErrorDialog(parent, user_message, details)
    dlg.ShowModal()
    dlg.Destroy()


# -----------------------------------------------------------------------
# Main frame
# -----------------------------------------------------------------------

class VPRTechModRestoreFrame(wx.Frame):
    """
    VPRTechModRestoreFrame: Main window with tree (left), details (right),
    and Restore/Quit buttons.
    """

    def __init__(self, parent=None, title="VPRTech Starfield Mod Restore"):
        super().__init__(parent, title=title, size=(900, 600))
        self._selected_file_path = None

        self._init_ui()
        self._center_on_screen()
        self._populate_tree()

    def _init_ui(self):
        """
        _init_ui: Build the splitter, tree, details pane, and buttons.
        """
        panel = wx.Panel(self)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Splitter for left/right panes
        splitter = wx.SplitterWindow(panel, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(150)

        # Left: Tree
        self.tree = wx.TreeCtrl(
            splitter,
            style=wx.TR_HAS_BUTTONS | wx.TR_SINGLE | wx.TR_HIDE_ROOT
        )

        # Right: Details text box (read-only, multi-line)
        self.details_text = wx.TextCtrl(
            splitter,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        )

        splitter.SplitVertically(self.tree, self.details_text, sashPosition=300)

        # Buttons under panes
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_restore = wx.Button(panel, label="Restore")
        self.btn_quit = wx.Button(panel, label="Quit")

        btn_sizer.AddStretchSpacer(1)
        btn_sizer.Add(self.btn_restore, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_quit, 0, wx.ALL, 5)

        main_sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        panel.SetSizer(main_sizer)

        # Events
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_tree_selection_changed)
        self.btn_restore.Bind(wx.EVT_BUTTON, self._on_restore_clicked)
        self.btn_quit.Bind(wx.EVT_BUTTON, self._on_quit_clicked)

    def _center_on_screen(self):
        """
        _center_on_screen: Center the frame on the current display.
        """
        self.Centre()

    def _populate_tree(self):
        """
        _populate_tree: Build the tree from BACKUP_ROOT and VPR_Tech_ folders.
        """
        try:
            if not os.path.isdir(BACKUP_ROOT):
                raise FileNotFoundError(f"Backup root not found: {BACKUP_ROOT}")

            root = self.tree.AddRoot("Starfield_Mods")

            # Find folders starting with VPR_Tech_
            folder_names = [
                name for name in os.listdir(BACKUP_ROOT)
                if os.path.isdir(os.path.join(BACKUP_ROOT, name))
                and name.startswith(BACKUP_FOLDER_PREFIX)
            ]
            folder_names.sort()

            for folder_name in folder_names:
                folder_path = os.path.join(BACKUP_ROOT, folder_name)
                folder_item = self.tree.AppendItem(root, folder_name)

                # List files (max 10, sorted ascending by name)
                file_names = [
                    f for f in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, f))
                ]
                file_names.sort()
                file_names = file_names[:10]

                for file_name in file_names:
                    file_path = os.path.join(folder_path, file_name)
                    child_item = self.tree.AppendItem(folder_item, file_name)
                    # Store full path in item data
                    self.tree.SetItemData(child_item, file_path)

                # Start collapsed
                self.tree.Collapse(folder_item)

        except Exception as exc:
            show_error(
                self,
                "Error building Starfield_Mods tree.\n"
                "Verify the backup folder exists and is accessible.",
                exc
            )

    def _on_tree_selection_changed(self, event):
        """
        _on_tree_selection_changed: When a file is selected, show its details.
        """
        item = event.GetItem()
        if not item.IsOk():
            self._selected_file_path = None
            self.details_text.SetValue("")
            return

        data = self.tree.GetItemData(item)
        if data is None:
            # Folder node
            self._selected_file_path = None
            self.details_text.SetValue("")
            return

        file_path = data
        self._selected_file_path = file_path

        try:
            self._update_details_for_file(file_path)
        except Exception as exc:
            show_error(
                self,
                "Unable to read file details.\n"
                "Verify the file is accessible.",
                exc
            )

    def _update_details_for_file(self, file_path):
        """
        _update_details_for_file: Show full Windows Properties > Details metadata.
        Works on Python 3.11.9 + wxPython 3.x.
        """

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Selected path is not a file: {file_path}")

        stat = os.stat(file_path)

        # Basic info
        created  = datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        accessed = datetime.datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S")

        lines = []
        lines.append(f"File Name: {os.path.basename(file_path)}")
        lines.append(f"Full Path: {file_path}")
        lines.append(f"Size: {stat.st_size} bytes")
        lines.append(f"Created: {created}")
        lines.append(f"Modified: {modified}")
        lines.append(f"Accessed: {accessed}")
        lines.append("")

        # Windows Shell extended metadata (Properties > Details)
        try:
            shell = win32com.client.Dispatch("Shell.Application")
            folder = shell.NameSpace(os.path.dirname(file_path))
            item = folder.ParseName(os.path.basename(file_path))

            # Windows exposes ~300 possible metadata fields (0–287)
            for i in range(0, 288):
                key = folder.GetDetailsOf(None, i)
                value = folder.GetDetailsOf(item, i)
                if key and value:
                    lines.append(f"{key}: {value}")

        except Exception as exc:
            lines.append("")
            lines.append("Extended metadata unavailable.")
            lines.append(f"Reason: {exc}")

        self.details_text.SetValue("\n".join(lines))


    def _on_restore_clicked(self, event):
        """
        _on_restore_clicked: Copy selected backup file into Starfield Data,
        stripping timestamp and overwriting the .esp.
        """
        if not self._selected_file_path:
            show_error(
                self,
                "No file selected.\nSelect a backup file in the Starfield_Mods tree before restoring."
            )
            return

        src_path = self._selected_file_path

        try:
            if not os.path.isfile(src_path):
                raise FileNotFoundError(f"Selected file not found: {src_path}")

            if not os.path.isdir(STARFIELD_DATA):
                raise FileNotFoundError(f"Starfield Data folder not found: {STARFIELD_DATA}")

            base_name = os.path.basename(src_path)

            # Strip everything to the right of ".esp"
            esp_index = base_name.lower().find(".esp")
            if esp_index == -1:
                raise ValueError(
                    "Selected file does not contain '.esp' in its name.\n"
                    "Expected format: VPRTech_Something.esp.YYYYMMDDHHMMSS"
                )

            dest_file_name = base_name[:esp_index + 4]  # include ".esp"
            dest_path = os.path.join(STARFIELD_DATA, dest_file_name)

            # Perform copy (overwrite)
            shutil.copy2(src_path, dest_path)

            wx.MessageBox(
                f"Restore completed.\n\nSource:\n{src_path}\n\nDestination:\n{dest_path}",
                "Restore Successful",
                style=wx.OK | wx.ICON_INFORMATION,
                parent=self
            )

        except PermissionError as exc:
            show_error(
                self,
                "Error 34000fc has occurred.\n"
                "File was unable to copy due to a permissions issue.\n"
                "Verify the Creation Kit or Starfield is not currently running\n"
                "and that you have write access to the Starfield Data folder.",
                exc
            )
        except Exception as exc:
            show_error(
                self,
                "An unexpected error occurred while restoring the file.\n"
                "Restore did not complete.",
                exc
            )

    def _on_quit_clicked(self, event):
        """
        _on_quit_clicked: Exit the program smoothly.
        """
        self.Close()


# -----------------------------------------------------------------------
# Application bootstrap
# -----------------------------------------------------------------------

class VPRTechModRestoreApp(wx.App):
    """
    VPRTechModRestoreApp: wxPython application wrapper.
    """

    def OnInit(self):
        frame = VPRTechModRestoreFrame()
        frame.Show()
        self.SetTopWindow(frame)
        return True


def main():
    """
    main: Entry point for the VPRTech mod restore utility.
    """
    app = VPRTechModRestoreApp(False)
    app.MainLoop()


if __name__ == "__main__":
    main()
