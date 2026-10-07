# ***********************************************************************
"""
Module Name : restore_manager.py
Author      : Chris Anderson
Create Date : 2026-10-04
Description : Handles restoring ESP backups (source code only).

Rules:
    - Restore ONLY applies to ESP backups.
    - ESM files (Published) are NOT restorable.
    - Selected file is copied back into RestorePath.
"""
# ***********************************************************************

import os
import shutil

from dialogs.error_dialog import ErrorDialog


class RestoreManager:
    def __init__(self, ini_mgr, parent_window):
        self.ini = ini_mgr
        self.parent = parent_window

    # ------------------------------------------------------------------

    def run_restore(self, src_path):
        """Restore the selected ESP backup file."""
        if not src_path:
            ErrorDialog.show(
                self.parent,
                "Restore Error",
                "No backup file selected."
            )
            return

        restore_path = self.ini.restore_path

        if not os.path.isdir(restore_path):
            ErrorDialog.show(
                self.parent,
                "Restore Error",
                f"RestorePath does not exist:\n{restore_path}"
            )
            return

        # ESP only — reject ESM
        if src_path.lower().endswith(".esm") or ".esm." in src_path.lower():
            ErrorDialog.show(
                self.parent,
                "Restore Error",
                "ESM files cannot be restored.\n\n"
                "They are published output, not source code."
            )
            return

        # Determine destination filename (strip timestamp)
        filename = os.path.basename(src_path)
        base_name = filename.split(".")[0] + ".esp"
        dst_path = os.path.join(restore_path, base_name)

        try:
            shutil.copy2(src_path, dst_path)
        except Exception as e:
            ErrorDialog.show(
                self.parent,
                "Restore Error",
                f"Failed to restore file:\n{e}"
            )
            return
        
        # SUCCESS MESSAGE
        ErrorDialog.show(
            self.parent,
            "Restore Complete",
            f'File "{base_name}" was restored.'
        )
