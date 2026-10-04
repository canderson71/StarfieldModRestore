# ***********************************************************************
"""
Module Name : ini_manager.py
Author      : Chris Anderson
Create Date : 2026-10-04
Description : Handles loading, saving, and updating espr.ini settings.

INI fields:
    BackupPath     - Where ESP backups and Published folder live
    RestorePath    - Where Starfield ESP source files live
    Identifier     - Match string (anywhere in filename)
    PublishedPath  - Folder name only (joined with BackupPath)

Default Published folder:
    BackupPath + "\\" + PublishedPath

"""
# ***********************************************************************

import os
import configparser
import sys


INI_NAME = "espr.ini"
INI_SECTION = "ESPR"


class IniManager:
    def __init__(self):
        self.config = configparser.ConfigParser()

        # Default values
        self.backup_path = r"C:\Users\chris\Mod-Backup"
        self.restore_path = r"C:\Program Files (x86)\Steam\steamapps\common\Starfield\Data"
        self.identifier = "VPRTech"
        self.published_path = "Published"   # folder name only

        self._load_or_create()

    # ------------------------------------------------------------------

    def _load_or_create(self):
        if os.path.exists(INI_NAME):
            try:
                self.config.read(INI_NAME)

                if self.config.has_section(INI_SECTION):
                    self.backup_path = self.config.get(INI_SECTION, "BackupPath", fallback=self.backup_path)
                    self.restore_path = self.config.get(INI_SECTION, "RestorePath", fallback=self.restore_path)
                    self.identifier = self.config.get(INI_SECTION, "Identifier", fallback=self.identifier)
                    self.published_path = self.config.get(INI_SECTION, "PublishedPath", fallback=self.published_path)
                else:
                    self._save()

            except Exception:
                # Corrupt INI → recreate cleanly
                self._save()

        else:
            # Missing INI → create with defaults
            self._save()

    # ------------------------------------------------------------------

    def get_resource_path(self, relative_path: str) -> str:
        if getattr(sys, 'frozen', False):
            base_path: str = sys._MEIPASS  # type: ignore[attr-defined]
        else:
            base_path: str = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    def _save(self):
        if not self.config.has_section(INI_SECTION):
            self.config.add_section(INI_SECTION)

        self.config.set(INI_SECTION, "BackupPath", self.backup_path)
        self.config.set(INI_SECTION, "RestorePath", self.restore_path)
        self.config.set(INI_SECTION, "Identifier", self.identifier)
        self.config.set(INI_SECTION, "PublishedPath", self.published_path)

        with open(INI_NAME, "w") as f:
            self.config.write(f)

    # ------------------------------------------------------------------

    def update(self, backup_path, restore_path, identifier, published_path):
        self.backup_path = backup_path
        self.restore_path = restore_path
        self.identifier = identifier
        self.published_path = published_path
        self._save()

    # ------------------------------------------------------------------

    def get_published_full_path(self):
        """Return BackupPath + PublishedPath (folder name only)."""
        return os.path.join(self.backup_path, self.published_path)
