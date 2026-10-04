# ***********************************************************************
r"""
Module Name : backup_manager.py
Author      : Chris Anderson
Create Date : 2026-10-04
Description : Handles ESP + ESM backup operations.

Rules:
    - ESP files (source code):
        * Identifier may appear ANYWHERE in filename
        * Backed up into per-mod folders
        * Keep last 10 backups per mod
        * Timestamp appended: .YYYYMMDDHHMMSS

    - ESM files (compiled/published):
        * Identifier may appear ANYWHERE in filename
        * Backed up into BackupPath\PublishedPath
        * Keep ONLY the newest version
        * Timestamp appended: .YYYYMMDDHHMMSS

"""
# ***********************************************************************

import os
import shutil
from datetime import datetime

from dialogs.error_dialog import ErrorDialog


class BackupManager:
    def __init__(self, ini_mgr, parent_window):
        self.ini = ini_mgr
        self.parent = parent_window

    # ------------------------------------------------------------------

    def run_backup(self):
        restore_path = self.ini.restore_path
        backup_path = self.ini.backup_path
        ident = self.ini.identifier.lower()
        published_full = self.ini.get_published_full_path()

        if not os.path.isdir(restore_path):
            ErrorDialog.show(
                self.parent,
                "Backup Error",
                f"RestorePath does not exist:\n{restore_path}"
            )
            return

        os.makedirs(backup_path, exist_ok=True)
        os.makedirs(published_full, exist_ok=True)

        files = os.listdir(restore_path)
        esp_files = [f for f in files if f.lower().endswith(".esp") and ident in f.lower()]
        esm_files = [f for f in files if f.lower().endswith(".esm") and ident in f.lower()]

        # Backup ESP (source)
        for esp in esp_files:
            self._backup_esp(restore_path, backup_path, esp)

        # Backup ESM (published)
        for esm in esm_files:
            self._backup_esm(restore_path, published_full, esm)

    # ------------------------------------------------------------------
    # ESP BACKUP
    # ------------------------------------------------------------------

    def _backup_esp(self, restore_path, backup_path, filename):
        src = os.path.join(restore_path, filename)

        base_name = os.path.splitext(filename)[0]
        mod_folder = os.path.join(backup_path, base_name)
        os.makedirs(mod_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        dst_name = f"{filename}.{timestamp}"
        dst = os.path.join(mod_folder, dst_name)

        shutil.copy2(src, dst)

        # Keep last 10 backups
        self._trim_old_backups(mod_folder, keep=10)

    # ------------------------------------------------------------------
    # ESM BACKUP (Published)
    # ------------------------------------------------------------------

    def _backup_esm(self, restore_path, published_full, filename):
        src = os.path.join(restore_path, filename)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        dst_name = f"{filename}.{timestamp}"
        dst = os.path.join(published_full, dst_name)

        shutil.copy2(src, dst)

        # Keep ONLY newest
        self._trim_old_backups(published_full, keep=1)

    # ------------------------------------------------------------------

    def _trim_old_backups(self, folder, keep):
        files = sorted(
            os.listdir(folder),
            key=lambda f: os.path.getmtime(os.path.join(folder, f)),
            reverse=True
        )

        for old in files[keep:]:
            try:
                os.remove(os.path.join(folder, old))
            except Exception:
                pass
