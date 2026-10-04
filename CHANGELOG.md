# ESPRestore — CHANGELOG
Versioning Format: MAJOR.MINOR.PATCH  
Author: Chris Anderson  
Project Start: October 2026

---

## [1.0.0] — 2026-10-04
### Initial Release
- Introduced ESPRestore as a standalone Starfield mod backup/restore utility.
- Added automatic ESP (source code) backup system.
  - Per‑mod folders created automatically.
  - Timestamped backups.
  - Keeps last 10 backups per mod.
- Added automatic ESM (compiled output) archival.
  - Stored in BackupPath\PublishedPath.
  - Only newest version retained.
  - Not shown in UI, not restorable.
- Implemented full INI configuration system:
  - BackupPath
  - RestorePath
  - Identifier (match anywhere in filename)
  - PublishedPath (folder name only)
- Added Settings dialog for editing INI values.
- Added Backup button (ESP + ESM logic).
- Added Restore button (ESP only).
- Added Quit button.
- Added TreeView panel for browsing ESP backups.
- Added error dialog system.
- Added Published folder behavior documentation.
- Added ESPRestore.md combined README + User Manual.

---

## [1.0.1] — 2026-10-04
### Documentation Improvements
- Updated ESPRestore.md to clarify:
  - ESM files are **not** restored.
  - ESM files do **not** appear in the TreeView.
  - Published folder is archival only.
- Improved installation section:
  - Added recommended `C:\Tools\ESPRestore\` workflow.
  - Clarified PATH usage.
- Cleaned formatting and indentation across the manual.

---

## [1.0.2] — 2026-10-04
### Codebase Cleanup
- Converted all header blocks to raw triple‑quoted strings (`r""" ... """`) to eliminate Pylance escape warnings.
- Minor comment and formatting corrections across modules.
- Updated restore logic documentation to match UI behavior.

---

## Planned Features (Future)
### Not yet scheduled
- Optional logging module (debug + verbose modes).
- Version tagging for backups.
- “Compare ESP to previous backup” diff viewer. - Maybe
- Exportable backup manifest.

