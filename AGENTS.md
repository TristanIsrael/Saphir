# Project overview

Saphir is a **sheep-dip**: a secure workstation that scans external media (USB disks) for malware before they enter the organization's network. It is built on **Safecor**, a multi-domain (multi-VM) operating system for security products, and runs on **Alpine Linux** (v3.20/3.21), distributed as a bootable ISO.

## Key functions

- Scan a whole USB disk, or a selected partition/files, via **multiple antivirus engines with a consensus verdict**: a file is infected if *any* engine flags it; clean only when all agree (`ANTIVIRUS_NEEDED = 2`).
- Copy only clean files to a second external disk.
- Generate a **PDF scan report** (Jinja2 + WeasyPrint) and copy it with the journal to the target disk.
- **Viewer**: a separate read-only file/preview browser (images, video, audio, Office, PDF) with Office→PDF conversion via LibreOffice; swappable with the main GUI on the same screen.
- Full system state machine: boot → analyze → copy → report → reset/shutdown, with an EMA-based remaining-time estimate.

## Tech stack

| Layer | Technologies |
|---|---|
| Language | Python 3.9+ (core); minimal C++ Qt (Viewer scaffold, 3D test) |
| GUI | PySide6 (Qt 6) + QML, Material Design, bilingual EN/FR, kiosk mode |
| Antivirus | ClamAV (`clamdscan`) + ESET Endpoint (in a trimmed LXC container) |
| Communication | MQTT via the Safecor API; custom protocol `saphir/analysis/{request,response,status,stop,resume,reset}` |
| Architecture | Multi-VM isolated domains (GUI, ClamAV, ESET); event-driven; MVVM (QObject signals ↔ QML); Template Method for AV controllers; bounded queue + worker pool |
| Packaging | Alpine `APKBUILD` packages (abuild), PyInstaller binaries, signed APK repo, bootable ISO (mkimg/apkovl) |
| CI/CD | GitHub Actions: change detection → `abuild` in an `alpine:3.21` container → rsync publish to the official repo |
| Dev | Local Docker (Alpine + APK repo), `DEVMODE` with mocks (no appliance needed), pytest, Doxygen |

## Repository structure

```
python/
├── gui/         # Main GUI app (entry: src/Saphir/main.py)
├── viewer/      # File viewer app (entry: src/viewer/main.py)
└── libsaphir/   # Shared library: AV controllers (Clam, ESET), enums, constants
setup/
├── packages/    # 8 APKBUILD packages (core, lib, gui, viewer, splash, av-clamav, av-eset, container-eset)
├── iso/         # Bootable ISO build
└── docker/      # Local dev environment
.github/         # CI/CD (build-all.yml)
docs/            # Developer + user documentation
```

## Key code locations

- Main entry point: `python/gui/src/Saphir/main.py` → `ApplicationController.start()` (connects MQTT + Safecor API, loads `MainScreen.qml`).
- Central controller: `python/gui/src/Saphir/Saphir/application_controller.py` (mediator between the Safecor platform and the QML UI, owns the state machine).
- Analysis orchestration: `python/gui/src/Saphir/Saphir/analysis_controller.py`; consensus rule in `analysis_helper.py`.
- AV controllers: `python/libsaphir/src/libsaphir/` (`_abstract_antivirus_controller.py`, `_clam_antivirus_controller.py`, `_eea_antivirus_controller.py`).
- Viewer backend: `python/viewer/src/viewer/Viewer/application_controller.py`.

# Project rules

## Coding standards

- Follow the existing naming conventions

## Chat rules

- Respond in the same language as the prompt's
- Never commit or push unless explicitly asked to do so

## Documentation standards

- Write documentation, comments and commits in english language even if the prompt is in another language.
- Update the documentation in /docs and the Doxygen comments of the source code up to date when applying changes.
- The Doxygen documentation must be written only in the implementation files unless the function is encoded in the header file.
- Keep `Readme.md` ("Current features") and `docs/manual.md` in sync with user-visible changes.
- Keep `README.fr.md` (French language) and `README.md` (English language) in sync together.