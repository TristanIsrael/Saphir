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
| Language | Python 3.9+ (core); minimal C++ Qt (Viewer Qt Studio scaffold: `main.cpp` + QML) |
| GUI | PySide6 (Qt 6) + QML, Material Design, bilingual EN/FR, kiosk mode |
| Antivirus | ClamAV (`clamdscan`) + ESET Endpoint (in a trimmed LXC container) |
| Communication | MQTT via the Safecor API (`from safecor import Api, Topics`); custom protocol `saphir/analysis/{request,response,status,error,stop,resume,reset}` |
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
├── packages/       # 8 APKBUILD packages (core, lib, gui, viewer, splash, av-clamav, av-eset, container-eset)
├── iso/            # Bootable ISO build (mkimg/apkovl)
├── infrastructure/ # Alpine/Safecor/Saphir repo sync scripts
└── docker/         # Local dev environment (Alpine + APK repo)
.github/         # CI/CD (build-all.yml)
docs/            # Developer + user documentation
```

## Key code locations

- Main entry point: `python/gui/src/Saphir/main.py` → `ApplicationController.start()` (connects MQTT + Safecor API, loads `MainScreen.qml`).
- Central controller: `python/gui/src/Saphir/Saphir/application_controller.py` (mediator between the Safecor platform and the QML UI, owns the state machine).
- Analysis orchestration: `python/gui/src/Saphir/Saphir/analysis_controller.py`; consensus rule in `analysis_helper.py`.
- AV controllers: `python/libsaphir/src/libsaphir/` (`_abstract_antivirus_controller.py`, `_clam_antivirus_controller.py`, `_eea_antivirus_controller.py`).
- Multi-VM topology: `setup/packages/saphir/saphir/topology.json` (defines the three Safecor domains `saphir-gui`, `saphir-av-clamav`, `saphir-av-eset` + hardware profiles).
- PDF scan report: `python/gui/src/Saphir/Saphir/report_controller.py` (Jinja2 templates in `Saphir/templates/`, rendered with WeasyPrint).
- Remaining-time estimate: `python/gui/src/Saphir/Saphir/EMA_ETA_estimator.py` (exponential moving average).
- Viewer backend: `python/viewer/src/viewer/Viewer/application_controller.py`.

# Project rules

## Build

- Versioning rule (scheme `MAJOR.MINOR.PATCH`, e.g. `2.2.0`):
  - A bug fix bumps the last digit (patch) only.
  - A new feature bumps the second digit (minor) and resets the last digit to 0.
  - The first digit (major) is bumped only by the product maintainer.
- The python dependencies that are used only in development and tests must lie in the file requirements-dev.txt.
- The python dependencies that are used in production, in developpement and tests must lie in the file requirements.txt.

## Coding standards

- Follow the existing naming conventions. The codebase is the reference; when in doubt, match the surrounding code.

Naming conventions:

| Domain | Convention | Examples |
|---|---|---|
| Python — classes | `PascalCase` | `ApplicationController`, `EMAETAEstimator` |
| Python — methods / variables | `snake_case` | `start_transfer`, `remaining_time` |
| Python — private methods | double-underscore (name mangling) | `__set_system_state`, `__handle_disk_state` |
| Python — constants | `UPPER_SNAKE` | `ANTIVIRUS_NEEDED`, `TOPIC_ANALYSIS`, `DEVMODE` |
| Python — enums | `PascalCase` (no underscores) | `SystemAnalysisRunning`, `FileClean` |
| QML — components | `PascalCase` | `AnalysisPanel`, `FilesSelectionPanel` |
| QML — properties / bindings | `camelCase` | `systemState`, `queueSize`, `nbClean` |
| MQTT topics | `saphir/analysis/{request,response,status,error,stop,resume,reset}`; `system/...` | — |

- Comments, documentation and commits are in **English** (see *Documentation standards*).

## Chat rules

- Respond in the same language as the prompt's
- Never commit or push unless explicitly asked to do so

## Documentation standards

- Write documentation, comments and commits in english language even if the prompt is in another language.
- Update the documentation in /docs and the Doxygen comments of the source code up to date when applying changes.
- Keep `Readme.md` ("Current features") and `docs/manual.md` in sync with user-visible changes.
- Keep `README.fr.md` (French language) and `README.md` (English language) in sync together.
- Use the documentation from **Safecor** to adapt the behaviour of Saphir.
- All the interactions of Saphir and Safecor must use Safecor's API.
